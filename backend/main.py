from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from db import init_db, list_runs, get_run, delete_run, insert_run, get_conn
from parser import parse_gpx_bytes, parse_kml_bytes, parse_csv_bytes
from garmin_sync import sync as garmin_sync_func
from whoop_sync import sync as whoop_sync_func
from linker import build_unified_timeline, get_whoop_for_run
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = FastAPI(title="Volkov Run Lab API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# === APScheduler: Garmin sync every 30 minutes ===
scheduler = BackgroundScheduler()

def scheduled_garmin_sync():
    try:
        count = garmin_sync_func(limit=10)
        print(f"[Scheduler] Garmin sync done: {count} new activities")
    except Exception as e:
        print(f"[Scheduler] Garmin sync failed: {e}")

def scheduled_whoop_sync():
    try:
        result = whoop_sync_func(days=1)
        print(f"[Scheduler] Whoop sync done: {result}")
    except Exception as e:
        print(f"[Scheduler] Whoop sync failed: {e}")

@app.on_event("startup")
def startup():
    init_db()
    scheduler.add_job(scheduled_garmin_sync, 'interval', minutes=30, id='garmin_sync')
    scheduler.add_job(scheduled_whoop_sync, 'interval', minutes=15, id='whoop_sync')
    scheduler.start()

@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown(wait=False)

atexit.register(lambda: scheduler.shutdown(wait=False))

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    fname = (file.filename or "").lower()
    try:
        if fname.endswith(".gpx") or b"<gpx" in data[:800]:
            stats = parse_gpx_bytes(data)
        elif fname.endswith(".kml") or b"<kml" in data[:800]:
            stats = parse_kml_bytes(data)
        elif fname.endswith(".csv") or fname.endswith(".txt"):
            # try gpx first if txt contains xml
            if b"<gpx" in data[:800] or b"<kml" in data[:800]:
                try: stats = parse_gpx_bytes(data)
                except: stats = parse_kml_bytes(data)
            else:
                stats = parse_csv_bytes(data)
        else:
            stats = parse_gpx_bytes(data)
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(400, f"Parse error: {e}")
    run_data = {
        "file_name": file.filename,
        "date": stats.get("date") or "",
        "distance_km": float(stats.get("distance_km",0) or 0),
        "duration_sec": int(stats.get("duration_sec",0) or 0),
        "duration_str": str(stats.get("duration_str","")),
        "avg_pace_min_km": str(stats.get("avg_pace","")),
        "avg_hr": int(stats.get("avg_hr",0) or 0),
        "max_hr": int(stats.get("max_hr",0) or 0),
        "total_ascent": float(stats.get("total_ascent",0) or 0),
        "is_continuous": 1 if stats.get("is_continuous") else 0,
        "points_json": json.dumps(stats.get("points",[])),
        "laps_json": json.dumps(stats.get("laps",[])),
        "raw_stats_json": json.dumps(stats, default=str)
    }
    rid = insert_run(run_data)
    return {"id": rid, **run_data, "points": stats.get("points",[])}

@app.get("/api/runs")
def api_list_runs():
    return list_runs()

@app.get("/api/runs/{run_id}")
def api_get_run(run_id: int):
    r = get_run(run_id)
    if not r:
        raise HTTPException(404, "Not found")
    # Attach Whoop data if available
    try:
        run_date = r.get("date", "")[:10]
        if run_date:
            conn = get_conn()
            run_start_utc = datetime.fromisoformat(run_date + "T12:00:00+00:00")
            rec, sleep, cyc, _ = get_whoop_for_run(conn, run_start_utc)
            conn.close()
            r["whoop"] = {
                "recovery": dict(rec) if rec else None,
                "sleep": dict(sleep) if sleep else None,
                "cycle": dict(cyc) if cyc else None,
            }
    except Exception as e:
        print(f"[Whoop] Link failed for run {run_id}: {e}")
        r["whoop"] = None
    return r

@app.delete("/api/runs/{run_id}")
def api_delete(run_id: int):
    delete_run(run_id)
    return {"ok": True}

@app.post("/api/sync/garmin")
def api_sync_garmin(limit: int = 10):
    try:
        count = garmin_sync_func(limit)
        return {"synced": count}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"Garmin sync failed: {e}. Check .env and 2FA token.")

@app.get("/api/stats/summary")
def api_summary():
    runs = list_runs(1000)
    total_km = sum((r["distance_km"] or 0) for r in runs)
    return {"total_runs": len(runs), "total_km": round(total_km,2), "runs": runs}

# === Whoop ===

@app.post("/api/sync/whoop")
def api_sync_whoop(days: int = 7):
    try:
        result = whoop_sync_func(days)
        return {"synced": result}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"Whoop sync failed: {e}")

@app.get("/api/whoop/recovery")
def api_whoop_recovery(limit: int = 30):
    conn = get_conn()
    rows = conn.execute("SELECT cycle_id, recovery_score, resting_heart_rate, hrv_rmssd_ms, spo2_pct, skin_temp_c, day_strain, created_at FROM whoop_recovery ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/whoop/sleep")
def api_whoop_sleep(limit: int = 30):
    conn = get_conn()
    rows = conn.execute("SELECT sleep_id, date, sleep_performance_pct, sleep_efficiency_pct, total_sleep_milli, deep_sleep_milli, rem_sleep_milli, light_sleep_milli, sleep_need_milli, created_at FROM whoop_sleep ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/whoop/cycle")
def api_whoop_cycle(limit: int = 30):
    conn = get_conn()
    rows = conn.execute("SELECT cycle_id, date, strain, kilojoule, avg_heart_rate, max_heart_rate, energy_burned_cal, created_at FROM whoop_cycle ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# === Timeline — Whoop + Garmin unified ===

@app.get("/api/timeline")
def api_timeline(date: str):
    """date = 2026-07-14 (IDT date). Returns unified Whoop+Garmin timeline."""
    conn = get_conn()
    try:
        # Get runs for that date
        runs = list_runs(1000)
        date_runs = [r for r in runs if (r.get("date", "") or "")[:10] == date]

        # Get Whoop data for that date
        run_start_utc = datetime.fromisoformat(date + "T12:00:00+00:00")
        rec, sleep, cyc, hr24 = get_whoop_for_run(conn, run_start_utc)

        # Build garmin points from all runs on that date
        all_points = []
        for r in date_runs:
            full_run = get_run(r["id"])
            if full_run:
                pts = json.loads(full_run.get("points_json", "[]"))
                for p in pts:
                    all_points.append({
                        "t_utc": datetime.fromisoformat(p.get("time_iso", date + "T12:00:00+00:00")),
                        "hr": p.get("hr", 0),
                        "ele": p.get("ele", 0),
                        "speed": p.get("speed_kmh", 0),
                        "pace": p.get("pace", ""),
                    })

        whoop_stream = [
            {"ts_utc": datetime.fromisoformat(row[0]), "hr": row[1]}
            for row in hr24
        ] if hr24 else []

        unified = build_unified_timeline(all_points, whoop_stream, rec, sleep, cyc)
        unified["runs"] = date_runs
        return unified
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"Timeline failed: {e}")
    finally:
        conn.close()
