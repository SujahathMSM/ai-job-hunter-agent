@echo off
title NexusHunt AI Launcher
echo ====================================================
echo        Launching NexusHunt AI (Backend + UI)        
echo ====================================================
echo.

if "%BACKEND_PORT%"=="" set BACKEND_PORT=8005

:: Single-user local mode: use the app on this PC without signing in.
:: The backend only listens on 127.0.0.1. Remove this line to require sign-in.
if "%ALLOW_DEV_AUTH%"=="" set ALLOW_DEV_AUTH=true

:: 1. Launch FastAPI Backend
:: Use uv when installed (installs/updates dependencies from uv.lock automatically),
:: otherwise the Python environment you installed requirements.txt into.
where uv >nul 2>nul
if %ERRORLEVEL%==0 (
    set "BACKEND_CMD=uv run uvicorn api:app --port %BACKEND_PORT% --reload"
) else (
    set "BACKEND_CMD=python -m uvicorn api:app --port %BACKEND_PORT% --reload"
)
start "NexusHunt - FastAPI Backend (:%BACKEND_PORT%)" cmd /k "cd /d "%~dp0" && %BACKEND_CMD%"

:: 2. Launch Next.js Frontend on port 3000
start "NexusHunt - Next.js Frontend (:3000)" cmd /k "cd /d "%~dp0frontend" && set BACKEND_PORT=%BACKEND_PORT% && npm run dev"

echo [OK] Backend server started at: http://127.0.0.1:%BACKEND_PORT%
echo [OK] Frontend web app starting at: http://localhost:3000
echo.
echo Leave this window or close it. Press any key to exit launcher...
pause >nul
