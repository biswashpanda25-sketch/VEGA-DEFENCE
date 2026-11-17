@echo off
REM Start VEGA unified server (FastAPI serving API + prebuilt Frontend on port 8000)
cd /d "%~dp0"

echo ========================================================
echo Starting VEGA (Gotham India) Unified Server...
echo ========================================================

IF NOT EXIST "backend\.venv\Scripts\python.exe" (
    echo Virtual environment not found. Setting up...
    cd backend
    uv venv --python 3.12
    uv pip install -r requirements.txt
    cd ..
)

echo.
echo Application will be available at: http://localhost:8000
echo API documentation available at:   http://localhost:8000/api/docs
echo.
echo Demo Accounts (Password for all: Gotham@2026):
echo   - analyst@gotham-demo.in   (Analyst - Infrastructure Directorate)
echo   - reviewer@gotham-demo.in  (Reviewer - Approval Authority)
echo   - admin@gotham-demo.in     (Platform Administrator)
echo   - disaster@gotham-demo.in  (Disaster Coordination Cell)
echo.
echo Press Ctrl+C to stop the server.
echo.

backend\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
pause

