# סנכרון Garmin - בטוח, עם tokens/ לא ב-git
import os, json
from datetime import datetime
from dotenv import load_dotenv
from db import get_conn
from parser import parse_gpx_bytes
from email_report import send_report

load_dotenv(override=True)
TOKEN_DIR = os.getenv("GARMIN_TOKEN_DIR", "./tokens")
os.makedirs(TOKEN_DIR, exist_ok=True)


def link_whoop_to_run(run_data):
    """After saving a run, try to link Whoop HR data for the same time window."""
    try:
        from linker import get_whoop_for_date, interpolate_hr
        conn = get_conn()
        run_date = (run_data.get("date") or "")[:10]
        if run_date:
            run_start = datetime.fromisoformat(run_date + "T12:00:00+00:00")
            rec, sleep, cyc, hr24 = get_whoop_for_date(conn, run_date)
            if hr24:
                print(f"[Linker] Found {len(hr24)} Whoop HR points for {run_date}")
        conn.close()
    except Exception as e:
        print(f"[Linker] Whoop link failed (non-fatal): {e}")


def get_client():
    from garminconnect import Garmin
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        raise ValueError("Set GARMIN_EMAIL and GARMIN_PASSWORD in .env")
    try:
        client = Garmin()
        client.login(TOKEN_DIR)
        return client
    except Exception as e:
        print(f"No valid token, login with credentials: {e}")
        client = Garmin(email, password)
        client.login()
        try:
            client.garth.dump(TOKEN_DIR)
        except:
            pass
        return client


def sync(limit=10):
    """Fetch Garmin activities, save new ones, link Whoop, send email report."""
    try:
        client = get_client()
    except ValueError as e:
        print(f"[Garmin] {e}")
        return 0

    activities = client.get_activities(0, limit)
    new_count = 0
    conn = get_conn()

    for act in activities:
        gid = act.get("activityId")
        if not gid:
            continue
        exists = conn.execute("SELECT 1 FROM runs WHERE raw_stats LIKE ?", (f'%"garmin_activity_id": {gid}%',)).fetchone()
        if exists:
            continue

        print(f"[Garmin] New activity {gid} {act.get('activityName')}")
        try:
            gpx_bytes = client.download_activity(gid, dl_fmt=client.ActivityDownloadFormat.GPX)
            if isinstance(gpx_bytes, str):
                gpx_bytes = gpx_bytes.encode("utf-8")
            stats = parse_gpx_bytes(gpx_bytes)

            start_time = act.get("startTimeLocal") or act.get("startTimeGMT") or datetime.now().isoformat()
            run_data = {
                "garmin_activity_id": gid,
                "date": start_time,
                "distance_km": act.get("distance", 0) / 1000 if act.get("distance") else stats.get("distance_km"),
                "duration_sec": int(act.get("duration", 0)),
                "avg_pace": stats.get("avg_pace", ""),
                "avg_hr": act.get("averageHR") or stats.get("avg_hr"),
                "max_hr": act.get("maxHR") or stats.get("max_hr"),
                "total_ascent": act.get("elevationGain") or stats.get("total_ascent"),
                "total_descent": act.get("elevationLoss") or 0,
                "shoes": "EVO SL",
                "raw_stats": json.dumps({**act, "garmin_activity_id": gid}, default=str),
            }

            cur = conn.execute(
                "INSERT INTO runs (start_time, distance, duration, avg_pace, avg_hr, max_hr, total_ascent, total_descent, shoes, raw_stats) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (run_data["date"], run_data["distance_km"], run_data["duration_sec"],
                 run_data["avg_pace"], run_data["avg_hr"], run_data["max_hr"],
                 run_data["total_ascent"], run_data["total_descent"], run_data["shoes"], run_data["raw_stats"])
            )
            run_id = cur.lastrowid

            # Save points
            for p in stats.get("points", []):
                conn.execute(
                    "INSERT INTO points (run_id, lat, lon, ele, ele_smooth, hr, speed, pace, dist) VALUES (?,?,?,?,?,?,?,?,?)",
                    (run_id, p.get("lat", 0), p.get("lon", 0), p.get("ele", 0), p.get("ele_smooth", 0),
                     p.get("hr", 0), p.get("speed_kmh", 0), p.get("pace", 0), p.get("dist_km", 0))
                )

            conn.commit()
            new_count += 1
            print(f"[Garmin] Saved run {run_id}: {run_data['distance_km']}km")

            # Link Whoop
            link_whoop_to_run(run_data)

            # Send email report
            try:
                send_report(run_id)
            except Exception as e:
                print(f"[Email] Report failed (non-fatal): {e}")

        except Exception as e:
            print(f"[Garmin] Failed activity {gid}: {e}")
            continue

    conn.close()
    print(f"[Garmin] Sync done: {new_count} new runs")
    return new_count


if __name__ == "__main__":
    sync(5)