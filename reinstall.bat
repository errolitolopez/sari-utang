@echo off
rem Reinstall Sari Utang: a fresh copy of the app and of its Python packages.
rem KEPT:    the credit list and PIN (instance\), backups\, logs\,
rem          config\settings.json and config\units.json, Desktop icons and auto-start.
rem REPLACED: the app's own files (reset to the newest version on GitHub)
rem           and the Python packages (.venv, installed again).

rem git may replace this very file, and Windows reads a .bat while running it,
rem so first copy it to the TEMP folder and run it from there.
if not "%~1"=="--from-temp" (
    copy /y "%~f0" "%TEMP%\sari-utang-reinstall.bat" >nul
    "%TEMP%\sari-utang-reinstall.bat" --from-temp "%~dp0"
)
title Sari Utang - Reinstall
cd /d "%~2"

echo This will reinstall Sari Utang.
echo   Kept:     credit list, PIN, backups, store name, units, Desktop icons.
echo   Replaced: the app's files (newest version from GitHub) and its Python packages.
echo.
choice /c YN /m "Continue"
if errorlevel 2 exit /b 0

echo.
echo [1/5] Stopping Sari Utang...
if exist ".venv\Scripts\python.exe" ".venv\Scripts\python.exe" start.py --stop

echo [2/5] Backing up the database...
if not exist backups mkdir backups
if exist "instance\sari_utang.db" copy /y "instance\sari_utang.db" "backups\before-reinstall.db" >nul

echo [3/5] Getting a fresh copy of the app from GitHub...
call :fresh_copy

echo [4/5] Reinstalling the Python packages...
if exist ".venv" rmdir /s /q ".venv"
call windows\setup.bat
if errorlevel 1 (
    echo.
    echo Reinstall did not finish. Fix the problem above, then run reinstall.bat again.
    pause
    exit /b 1
)

echo [5/5] Starting Sari Utang...
start "" ".venv\Scripts\pythonw.exe" start.py --background --open
echo.
echo Done. Sari Utang was reinstalled and your data was kept.
echo (A copy of the database from before is in backups\before-reinstall.db)
pause
exit /b 0

:fresh_copy
where git >nul 2>nul
if errorlevel 1 (
    echo Git is not installed: keeping the current app files.
    exit /b 0
)
git fetch --quiet
if errorlevel 1 (
    echo No internet: keeping the current app files.
    exit /b 0
)
rem Replace the app's files with the newest version. Files git ignores
rem (instance\, backups\, logs\, config\*.json, .venv) are not touched here.
git reset --hard --quiet @{upstream}
git clean -fd --quiet
exit /b 0
