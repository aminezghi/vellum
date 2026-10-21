@echo off
setlocal enabledelayedexpansion
title Vellum - Launching All Three Web Editions
cd /d "%~dp0"

echo =====================================================================
echo       VELLUM - LAUNCHING ALL THREE WEB EDITIONS
echo       Classic :3000   Apple :3001   Fernly :3002
echo =====================================================================
echo.
echo   Each edition keeps its OWN notebooks and preferences, even when
echo   they end up sharing a port, so the three never overwrite
echo   each other's work.
echo.

start "Vellum Web (Classic)"      "%~dp04_launch_web_app.bat"
start "Vellum Web (Apple)"        "%~dp05_launch_apple_web_app.bat"
start "Vellum Web (Fernly Bento)" "%~dp02_launch_fernly_web_app.bat"

echo [OK] All three web editions launched.
echo      Classic : http://localhost:3000
echo      Apple   : http://localhost:3001
echo      Fernly  : http://localhost:3002
echo.
timeout /t 3 >nul
exit /b 0
