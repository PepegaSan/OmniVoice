# Einfache deutsche OmniVoice Web-UI
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Port = 7860
if ($args.Count -gt 0) { $Port = [int]$args[0] }

if (-not (Test-Path $Python)) {
    Write-Host "Bitte zuerst .\install.ps1 ausführen." -ForegroundColor Red
    exit 1
}

Write-Host "Starte einfache Web-UI: http://localhost:$Port" -ForegroundColor Green
Write-Host "Hinweis: Beim ersten Start werden Modelle geladen (einmalig, danach aus Cache)." -ForegroundColor Yellow
Write-Host "Für Auto-Transkription: .\start_simple_webui.ps1 -WithAsr`n" -ForegroundColor DarkGray

$extraArgs = @()
if ($WithAsr) { $extraArgs += "--with-asr" }

& $Python (Join-Path $ProjectRoot "simple_webui.py") --ip 127.0.0.1 --port $Port @extraArgs
