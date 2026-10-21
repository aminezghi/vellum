@echo off
title Vellum Web (Fernly Botanical Bento Edition) - Academic Research Studio
cd /d "%~dp0"

echo =====================================================================
echo       VELLUM WEB (FERNLY BOTANICAL BENTO EDITION)
echo       Academic Research Studio - Force Networks - AI Screening
echo =====================================================================
echo.

:: Verify Node.js presence
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 18+ was not found on your system!
    echo Please install Node.js from https://nodejs.org/ (LTS recommended)
    echo Ensure "Add to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Node.js environment detected.
echo [*] Starting Next.js 16 Turbopack server on http://localhost:3002 ...
echo.

:: Launch browser in background after 3 seconds
start "" cmd /c "timeout /t 3 >nul & start http://localhost:3002"

:: Run Next.js server on port 3002
set PORT=3002
call npx next dev --turbopack -p 3002
if %errorlevel% neq 0 (
    echo [ERROR] Server exited with an error code.
    pause
)
