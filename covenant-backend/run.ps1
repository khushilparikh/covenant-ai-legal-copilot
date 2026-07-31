# Run this from INSIDE the covenant-backend folder:
#   .\run.ps1
$ErrorActionPreference = "Stop"

if (-not (Test-Path "venv")) {
    Write-Host "No venv found. Run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

& .\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
