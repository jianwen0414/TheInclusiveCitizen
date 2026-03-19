# Copy Mak Cik Rohani MP3 into public/demo for the browser demo page.
$ErrorActionPreference = "Stop"
# scripts/ -> repo root
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $root "package.json"))) {
    Write-Error "Run this script from the project repo (package.json not found above scripts/)."
    exit 1
}
$src = Get-ChildItem -LiteralPath $root -Filter "ElevenLabs_*Mak Cik Rohani*.mp3" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $src) {
    Write-Error "Could not find ElevenLabs_*Mak Cik Rohani*.mp3 in repo root. Place the file there or set -SourcePath."
    exit 1
}
$destDir = Join-Path $root "public\demo"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
$dest = Join-Path $destDir "mak_cik_rohani.mp3"
Copy-Item -LiteralPath $src.FullName -Destination $dest -Force
Write-Host "Copied -> $dest"
