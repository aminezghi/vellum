@echo off
title Vellum Web (Apple Design Edition) - Academic Research Studio
cd /d "%~dp0"

echo =====================================================================
echo       VELLUM WEB (APPLE DESIGN EDITION) - AMINE ZOUAGHI
echo       Fluid Physics - Translucent Vibrancy - Continuous Squircles
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

echo [OK] Apple Design environment verified.
echo [*] Starting Next.js 16 Turbopack server on http://localhost:3001 ...
echo.

:: Launch browser in background after 3 seconds targeting port 3001
start "" cmd /c "timeout /t 3 >nul & start http://localhost:3001"

:: Start the Next.js dev server on port 3001
set PORT=3001
call npx next dev --turbopack -p 3001
if %errorlevel% neq 0 (
    echo [ERROR] Next.js dev server exited with an error.
    pause
)
