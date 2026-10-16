@echo off
title MR. STARK // BACKEND API SERVER
cd /d "%~dp0"
echo ===================================================
echo   MR. STARK // AI INTELLIGENCE GATEWAY (FASTAPI)
echo ===================================================
echo Starting FastAPI backend on http://127.0.0.1:8000 ...
".venv\Scripts\python.exe" -m uvicorn server.api:app --host 127.0.0.1 --port 8000 --reload
pause
