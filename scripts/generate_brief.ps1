param(
    [switch]$Mock,
    [switch]$NoAi
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    Write-Host "Python was not found in PATH. Please open a new PowerShell window or reinstall Python with Add to PATH enabled."
    exit 1
}

$ArgsList = @(".\backend\app\morning_brief_demo.py", "--save")

if ($Mock) {
    $ArgsList += @("--mock-weather", "--mock-market", "--mock-news", "--mock-themes", "--mock-companies")
}

if ($NoAi) {
    $ArgsList += "--no-ai"
}

& python @ArgsList
