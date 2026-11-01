@echo off
title Vellum by Amine - Launching Both Apps
cd /d "%~dp0"

echo =====================================================================
echo       VELLUM BY AMINE - LAUNCHING DESKTOP WORKBENCH + WEB STUDIO
echo       Desktop: http://localhost:8501   ^|   Web: http://localhost:3002
echo =====================================================================
echo.

start "Vellum Desktop Workbench" "%~dp0launch_desktop.bat"
start "Vellum Web Studio" "%~dp0launch_web.bat"

echo [OK] Both applications launched.
echo      Desktop Workbench : http://localhost:8501
echo      Web Studio        : http://localhost:3002
echo.
timeout /t 3 >nul
exit /b 0
