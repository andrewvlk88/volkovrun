"""Whoop sync — fetches recovery, sleep, and cycle data from Whoop API v2.

Token management: reads access/refresh tokens from .env, auto-refreshes on 401.
Data stored in whoop_recovery, whoop_sleep, whoop_cycle tables.
"""
import os, json, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db import get_conn

load_dotenv(override=True)

WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v2"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
CLIENT_ID = os.getenv("WHOOP_CLIENT_ID", "8eacd401-66dc-4bc5-8d1f-149f25823a99")
CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET", "172849b0a21982024d9c4e382df9a719d93f764999fe4bd50ee871b4c7d4178a")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def _get_token():
    return os.getenv("WHOOP_ACCESS_TOKEN", "")


def _refresh_token():
    """Refresh the Whoop access token using the refresh token."""
    refresh = os.getenv("WHOOP_REFRESH_TOKEN", "")
    if not refresh:
        raise ValueError("No WHOOP_REFRESH_TOKEN in .env")

    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh,
    }).encode()

    req = urllib.request.Request(WHOOP_TOKEN_URL, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": UA,
    })
    resp = urllib.request.urlopen(req, timeout=20)
    tokens = json.load(resp)

    # Save to .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    lines = []
    found_a = found_r = False
    with open(env_path) as f:
        for line in f:
            if line.startswith("WHOOP_ACCESS_TOKEN"):
                lines.append(f"WHOOP_ACCESS_TOKEN={tokens['access_token']}\n")
                found_a = True
            elif line.startswith("WHOOP_REFRESH_TOKEN"):
                lines.append(f"WHOOP_REFRESH_TOKEN={tokens.get('refresh_token', refresh)}\n")
                found_r = True
            else:
                lines.append(line)
    if not found_a:
        lines.append(f"WHOOP_ACCESS_TOKEN={tokens['access_token']}\n")
    if not found_r:
        lines.append(f"WHOOP_REFRESH_TOKEN={tokens.get('refresh_token', refresh)}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)

    os.environ["WHOOP_ACCESS_TOKEN"] = tokens["access_token"]
    if tokens.get("refresh_token"):
        os.environ["WHOOP_REFRESH_TOKEN"] = tokens["refresh_token"]

    return tokens["access_token"]


def _api_get(endpoint, params=None):
    """Make a GET request to Whoop API, auto-refresh on 401."""
    token = _get_token()
    url = f"{WHOOP_API_BASE}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    def _do(t):
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {t}",
            "Accept": "application/json",
            "User-Agent": UA,
        })
        return urllib.request.urlopen(req, timeout=20)

    try:
        resp = _do(token)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("[Whoop] Token expired, refreshing...")
            new_token = _refresh_token()
            resp = _do(new_token)
        else:
            raise

    return json.load(resp)


def _ensure_tables():
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS whoop_recovery (
      id INTEGER PRIMARY KEY,
      cycle_id INTEGER UNIQUE,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      recovery_score INTEGER,
      resting_heart_rate REAL,
      hrv_rmssd_ms REAL,
      spo2_pct REAL,
      skin_temp_c REAL,
      sleep_need_str INTEGER,
      day_strain REAL,
      raw_json TEXT
    );
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS whoop_sleep (
      id INTEGER PRIMARY KEY,
      sleep_id INTEGER UNIQUE,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      date TEXT,
      sleep_performance_pct REAL,
      sleep_efficiency_pct REAL,
      total_in_bed_milli INTEGER,
      total_awake_milli INTEGER,
      total_sleep_milli INTEGER,
      deep_sleep_milli INTEGER,
      rem_sleep_milli INTEGER,
      light_sleep_milli INTEGER,
      awake_milli INTEGER,
      sleep_need_milli INTEGER,
      raw_json TEXT
    );
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS whoop_cycle (
      id INTEGER PRIMARY KEY,
      cycle_id INTEGER UNIQUE,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      date TEXT,
      strain REAL,
      kilojoule REAL,
      avg_heart_rate INTEGER,
      max_heart_rate INTEGER,
      energy_burned_cal REAL,
      raw_json TEXT
    );
    """)
    conn.commit()
    conn.close()


def _sync_recovery(days=7):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    data = _api_get("recovery", {
        "start": start.strftime("%Y-%m-%dT00:00:00.000Z"),
        "end": end.strftime("%Y-%m-%dT23:59:59.000Z"),
        "limit": 25,
    })
    conn = get_conn()
    count = 0
    for item in data.get("records", []):
        cycle_id = item.get("cycle_id")
        score = item.get("score", {})
        try:
            conn.execute("""
                INSERT OR REPLACE INTO whoop_recovery
                (cycle_id, recovery_score, resting_heart_rate, hrv_rmssd_ms, spo2_pct, skin_temp_c, sleep_need_str, day_strain, raw_json)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                cycle_id,
                score.get("recovery_score"),
                score.get("resting_heart_rate"),
                score.get("hrv_rmssd_milli"),
                score.get("spo2_percentage"),
                score.get("skin_temp_celsius"),
                score.get("sleep_need_quality_seconds_in_inBed"),
                score.get("day_strain"),
                json.dumps(item),
            ))
            count += 1
        except Exception as e:
            print(f"[Whoop] Recovery insert error: {e}")
    conn.commit()
    conn.close()
    return count


def _sync_sleep(days=7):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    data = _api_get("activity/sleep", {
        "start": start.strftime("%Y-%m-%dT00:00:00.000Z"),
        "end": end.strftime("%Y-%m-%dT23:59:59.000Z"),
        "limit": 25,
    })
    conn = get_conn()
    count = 0
    for item in data.get("records", []):
        sleep_id = item.get("id")
        summary = item.get("score", {}).get("stage_summary", {})
        sleeps = item.get("score", {}).get("stage_summary", {})
        need = item.get("score", {}).get("sleep_needed", {})
        try:
            conn.execute("""
                INSERT OR REPLACE INTO whoop_sleep
                (sleep_id, date, sleep_performance_pct, sleep_efficiency_pct,
                 total_in_bed_milli, total_awake_milli, total_sleep_milli,
                 deep_sleep_milli, rem_sleep_milli, light_sleep_milli, awake_milli,
                 sleep_need_milli, raw_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                sleep_id,
                item.get("created_at", "")[:10],
                item.get("score", {}).get("sleep_performance_percentage"),
                item.get("score", {}).get("sleep_efficiency_percentage"),
                summary.get("total_in_bed_time_milli"),
                summary.get("total_awake_time_milli"),
                summary.get("total_sleep_time_milli"),
                summary.get("deep_sleep_time_milli"),
                summary.get("rem_sleep_time_milli"),
                summary.get("light_sleep_time_milli"),
                summary.get("awake_time_milli"),
                need.get("baseline_milli"),
                json.dumps(item),
            ))
            count += 1
        except Exception as e:
            print(f"[Whoop] Sleep insert error: {e}")
    conn.commit()
    conn.close()
    return count


def _sync_cycles(days=7):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    data = _api_get("cycle", {
        "start": start.strftime("%Y-%m-%dT00:00:00.000Z"),
        "end": end.strftime("%Y-%m-%dT23:59:59.000Z"),
        "limit": 25,
    })
    conn = get_conn()
    count = 0
    for item in data.get("records", []):
        cycle_id = item.get("id")
        try:
            kj = item.get("kilojoule", 0) or 0
            conn.execute("""
                INSERT OR REPLACE INTO whoop_cycle
                (cycle_id, date, strain, kilojoule, avg_heart_rate, max_heart_rate, energy_burned_cal, raw_json)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                cycle_id,
                item.get("created_at", "")[:10],
                item.get("strain"),
                kj,
                item.get("average_heart_rate"),
                item.get("max_heart_rate"),
                round(kj * 0.239006, 1),  # kJ to kcal
                json.dumps(item),
            ))
            count += 1
        except Exception as e:
            print(f"[Whoop] Cycle insert error: {e}")
    conn.commit()
    conn.close()
    return count


def sync(days=7):
    """Sync Whoop data: recovery, sleep, cycles for the last N days."""
    _ensure_tables()
    r = _sync_recovery(days)
    s = _sync_sleep(days)
    c = _sync_cycles(days)
    print(f"[Whoop] Sync done: {r} recovery, {s} sleep, {c} cycles")
    return {"recovery": r, "sleep": s, "cycle": c}


if __name__ == "__main__":
    result = sync(7)
    print(json.dumps(result, indent=2))