@echo off
TITLE PriceScope Intelligence - LOCAL SETUP
echo ==========================================================
echo    PRICESCOPE AI - AUTOMATED LOCAL INSTALLATION
echo ==========================================================
echo.

:: 1. Backend Installation
echo [1/3] Installing Python dependencies...
pip install -r backend/requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ ERROR: Python install failed. Ensure you have Python installed and venv active.
    pause
    exit /b %ERRORLEVEL%
)

:: 2. Playwright Browser Installation
echo.
echo [2/3] Installing Scraper Browser (Chromium)...
playwright install chromium
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ ERROR: Playwright install failed.
    pause
    exit /b %ERRORLEVEL%
)

:: 3. Frontend Installation
echo.
echo [3/3] Installing Node.js dependencies (Frontend)...
cd frontend
call npm install
cd ..
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ ERROR: Node.js install failed. Ensure you have Node.js installed.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ==========================================================
echo ✅ SETUP COMPLETE! 
echo You can now run the app using: run_local.bat
echo ==========================================================
pause
