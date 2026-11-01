@echo off
setlocal enabledelayedexpansion
title Vellum by Amine - Desktop App
cd /d "%~dp0"

cls
echo =====================================================================
echo       VELLUM BY AMINE - DESKTOP WORKBENCH
echo       Active Learning Screening + Citation Exploration + Batch Harvester
echo =====================================================================
echo.

set "PY_BIN="

:: 1. Check dedicated Desktop_App virtualenv
if exist "%~dp0Desktop_App\.venv\Scripts\python.exe" (
    set "PY_BIN=%~dp0Desktop_App\.venv\Scripts\python.exe"
    echo [OK] Located dedicated local virtual environment [.venv]
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_BIN=%~dp0.venv\Scripts\python.exe"
    echo [OK] Located root virtual environment [.venv]
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
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [*] Target Directory: %~dp0Desktop_App
cd /d "%~dp0Desktop_App"

:: 2. Launch Streamlit app
echo [*] Starting Vellum Desktop on http://localhost:8501 ...
echo.
"%PY_BIN%" -m streamlit run pdf_downloader_app.py --browser.serverAddress localhost --server.port 8501
if !errorlevel! neq 0 (
    echo [ERROR] Failed to start Vellum Desktop.
    pause
    exit /b 1
)
