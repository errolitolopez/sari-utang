@echo off
rem Stop Sari Utang from starting by itself when this computer turns on.
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Sari Utang.lnk" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Sari Utang.bat" 2>nul
echo Done. Sari Utang will no longer start by itself.
pause
