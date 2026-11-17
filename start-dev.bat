@echo off
REM Start VEGA in Development Mode (Backend API on 8000 + Frontend Vite on 5173)
cd /d "%~dp0"

echo ========================================================
echo Starting VEGA Development Environment
echo ========================================================

start "VEGA Backend (FastAPI)" cmd /k "cd /d %~dp0backend && .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
start "VEGA Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

echo.
echo Started Backend on:  http://127.0.0.1:8000
echo Started Frontend on: http://localhost:5173
echo.
echo Demo Accounts (Password: Gotham@2026):
echo   - analyst@gotham-demo.in
echo   - reviewer@gotham-demo.in
echo   - admin@gotham-demo.in
echo   - disaster@gotham-demo.in
echo.
pause

