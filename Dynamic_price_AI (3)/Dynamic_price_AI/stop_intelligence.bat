@echo off
TITLE PriceScope Intelligence - System Shutdown
echo ==========================================================
echo    PRICESCOPE AI - SECURE SHUTDOWN SEQUENCE
echo ==========================================================
echo.
echo Deactivating all intelligence nodes...
docker compose down

echo.
echo [COMPLETED] System is offline.
pause
