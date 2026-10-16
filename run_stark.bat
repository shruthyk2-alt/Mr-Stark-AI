@echo off
title MR. STARK // MASTER LAUNCHER
cd /d "%~dp0"
echo ===================================================
echo   INITIALIZING MR. STARK AI COMMAND CENTRE v2.0
echo ===================================================
echo [1/2] Launching Python FastAPI Intelligence Node...
start "MR. STARK BACKEND" run_backend.bat

echo [2/2] Launching Vite React Three.js Frontend...
start "MR. STARK FRONTEND" run_frontend.bat

echo Waiting 3 seconds for servers to initialize...
timeout /t 3 /nobreak >nul

echo Launching Mr. Stark Command Centre in browser...
start http://localhost:5173

echo System initialized. Press any key to exit this launcher window.
pause >nul
