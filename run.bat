@echo off
rem Start Sari Utang on Windows. Double-click this file.
rem The first time it sets everything up (needs internet once to download packages).
title Sari Utang
cd /d "%~dp0"

rem 1. Python virtual environment (only the first time)
if not exist ".venv\Scripts\python.exe" (
    echo Setting up Sari Utang for the first time...
    py -3 -m venv .venv 2>nul || python -m venv .venv 2>nul
)
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Python is not installed.
    echo Install it from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" on the first screen of the installer.
    echo.
    pause
    exit /b 1
)

rem 2. Packages (only when requirements.txt changed, so it also works offline)
fc /b requirements.txt .venv\installed-requirements.txt >nul 2>nul
if errorlevel 1 (
    echo Installing packages...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Could not install the packages. Connect to the internet and try again.
        echo.
        pause
        exit /b 1
    )
    copy /y requirements.txt .venv\installed-requirements.txt >nul
)

rem 3. Start (database, PIN, backup, server)
".venv\Scripts\python.exe" start.py
echo.
echo Sari Utang stopped.
pause
