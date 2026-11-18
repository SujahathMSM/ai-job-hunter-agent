@echo off
title NexusHunt AI Launcher
echo ====================================================
echo        Launching NexusHunt AI (Backend + UI)        
echo ====================================================
echo.

if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8005"

:: Single-user local mode: use the app on this PC without signing in.
:: The backend only listens on 127.0.0.1. Remove this line to require sign-in.
if "%ALLOW_DEV_AUTH%"=="" set "ALLOW_DEV_AUTH=true"

:: 1. Launch FastAPI Backend (api.py sets up auto-reload, ignoring .venv and frontend)
:: Uses uv when installed (installs/updates dependencies from uv.lock first),
:: otherwise the Python environment you installed requirements.txt into.
where uv >nul 2>nul
if %ERRORLEVEL%==0 (
    start "NexusHunt - FastAPI Backend" cmd /k "cd /d "%~dp0" && uv run python api.py"
) else (
    start "NexusHunt - FastAPI Backend" cmd /k "cd /d "%~dp0" && python api.py"
)

:: 2. Launch Next.js Frontend on port 3000 (inherits BACKEND_PORT from this window)
start "NexusHunt - Next.js Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [OK] Backend server started at: http://127.0.0.1:%BACKEND_PORT%
echo [OK] Frontend web app starting at: http://localhost:3000
echo.
echo Leave this window or close it. Press any key to exit launcher...
pause >nul
