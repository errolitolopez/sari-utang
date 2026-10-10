@echo off
rem Make Sari Utang start by itself (minimized) every time this computer turns on.
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
> "%STARTUP%\Sari Utang.bat" echo @start "Sari Utang" /min "%~dp0run.bat"
if exist "%STARTUP%\Sari Utang.bat" (
    echo Done. Sari Utang will start when this computer turns on.
    echo To undo, run remove-autostart.bat
) else (
    echo Could not set up auto-start.
)
pause
