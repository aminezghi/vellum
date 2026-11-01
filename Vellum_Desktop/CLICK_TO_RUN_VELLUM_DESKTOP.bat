@echo off
setlocal enabledelayedexpansion
title Vellum Desktop V2.1 - Botanical Bento Edition
cd /d "%~dp0"

cls
echo =====================================================================
echo       VELLUM DESKTOP V2.1 (FERNLY BOTANICAL BENTO EDITION)
echo       ASReview Active Learning Screening + Connected Papers Hub
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

:: 2. Fast sanity check on dependencies
"%PY_BIN%" -c "import streamlit, sklearn, pandas" >nul 2>nul
if !errorlevel! neq 0 (
    echo [..] Installing required scientific packages into virtualenv...
    "%PY_BIN%" -m pip install -r requirements.txt scikit-learn
    if !errorlevel! neq 0 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

echo [*] Initializing Vellum Desktop V2.1 server...
echo [*] Opening interface at http://localhost:8501 ...
echo.

:: 3. Launch Streamlit and open browser window
start "Vellum Desktop Server" "%PY_BIN%" -m streamlit run pdf_downloader_app.py --server.port=8501 --server.headless=false --browser.gatherUsageStats=false

echo =====================================================================
echo [SUCCESS] Vellum Desktop V2.1 is now running!
echo Interface URL: http://localhost:8501
echo =====================================================================
ping 127.0.0.1 -n 3 >nul
exit /b 0
