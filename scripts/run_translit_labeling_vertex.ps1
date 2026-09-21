# Grinds the transliteration teacher labelling on Vertex AI (resume-safe, no
# API-key throttling). Usage: pwsh -File scripts/run_translit_labeling_vertex.ps1 [-Sample 34412]
param(
    [int]$Sample = 34412,
    [string]$RunName = "translit_corpus_v1",
    [string]$Split = "corpus",
    [string]$Model = "gemini-flash-lite-latest",
    [int]$BatchSize = 80,
    [int]$Passes = 6,
    [int]$ShardIndex = 0,
    [int]$ShardTotal = 1,
    [switch]$BreakOnFail,
    [string]$Project = "gen-lang-client-0379007532",
    [string]$Location = "global"
)
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$logDir = Join-Path $root "R_data\raw\gemini\$RunName"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
Start-Transcript -Path (Join-Path $logDir "label_run.log") -Append | Out-Null
$breakFlag = @()
if ($BreakOnFail) { $breakFlag = @("--break-on-fail") }
for ($pass = 1; $pass -le $Passes; $pass++) {
    Write-Output "=== pass $pass/$Passes $(Get-Date -Format s) model=$Model shard=$ShardIndex/$ShardTotal ==="
    & python -u scripts/api_translit_label.py --split $Split --run-name $RunName --sample $Sample --sample-mode coverage --vertex --vertex-project $Project --vertex-location $Location --model $Model --batch-size $BatchSize --attempts 2 --sleep-between 2 --shard-index $ShardIndex --shard-total $ShardTotal @breakFlag
    Start-Sleep -Seconds 10
}
Write-Output "=== done $(Get-Date -Format s) ==="
Stop-Transcript | Out-Null
