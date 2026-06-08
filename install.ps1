# OmniVoice Installation (Windows)
# Erstellt venv, installiert PyTorch (CUDA) und OmniVoice.

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvDir = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host "=== OmniVoice Installation ===" -ForegroundColor Cyan
Write-Host "Projekt: $ProjectRoot`n"

if (-not (Test-Path $Python)) {
    Write-Host "[1/3] Erstelle virtuelle Umgebung..." -ForegroundColor Yellow
    python -m venv $VenvDir
}

Write-Host "[2/3] Installiere PyTorch (CUDA 12.8)..." -ForegroundColor Yellow
& $Pip install --upgrade pip
& $Pip install torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128

Write-Host "[3/3] Installiere OmniVoice (editable)..." -ForegroundColor Yellow
& $Pip install -e $ProjectRoot

Write-Host "`n=== Installation abgeschlossen ===" -ForegroundColor Green
Write-Host "Web UI starten mit:  .\start_webui.ps1"
Write-Host "Oder direkt:         omnivoice-demo --ip 127.0.0.1 --port 7860"
