@echo off
setlocal enabledelayedexpansion

:: create-scratch-org.bat
::
:: Windows launcher for the Scratch Org Creator web UI.
:: Equivalent of: bash create-scratch-org.sh --web
::
:: Prerequisites:
::   - Python 3 (python or python3 on PATH)
::   - Salesforce CLI (sf) on PATH
::   - A Salesforce Dev Hub org
::
:: Usage:
::   create-scratch-org.bat          Launch the interactive web UI
::   create-scratch-org.bat --help   Show help

title Scratch Org Creator

:: ── Argument parsing ─────────────────────────────────────────
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
goto :start

:show_help
echo.
echo   Scratch Org Creator — Interactive Web UI for Salesforce Scratch Orgs
echo.
echo   Usage:  create-scratch-org.bat [OPTIONS]
echo.
echo   Options:
echo     --help     Show this help message
echo.
echo   Prerequisites:
echo     python3    https://www.python.org/downloads/
echo     sf CLI     https://developer.salesforce.com/tools/salesforcecli
echo.
exit /b 0

:: ── Main logic ───────────────────────────────────────────────
:start
echo.
echo  ╔══════════════════════════════════════╗
echo  ║      Scratch Org Creator  v1.0       ║
echo  ╚══════════════════════════════════════╝
echo.

:: ── Detect Python ────────────────────────────────────────────
set "PYTHON_CMD="

where python3 >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_CMD=python3"
    goto :python_found
)

where python >nul 2>&1
if %errorlevel%==0 (
    :: Verify it's Python 3, not Python 2
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do (
        set "PY_VER=%%v"
    )
    if "!PY_VER:~0,1!"=="3" (
        set "PYTHON_CMD=python"
        goto :python_found
    ) else (
        echo [x] Python found but it's version !PY_VER! — Python 3 is required.
        echo     Download from: https://www.python.org/downloads/
        exit /b 1
    )
)

echo [x] Python 3 is not installed or not on PATH.
echo     Download from: https://www.python.org/downloads/
echo     Make sure to check "Add Python to PATH" during installation.
exit /b 1

:python_found
for /f "delims=" %%v in ('!PYTHON_CMD! --version 2^>^&1') do set "PY_VERSION=%%v"
echo [✓] %PY_VERSION% found

:: ── Check Salesforce CLI ─────────────────────────────────────
where sf >nul 2>&1
if %errorlevel% neq 0 (
    echo [x] Salesforce CLI ^(sf^) is not installed or not on PATH.
    echo     Install: npm install -g @salesforce/cli
    echo     Docs:    https://developer.salesforce.com/tools/salesforcecli
    exit /b 1
)
for /f "delims=" %%v in ('sf --version 2^>^&1') do (
    set "SF_VERSION=%%v"
    goto :sf_done
)
:sf_done
echo [✓] sf CLI found: %SF_VERSION%

:: ── Resolve paths ────────────────────────────────────────────
set "SCRIPT_DIR=%~dp0"
:: Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "UI_DIR=%SCRIPT_DIR%\scratch-org-ui"
set "VENDOR_PATH=%UI_DIR%\vendor"
set "OUT_DIR=%SCRIPT_DIR%\scratch-orgs-templates"

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

:: ── Install Flask if needed ──────────────────────────────────
echo [i] Checking Flask installation...

!PYTHON_CMD! -c "import sys; sys.path.insert(0, r'%VENDOR_PATH%'); import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [i] Installing Flask ^(one-time setup^)...
    
    !PYTHON_CMD! -m pip install --quiet --target "%VENDOR_PATH%" flask >nul 2>&1
    if !errorlevel!==0 (
        echo [✓] Flask installed to local vendor directory.
    ) else (
        pip install --quiet --target "%VENDOR_PATH%" flask >nul 2>&1
        if !errorlevel!==0 (
            echo [✓] Flask installed to local vendor directory.
        ) else (
            echo [x] Could not install Flask automatically.
            echo     Please run: pip install flask
            exit /b 1
        )
    )
) else (
    echo [✓] Flask is available
)

:: ── Find available port ──────────────────────────────────────
for /f "delims=" %%p in ('!PYTHON_CMD! -c "import socket;s=socket.socket();exec('try:\n s.bind((chr(39)+chr(39),8484));s.close();print(8484)\nexcept OSError:\n s2=socket.socket();s2.bind((chr(39)+chr(39),0));print(s2.getsockname()[1]);s2.close()')"') do set "PORT=%%p"
if not defined PORT set "PORT=8484"

echo.
echo [i] Starting web server on http://localhost:%PORT% ...
echo.

:: ── Launch Flask server ──────────────────────────────────────
start /b "" !PYTHON_CMD! "%UI_DIR%\app.py" %PORT%

:: Give server a moment to start
!PYTHON_CMD! -c "import time; time.sleep(1.5)"

:: ── Open browser ─────────────────────────────────────────────
echo [✓] Web UI running at: http://localhost:%PORT%
echo.
start "" "http://localhost:%PORT%"

echo.
echo ─────────────────────────────────────────────────────────────
echo   The web UI is now open in your default browser.
echo.
echo   Press any key to stop the server and exit.
echo ─────────────────────────────────────────────────────────────
echo.

pause >nul

:: ── Cleanup: kill the Python server ──────────────────────────
:: Find and kill the python process running app.py on our port
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT%.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [✓] Server stopped. Goodbye!
exit /b 0
