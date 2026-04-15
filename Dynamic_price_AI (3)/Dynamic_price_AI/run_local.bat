@echo off
TITLE PriceScope Intelligence - LOCAL RUN
SETLOCAL EnableDelayedExpansion

echo ==========================================================
echo    PRICESCOPE AI - LOCAL DEPLOYMENT (No Docker)
echo ==========================================================
echo.

:: Start Backend in a new window
echo [1/2] Launching Backend Server...
start "PriceScope Backend" cmd /k "cd backend && python main.py"

:: Start Frontend in a new window
echo [2/2] Launching Frontend Dashboard...
start "PriceScope Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ----------------------------------------------------------
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo ----------------------------------------------------------
echo.
echo Both services are starting in separate windows.
echo Keep those windows open while using the app!
echo.
pause
