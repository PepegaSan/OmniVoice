@echo off
REM Beendet Prozesse, die auf einem Port lauschen.
REM Aufruf: kill_port.bat 7860
setlocal enabledelayedexpansion
set PORT=%~1
if "%PORT%"=="" set PORT=7860

set FOUND=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "0.0.0.0:0"') do (
    if not "%%a"=="0" (
        set FOUND=1
        echo Beende alten Prozess auf Port %PORT% ^(PID %%a^)...
        taskkill /PID %%a /F >nul 2>&1
    )
)

if "!FOUND!"=="1" (
    timeout /t 2 /nobreak >nul
    echo Port %PORT% freigegeben.
) else (
    echo Port %PORT% ist frei.
)

endlocal
