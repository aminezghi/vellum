@echo off
setlocal enabledelayedexpansion
title Vellum Desktop V2.0 - Botanical Bento Edition
cd /d "%~dp0"

cls
echo =====================================================================
echo       VELLUM DESKTOP V2.0 (FERNLY BOTANICAL BENTO EDITION)
echo       ASReview Active Learning Screening + Connected Papers Hub
echo =====================================================================
echo.

set "PY_BIN="

if exist ".venv\Scripts\python.exe" (
    set "PY_BIN=.venv\Scripts\python.exe"
    echo [OK] Using local virtual environment [.venv]
) else (
    where python >nul 2>nul
    if !errorlevel! equ 0 (
        set "PY_BIN=python"
        echo [OK] Using system Python
    ) else (
        where py >nul 2>nul
        if !errorlevel! equ 0 (
            set "PY_BIN=py -3"
            echo [OK] Using Python Launcher
        )
    )
)

if "%PY_BIN%"=="" (
    echo [ERROR] Python 3.10+ was not found on your system!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [*] Launching Vellum Desktop V2.0 at http://localhost:8501 ...
start "Vellum Desktop Server" "%PY_BIN%" -m streamlit run pdf_downloader_app.py --server.port=8501 --server.headless=false --browser.gatherUsageStats=false

ping 127.0.0.1 -n 3 >nul
exit /b 0
