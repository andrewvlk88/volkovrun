
# Volkov Run Lab - Garmin Auto Sync Edition

מערכת מלאה לניתוח ריצות Garmin עם מפה, גובה, מהירות, דופק והיסטוריה.

## מה יש בפנים
- Backend FastAPI + SQLite
- פרסור GPX / KML / CSV (כולל פורמט Interval של Garmin)
- סנכרון אוטומטי מ Garmin Connect עם garminconnect + שמירת טוקן
- Frontend React + Leaflet + Chart.js עם צביעה לפי מהירות/גובה/דופק
- זיהוי ריצה רציפה וסימון דקות 12.5-15 (עלייה) ו 16-18 (דיליי עייפות)

## הרצה מהירה
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# ערוך .env עם GARMIN_EMAIL ו GARMIN_PASSWORD - רק מקומית!
uvicorn main:app --reload --port 8000

# טרמינל שני
cd frontend
npm install
npm run dev
```
פתח http://localhost:5173

## סנכרון Garmin - בטוח
1. צור .env מקומי, אל תעלה ל git
2. הרצה ראשונה: `python garmin_sync.py` - יבקש קוד 2FA פעם אחת וישמור tokens/ 
3. מעכשיו הרצה אוטומטית: `POST /api/sync/garmin` או cron כל 30 דקות
4. הטוקן מתרענן לבד, אין צורך בסיסמה שוב

## Docker
```bash
docker-compose up --build
```

## להרמס Agent (GLM 5.2)
תן להרמס את כל התיקייה הזו כפי שהיא. הפרומפט:
"בנה והרץ את Volkov Run Lab לפי הקוד המצורף. אל תשנה לוגיקת haversine ו moving_average. ודא ש POST /api/upload עובד עם הקבצים המצורפים gpx.txt ו kml.txt. הוסף דף /settings לשמירת GARMIN_EMAIL ב localStorage וקריאה מ .env ב backend. הוסף background job כל 30 דקות שקורא ל garmin_sync.sync()"

## דוגמת נתונים
ריצת הבוקר 3.01 ק"מ 22:39 קצב 7:32 דופק 133 - העלייה האמיתית 8.6מ' ב 12.5-15 דק', הירידה 2.7מ' ב 16-18 דק' עם דופק 138.
