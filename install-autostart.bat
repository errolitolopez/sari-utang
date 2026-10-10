@echo off
rem Make Sari Utang start by itself in the background (no window) every time this computer turns on.
cd /d "%~dp0"
rem Remove the older auto-start (a .bat that showed a window), if any
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Sari Utang.bat" 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -File "windows\make-shortcut.ps1" -Folder Startup -Name "Sari Utang" -Flags "--background"
if errorlevel 1 (
    echo Could not set up auto-start.
) else (
    echo Done. Sari Utang will start in the background when this computer turns on.
    echo To undo, run remove-autostart.bat
)
pause
