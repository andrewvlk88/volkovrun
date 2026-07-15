"""Linker — איחוד נתוני Garmin + Whoop לטיימליין מאוחד.

ממיר Garmin Zulu + Whoop UTC ל-Asia/Jerusalem IDT +3,
עושה resample של Whoop מדגימה בדקה ל-1 שנייה עם interpolation לינארי,
ומחזיר timeline מאוחד.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import bisect

IDT = ZoneInfo("Asia/Jerusalem")


def align_to_idt(dt_utc: datetime) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))
    return dt_utc.astimezone(IDT)


def interpolate_hr(whoop_stream, target_ts_utc):
    """whoop_stream: sorted list of {ts_utc, hr} ~1/min. target_ts_utc: garmin point utc."""
    if not whoop_stream:
        return None
    times = [x['ts_utc'] for x in whoop_stream]
    idx = bisect.bisect_left(times, target_ts_utc)
    if idx == 0:
        return whoop_stream[0]['hr']
    if idx >= len(times):
        return whoop_stream[-1]['hr']
    a = whoop_stream[idx - 1]
    b = whoop_stream[idx]
    dt_total = (b['ts_utc'] - a['ts_utc']).total_seconds() or 1
    dt_target = (target_ts_utc - a['ts_utc']).total_seconds()
    ratio = dt_target / dt_total
    return a['hr'] + (b['hr'] - a['hr']) * ratio


def build_unified_timeline(garmin_points, whoop_hr_24h, whoop_recovery, whoop_sleep, whoop_cycle):
    unified = []
    for gp in garmin_points:
        whr = interpolate_hr(whoop_hr_24h, gp['t_utc'])
        unified.append({
            "t_utc": gp['t_utc'].isoformat(),
            "t_idt": align_to_idt(gp['t_utc']).strftime("%H:%M:%S"),
            "garmin_hr": gp['hr'],
            "whoop_hr": round(whr) if whr else None,
            "diff": round(gp['hr'] - whr) if whr else None,
            "ele": gp['ele'],
            "speed": gp['speed'],
            "pace": gp['pace'],
        })
    return {
        "recovery": dict(whoop_recovery) if whoop_recovery else None,
        "sleep": dict(whoop_sleep) if whoop_sleep else None,
        "cycle": dict(whoop_cycle) if whoop_cycle else None,
        "timeline": unified,
        "whoop_24h": [
            {"t_idt": align_to_idt(x['ts_utc']).strftime("%H:%M"), "hr": x['hr']}
            for x in whoop_hr_24h
        ],
    }


def get_whoop_for_run(conn, run_start_utc):
    """Fetch Whoop data matching a run's start time."""
    run_date_idt = align_to_idt(run_start_utc).date()
    rec = conn.execute(
        "SELECT * FROM whoop_recovery WHERE cycle_id IN (SELECT cycle_id FROM whoop_recovery ORDER BY created_at DESC LIMIT 1)"
    ).fetchone()
    sleep = conn.execute(
        "SELECT * FROM whoop_sleep WHERE date = ? ORDER BY date DESC LIMIT 1",
        (str(run_date_idt - timedelta(days=1)),),
    ).fetchone()
    cyc = conn.execute(
        "SELECT * FROM whoop_cycle WHERE date = ? ORDER BY date DESC LIMIT 1",
        (str(run_date_idt),),
    ).fetchone()
    hr24 = conn.execute(
        "SELECT ts_utc, hr FROM whoop_heart_rate WHERE date(ts_utc) = ? ORDER BY ts_utc",
        (str(run_date_idt),),
    ).fetchall()
    return rec, sleep, cyc, hr24