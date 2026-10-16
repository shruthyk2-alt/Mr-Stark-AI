@echo off
title MR. STARK // VITE REACT FRONTEND
cd /d "%~dp0frontend"
echo ===================================================
echo   MR. STARK // VITE + REACT + THREE.JS COMMAND UI
echo ===================================================
set "PATH=C:\Users\Admin\.node;%PATH%"
echo Starting Vite Dev Server on http://localhost:5173 ...
call npm run dev
pause
