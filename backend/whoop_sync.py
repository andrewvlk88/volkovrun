# סנכרון Whoop API v2 + HR timeseries
import os, requests, json, sqlite3
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from db import get_conn

load_dotenv(override=True)

CLIENT_ID = os.getenv("WHOOP_CLIENT_ID", "8eacd401-66dc-4bc5-8d1f-149f25823a99")
CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET", "")
ACCESS_TOKEN = os.getenv("WHOOP_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.getenv("WHOOP_REFRESH_TOKEN", "")
BASE = "https://api.prod.whoop.com/developer/v2"


def _headers():
    return {
        "Authorization": f"Bearer {os.getenv('WHOOP_ACCESS_TOKEN', ACCESS_TOKEN)}",
        "Accept": "application/json",
    }


def refresh_token():
    """Refresh access token using refresh token."""
    global ACCESS_TOKEN
    rt = os.getenv("WHOOP_REFRESH_TOKEN", REFRESH_TOKEN)
    if not rt:
        raise ValueError("No refresh token")
    resp = requests.post(
        f"{BASE.replace('/developer/v2','/oauth/oauth2')}/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": rt,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        raise ValueError(f"Token refresh failed: {resp.status_code} {resp.text}")
    tokens = resp.json()
    # Update env
    os.environ["WHOOP_ACCESS_TOKEN"] = tokens["access_token"]
    os.environ["WHOOP_REFRESH_TOKEN"] = tokens.get("refresh_token", "")
    # Update .env files
    _save_tokens(tokens["access_token"], tokens.get("refresh_token", ""))
    print(f"[Whoop] Token refreshed OK")
    return tokens["access_token"]


def _save_tokens(access, refresh):
    """Save tokens to .env files."""
    for path in [os.path.expanduser("~/.hermes/.env"),
                 os.path.join(os.path.dirname(__file__), ".env")]:
        if not os.path.exists(path):
            continue
        lines = []
        with open(path) as f:
            for l in f:
                if l.startswith("WHOOP_ACCESS_TOKEN="):
                    lines.append(f"WHOOP_ACCESS_TOKEN={access}\n")
                elif l.startswith("WHOOP_REFRESH_TOKEN="):
                    lines.append(f"WHOOP_REFRESH_TOKEN={refresh}\n")
                else:
                    lines.append(l)
        with open(path, "w") as f:
            f.writelines(lines)


def _api_get(endpoint, params=None, retry=True):
    """GET with auto-refresh on 401."""
    url = f"{BASE}/{endpoint}"
    resp = requests.get(url, headers=_headers(), params=params or {}, timeout=20)
    if resp.status_code == 401 and retry:
        print("[Whoop] 401 — refreshing token...")
        refresh_token()
        resp = requests.get(url, headers=_headers(), params=params or {}, timeout=20)
    if resp.status_code != 200:
        print(f"[Whoop] {endpoint} returned {resp.status_code}: {resp.text[:200]}")
        return []
    return resp.json().get("records", [])


def sync(days=14):
    """Sync recovery, sleep, cycle, and heart_rate for last N days."""
    print(f"[Whoop] Syncing last {days} days...")
    conn = get_conn()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    start_str = start.strftime("%Y-%m-%dT00:00:00.000Z")
    end_str = end.strftime("%Y-%m-%dT23:59:59.000Z")

    # 1. Recovery
    records = _api_get("recovery", {"start": start_str, "end": end_str, "limit": 25})
    for r in records:
        s = r.get("score", {})
        date = r.get("created_at", "")[:10]
        conn.execute("""INSERT OR REPLACE INTO whoop_recovery 
            (date, recovery_score, resting_heart_rate, hrv_rmssd_ms, spo2_pct, skin_temp_c, day_strain) 
            VALUES (?,?,?,?,?,?,?)""",
            (date, s.get("recovery_score"), s.get("resting_heart_rate"),
             s.get("hrv_rmssd_milli"), s.get("spo2_percentage"),
             s.get("skin_temp_celsius"), r.get("day_strain")))
    print(f"[Whoop] Recovery: {len(records)} records")

    # 2. Sleep
    records = _api_get("activity/sleep", {"start": start_str, "end": end_str, "limit": 25})
    for r in records:
        sc = r.get("score", {})
        ss = sc.get("stage_summary", {})
        date = r.get("created_at", "")[:10]
        conn.execute("""INSERT OR REPLACE INTO whoop_sleep
            (date, start, end, total_sleep_milli, sleep_performance_pct, deep_sleep_milli, rem_sleep_milli, light_sleep_milli)
            VALUES (?,?,?,?,?,?,?,?)""",
            (date, r.get("start"), r.get("end"),
             ss.get("total_sleep_time_milli"), sc.get("sleep_performance_percentage"),
             ss.get("deep_sleep_time_milli"), ss.get("rem_sleep_time_milli"),
             ss.get("light_sleep_time_milli")))
    print(f"[Whoop] Sleep: {len(records)} records")

    # 3. Cycle
    records = _api_get("cycle", {"start": start_str, "end": end_str, "limit": 25})
    for r in records:
        date = (r.get("start") or r.get("created_at") or "")[:10]
        s = r.get("score", {})
        conn.execute("""INSERT OR REPLACE INTO whoop_cycle
            (date, start, end, strain, kilojoule, avg_heart_rate, max_heart_rate)
            VALUES (?,?,?,?,?,?,?)""",
            (date, r.get("start"), r.get("end"), s.get("strain"),
             s.get("kilojoule"), s.get("average_heart_rate"), s.get("max_heart_rate")))
    print(f"[Whoop] Cycle: {len(records)} records")

    # 4. Heart Rate — v1 endpoint, fetch per day
    hr_count = 0
    for d in range(days):
        day = start + timedelta(days=d)
        day_start = day.strftime("%Y-%m-%dT00:00:00.000Z")
        day_end = day.strftime("%Y-%m-%dT23:59:59.000Z")
        # Try v1/metrics/heart_rate first
        url = f"https://api.prod.whoop.com/developer/v1/metrics/heart_rate"
        resp = requests.get(url, headers=_headers(),
                           params={"start": day_start, "end": day_end}, timeout=20)
        if resp.status_code == 401:
            refresh_token()
            resp = requests.get(url, headers=_headers(),
                               params={"start": day_start, "end": day_end}, timeout=20)
        if resp.status_code != 200:
            continue
        records = resp.json().get("records", [])
        date_str = day.strftime("%Y-%m-%d")
        for r in records:
            data = r.get("data", {})
            conn.execute("""INSERT OR IGNORE INTO whoop_heart_rate (ts_utc, hr, date) VALUES (?,?,?)""",
                (data.get("time", date_str), data.get("value", 0), date_str))
            hr_count += 1
    print(f"[Whoop] Heart Rate: {hr_count} records across {days} days")

    conn.commit()
    conn.close()
    print(f"[Whoop] Sync complete ✅")


if __name__ == "__main__":
    sync(14)