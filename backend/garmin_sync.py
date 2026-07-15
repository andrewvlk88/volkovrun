import os, json
from datetime import datetime
from dotenv import load_dotenv
from db import exists_garmin_id, insert_run, get_conn
from parser import parse_gpx_bytes

load_dotenv()
TOKEN_DIR = os.getenv("GARMIN_TOKEN_DIR", "./tokens")
os.makedirs(TOKEN_DIR, exist_ok=True)


def link_whoop_to_run(run_data):
    """After saving a run, try to link Whoop HR data for the same time window."""
    try:
        from linker import get_whoop_for_run, interpolate_hr
        from datetime import datetime
        conn = get_conn()
        run_date = (run_data.get("date") or "")[:10]
        if run_date:
            run_start = datetime.fromisoformat(run_date + "T12:00:00+00:00")
            rec, sleep, cyc, hr24 = get_whoop_for_run(conn, run_start)
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
        raise ValueError("Set GARMIN_EMAIL and GARMIN_PASSWORD in .env (never commit .env)")
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
    client = get_client()
    activities = client.get_activities(0, limit)
    new_count=0
    for act in activities:
        gid = act.get('activityId')
        if exists_garmin_id(gid):
            continue
        print(f"New activity {gid} {act.get('activityName')}")
        try:
            gpx_bytes = client.download_activity(gid, dl_fmt=client.ActivityDownloadFormat.GPX)
            if isinstance(gpx_bytes, str):
                gpx_bytes = gpx_bytes.encode('utf-8')
            stats = parse_gpx_bytes(gpx_bytes)
            run_data = {
                "garmin_activity_id": gid,
                "file_name": f"{gid}.gpx",
                "date": act.get('startTimeLocal') or act.get('startTimeGMT') or datetime.now().isoformat(),
                "distance_km": act.get('distance',0)/1000 if act.get('distance') else stats.get('distance_km'),
                "duration_sec": int(act.get('duration',0)),
                "duration_str": stats.get('duration_str'),
                "avg_pace_min_km": stats.get('avg_pace'),
                "avg_hr": act.get('averageHR') or stats.get('avg_hr'),
                "max_hr": act.get('maxHR') or stats.get('max_hr'),
                "total_ascent": act.get('elevationGain') or stats.get('total_ascent'),
                "total_descent": act.get('elevationLoss') or 0,
                "avg_cadence": act.get('averageRunningCadenceInStepsPerMinute'),
                "is_continuous": 1 if stats.get('is_continuous') else 0,
                "points_json": json.dumps(stats.get('points',[])),
                "laps_json": json.dumps([]),
                "raw_stats_json": json.dumps(act, default=str)
            }
            # remove None values for sqlite
            run_data = {k: (v if v is not None else 0) if k not in ["points_json","laps_json","raw_stats_json","date","duration_str","avg_pace_min_km","file_name"] else v for k,v in run_data.items()}
            insert_run(run_data)
            link_whoop_to_run(run_data)
            new_count+=1
        except Exception as ex:
            print(f"Failed {gid}: {ex}")
            import traceback; traceback.print_exc()
    print(f"Sync done, {new_count} new")
    conn = get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO garmin_state (id, last_sync, last_activity_id) VALUES (1, ?, ?)", (datetime.now().isoformat(), activities[0]['activityId'] if activities else 0))
        conn.commit()
    finally:
        conn.close()
    return new_count

if __name__ == "__main__":
    sync()
