@echo off
REM Run all backend tests and frontend typecheck
cd /d "%~dp0"

echo ========================================================
echo Running Backend Pytest Suite (61 tests)...
echo ========================================================
cd backend
.venv\Scripts\python -m pytest tests -v
IF %ERRORLEVEL% NEQ 0 (
    echo Backend tests failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo Running AI Grounded Evaluation...
echo ========================================================
.venv\Scripts\python -m tests.eval_ai

echo.
echo ========================================================
echo Running Frontend Typecheck...
echo ========================================================
cd ..\frontend
call npm.cmd run typecheck
IF %ERRORLEVEL% NEQ 0 (
    echo Frontend typecheck failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo All checks passed successfully!
echo ========================================================
pause

