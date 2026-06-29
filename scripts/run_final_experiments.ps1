$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\.."

$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path "runs" "final_$runId"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$summaryPath = Join-Path $runDir "summary.txt"
$statusPath = Join-Path $runDir "status.txt"

"STARTED: $(Get-Date -Format s)" | Set-Content -Path $statusPath -Encoding utf8
"Run directory: $runDir" | Set-Content -Path $summaryPath -Encoding utf8

function Run-Experiment {
    param(
        [string]$Name,
        [string]$SamplePercent,
        [string]$MaxSample,
        [string]$MaxEval,
        [string]$Prefix,
        [string]$EnableLastfm = "0",
        [string]$LastfmMaxCalls = "1500"
    )

    $logPath = Join-Path $runDir "$Prefix.log"
    Add-Content -Path $summaryPath -Value ""
    Add-Content -Path $summaryPath -Value "[$(Get-Date -Format s)] START $Name"

    $env:MIDTERM_SAMPLE_PERCENT = $SamplePercent
    $env:MIDTERM_MAX_SAMPLE_PLAYLISTS = $MaxSample
    $env:MIDTERM_MAX_EVAL_PLAYLISTS = $MaxEval
    $env:MIDTERM_OUTPUT_PREFIX = $Prefix
    $env:MIDTERM_ENABLE_LASTFM = $EnableLastfm
    $env:MIDTERM_LASTFM_MAX_CALLS = $LastfmMaxCalls

    if ($EnableLastfm -ne "1") {
        Remove-Item Env:LASTFM_API_KEY -ErrorAction SilentlyContinue
    }

    $start = Get-Date
    "[$($start.ToString('s'))] Running $Name" | Tee-Object -FilePath $logPath -Append
    python hito2_spotify_lastfm_midterm.py 2>&1 | Tee-Object -FilePath $logPath -Append
    $exitCode = $LASTEXITCODE
    $end = Get-Date
    $duration = [math]::Round(($end - $start).TotalMinutes, 2)

    Add-Content -Path $summaryPath -Value "[$($end.ToString('s'))] END $Name exit=$exitCode minutes=$duration"
    if ($exitCode -ne 0) {
        "FAILED: $Name" | Set-Content -Path $statusPath -Encoding utf8
        throw "Experiment $Name failed with exit code $exitCode"
    }
}

try {
    Run-Experiment -Name "Final 30 full" -SamplePercent "30" -MaxSample "0" -MaxEval "63851" -Prefix "resultados_hito2_final_30_full"
    Run-Experiment -Name "Final 20 sensitivity" -SamplePercent "20" -MaxSample "30000" -MaxEval "30000" -Prefix "resultados_hito2_final_20_sens"

    "COMPLETED: $(Get-Date -Format s)" | Set-Content -Path $statusPath -Encoding utf8
    Add-Content -Path $summaryPath -Value ""
    Add-Content -Path $summaryPath -Value "Outputs expected in repository root:"
    Add-Content -Path $summaryPath -Value "- resultados_hito2_final_30_full.*"
    Add-Content -Path $summaryPath -Value "- resultados_hito2_final_20_sens.*"
}
catch {
    Add-Content -Path $summaryPath -Value ""
    Add-Content -Path $summaryPath -Value "ERROR: $($_.Exception.Message)"
    throw
}
