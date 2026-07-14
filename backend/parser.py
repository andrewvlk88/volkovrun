import math
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2-lat1); dlambda = math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))

def moving_average(arr, w=15):
    if len(arr) < w: return arr
    import numpy as np
    a = np.array(arr, dtype=float)
    # Edge-padded convolution to avoid artificial ramps at start/end
    padded = np.pad(a, (w//2, w//2), mode='edge')
    result = np.convolve(padded, np.ones(w)/w, mode='valid')
    return list(result[:len(arr)])

def build_stats_from_points(raw_points):
    import numpy as np
    if not raw_points: return {"distance_km":0,"duration_sec":0,"duration_str":"0:00","avg_pace":"--","avg_hr":0,"max_hr":0,"total_ascent":0,"is_continuous":False,"points":[]}
    # times
    times = []
    for p in raw_points:
        t = p.get("_time_obj")
        times.append(t)
    start = next((t for t in times if t), None)
    dist_cum = 0
    out = []
    prev = None
    for i, p in enumerate(raw_points):
        lat, lon, ele = p["lat"], p["lon"], p.get("ele",0)
        sec = (times[i]-start).total_seconds() if times[i] and start else float(i)
        speed = 0; pace = 0
        if prev:
            d = haversine(prev["lat"], prev["lon"], lat, lon)
            dt = 1
            if times[i] and prev.get("_t"):
                dt = (times[i]-prev["_t"]).total_seconds() or 1
            if dt>0:
                speed = d/dt*3.6
                if d>0: pace = (dt/60)/(d/1000)
            dist_cum += d
        out.append({
            "lat": lat, "lon": lon, "ele": ele,
            "hr": p.get("hr",0) or 0,
            "cad": p.get("cad",0) or 0,
            "dist_km": dist_cum/1000,
            "time_sec": sec,
            "speed_kmh": min(speed, 30),
            "pace_min": pace
        })
        prev = {"lat": lat, "lon": lon, "_t": times[i]}
    eles = [o["ele"] for o in out]
    ele_smooth = moving_average(eles, 15)
    for i, o in enumerate(out):
        o["ele_smooth"] = float(ele_smooth[i]) if i < len(ele_smooth) else float(o["ele"])
    # Stronger smoothing + threshold-based ascent calculation
    # Garmin reports net ascent per climb, not sum of every GPS jitter
    ele_smooth = moving_average(eles, 30)  # wider window = less noise
    for i, o in enumerate(out):
        o["ele_smooth"] = float(ele_smooth[i]) if i < len(ele_smooth) else float(o["ele"])
    
    # Ascent calculation: sample elevation at 60-second intervals
    # then count only sustained climbs >= 2m between samples
    # Edge-padded smoothing + 60s sampling filters GPS jitter effectively
    total_ascent = 0
    if len(out) > 2:
        sample_interval = 60  # seconds
        sampled = []
        last_t = -999
        for o in out:
            t = o.get("time_sec", 0)
            if t - last_t >= sample_interval or not sampled:
                sampled.append(o.get("ele_smooth", o.get("ele", 0)))
                last_t = t
        if not sampled:
            sampled = [o.get("ele_smooth", o.get("ele", 0)) for o in out]
        
        valley = sampled[0]
        peak = sampled[0]
        for i in range(1, len(sampled)):
            if sampled[i] > peak:
                peak = sampled[i]
            elif sampled[i] < peak - 2.0:
                if peak - valley >= 2.0:
                    total_ascent += (peak - valley)
                valley = sampled[i]
                peak = sampled[i]
        if peak - valley >= 2.0:
            total_ascent += (peak - valley)
    total_ascent = round(total_ascent, 1)
    duration = out[-1]["time_sec"] if out else 0
    distance = out[-1]["dist_km"] if out else 0
    avg_hr = int(np.mean([o["hr"] for o in out if o["hr"]>0])) if any(o["hr"] for o in out) else 0
    max_hr = max([o["hr"] for o in out], default=0)
    is_continuous = duration >= 18*60 and duration <= 45*60
    return {
        "points": out[::max(1, len(out)//600)],
        "distance_km": round(distance,2),
        "duration_sec": int(duration),
        "duration_str": f"{int(duration//60)}:{int(duration%60):02d}",
        "avg_pace": f"{int(duration//60/distance) if distance>0 else 0}:{int((duration/distance)%60) if distance>0 else 0:02d}" if distance>0 else "--",
        "avg_hr": avg_hr, "max_hr": max_hr,
        "total_ascent": round(total_ascent,1),
        "is_continuous": is_continuous
    }

def parse_gpx_bytes(data: bytes):
    import gpxpy
    gpx = gpxpy.parse(data.decode('utf-8', errors='ignore'))
    raw = []
    for track in gpx.tracks:
        for seg in track.segments:
            for p in seg.points:
                hr = 0; cad = 0
                if p.extensions:
                    for ext in p.extensions:
                        # Garmin extensions
                        try:
                            for elem in ext.iter():
                                if elem.tag.endswith('}hr'): hr = int(float(elem.text))
                                if elem.tag.endswith('}cad'): cad = int(float(elem.text))
                        except: pass
                raw.append({"lat": p.latitude, "lon": p.longitude, "ele": p.elevation or 0, "_time_obj": p.time, "hr": hr, "cad": cad})
    return build_stats_from_points(raw)

def parse_kml_bytes(data: bytes):
    text = data.decode('utf-8', errors='ignore')
    coords_blocks = re.findall(r"<coordinates>(.*?)</coordinates>", text, re.DOTALL)
    raw=[]
    for block in coords_blocks:
        for pair in block.strip().split():
            parts = pair.split(",")
            if len(parts)>=2:
                try:
                    lon=float(parts[0]); lat=float(parts[1]); alt=float(parts[2]) if len(parts)>2 else 0
                    raw.append({"lat": lat, "lon": lon, "ele": alt, "_time_obj": None, "hr":0,"cad":0})
                except: pass
    # synthesize times if missing
    for i, p in enumerate(raw):
        p["_time_obj"] = None
    return build_stats_from_points(raw)

def parse_csv_bytes(data: bytes):
    import pandas as pd, io
    s = data.decode('utf-8', errors='ignore')
    try:
        df = pd.read_csv(io.StringIO(s))
    except:
        return {"distance_km":0,"duration_sec":0,"duration_str":"0:00","avg_pace":"--","avg_hr":0,"max_hr":0,"total_ascent":0,"is_continuous":False,"points":[],"laps":[]}
    if 'Laps' in df.columns:
        # Garmin export format from earlier
        summary = df[df['Laps'].astype(str).str.lower()=='summary']
        if not summary.empty:
            row = summary.iloc[0]
            try:
                dist = float(row.get('Distance km',0))
            except: dist=0
            return {
                "distance_km": dist,
                "duration_sec": 0,
                "duration_str": str(row.get('Time','')),
                "avg_pace": str(row.get('Avg Pace min/km','')),
                "avg_hr": int(float(row.get('Avg HR bpm',0))) if str(row.get('Avg HR bpm','')).replace('.','',1).isdigit() else 0,
                "max_hr": int(float(row.get('Max HR bpm',0))) if str(row.get('Max HR bpm','')).replace('.','',1).isdigit() else 0,
                "total_ascent": float(row.get('Total Ascent m',0) or 0),
                "is_continuous": True,
                "points": [],
                "laps": df.to_dict(orient='records')
            }
    return {"distance_km":0,"duration_sec":0,"duration_str":"0:00","avg_pace":"--","avg_hr":0,"is_continuous":False,"points":[],"laps":[]}
