@echo off
title Vellum - Launching Desktop Workbench + Web Studio
cd /d "%~dp0"

echo =====================================================================
echo       VELLUM - LAUNCHING DESKTOP WORKBENCH + WEB STUDIO
echo       Desktop: http://localhost:8501   |   Web: http://localhost:3002
echo =====================================================================
echo.

start "Vellum Desktop Workbench" "%~dp0Vellum_Desktop\1_launch_desktop_app.bat"
start "Vellum Web Studio" "%~dp0Vellum_Web\2_launch_fernly_web_app.bat"

echo [OK] Both applications launched.
echo      Desktop Workbench : http://localhost:8501
echo      Web Studio       : http://localhost:3002
echo.
timeout /t 3 >nul
exit /b 0
