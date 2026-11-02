# VerifAI Local Fullstack Development Launcher (PowerShell)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "=== VerifAI Services Initialization ===" -ForegroundColor Cyan

# 1. Start Backend FastAPI on port 8000
Write-Host "[+] Starting FastAPI backend on http://127.0.0.1:8000..." -ForegroundColor Green
$env:PYTHONPATH = "backend"
$backendProcess = Start-Process -FilePath "$scriptDir\.venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000" `
    -PassThru

# Wait for backend health
Start-Sleep -Seconds 3

# 2. Start Frontend Dev Server on port 3000
Write-Host "[+] Starting Frontend dev server on http://localhost:3000..." -ForegroundColor Green
Set-Location "$scriptDir\frontend"
$frontendProcess = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run dev" `
    -PassThru

Write-Host "`n=== VerifAI Services Running ===" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend API: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "`nPress Ctrl+C or close windows to stop."
