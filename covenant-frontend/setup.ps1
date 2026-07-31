# Run this from INSIDE the covenant-frontend folder:
#   .\setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "== Covenant frontend setup ==" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env (default: VITE_API_BASE_URL=http://localhost:8000)"
}

npm install

Write-Host ""
Write-Host "Setup complete. Start it with:" -ForegroundColor Green
Write-Host "    .\run.ps1"
Write-Host "or manually:"
Write-Host "    npm run dev"
