@echo off
rem Makes sure Python's environment (.venv) and the packages are ready.
rem Used by run.bat and reinstall.bat. Ends with error 1 if something is missing.
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    echo Setting up Sari Utang...
    py -3 -m venv .venv 2>nul || python -m venv .venv 2>nul
)
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Python is not installed.
    echo Install it from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" on the first screen of the installer.
    echo.
    exit /b 1
)

rem Install packages only when requirements.txt changed, so it also works offline
fc /b requirements.txt .venv\installed-requirements.txt >nul 2>nul
if errorlevel 1 (
    echo Installing packages...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Could not install the packages. Connect to the internet and try again.
        echo.
        exit /b 1
    )
    copy /y requirements.txt .venv\installed-requirements.txt >nul
)
exit /b 0
