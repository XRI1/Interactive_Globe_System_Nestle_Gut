@echo off
REM Starts the local server and opens the Interactive Globe fullscreen in Chrome (kiosk mode).
REM Autoplay flag lets the videos play with sound without a click.
cd /d "%~dp0"
set NO_BROWSER=1
start "Globe Server" /min python server.py
timeout /t 2 /nobreak >nul

set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if exist %CHROME% (
  start "" %CHROME% --kiosk --autoplay-policy=no-user-gesture-required --use-fake-ui-for-media-stream --user-data-dir="%TEMP%\globe-chrome" http://localhost:8000/index.html
) else (
  start "" msedge --kiosk --edge-kiosk-type=fullscreen --autoplay-policy=no-user-gesture-required http://localhost:8000/index.html
)
