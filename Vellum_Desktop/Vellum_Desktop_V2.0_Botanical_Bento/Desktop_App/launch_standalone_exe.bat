@echo off
title Vellum Desktop - Standalone Executable
cd /d "%~dp0"

echo =====================================================================
echo          VELLUM DESKTOP - STANDALONE EXECUTABLE (NO PYTHON REQUIRED)
echo          Author: Amine Zouaghi
echo =====================================================================
echo.

if exist "dist\Vellum\Vellum.exe" (
    echo [*] Launching compiled standalone Vellum.exe...
    start "" "dist\Vellum\Vellum.exe"
    echo [OK] Standalone Vellum is running!
) else (
    echo [!] Standalone binary not found at dist\Vellum\Vellum.exe.
    echo [*] Falling back to standard Python launcher...
    call Launch_Desktop.bat
)

timeout /t 3 >nul
exit /b 0
