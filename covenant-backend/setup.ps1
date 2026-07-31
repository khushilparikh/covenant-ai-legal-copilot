# Run this from INSIDE the covenant-backend folder:
#   .\setup.ps1
#
# If PowerShell blocks scripts, first run (one time, as your user, not admin):
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$ErrorActionPreference = "Stop"

Write-Host "== Covenant backend setup ==" -ForegroundColor Cyan

# --- 1. Find a compatible Python (3.11 or 3.12 - NOT 3.13/3.14, wheels aren't ready yet) ---
$pythonCmd = $null
foreach ($ver in @("3.12", "3.11")) {
    $check = & py "-$ver" --version 2>$null
    if ($LASTEXITCODE -eq 0) { $pythonCmd = "-$ver"; break }
}
if (-not $pythonCmd) {
    Write-Host "No Python 3.11 or 3.12 found via 'py'. Install Python 3.12 from python.org, then re-run this script." -ForegroundColor Red
    exit 1
}
Write-Host "Using Python $pythonCmd"

# --- 2. Create venv if it doesn't already exist ---
if (-not (Test-Path "venv")) {
    py $pythonCmd -m venv venv
    Write-Host "Created venv/"
} else {
    Write-Host "venv/ already exists - reusing it"
}

# --- 3. Activate and install ---
& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# --- 4. .env ---
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Created .env - EDIT IT NOW and set DATABASE_URL to your real Postgres password," -ForegroundColor Yellow
    Write-Host "then re-run this script (or just continue manually from 'Train models' below)." -ForegroundColor Yellow
    notepad .env
    Read-Host "Press Enter once you've saved .env with your Postgres password"
}

# --- 5. Train ML models ---
Write-Host ""
Write-Host "== Training clause classifier ==" -ForegroundColor Cyan
python -m app.ml.train_clause_classifier
Write-Host ""
Write-Host "== Training risk scoring model ==" -ForegroundColor Cyan
python -m app.ml.train_risk_model

# --- 6. Seed database ---
Write-Host ""
Write-Host "== Creating tables + demo user ==" -ForegroundColor Cyan
Write-Host "(Make sure PostgreSQL is running and the 'covenant' database exists - see README.md)" -ForegroundColor Yellow
python -m app.db.seed

Write-Host ""
Write-Host "Setup complete. Start the server with:" -ForegroundColor Green
Write-Host "    .\run.ps1"
Write-Host "or manually:"
Write-Host "    venv\Scripts\activate"
Write-Host "    uvicorn app.main:app --reload --port 8000"
