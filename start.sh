#!/bin/bash
# Volkov Run Lab — startup script
# מפעיל backend + frontend אחרי ריבוט
# שימוש: bash start.sh

set -e
cd "$(dirname "$0")"

echo "🚀 Volkov Run Lab starting..."

# Backend
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -q 2>/dev/null
python -c "from db import init_db; init_db()" 2>/dev/null
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ Backend PID $BACKEND_PID on :8000"

# Frontend
cd ../frontend
npm install -q 2>/dev/null
npx vite --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
echo "✅ Frontend PID $FRONTEND_PID on :5173"

# Jobs (cron-style)
# כל 30 דקות: Garmin sync
# כל 15 דקות: Whoop sync
# מופעל דרך Hermes cron — לא כאן

echo ""
echo "🪽 Volkov Run Lab running:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API docs: http://localhost:8000/docs"
echo ""

# Wait for exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped'" EXIT
wait