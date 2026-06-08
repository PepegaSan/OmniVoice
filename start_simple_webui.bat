@echo off
setlocal
cd /d "%~dp0"

set PORT=7860
if not "%~1"=="" set PORT=%~1

if not exist ".venv\Scripts\python.exe" (
    echo Virtuelle Umgebung fehlt. Bitte zuerst install.bat ausfuehren.
    pause
    exit /b 1
)

call "%~dp0kill_port.bat" %PORT%

echo.
echo Starte OmniVoice Web-UI: http://localhost:%PORT%
echo Beenden mit Ctrl+C
echo.

".venv\Scripts\python.exe" simple_webui.py --ip 127.0.0.1 --port %PORT%
pause
