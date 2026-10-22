@echo off
setlocal enabledelayedexpansion
title Vellum Desktop - Academic Literature Suite
cd /d "%~dp0"

echo =====================================================================
echo              VELLUM DESKTOP - ACADEMIC WORKBENCH
echo              Author: Amine Zouaghi
echo =====================================================================
echo.

:: Detect Python environment
set "PY_BIN="
if exist ".venv\Scripts\python.exe" (
    set "PY_BIN=.venv\Scripts\python.exe"
    echo [OK] Using dedicated local virtualenv (.venv)
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_BIN=python"
        echo [OK] Using system Python
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 (
            set "PY_BIN=py -3"
            echo [OK] Using Python Launcher (py -3)
        )
    )
)

if "%PY_BIN%"=="" (
    if exist "dist\Vellum\Vellum.exe" (
        echo [!] Python not found on system.
        echo [*] Launching standalone Vellum.exe (zero Python required)...
        start "" "dist\Vellum\Vellum.exe"
        timeout /t 3 >nul
        exit /b 0
    )
    echo [ERROR] Python 3.10+ was not found on your system!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Check if requirements are installed
echo [..] Checking dependencies...
"%PY_BIN%" -c "import streamlit, requests" >nul 2>nul
if %errorlevel% neq 0 (
    echo [..] Installing required packages from requirements.txt...
    "%PY_BIN%" -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install packages.
        pause
        exit /b 1
    )
)

echo.
echo [*] Launching Vellum Desktop Application...
if exist "vellum_launcher.py" (
    start "" "%PY_BIN%" vellum_launcher.py
) else (
    start "" "%PY_BIN%" -m streamlit run pdf_downloader_app.py
)

echo [OK] Vellum Desktop is running!
timeout /t 3 >nul
exit /b 0
