@echo off
setlocal enabledelayedexpansion
title Vellum Desktop V2.0 - Standalone Executable
cd /d "%~dp0"

cls
echo =====================================================================
echo       VELLUM DESKTOP V2.0 (STANDALONE EXECUTABLE)
echo       Zero Python Required - Native Windows Bundle
echo =====================================================================
echo.

:: 1. Prefer an installed copy (per-user install location used by the installer).
set "INSTALLED=%LOCALAPPDATA%\Programs\Vellum Desktop\Vellum.exe"

:: 2. Fall back to the portable bundle shipped inside Desktop_App\dist.
set "PORTABLE=%~dp0Desktop_App\dist\Vellum\Vellum.exe"

if exist "%INSTALLED%" (
    echo [*] Launching installed Vellum Desktop V2.0...
    start "" "%INSTALLED%"
    echo [OK] Vellum Desktop V2.0 is running!
) else if exist "%PORTABLE%" (
    echo [*] Launching portable Vellum.exe...
    start "" "%PORTABLE%"
    echo [OK] Vellum Desktop V2.0 is running!
) else (
    echo [!] No compiled binary found.
    echo [*] Run Vellum-Desktop-V2.0-Setup-x64.exe in this folder, or fall back to the source launcher...
    call "%~dp0CLICK_TO_RUN_VELLUM_DESKTOP.bat"
)

ping 127.0.0.1 -n 3 >nul
exit /b 0
