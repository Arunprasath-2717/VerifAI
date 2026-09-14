@echo off
echo Starting VerifAI Backend...
start cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"

echo Starting VerifAI Frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)
call npm run dev
