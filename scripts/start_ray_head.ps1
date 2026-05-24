param(
    [string]$Python = "python",
    [int]$Port = 6379,
    [int]$DashboardPort = 8265
)

& $Python -m ray start --head --port=$Port --dashboard-host=0.0.0.0 --dashboard-port=$DashboardPort

