# Ingest all PDFs in this folder. Run from seed_docs.
# Backend must be running: cd backend; python main.py

$base = "http://localhost:8000"

Write-Host "Checking backend..." -ForegroundColor Cyan
try {
    $null = Invoke-WebRequest -Uri "$base/api/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "Backend OK`n" -ForegroundColor Green
} catch {
    Write-Host "Backend not reachable at $base. Start it first: cd backend; python main.py" -ForegroundColor Red
    exit 1
}

$pdfs = Get-ChildItem -Path $PSScriptRoot -Filter "*.pdf"
if ($pdfs.Count -eq 0) {
    Write-Host "No PDF files in $PSScriptRoot" -ForegroundColor Yellow
    exit 1
}

foreach ($f in $pdfs) {
    Write-Host "Ingesting $($f.Name)..." -ForegroundColor Cyan
    $result = & curl.exe -s -w "`n%{http_code}" -X POST "$base/api/ingest" -F "file=@$($f.FullName)" -F "doc_type=government_guide"
    $lines = $result -split "`n"
    $code = $lines[-1]
    $body = $lines[0..($lines.Length-2)] -join "`n"
    if ($code -eq "200") {
        $json = $body | ConvertFrom-Json
        Write-Host "  -> $($json.chunks_created) chunks" -ForegroundColor Green
    } else {
        Write-Host "  -> HTTP $code : $body" -ForegroundColor Red
    }
}

Write-Host "`nDone." -ForegroundColor Green
