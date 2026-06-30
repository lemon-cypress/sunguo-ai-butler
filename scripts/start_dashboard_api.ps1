$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Python = "python"
$Port = 8765
$Url = "http://127.0.0.1:$Port/frontend/"

try {
    $Response = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/api/reminders" -TimeoutSec 2
    if ($Response.StatusCode -eq 200) {
        Start-Process $Url
        exit 0
    }
} catch {
    # Server is not running yet.
}

Start-Process -FilePath $Python -ArgumentList "backend\app\dashboard_server.py","--port",$Port -WorkingDirectory $ProjectRoot -WindowStyle Hidden
Start-Sleep -Seconds 2
Start-Process $Url
