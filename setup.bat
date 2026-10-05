@echo off
REM Opens the Detection Zone Setup page (drag / resize the zone, then Save).
REM Run this before start.bat whenever the camera or the zone needs adjusting.
cd /d "%~dp0"
REM Stop an old server that may still be running (it would keep serving old code)
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"
set NO_BROWSER=1
start "Globe Server" /min python server.py
timeout /t 2 /nobreak >nul

set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if exist %CHROME% (
  start "" %CHROME% --app=http://localhost:8000/setup.html --start-maximized --autoplay-policy=no-user-gesture-required --use-fake-ui-for-media-stream --user-data-dir="%TEMP%\globe-chrome"
) else (
  start "" msedge --app=http://localhost:8000/setup.html --start-maximized --autoplay-policy=no-user-gesture-required
)
