# Grinds the transliteration teacher labeling across API-key and model buckets
# (resume-safe). Usage: pwsh -File scripts/run_translit_labeling.ps1 [-Sample 2000]
param(
    [int]$Sample = 2000,
    [string]$RunName = "translit_corpus_v1",
    [string]$Split = "corpus",
    [int]$ShardIndex = 0,
    [int]$ShardTotal = 1,
    [int]$BatchSize = 40,
    [int]$Passes = 1
)
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$keys = @(
    "GEMINI_API_KEY",
    "GEMINI_API_KEY_ALT2",
    "GEMINI_API_KEY_ALT3",
    "GEMINI_API_KEY_ALT4",
    "PRAKA_GEMINI_KEY"
)
$models = @(
    "gemini-3.5-flash",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash"
)
Set-Location -LiteralPath $root
for ($pass = 1; $pass -le $Passes; $pass++) {
    Write-Output "=== pass $pass/$Passes $(Get-Date -Format s) ==="
    foreach ($k in $keys) {
        foreach ($m in $models) {
            Write-Output "--- key=$k model=$m shard=$ShardIndex/$ShardTotal ---"
            & python -u scripts/api_translit_label.py --split $Split --run-name $RunName --sample $Sample --sample-mode coverage --model $m --key-var $k --batch-size $BatchSize --attempts 1 --sleep-between 3 --break-on-fail --shard-index $ShardIndex --shard-total $ShardTotal
            Start-Sleep -Seconds 8
        }
    }
}
Write-Output "=== done $(Get-Date -Format s) ==="
