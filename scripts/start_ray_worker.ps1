param(
    [string]$Ray = "",
    [Parameter(Mandatory=$true)]
    [string]$HeadAddress
)

if ([string]::IsNullOrWhiteSpace($Ray)) {
    $venvRay = Join-Path $PSScriptRoot "..\.venv\Scripts\ray.exe"
    if (Test-Path $venvRay) {
        $Ray = (Resolve-Path $venvRay).Path
    } else {
        $Ray = "ray"
    }
}

& $Ray start --address=$HeadAddress
