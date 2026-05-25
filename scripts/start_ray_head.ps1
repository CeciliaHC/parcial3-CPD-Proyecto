param(
    [string]$Ray = "",
    [int]$Port = 6379,
    [int]$DashboardPort = 8265
)

if ([string]::IsNullOrWhiteSpace($Ray)) {
    $venvRay = Join-Path $PSScriptRoot "..\.venv\Scripts\ray.exe"
    if (Test-Path $venvRay) {
        $Ray = (Resolve-Path $venvRay).Path
    } else {
        $Ray = "ray"
    }
}

& $Ray start --head --port=$Port --dashboard-host=0.0.0.0 --dashboard-port=$DashboardPort
