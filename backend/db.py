
import sqlite3, os, json
from datetime import datetime
DB_PATH = "volkov.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time TEXT,
        distance REAL,
        duration REAL,
        avg_pace TEXT,
        avg_hr REAL,
        max_hr REAL,
        total_ascent REAL,
        total_descent REAL,
        shoes TEXT DEFAULT 'EVO SL',
        raw_stats TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS whoop_recovery (
        id INTEGER PRIMARY KEY,
        date TEXT,
        recovery_score REAL,
        resting_heart_rate REAL,
        hrv_rmssd_ms REAL,
        spo2_pct REAL,
        skin_temp_c REAL,
        day_strain REAL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS whoop_sleep (
        id INTEGER PRIMARY KEY,
        date TEXT,
        start TEXT,
        end TEXT,
        total_sleep_milli INTEGER,
        sleep_performance_pct REAL,
        deep_sleep_milli INTEGER,
        rem_sleep_milli INTEGER,
        light_sleep_milli INTEGER
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS whoop_cycle (
        id INTEGER PRIMARY KEY,
        start TEXT,
        end TEXT,
        strain REAL,
        kilojoule REAL,
        avg_heart_rate REAL,
        max_heart_rate REAL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS whoop_heart_rate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_utc TEXT NOT NULL,
        hr INTEGER NOT NULL,
        date TEXT
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_whoop_hr_ts ON whoop_heart_rate(ts_utc)")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        t REAL,
        lat REAL,
        lon REAL,
        ele REAL,
        ele_smooth REAL,
        hr INTEGER,
        speed REAL,
        pace REAL,
        dist REAL,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )""")
    conn.commit()
    conn.close()

def get_runs():
    conn=get_conn()
    rows=conn.execute("SELECT * FROM runs ORDER BY start_time DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_run(run_id):
    conn=get_conn()
    row=conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
