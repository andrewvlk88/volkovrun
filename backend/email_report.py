import os, json, smtplib, sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv(override=True)

IDT = ZoneInfo("Asia/Jerusalem")
DB_PATH = os.getenv("VOLKOV_DB", "volkov.db")

EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def generate_html(run_id: int) -> str:
    """Build an HTML report for a run — inline CSS, same design as the app."""
    conn = _get_conn()
    run = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if not run:
        conn.close()
        return f"<p>Run {run_id} not found</p>"

    run = dict(run)
    raw = json.loads(run.get("raw_stats", "{}"))
    pts = conn.execute("SELECT * FROM points WHERE run_id=? ORDER BY t", (run_id,)).fetchall()
    conn.close()

    # Build polyline coords for inline map
    coords = ",".join(f"{p['lat']},{p['lon']}" for p in pts[:200])  # sample every Nth

    dist = run.get("distance", 0)
    dur = run.get("duration", 0)
    mins = int(dur // 60) if dur else 0
    secs = int(dur % 60) if dur else 0
    avg_hr = run.get("avg_hr", 0)
    max_hr = run.get("max_hr", 0)
    ascent = run.get("total_ascent", 0)
    descent = run.get("total_descent", 0) or 0
    pace = run.get("avg_pace", "")
    shoes = run.get("shoes", "EVO SL")
    start = run.get("start_time", "")

    # Laps from raw_stats
    laps_html = ""
    if raw.get("laps"):
        laps_html = "<table style='width:100%;border-collapse:collapse;font-family:JetBrains Mono,monospace;font-size:12px;margin-top:12px'>"
        laps_html += "<tr style='background:#f4f4f5'><th style='padding:8px;text-align:right'>Lap</th><th>Time</th><th>Dist</th><th>Pace</th><th>HR</th><th>Power</th></tr>"
        # placeholder — real laps would come from CSV parsing
        laps_html += f"<tr><td style='padding:8px;text-align:right'>{raw.get('laps','?')} laps</td><td>{mins}:{secs:02d}</td><td>{dist}km</td><td>{pace}</td><td>{avg_hr}/{max_hr}</td><td>{raw.get('avg_power','—')}W</td></tr>"
        laps_html += "</table>"

    # Whoop section
    whoop_html = ""
    if run.get("whoop") and isinstance(run["whoop"], dict):
        w = run["whoop"]
        whoop_html = f"""
        <div style="background:#f8f7f5;border-radius:24px;padding:20px;margin-top:16px">
          <div style="font-size:11px;font-weight:900;letter-spacing:2px;color:#71717a">WHOOP RECOVERY</div>
          <div style="display:flex;gap:24px;margin-top:8px">
            <div><span style="font-size:36px;font-weight:900">{w.get('recovery_score','—')}%</span></div>
            <div style="font-family:JetBrains Mono,monospace;font-size:14px">
              RHR: <b>{w.get('resting_heart_rate','—')}</b> &nbsp;
              HRV: <b>{w.get('hrv_rmssd_ms','—')}ms</b> &nbsp;
              Strain: <b>{w.get('day_strain','—')}</b>
            </div>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
  *{{font-family:'Heebo',sans-serif}}
  .mono{{font-family:'JetBrains Mono',monospace!important}}
  body{{background:#f8f7f5;margin:0;padding:24px}}
  .card{{background:#fff;border-radius:24px;box-shadow:0 8px 30px rgba(0,0,0,0.04);border:1px solid #f4f4f5;padding:24px;margin-bottom:16px}}
  .pill{{display:inline-block;border-radius:9999px;padding:6px 14px;font-size:11px;font-weight:900;letter-spacing:2px;text-transform:uppercase}}
  .kpi{{display:flex;gap:16px;margin-bottom:16px}}
  .kpi-card{{flex:1;background:#fff;border-radius:24px;box-shadow:0 8px 30px rgba(0,0,0,0.04);border:1px solid #f4f4f5;padding:20px;text-align:center}}
  .kpi-val{{font-size:32px;font-weight:900;font-family:'JetBrains Mono',monospace}}
  .kpi-label{{font-size:10px;font-weight:900;letter-spacing:2px;color:#71717a;text-transform:uppercase;margin-top:4px}}
  h1{{font-size:22px;font-weight:900;letter-spacing:-0.02em;margin:0}}
  h2{{font-size:18px;font-weight:900;letter-spacing:-0.02em;margin:0 0 12px}}
  .action{{color:#ef4444}} .positive{{color:#22c55e}} .amber{{color:#f59e0b}} .info{{color:#3b82f6}}
</style></head>
<body>
  <div style="max-width:680px;margin:0 auto">
    <div class="card" style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <h1>VOLKOV RUN LAB</h1>
        <div style="font-size:12px;color:#71717a;margin-top:4px">{start[:16] if start else ''} IDT</div>
      </div>
      <span class="pill" style="background:#ef4444;color:#fff">{shoes}</span>
    </div>

    <div class="kpi">
      <div class="kpi-card"><div class="kpi-val action">{dist}</div><div class="kpi-label">ק"מ</div></div>
      <div class="kpi-card"><div class="kpi-val">{mins}:{secs:02d}</div><div class="kpi-label">זמן</div></div>
      <div class="kpi-card"><div class="kpi-val action">{avg_hr}</div><div class="kpi-label">דופק ממוצע</div></div>
      <div class="kpi-card"><div class="kpi-val amber">{ascent}מ'</div><div class="kpi-label">עלייה</div></div>
    </div>

    <div class="card">
      <h2>פרטי ריצה</h2>
      <div class="mono" style="font-size:13px;line-height:2">
        קצב ממוצע: <b>{pace}</b> דק'/ק"מ &nbsp;•&nbsp;
        דופק מקס: <b class="action">{max_hr}</b> &nbsp;•&nbsp;
        עלייה: <b class="amber">{ascent}מ'</b> &nbsp;•&nbsp;
        ירידה: <b class="info">{descent}מ'</b><br>
        הספק: <b>{raw.get('avg_power','—')}W</b> ({raw.get('avg_w_kg','—')} W/kg) &nbsp;•&nbsp;
        קאדנס: <b>{raw.get('avg_cadence','—')}</b> spm &nbsp;•&nbsp;
        GCT: <b>{raw.get('avg_gct','—')}ms</b> &nbsp;•&nbsp;
        צעד: <b>{raw.get('avg_stride','—')}מ'</b><br>
        סוג: <b>{raw.get('type','running')}</b> &nbsp;•&nbsp;
        הקפות: <b>{raw.get('laps','—')}</b> &nbsp;•&nbsp;
        קלוריות: <b>{raw.get('calories','—')}</b>
      </div>
      {laps_html}
    </div>

    {whoop_html}

    <div class="card" style="text-align:center">
      <div style="font-size:11px;font-weight:900;letter-spacing:2px;color:#71717a">נקודות GPS</div>
      <div class="mono" style="font-size:24px;font-weight:900;margin-top:4px">{len(pts)}</div>
    </div>

    <div style="text-align:center;font-size:11px;color:#a1a1aa;margin-top:24px">
      🪽 Hermes · {datetime.now(IDT).strftime('%Y-%m-%d %H:%M')} IDT
    </div>
  </div>
</body></html>"""
    return html


def save_report(run_id: int) -> str:
    """Generate HTML and save to reports/ directory."""
    os.makedirs("reports", exist_ok=True)
    html = generate_html(run_id)
    path = f"reports/run_{run_id}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[Email] Report saved: {path}")
    return path


def send_report(run_id: int):
    """Generate HTML report and send via Gmail SMTP."""
    if not EMAIL_FROM or not GMAIL_APP_PASSWORD:
        print("[Email] EMAIL_FROM or GMAIL_APP_PASSWORD not set — skipping send")
        return save_report(run_id)

    html = generate_html(run_id)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏃 Volkov Run Lab — ריצה #{run_id} {datetime.now(IDT).strftime('%d/%m %H:%M')}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO or EMAIL_FROM
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, GMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_FROM, msg["To"], msg.as_string())
        print(f"[Email] Sent report for run {run_id} to {msg['To']}")
    except Exception as e:
        print(f"[Email] Send failed: {e}")

    return save_report(run_id)


if __name__ == "__main__":
    import sys
    rid = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    path = send_report(rid)
    print(f"Done: {path}")