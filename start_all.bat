@echo off
title NexusCompute Launcher
echo ========================================================
echo      Starting NexusCompute Decentralized Marketplace
echo ========================================================
echo.

echo [1/3] Starting Backend Coordinator on http://localhost:8000...
start "NexusCompute Backend" cmd /k "cd backend && ..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Frontend Web Dashboard on http://localhost:3000...
start "NexusCompute Frontend" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 3000"

timeout /t 2 /nobreak >nul

echo [3/3] Starting Provider Worker Daemon...
start "NexusCompute Worker Daemon" cmd /k ".\.venv\Scripts\python worker/nexus_worker/cli.py start --token nx-node-0a0a3b29ed4e323af354549a6681821a1b75157e --emulate"

echo.
echo ========================================================
echo All 3 services are running!
echo Opening browser to: http://localhost:3000
echo ========================================================
timeout /t 2 /nobreak >nul
start http://localhost:3000
