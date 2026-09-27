@echo off
echo ======================================================================
echo Iniciando GeoAI-Au Explorer (Backend FastAPI + Frontend Next.js)
echo ======================================================================

echo [1/2] Levantando Backend FastAPI en http://localhost:8000 ...
start "GeoAI-Au API Backend" cmd /k "python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Levantando Frontend Next.js en http://localhost:3000 ...
cd apps\web
start "GeoAI-Au Web Frontend" cmd /k "npm run dev"

echo.
echo GeoAI-Au Explorer iniciado correctamente.
echo Accede en tu navegador a: http://localhost:3000
echo Documentacion de la API:  http://localhost:8000/docs
echo ======================================================================
