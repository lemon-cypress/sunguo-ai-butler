param(
    [switch]$Mock,
    [switch]$NoAi
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PythonCommand = $null
$SystemPython = Get-Command python -ErrorAction SilentlyContinue
if ($SystemPython) {
    $PythonCommand = $SystemPython.Source
} else {
    $BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $BundledPython) {
        $PythonCommand = $BundledPython
    }
}

if (-not $PythonCommand) {
    Write-Host "Python was not found. Please install Python 3.11+ or open the project from Codex so the bundled runtime is available."
    exit 1
}

$ArgsList = @(".\backend\app\morning_brief_demo.py", "--save")

if ($Mock) {
    $ArgsList += @("--mock-weather", "--mock-market", "--mock-news", "--mock-themes", "--mock-companies")
}

if ($NoAi) {
    $ArgsList += "--no-ai"
}

& $PythonCommand @ArgsList
