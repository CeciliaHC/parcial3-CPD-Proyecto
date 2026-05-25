param(
    [string]$Python = "",
    [Parameter(Mandatory=$true)]
    [string]$HeadAddress
)

if ([string]::IsNullOrWhiteSpace($Python)) {
    $venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $Python = (Resolve-Path $venvPython).Path
    } else {
        $Python = "py"
    }
}

& $Python -m ray start --address=$HeadAddress
