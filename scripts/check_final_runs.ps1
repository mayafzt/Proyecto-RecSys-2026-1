Set-Location "$PSScriptRoot\.."

$latest = Get-ChildItem runs -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) {
    Write-Output "No run directory found in runs/."
    exit 0
}

Write-Output "Latest run: $($latest.FullName)"

$status = Join-Path $latest.FullName "status.txt"
$summary = Join-Path $latest.FullName "summary.txt"
if (Test-Path $status) {
    Write-Output ""
    Write-Output "Status:"
    Get-Content $status
}

if (Test-Path $summary) {
    Write-Output ""
    Write-Output "Summary tail:"
    Get-Content $summary | Select-Object -Last 20
}

Write-Output ""
Write-Output "Recent log files:"
Get-ChildItem $latest.FullName -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object Name, LastWriteTime, Length
