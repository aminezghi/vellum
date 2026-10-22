@echo off
title Vellum Web (Fernly Botanical Bento Edition) - Academic Research Studio
cd /d "%~dp0"

:: NOTE ON STYLE: this script uses goto labels rather than a parenthesised
:: "if (...)" block for the error paths. A closing parenthesis inside an echo
:: line - for example "echo ... (LTS recommended)" - silently terminates the
:: block and makes cmd.exe misparse everything after it. Labels cannot be
:: broken that way.

echo =====================================================================
echo       VELLUM WEB (FERNLY BOTANICAL BENTO EDITION)
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
echo         Alternatively, send the colleague the self-contained package
echo         Vellum_Web_Fernly_SHARE.zip - it bundles its own Node.js
echo         runtime and needs nothing installed at all.
echo.
pause
exit /b 1
