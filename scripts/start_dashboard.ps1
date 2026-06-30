$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    Write-Host "Python was not found in PATH. Please open a new PowerShell window or reinstall Python with Add to PATH enabled."
    exit 1
}

$Url = "http://localhost:8765/frontend/"

try {
    $Response = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8765/frontend/" -TimeoutSec 2
    if ($Response.StatusCode -eq 200) {
        Write-Host "Sunguo dashboard is already running:"
        Write-Host $Url
        Start-Process $Url
        exit 0
    }
} catch {
    # Server is not running yet.
}

Start-Process -FilePath "python" -ArgumentList "-m","http.server","8765","--bind","127.0.0.1" -WorkingDirectory $ProjectRoot -WindowStyle Hidden
Start-Sleep -Seconds 1

Write-Host "Sunguo dashboard started:"
Write-Host $Url
Start-Process $Url
