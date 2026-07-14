import sqlite3
import json
import os

DB_PATH = os.getenv("DATABASE_URL", "./runs.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      garmin_activity_id INTEGER UNIQUE,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      file_name TEXT,
      date TEXT,
      distance_km REAL,
      duration_sec INTEGER,
      duration_str TEXT,
      avg_pace_min_km TEXT,
      avg_hr INTEGER,
      max_hr INTEGER,
      avg_power INTEGER,
      avg_cadence INTEGER,
      total_ascent REAL,
      total_descent REAL,
      avg_gct INTEGER,
      avg_stride REAL,
      shoes TEXT DEFAULT 'EVO SL',
      is_continuous BOOLEAN,
      points_json TEXT,
      laps_json TEXT,
      raw_stats_json TEXT
    );
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS garmin_state (
      id INTEGER PRIMARY KEY,
      last_sync TEXT,
      last_activity_id INTEGER
    );
    """)
    conn.commit()
    conn.close()

def insert_run(run_data: dict):
    conn = get_conn()
    cols = ",".join(run_data.keys())
    placeholders = ",".join(["?"]*len(run_data))
    sql = f"INSERT OR REPLACE INTO runs ({cols}) VALUES ({placeholders})"
    conn.execute(sql, list(run_data.values()))
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return row_id

def list_runs(limit=1000):
    conn = get_conn()
    rows = conn.execute("SELECT id, garmin_activity_id, created_at, file_name, date, distance_km, duration_sec, duration_str, avg_pace_min_km, avg_hr, max_hr, total_ascent, is_continuous FROM runs ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_run(run_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    conn.close()
    if not row: return None
    return dict(row)

def delete_run(run_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM runs WHERE id=?", (run_id,))
    conn.commit()
    conn.close()

def exists_garmin_id(garmin_id: int) -> bool:
    conn = get_conn()
    r = conn.execute("SELECT 1 FROM runs WHERE garmin_activity_id=?", (garmin_id,)).fetchone()
    conn.close()
    return r is not None
