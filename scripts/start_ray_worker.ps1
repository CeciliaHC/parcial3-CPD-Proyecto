param(
    [string]$Python = "python",
    [Parameter(Mandatory=$true)]
    [string]$HeadAddress
)

& $Python -m ray start --address=$HeadAddress

