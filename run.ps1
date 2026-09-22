# CampusShare - Run Script

Write-Host "Starting CampusShare..." -ForegroundColor Cyan

# Create venv if missing
if (-not (Test-Path "venv")) {
    Write-Host "Setting up virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    .\venv\Scripts\pip install -r requirements.txt
}

# Create .env if missing
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env file" -ForegroundColor Green
}

# Create uploads folder if missing
if (-not (Test-Path "uploads")) { New-Item -ItemType Directory -Path "uploads" | Out-Null }

# Open browser after 2 seconds in background
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8000"
} | Out-Null

Write-Host "Server starting at http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start server
.\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
