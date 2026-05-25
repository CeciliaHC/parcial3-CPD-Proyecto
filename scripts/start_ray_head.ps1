param(
    [string]$Python = "",
    [int]$Port = 6379,
    [int]$DashboardPort = 8265
)

if ([string]::IsNullOrWhiteSpace($Python)) {
    $venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $Python = (Resolve-Path $venvPython).Path
    } else {
        $Python = "py"
    }
}

& $Python -m ray start --head --port=$Port --dashboard-host=0.0.0.0 --dashboard-port=$DashboardPort
