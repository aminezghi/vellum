@echo off
title Vellum by Amine - Web App
cd /d "%~dp0"

echo =====================================================================
echo       VELLUM BY AMINE - WEB STUDIO
echo       Academic Research Studio - Force Networks - AI Screening
echo =====================================================================
echo.

where node >nul 2>nul
if errorlevel 1 goto no_node

echo [OK] Node.js environment detected.
set "PORT=3002"

:: Prefer the production build: it is faster, has no dev overlay and does
:: not recompile on every navigation. Fall back to the dev server only when
:: no production build is present.
if exist ".next\BUILD_ID" goto production

echo [*] No production build found - starting the development server
echo     on http://localhost:%PORT% ...
echo.
start "" cmd /c "timeout /t 3 >nul & start http://localhost:%PORT%"
call npx next dev -p %PORT%
if errorlevel 1 goto dev_failed
exit /b 0

:production
echo [*] Starting the production server on http://localhost:%PORT% ...
echo.
start "" cmd /c "timeout /t 3 >nul & start http://localhost:%PORT%"
call npx next start -p %PORT%
if errorlevel 1 goto prod_failed
exit /b 0

:prod_failed
echo [ERROR] The production server exited with an error code.
echo         Falling back to the development server...
call npx next dev -p %PORT%
if errorlevel 1 goto dev_failed
exit /b 0

:dev_failed
echo [ERROR] The development server exited with an error code.
echo         Build it first with:  npx next build
pause
exit /b 1

:no_node
echo [ERROR] Node.js 18 or newer was not found on your system.
echo         Please install the LTS release from https://nodejs.org/
echo         and tick "Add to PATH" during setup.
echo.
echo         Alternatively, run the self-contained package from DISTRIBUTABLES
echo         which bundles its own Node.js runtime and needs nothing installed.
echo.
pause
exit /b 1
