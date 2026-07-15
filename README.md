# Volkov Run Lab

> אפליקציה אישית לניתוח ריצות — מפה אינטראקטיבית, גרפי גובה/דופק/מהירות, זיהוי חכם של עליות וירידות, וסנכרון אוטומטי מ-Garmin Connect.

---

## מה האפליקציה עושה

Volkov Run Lab היא מערכת full-stack לניתוח נתוני ריצה. היא קולטת קבצי GPX/KML/CSV/TCX (העלאה ידנית או סנכרון אוטומטי מ-Garmin), מפרסרת את הנקודות, מחשבת סטטיסטיקות, ומציגה הכל בממשק RTL עברי עם מפה, גרפים, וניתוח חכם.

### תכונות עיקריות

| תכונה | תיאור |
|-------|--------|
| 🗺️ **מפה אינטראקטיבית** | מסלול הריצה על Leaflet/OpenStreetMap, עם צביעת הקו לפי מהירות / גובה / דופק |
| 📊 **גרפים** | גובה לפי מרחק (Area chart), דופק + מהירות משולבים (Line chart דו-צירי) — Recharts |
| 📈 **ניתוח חכם** | זיהוי ריצה רציפה (18-45 דק'), זיהוי עלייה משמעותית (דקות 12.5-15), זיהוי ירידה/דיליי עייפות (דקות 16-18) |
| ⌚ **סנכרון Garmin** | סנכרון אוטומטי כל 30 דק' מ-Garmin Connect דרך `garminconnect` + `garth` (טוקנים, ללא 2FA לאחר התחברות ראשונה) |
| 💜 **סנכרון Whoop** | סנכרון אוטומטי כל 15 דק' מ-Whoop API v2 — recovery, sleep, cycle (strain, HRV, SpO2, דופק מנוחה, שלבי שינה) |
| 📤 **העלאת קבצים** | גרירת GPX/KML/CSV/TCX להעלאה ידנית |
| 🗃️ **היסטוריה** | שמירת כל הריצות ב-SQLite, עם נתוני laps ו-raw stats |
| 👟 **מעקב נעליים** | שדה shoes (ברירת מחדל: EVO SL) |

---

## ארכיטקטורה

```
volkov-run-lab/
├── backend/                  # FastAPI + SQLite
│   ├── main.py               # API endpoints + APScheduler (Garmin sync כל 30 דק')
│   ├── parser.py             # פרסור GPX/KML/CSV + חישוב סטטיסטיקות
│   ├── db.py                 # SQLite CRUD
│   ├── garmin_sync.py        # סנכרון Garmin Connect + ניהול טוקנים
│   ├── whoop_sync.py          # סנכרון Whoop API v2 + OAuth2 refresh
│   ├── requirements.txt      # תלויות Python
│   ├── Dockerfile
│   ├── tokens/               # טוקני Garmin (לא ב-git!)
│   └── .env                  # GARMIN_EMAIL, GARMIN_PASSWORD, WHOOP_ACCESS_TOKEN, WHOOP_REFRESH_TOKEN (לא ב-git!)
│
├── frontend/                 # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.tsx           # דשבורד ראשי — סטטיסטיקות, מפה, גרפים, ניתוח
│   │   ├── main.tsx          # entry point
│   │   ├── components/
│   │   │   ├── UploadZone.tsx # אזור גרירת קבצים
│   │   │   └── MapView.tsx    # מפת Leaflet עם צביעת מסלול
│   │   └── lib/
│   │       ├── gpxParser.ts  # פרסור GPX בצד לקוח
│   │       └── haversine.ts  # חישוב מרחק הבוורסין
│   ├── index.html            # Tailwind CDN + config + Heebo font
│   ├── package.json
│   ├── vite.config.ts        # proxy /api → localhost:8000
│   ├── tailwind.config.js    # (כרגע לא פעיל — Tailwind רץ מ-CDN)
│   ├── postcss.config.js     # (כרגע לא פעיל)
│   └── Dockerfile
│
├── docker-compose.yml        # backend:8000 + frontend:5173
├── sample_gpx_gpx.txt        # דוגמת GPX לבדיקה
├── sample_kml_kml.txt        # דוגמת KML לבדיקה
└── README.md
```

---

## API Endpoints

| Method | Path | תיאור |
|--------|------|--------|
| `POST` | `/api/upload` | העלאת קובץ GPX/KML/CSV/TCX — מחזיר ריצה + נקודות |
| `GET` | `/api/runs` | רשימת כל הריצות (מיון לפי תאריך יורד) |
| `GET` | `/api/runs/{id}` | פרטי ריצה בודדת עם כל הנקודות |
| `DELETE` | `/api/runs/{id}` | מחיקת ריצה |
| `POST` | `/api/sync/garmin` | סנכרון ידני מ-Garmin (פרמטר `limit` אופציונלי, ברירת מחדל 10) |
| `POST` | `/api/sync/whoop` | סנכרון ידני מ-Whoop (פרמטר `days` אופציונלי, ברירת מחדל 7) |
| `GET` | `/api/whoop/recovery` | נתוני recovery — recovery_score, resting_hr, HRV, SpO2, skin_temp |
| `GET` | `/api/whoop/sleep` | נתוני שינה — performance%, efficiency%, שלבי שינה (deep/rem/light) |
| `GET` | `/api/whoop/cycle` | נתוני cycle — strain, קלוריות, דופק ממוצע/מקס |
| `GET` | `/api/stats/summary` | סיכום: מספר ריצות, סה"ב ק"מ |

---

## איך מריצים

### מקומית (Dev)

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # ערוך: GARMIN_EMAIL, GARMIN_PASSWORD
uvicorn main:app --reload --port 8000

# Frontend (טרמינל שני)
cd frontend
npm install
npm run dev
```

פתח http://localhost:5173

### Docker

```bash
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

---

## סנכרון Garmin — בטוח

1. צור `backend/.env` עם `GARMIN_EMAIL` ו-`GARMIN_PASSWORD` — **אל תעלה ל-git**
2. הרצה ראשונה: `python garmin_sync.py` — יבקש קוד 2FA פעם אחת וישמור טוקנים ב-`tokens/`
3. מעכשיו סנכרון אוטומטי: APScheduler רץ כל 30 דק' ברקע, או ידנית דרך `POST /api/sync/garmin`
4. הטוקן מתרענן לבד — אין צורך בסיסמה שוב

> **טוקנים ו-.env לעולם לא ב-git.** הקובץ `.gitignore` מדיר אותם.

---

## סנכרון Whoop — בטוח

1. צור OAuth app ב-[Whoop Developer Portal](https://developer.whoop.com) עם redirect URI `http://localhost:8081/callback`
2. השלם OAuth2 PKCE flow פעם אחת (דרך Hermes או ידנית) — מקבל `access_token` + `refresh_token`
3. הוסף ל-`backend/.env`:
   ```
   WHOOP_CLIENT_ID=your_client_id
   WHOOP_CLIENT_SECRET=your_client_secret
   WHOOP_ACCESS_TOKEN=your_access_token
   WHOOP_REFRESH_TOKEN=your_refresh_token
   ```
4. מעכשיו סנכרון אוטומטי: APScheduler רץ כל 15 דק' ברקע, או ידנית דרך `POST /api/sync/whoop`
5. ה-access token מתרענן אוטומטית ב-401 — ה-refresh token נשמר ב-.env

### טבלאות Whoop ב-DB

| טבלה | נתונים |
|------|--------|
| `whoop_recovery` | recovery_score, resting_heart_rate, hrv_rmssd_ms, spo2_pct, skin_temp_c, day_strain |
| `whoop_sleep` | sleep_performance_pct, sleep_efficiency_pct, total_sleep_milli, deep/rem/light_sleep_milli, sleep_need_milli |
| `whoop_cycle` | strain, kilojoule, energy_burned_cal, avg_heart_rate, max_heart_rate |

---

## לוגיקת עיבוד — לא לגעת

שתי פונקציות ליבה ב-`backend/parser.py` הן קריטיות ומכויילות לדיוק מקסימלי:

### `haversine(lat1, lon1, lat2, lon2)`
מרחק במטרים בין שתי נקודות (R = 6,371,000 מ'). סטנדרטי, לא לשנות.

### `moving_average(arr, w)`
החלקה (smoothing) עם **edge-padded convolution** — מונעת רמפות מלאכותיות בתחילת/סוף המסלול. חלון ברירת מחדל 15, מורחב ל-30 לגובה.

### חישוב עלייה (total_ascent)
- דגימת גובה ממוצע מקודקד כל **60 שניות** (מסנן noise של GPS)
- ספירת עליות **מתמשכות ≥ 2 מטר** בלבד בין דגימות (לא כל תנודה)
- זה מתאים לדרך ש-Garmin מדווח עלייה נטו לכל טיפוס, לא סכום של כל jitter

### זיהוי ריצה רציפה
`is_continuous = True` כאשר משך הריצה בין 18 ל-45 דקות.

---

## מה האפליקציה צריכה להיות (Roadmap)

### עיצוב — שפת עיצוב מלאה
האפליקציה כרגע מעוצבת **dark theme** (סגול/כחול) עם Tailwind CDN. יש ליישם שפת עיצוב חדשה בהשראת דוח עיצובי חיצוני:

- **פונט:** Heebo (במקום system-ui)
- **פלטה:** אדום `#ef4444` (פעולה), ירוק `#22c55e` (חיובי), ענבר `#f59e0b` (עלייה), כחול `#3b82f6` (ירידה)
- **בלי סגול** — להסיר את כל ה-accent violet/blue-500
- **Pills עגולים** (`rounded-full`), כותרות `font-black`, מספרים ב-`font-mono`
- **שני כיוונים:** Light theme (משטחים בהירים, רקע `#f8f7f5`, כרטיסים לבנים) ו-Dark theme (משטחים כהים עם אותה פלטה)

### מעבר ל-Tailwind Build-Time
כרגע Tailwind רץ מ-CDN (`cdn.tailwindcss.com`) — **לא מתאים לפרודקשן**. יש לעבור ל-pipeline build-time:
1. להוסיף `src/index.css` עם `@tailwind base/components/utilities`
2. לייבא אותו ב-`main.tsx`
3. להעביר טוקנים + Heebo ל-`tailwind.config.js`
4. להסיר את סקריפט ה-CDN מ-`index.html`

### תכונות עתידיות
- דף `/settings` לשמירת `GARMIN_EMAIL` ב-localStorage
- השוואת ריצות (side-by-side)
- ייצוא סיכום ל-PDF
- מעקב נעליים — ק"מ מצטברים והתראה על בלאי
- אינטגרציה Strava (נוסף על Garmin)
- PWA — שמירה לאופליין

---

## נקודת התחלה להרמס Agent

הפרומפט המקורי:

> "בנה והרץ את Volkov Run Lab לפי הקוד המצורף. אל תשנה לוגיקת haversine ו moving_average. ודא ש POST /api/upload עובד עם הקבצים המצורפים gpx.txt ו kml.txt. הוסף דף /settings לשמירת GARMIN_EMAIL ב localStorage וקריאה מ .env ב backend. הוסף background job כל 30 דקות שקורא ל garmin_sync.sync()"

---

## דוגמת נתונים

ריצת הבוקר: 3.01 ק"מ, 22:39 דק', קצב 7:32 דק'/ק"מ, דופק ממוצע 133.
העלייה האמיתית: 8.6 מ' בדקות 12.5-15, הירידה: 2.7 מ' בדקות 16-18 עם דופק 138.

---

## טכנולוגיות

| שכבה | טכנולוגיה |
|------|----------|
| Backend | FastAPI 0.110, Uvicorn, SQLite, APScheduler |
| פרסור | gpxpy 1.5, pandas 2.2, lxml 5.2, numpy 1.26 |
| Garmin | garminconnect 0.2.21 + garth (טוקנים) |
| Whoop | Whoop API v2 (OAuth2 PKCE, auto-refresh) |
| Frontend | React 18, Vite 5, TypeScript 5.3 |
| UI | Tailwind CSS 3.4 (CDN), Lucide icons |
| גרפים | Recharts 3.9 |
| מפות | React-Leaflet 4.2, OpenStreetMap |
| Container | Docker Compose (Python 3.11 + Node 20) |

---

🪽 Hermes · 2026-07-14