@echo off
echo Starting CampusShare...
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Setting up virtual environment...
    python -m venv venv
    echo Installing dependencies...
    .\venv\Scripts\pip install -r requirements.txt
    echo.
)

REM Create .env if it doesn't exist
if not exist ".env" (
    copy .env.example .env
    echo Created .env from .env.example
    echo.
)

REM Create uploads folder if it doesn't exist
if not exist "uploads" mkdir uploads

echo Opening browser at http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Open browser after 2 seconds
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

.\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
