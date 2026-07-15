
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import bisect

IDT = ZoneInfo("Asia/Jerusalem")
UTC = ZoneInfo("UTC")

def align_to_idt(dt_utc: datetime) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=UTC)
    return dt_utc.astimezone(IDT)

def interpolate_hr(whoop_stream, target_ts_utc):
    if not whoop_stream:
        return None
    # Ensure all timestamps are offset-aware (UTC)
    UTC = ZoneInfo("UTC")
    times = []
    for x in whoop_stream:
        ts = x['ts_utc']
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        times.append(ts)
    if target_ts_utc.tzinfo is None:
        target_ts_utc = target_ts_utc.replace(tzinfo=UTC)
    idx = bisect.bisect_left(times, target_ts_utc)
    if idx == 0:
        return whoop_stream[0]['hr']
    if idx >= len(times):
        return whoop_stream[-1]['hr']
    a = whoop_stream[idx-1]
    b = whoop_stream[idx]
    dt_total = (b['ts_utc'] - a['ts_utc']).total_seconds() or 1
    dt_target = (target_ts_utc - a['ts_utc']).total_seconds()
    ratio = dt_target / dt_total
    return a['hr'] + (b['hr'] - a['hr']) * ratio

def build_unified_timeline(garmin_points, whoop_hr_24h, whoop_recovery, whoop_sleep, whoop_cycle):
    unified=[]
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
            "pace": gp['pace']
        })
    return {
        "recovery": whoop_recovery,
        "sleep": whoop_sleep,
        "cycle": whoop_cycle,
        "timeline": unified,
        "whoop_24h": [{"t_idt": align_to_idt(x['ts_utc']).strftime("%H:%M"), "hr": x['hr']} for x in whoop_hr_24h]
    }

def get_whoop_for_date(db, date_str):
    # date_str IDT YYYY-MM-DD
    rec = db.execute("SELECT * FROM whoop_recovery WHERE date=?", (date_str,)).fetchone()
    sleep = db.execute("SELECT * FROM whoop_sleep WHERE date=?", (date_str,)).fetchone()
    cyc = db.execute("SELECT * FROM whoop_cycle WHERE date(start) = ?", (date_str,)).fetchone()
    hr = db.execute("SELECT ts_utc, hr FROM whoop_heart_rate WHERE date(ts_utc)=? ORDER BY ts_utc", (date_str,)).fetchall()
    return rec, sleep, cyc, hr
