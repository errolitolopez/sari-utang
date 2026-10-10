@echo off
rem Start Sari Utang on Windows. Double-click this file.
rem The first time it sets everything up (needs internet once to download packages).
title Sari Utang
cd /d "%~dp0"

rem 1-2. Python environment and packages
call windows\setup.bat
if errorlevel 1 (
    pause
    exit /b 1
)

rem 3. Start (update, database, PIN, backup, server).
rem Kept in one ( ) block: Windows reads the whole block before running it, so an
rem auto-update that changes this file while the app runs can't confuse it.
(
    ".venv\Scripts\python.exe" start.py
    echo.
    echo Sari Utang stopped.
    pause
    exit /b
)
