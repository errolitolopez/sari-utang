@echo off
rem Put two icons on the Desktop:
rem   "Sari Utang"      - starts the app in the background (no window) and opens it in the browser
rem   "Stop Sari Utang" - stops the app
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "windows\make-shortcut.ps1" -Folder Desktop -Name "Sari Utang" -Flags "--background --open"
powershell -NoProfile -ExecutionPolicy Bypass -File "windows\make-shortcut.ps1" -Folder Desktop -Name "Stop Sari Utang" -Flags "--stop"
pause
