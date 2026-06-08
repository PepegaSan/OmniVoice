# OmniVoice Web UI Starter
# Startet die offizielle Gradio-Demo lokal im Browser.

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvDemo = Join-Path $ProjectRoot ".venv\Scripts\omnivoice-demo.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Virtuelle Umgebung nicht gefunden. Bitte zuerst installieren:" -ForegroundColor Red
    Write-Host "  .\install.ps1"
    exit 1
}

$Port = 7860
if ($args.Count -gt 0) { $Port = [int]$args[0] }

Write-Host "Starte OmniVoice Web UI auf http://localhost:$Port" -ForegroundColor Green
Write-Host "Beim ersten Start werden Modelle von Hugging Face geladen (kann einige Minuten dauern)." -ForegroundColor Yellow
Write-Host "Beenden mit Ctrl+C`n"

if (Test-Path $VenvDemo) {
    & $VenvDemo --ip 127.0.0.1 --port $Port
} else {
    & $VenvPython -m omnivoice.cli.demo --ip 127.0.0.1 --port $Port
}
