param(
    [string]$Python = "python",
    [string]$Years = "",
    [string]$Engine = "ray",
    [int]$Chunksize = 100000,
    [int]$MaxRowsPerFile = 0,
    [switch]$WriteParquet
)

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

