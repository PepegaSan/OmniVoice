@echo off
setlocal
cd /d "%~dp0"

echo === OmniVoice Installation ===
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Erstelle virtuelle Umgebung...
    python -m venv .venv
    if errorlevel 1 (
        echo Fehler beim Erstellen der venv.
        pause
        exit /b 1
    )
)

echo [2/3] Installiere PyTorch ^(CUDA 12.8^)...
".venv\Scripts\pip.exe" install --upgrade pip
".venv\Scripts\pip.exe" install torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 (
    echo Fehler bei PyTorch-Installation.
    pause
    exit /b 1
)

echo [3/3] Installiere OmniVoice...
".venv\Scripts\pip.exe" install -e .
if errorlevel 1 (
    echo Fehler bei OmniVoice-Installation.
    pause
    exit /b 1
)

echo.
echo === Installation abgeschlossen ===
echo Web-UI starten: Doppelklick auf start_simple_webui.bat
echo.
pause
