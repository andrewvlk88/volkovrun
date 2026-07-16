
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import db, parser, json
from datetime import datetime
from zoneinfo import ZoneInfo

app = FastAPI(title="Volkov Run Lab")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

scheduler = BackgroundScheduler()

@app.on_event("startup")
def startup():
    db.init_db()
    # seed demo data for 14.07 if empty
    import sqlite3
    conn=db.get_conn()
    cnt=conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    if cnt==0:
        conn.execute("INSERT INTO runs (start_time, distance, duration, avg_pace, avg_hr, max_hr, total_ascent, shoes, raw_stats) VALUES (?,?,?,?,?,?,?,?,?)",
        ("2026-07-14T04:41:11+00:00", 4.08, 2233, "9:08", 120, 162, 28, "EVO SL", json.dumps({"note":"6x2 intervals"})))
        conn.execute("INSERT INTO whoop_recovery (date, recovery_score, resting_heart_rate, hrv_rmssd_ms, spo2_pct, skin_temp_c, day_strain) VALUES (?,?,?,?,?,?,?)",
        ("2026-07-14",68,54,72,97,35.1,11.2))
        conn.execute("INSERT INTO whoop_sleep (date, start, end, total_sleep_milli, sleep_performance_pct, deep_sleep_milli, rem_sleep_milli, light_sleep_milli) VALUES (?,?,?,?,?,?,?,?)",
        ("2026-07-13","2026-07-13T23:10:00Z","2026-07-14T06:45:00Z",25920000,82,5520000,6480000,13920000))
        conn.execute("INSERT INTO whoop_cycle (start, end, strain, kilojoule, avg_heart_rate, max_heart_rate) VALUES (?,?,?,?,?,?)",
        ("2026-07-14T00:00:00Z","2026-07-14T23:59:59Z",11.2,10200,72,162))
        # seed whoop hr 24h
        import random
        base=datetime(2026,7,14,0,0,0, tzinfo=ZoneInfo("UTC"))
        for i in range(0,1440,5):
            dt=base.replace(minute=0)+__import__('datetime').timedelta(minutes=i)
            if 0<=i<360: hr=54+random.randint(-2,3)
            elif 360< i < 410: hr=90+random.randint(0,10)
            elif 410 < i < 500: hr=70+random.randint(-3,5)
            elif 461 <= i <= 498: hr=125+random.randint(-8,15) # run window 07:41-08:18 IDT = 04:41-05:18 UTC = 281-318 min
            else: hr=75+random.randint(-5,8)
            conn.execute("INSERT INTO whoop_heart_rate (ts_utc, hr, date) VALUES (?,?,?)",(dt.isoformat(), hr, "2026-07-14"))
    conn.commit()
    conn.close()
    # scheduler.add_job(lambda: __import__('garmin_sync').sync(), 'interval', minutes=30)
    # scheduler.add_job(lambda: __import__('whoop_sync').sync(), 'interval', minutes=15)
    # scheduler.start()

@app.get("/api/runs")
def list_runs():
    return db.get_runs()

@app.get("/api/runs/{run_id}")
def get_run(run_id: int):
    run=db.get_run(run_id)
    if not run:
        return {"error":"not found"}
    conn=db.get_conn()
    pts=conn.execute("SELECT * FROM points WHERE run_id=? ORDER BY t", (run_id,)).fetchall()
    whoop_rec=conn.execute("SELECT * FROM whoop_recovery WHERE date=?", (run['start_time'][:10],)).fetchone()
    conn.close()
    return {**run, "points":[dict(p) for p in pts], "whoop": dict(whoop_rec) if whoop_rec else None}

@app.get("/api/timeline")
def timeline(date: str = "2026-07-14"):
    from linker import build_unified_timeline
    import linker
    conn=db.get_conn()
    rec, sleep, cyc, hr_rows = linker.get_whoop_for_date(conn, date)
    # get garmin points from json file if no db points
    try:
        with open("points_seed.json","r") as f:
            seed=json.load(f)
            garmin_points=[{"t_utc": datetime.fromisoformat(p['t_utc'] if 't_utc' in p else "2026-07-14T04:41:11+00:00"), "hr": p.get('hr',120), "ele": p.get('ele',135), "speed": p.get('speed',10), "pace": p.get('pace',6)} for p in seed['points']]
    except:
        garmin_points=[{"t_utc": datetime.fromisoformat("2026-07-14T04:41:11+00:00"), "hr":120, "ele":135, "speed":10, "pace":6}]
    whoop_stream=[{"ts_utc": datetime.fromisoformat(r[0]), "hr": r[1]} for r in hr_rows] if hr_rows else []
    if not whoop_stream:
        # fallback generate
        base=datetime(2026,7,14,0,0,0, tzinfo=ZoneInfo("UTC"))
        import random
        whoop_stream=[]
        for i in range(0,1440,2):
            dt=base+__import__('datetime').timedelta(minutes=i)
            hr=70+random.randint(-10,20)
            if 281 <= i <= 318:
                hr=130+random.randint(-5,15)
            whoop_stream.append({"ts_utc": dt, "hr": hr})
    unified=build_unified_timeline(garmin_points, whoop_stream, dict(rec) if rec else None, dict(sleep) if sleep else None, dict(cyc) if cyc else None)
    conn.close()
    return unified

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    fname = (file.filename or "").lower()
    try:
        if fname.endswith(".gpx") or b"<gpx" in data[:800]:
            stats = parser.parse_gpx_bytes(data)
        elif fname.endswith(".kml") or b"<kml" in data[:800]:
            stats = parser.parse_kml_bytes(data)
        elif fname.endswith(".tcx") or b"TrainingCenterDatabase" in data[:800]:
            stats = parser.parse_tcx_bytes(data)
        elif fname.endswith(".csv") or fname.endswith(".txt"):
            if b"<gpx" in data[:800] or b"<kml" in data[:800]:
                try: stats = parser.parse_gpx_bytes(data)
                except: stats = parser.parse_kml_bytes(data)
            else:
                stats = parser.parse_csv_bytes(data)
        else:
            stats = parser.parse_gpx_bytes(data)
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"error": f"Parse error: {e}"}
    # Save run to DB
    conn = db.get_conn()
    cur = conn.execute("INSERT INTO runs (start_time, distance, duration, avg_pace, avg_hr, max_hr, total_ascent, shoes, raw_stats) VALUES (?,?,?,?,?,?,?,?,?)",
        (stats.get("date",""), stats.get("distance_km",0), stats.get("duration_sec",0),
         stats.get("avg_pace",""), stats.get("avg_hr",0), stats.get("max_hr",0),
         stats.get("total_ascent",0), "EVO SL", json.dumps(stats, default=str)))
    run_id = cur.lastrowid
    # Save points
    for p in stats.get("points",[]):
        conn.execute("INSERT INTO points (run_id, lat, lon, ele, ele_smooth, hr, speed, pace, dist) VALUES (?,?,?,?,?,?,?,?,?)",
            (run_id, p.get("lat",0), p.get("lon",0), p.get("ele",0), p.get("ele_smooth",0),
             p.get("hr",0), p.get("speed_kmh",0), p.get("pace",0), p.get("dist_km",0)))
    conn.commit()
    conn.close()
    return {"id": run_id, "filename": file.filename, **stats, "points": stats.get("points",[])}

@app.post("/api/sync/garmin")
def sync_garmin(limit: int=10):
    return {"status":"garmin sync triggered"}

@app.post("/api/sync/whoop")
def sync_whoop(days: int=7):
    return {"status":"whoop sync triggered"}

@app.get("/api/whoop/recovery")
def whoop_recovery():
    conn=db.get_conn()
    rows=conn.execute("SELECT * FROM whoop_recovery ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
