# Start Chrome with remote debugging (port 9222) + fake microphone WAV for Mak Cik Rohani attach-mode demo.
# Run AFTER `npm run dev` is up. Then: npm run demo:voice-e2e:attach
#
# Uses a DEDICATED user-data-dir so this works even when your normal Chrome is open.
# (Without it, Windows often merges into the existing Chrome process and IGNORES --remote-debugging-port → ECONNREFUSED.)
#
# Requires: scripts/demo-cache/mak_cik_rohani_chromium.wav
#
# Run exactly:  npm run demo:chrome-cdp
# Do not append Chrome flags to npm (spaces in paths break; use this script only).

$ErrorActionPreference = "Stop"

$wav = Join-Path $PSScriptRoot "demo-cache\mak_cik_rohani_chromium.wav"
$wavForward = ($wav -replace "\\", "/")

$profileDir = Join-Path $PSScriptRoot "chrome-cdp-profile"
New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
$profileDirForward = ($profileDir -replace "\\", "/")

if (-not (Test-Path $wav)) {
  Write-Host "Missing WAV: $wav" -ForegroundColor Red
  Write-Host "Create it first, e.g. run once (launches its own browser): npm run demo:voice-e2e" -ForegroundColor Yellow
  Write-Host "Or convert MP3 with ffmpeg to that path (see docs/DEMO_MAK_CIK_ROHANI.md)." -ForegroundColor Yellow
  exit 1
}

$chromeCandidates = @(
  "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
)
$chrome = $chromeCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $chrome) {
  Write-Host "Google Chrome not found in usual install paths. Install Chrome or edit this script." -ForegroundColor Red
  exit 1
}

Write-Host "Starting Chrome (isolated profile + CDP :9222 + fake mic)..." -ForegroundColor Cyan
Write-Host "  $chrome" -ForegroundColor DarkGray
Write-Host "  user-data-dir: $profileDir" -ForegroundColor DarkGray

# Each flag with a path must be one argv; inner quotes handle spaces (e.g. Jian Wen Lee).
$userDataFlag = "--user-data-dir=`"$profileDirForward`""
$fakeMicFlag = "--use-file-for-fake-audio-capture=`"$wavForward`""

$argList = @(
  $userDataFlag,
  "--remote-debugging-port=9222",
  "--use-fake-device-for-media-stream",
  $fakeMicFlag,
  "http://localhost:3000/chat"
)

Start-Process -FilePath $chrome -ArgumentList $argList

Write-Host "Waiting for DevTools port..." -ForegroundColor DarkGray
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Milliseconds 500
  try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:9222/json/version" -UseBasicParsing -TimeoutSec 2
    $ok = $true
    break
  } catch {
    # Chrome still starting or port not ready
  }
}

Write-Host ""
if ($ok) {
  Write-Host 'CDP is up at http://127.0.0.1:9222 - run:' -ForegroundColor Green
} else {
  Write-Host 'Could not confirm CDP on port 9222 (firewall or port in use).' -ForegroundColor Yellow
  Write-Host 'Try: close other apps using 9222, or reboot and run this script again.' -ForegroundColor Yellow
  Write-Host 'If attach still fails, run:' -ForegroundColor Yellow
}
Write-Host '  npm run demo:voice-e2e:attach' -ForegroundColor White
Write-Host ""
