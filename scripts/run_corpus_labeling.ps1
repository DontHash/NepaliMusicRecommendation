# Grinds the corpus mood-relabel across model quota buckets (resume-safe).
# Usage: pwsh -File scripts/run_corpus_labeling.ps1
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$models = @(
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest"
)
Set-Location -LiteralPath $root
while ($true) {
    foreach ($m in $models) {
        Write-Output "=== $(Get-Date -Format s) model=$m ==="
        & python -u scripts/api_label.py --split corpus --batch-size 30 --run-name corpus_v2 --model $m --attempts 1 --sleep-between 6 --break-on-fail
        Start-Sleep -Seconds 15
    }
    Write-Output "=== pass complete; sleeping 10 min ==="
    Start-Sleep -Seconds 600
}
