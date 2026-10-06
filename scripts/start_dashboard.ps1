# scripts/start_dashboard.ps1
# Script para iniciar GeoAI-Au Explorer en desarrollo local en Windows PowerShell

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Iniciando GeoAI-Au Explorer: Mineral Prospectivity Intelligence" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Verificar fuentes científicas
Write-Host "[1/3] Verificando inmutabilidad de fuentes científicas selladas..." -ForegroundColor Yellow
python scripts/verify_dashboard_sources.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: La verificación de integridad científica falló. Abortando inicio." -ForegroundColor Red
    exit 1
}

# 2. Iniciar API Backend
Write-Host "[2/3] Iniciando backend FastAPI en http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload"

# 3. Iniciar Frontend Next.js
Write-Host "[3/3] Iniciando frontend Next.js en http://localhost:3000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location apps/web; npm run dev"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "GeoAI-Au Explorer en ejecución:" -ForegroundColor White
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "  - Documentación OpenAPI: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
