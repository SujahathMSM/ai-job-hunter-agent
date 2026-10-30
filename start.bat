@echo off
title NexusHunt AI Launcher
echo ====================================================
echo        Launching NexusHunt AI (Backend + UI)        
echo ====================================================
echo.

if "%BACKEND_PORT%"=="" set BACKEND_PORT=8000

:: 1. Launch FastAPI Backend
start "NexusHunt - FastAPI Backend (:%BACKEND_PORT%)" cmd /k "cd /d "%~dp0" && python -m uvicorn api:app --port %BACKEND_PORT% --reload"

:: 2. Launch Next.js Frontend on port 3000
start "NexusHunt - Next.js Frontend (:3000)" cmd /k "cd /d "%~dp0frontend" && set BACKEND_PORT=%BACKEND_PORT% && npm run dev"

echo [OK] Backend server started at: http://127.0.0.1:%BACKEND_PORT%
echo [OK] Frontend web app starting at: http://localhost:3000
echo.
echo Leave this window or close it. Press any key to exit launcher...
pause >nul
