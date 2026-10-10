@echo off
rem Change the login PIN. Run it while Sari Utang is stopped or running, both are fine.
title Sari Utang - Change PIN
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run run.bat first to set up Sari Utang.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m flask --app app set-pin
pause
