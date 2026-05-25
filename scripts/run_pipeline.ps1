param(
    [string]$Python = "",
    [string]$Years = "",
    [string]$Engine = "ray",
    [int]$Chunksize = 100000,
    [int]$MaxRowsPerFile = 0,
    [switch]$WriteParquet
)

if ([string]::IsNullOrWhiteSpace($Python)) {
    $venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $Python = (Resolve-Path $venvPython).Path
    } else {
        $Python = "py"
    }
}

$arguments = @(
    "-m", "atus_pipeline.cli",
    "--engine", $Engine,
    "--chunksize", "$Chunksize"
)

if ($Years.Trim().Length -gt 0) {
    $arguments += "--years"
    $arguments += $Years.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
}

if ($MaxRowsPerFile -gt 0) {
    $arguments += "--max-rows-per-file"
    $arguments += "$MaxRowsPerFile"
}

if ($WriteParquet) {
    $arguments += "--write-parquet"
}

& $Python @arguments
