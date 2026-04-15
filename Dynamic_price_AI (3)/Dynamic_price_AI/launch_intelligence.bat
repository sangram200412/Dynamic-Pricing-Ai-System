@echo off
TITLE PriceScope Intelligence - System Boot
SETLOCAL EnableDelayedExpansion

:: ── Professional Boot Sequence ──
echo ==========================================================
echo    PRICESCOPE AI - ADVANCED MARKET SURVEILLANCE v3.1.0
echo ==========================================================
echo.
echo [1/3] Terminating existing nodes...
docker compose down >nul 2>&1

echo [2/3] Initializing 7-Node Neural Fleet...
echo (Amazon, Flipkart, eBay, Meesho, Reliance, Myntra, Snapdeal)
echo.

:: Run docker-compose with build and force-recreate
docker compose up --build --force-recreate

echo.
echo [3/3] System Deployment Initialized.
echo ----------------------------------------------------------
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo ----------------------------------------------------------
echo.
echo Dashboard will be LIVE in a few seconds...
pause
