from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from db import init_db, list_runs, get_run, delete_run, insert_run
from parser import parse_gpx_bytes, parse_kml_bytes, parse_csv_bytes
from garmin_sync import sync as garmin_sync_func
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

@app.on_event("startup")
def startup():
    init_db()
    scheduler.add_job(scheduled_garmin_sync, 'interval', minutes=30, id='garmin_sync')
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
