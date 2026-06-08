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
echo Starte OmniVoice Demo: http://localhost:%PORT%
echo Beenden mit Ctrl+C
echo.

if exist ".venv\Scripts\omnivoice-demo.exe" (
    ".venv\Scripts\omnivoice-demo.exe" --ip 127.0.0.1 --port %PORT%
) else (
    ".venv\Scripts\python.exe" -m omnivoice.cli.demo --ip 127.0.0.1 --port %PORT%
)
pause
