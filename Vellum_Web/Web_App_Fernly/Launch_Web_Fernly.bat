@echo off
title Vellum Web (Fernly Botanical Bento Edition) - Academic Research Studio
cd /d "%~dp0"

echo =====================================================================
echo       VELLUM WEB (FERNLY BOTANICAL BENTO EDITION)
echo       Botanical Bento Workspace - Fluid Physics - Micro-Interactions
echo =====================================================================
echo.

:: Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 18+ was not found on your system!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Fernly Design environment verified.
echo [*] Starting Next.js 16 Turbopack server on http://localhost:3002 ...
echo.

:: Launch browser in background after 3 seconds targeting port 3002
start "" cmd /c "timeout /t 3 >nul & start http://localhost:3002"

:: Start the Next.js dev server on port 3002
set PORT=3002
call npx next dev --turbopack -p 3002
if %errorlevel% neq 0 (
    echo [ERROR] Next.js dev server exited with an error.
    pause
)
