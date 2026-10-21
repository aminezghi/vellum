@echo off
setlocal enabledelayedexpansion
title Vellum Web 2.4 - Academic Research Studio
cd /d "%~dp0"

echo =====================================================================
echo              VELLUM WEB 2.4 - LOCAL-FIRST RESEARCH STUDIO
echo              Author: Amine Zouaghi
echo =====================================================================
echo.

:: Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 18+ was not found on your system!
    echo Please install Node.js (LTS recommended) from https://nodejs.org/
    pause
    exit /b 1
)

:: Check if node_modules exists, otherwise install
if not exist "node_modules\" (
    echo [..] First-time setup: installing dependencies via npm...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
)

echo [OK] Dependencies verified.
echo [*] Starting Next.js 16 Turbopack server on http://localhost:3000 ...

:: Launch browser in background after 2 seconds
start "" cmd /c "timeout /t 2 >nul & start http://localhost:3000"

:: Start the Next.js dev server on port 3000.
:: The port is pinned on purpose: an unpinned "next dev" falls back to the next
:: free port, which would let this edition land on another edition's port.
set PORT=3000
call npx next dev --turbopack -p 3000
if %errorlevel% neq 0 (
    echo [ERROR] Next.js dev server exited with an error.
    pause
)

pause
