@echo off
title NexusHunt AI Launcher
echo ====================================================
echo        Launching NexusHunt AI (Backend + UI)        
echo ====================================================
echo.

:: 1. Launch FastAPI Backend on port 8000
start "NexusHunt - FastAPI Backend (:8000)" cmd /k "cd /d "%~dp0" && python -m uvicorn api:app --port 8000 --reload"

:: 2. Launch Next.js Frontend on port 3000
start "NexusHunt - Next.js Frontend (:3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [OK] Backend server started at: http://127.0.0.1:8000
echo [OK] Frontend web app starting at: http://localhost:3000
echo.
echo Leave this window or close it. Press any key to exit launcher...
pause >nul
