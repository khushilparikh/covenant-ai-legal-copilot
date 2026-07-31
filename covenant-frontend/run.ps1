# Run this from INSIDE the covenant-frontend folder:
#   .\run.ps1
$ErrorActionPreference = "Stop"

if (-not (Test-Path "node_modules")) {
    Write-Host "No node_modules found. Run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

npm run dev
