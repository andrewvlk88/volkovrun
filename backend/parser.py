
import math
import numpy as np

# לוגיקה קריטית - לא לגעת לפי README
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2*R*math.asin(math.sqrt(a))

def moving_average(arr, w=15):
    # edge-padded convolution - מונעת רמפות מלאכותיות
    if len(arr) < w:
        return np.array(arr)
    padded = np.pad(arr, (w//2, w//2), mode='edge')
    kernel = np.ones(w)/w
    return np.convolve(padded, kernel, mode='valid')[:len(arr)]

def calc_ascent(elevations, times):
    # דגימה כל 60 שניות + עליות מתמשכות >=2 מטר
    if not elevations:
        return 0
    sampled=[]
    last_t=times[0]
    for i,t in enumerate(times):
        if t - last_t >= 60 or i==0:
            sampled.append(elevations[i])
            last_t=t
    ascent=0
    for i in range(1,len(sampled)):
        diff=sampled[i]-sampled[i-1]
        if diff >= 2:
            ascent+=diff
    return ascent


def parse_gpx_bytes(data: bytes) -> dict:
    """Parse GPX file bytes — returns stats + points list. Uses haversine + moving_average."""
    import gpxpy
    import xml.etree.ElementTree as ET

    gpx = gpxpy.parse(data.decode('utf-8', errors='ignore'))
    points = []
    times_raw = []
    lats, lons, elevs, hrs = [], [], [], []

    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    root = ET.fromstring(data.decode('utf-8', errors='ignore'))

    for trk in gpx.tracks:
        for seg in trk.segments:
            for i, pt in enumerate(seg.points):
                lat = pt.latitude
                lon = pt.longitude
                ele = pt.elevation or 0
                t = pt.time
                hr = 0
                # try to get HR from extensions
                ext = pt.extensions
                if ext:
                    for child in ext:
                        for c in child:
                            if 'hr' in c.tag.lower():
                                try:
                                    hr = int(c.text)
                                except:
                                    pass
                points.append({
                    'lat': lat, 'lon': lon, 'ele': ele, 'hr': hr,
                    'time_iso': t.isoformat() if t else '',
                    'time_sec': 0, 'dist_km': 0, 'speed_kmh': 0, 'pace': 0,
                    'ele_smooth': 0,
                })
                lats.append(lat)
                lons.append(lon)
                elevs.append(ele)
                hrs.append(hr)
                times_raw.append(t.timestamp() if t else i)

    if len(points) < 2:
        return {'distance_km': 0, 'duration_sec': 0, 'duration_str': '', 'avg_pace': '',
                'avg_hr': 0, 'max_hr': 0, 'total_ascent': 0, 'is_continuous': False, 'points': points}

    # Distance via haversine
    dist_m = 0
    for i in range(1, len(points)):
        d = haversine(lats[i-1], lons[i-1], lats[i], lons[i])
        dist_m += d
        points[i]['dist_km'] = round(dist_m / 1000, 3)

    # Time
    t0 = times_raw[0]
    for i in range(len(points)):
        points[i]['time_sec'] = times_raw[i] - t0

    total_sec = times_raw[-1] - t0

    # Speed & pace
    for i in range(1, len(points)):
        dt = points[i]['time_sec'] - points[i-1]['time_sec']
        dd = points[i]['dist_km'] - points[i-1]['dist_km']
        if dt > 0:
            points[i]['speed_kmh'] = round(dd / dt * 3600, 1)
            pace_sec = dt / dd if dd > 0 else 0
            points[i]['pace'] = f"{int(pace_sec//60)}:{int(pace_sec%60):02d}"

    # Elevation smoothing
    if len(elevs) > 30:
        smooth = moving_average(np.array(elevs, dtype=float), 30)
    else:
        smooth = moving_average(np.array(elevs, dtype=float), 15)
    for i in range(len(points)):
        points[i]['ele_smooth'] = round(float(smooth[i]), 1)

    # Ascent
    ascent = calc_ascent(elevs, times_raw)

    # HR
    avg_hr = int(np.mean([h for h in hrs if h > 0])) if any(h > 0 for h in hrs) else 0
    max_hr = max(hrs) if hrs else 0

    # Duration
    mins = int(total_sec // 60)
    secs = int(total_sec % 60)
    duration_str = f"{mins}:{secs:02d}"

    # Pace
    dist_km = dist_m / 1000
    avg_pace = ''
    if dist_km > 0 and total_sec > 0:
        pace_sec = total_sec / dist_km
        avg_pace = f"{int(pace_sec//60)}:{int(pace_sec%60):02d}"

    is_continuous = 18*60 <= total_sec <= 45*60

    return {
        'distance_km': round(dist_km, 2),
        'duration_sec': int(total_sec),
        'duration_str': duration_str,
        'avg_pace': avg_pace,
        'avg_hr': avg_hr,
        'max_hr': max_hr,
        'total_ascent': round(ascent, 1),
        'is_continuous': is_continuous,
        'points': points,
    }


def parse_kml_bytes(data: bytes) -> dict:
    """Parse KML file bytes — basic extraction."""
    from lxml import etree
    root = etree.fromstring(data)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    coords_text = ''
    for pm in root.findall('.//kml:Placemark', ns):
        for geom in pm.findall('.//kml:coordinates', ns):
            coords_text = geom.text or ''
            break
    if not coords_text:
        # try without namespace
        for geom in root.iter():
            if 'coordinates' in (geom.tag or ''):
                coords_text = geom.text or ''
                break
    points = []
    lats, lons, elevs = [], [], []
    for line in coords_text.strip().split('\n'):
        parts = line.strip().split(',')
        if len(parts) >= 2:
            lon, lat = float(parts[0]), float(parts[1])
            ele = float(parts[2]) if len(parts) > 2 else 0
            points.append({'lat': lat, 'lon': lon, 'ele': ele, 'hr': 0, 'time_sec': 0, 'dist_km': 0, 'speed_kmh': 0, 'pace': 0, 'ele_smooth': 0, 'time_iso': ''})
            lats.append(lat)
            lons.append(lon)
            elevs.append(ele)
    if len(points) < 2:
        return {'distance_km': 0, 'duration_sec': 0, 'duration_str': '', 'avg_pace': '', 'avg_hr': 0, 'max_hr': 0, 'total_ascent': 0, 'is_continuous': False, 'points': points}
    dist_m = 0
    for i in range(1, len(points)):
        d = haversine(lats[i-1], lons[i-1], lats[i], lons[i])
        dist_m += d
        points[i]['dist_km'] = round(dist_m / 1000, 3)
    if len(elevs) > 30:
        smooth = moving_average(np.array(elevs, dtype=float), 30)
    else:
        smooth = moving_average(np.array(elevs, dtype=float), 15)
    for i in range(len(points)):
        points[i]['ele_smooth'] = round(float(smooth[i]), 1)
    ascent = calc_ascent(elevs, list(range(len(elevs))))
    return {
        'distance_km': round(dist_m / 1000, 2),
        'duration_sec': 0,
        'duration_str': '',
        'avg_pace': '',
        'avg_hr': 0,
        'max_hr': 0,
        'total_ascent': round(ascent, 1),
        'is_continuous': False,
        'points': points,
    }


def parse_csv_bytes(data: bytes) -> dict:
    """Parse CSV — basic."""
    import csv, io
    text = data.decode('utf-8', errors='ignore')
    reader = csv.DictReader(io.StringIO(text))
    points = []
    lats, lons, elevs = [], [], []
    for i, row in enumerate(reader):
        lat = float(row.get('lat', row.get('latitude', 0)) or 0)
        lon = float(row.get('lon', row.get('longitude', 0)) or 0)
        ele = float(row.get('ele', row.get('elevation', 0)) or 0)
        hr = int(float(row.get('hr', row.get('heart_rate', 0)) or 0))
        points.append({'lat': lat, 'lon': lon, 'ele': ele, 'hr': hr, 'time_sec': i, 'dist_km': 0, 'speed_kmh': 0, 'pace': 0, 'ele_smooth': 0, 'time_iso': ''})
        lats.append(lat)
        lons.append(lon)
        elevs.append(ele)
    if len(points) < 2:
        return {'distance_km': 0, 'duration_sec': 0, 'duration_str': '', 'avg_pace': '', 'avg_hr': 0, 'max_hr': 0, 'total_ascent': 0, 'is_continuous': False, 'points': points}
    dist_m = 0
    for i in range(1, len(points)):
        d = haversine(lats[i-1], lons[i-1], lats[i], lons[i])
        dist_m += d
        points[i]['dist_km'] = round(dist_m / 1000, 3)
    if len(elevs) > 30:
        smooth = moving_average(np.array(elevs, dtype=float), 30)
    else:
        smooth = moving_average(np.array(elevs, dtype=float), 15)
    for i in range(len(points)):
        points[i]['ele_smooth'] = round(float(smooth[i]), 1)
    ascent = calc_ascent(elevs, list(range(len(elevs))))
    return {
        'distance_km': round(dist_m / 1000, 2),
        'duration_sec': 0,
        'duration_str': '',
        'avg_pace': '',
        'avg_hr': 0,
        'max_hr': 0,
        'total_ascent': round(ascent, 1),
        'is_continuous': False,
        'points': points,
    }
