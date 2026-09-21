# Grinds the transliteration teacher labelling on Vertex AI (resume-safe, no
# API-key throttling). Usage: pwsh -File scripts/run_translit_labeling_vertex.ps1 [-Sample 34412]
param(
    [int]$Sample = 34412,
    [string]$RunName = "translit_corpus_v1",
    [string]$Split = "corpus",
    [string]$Model = "gemini-flash-lite-latest",
    [int]$BatchSize = 40,
    [int]$Passes = 4,
    [string]$Project = "gen-lang-client-0379007532",
    [string]$Location = "global"
)
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
for ($pass = 1; $pass -le $Passes; $pass++) {
    Write-Output "=== pass $pass/$Passes $(Get-Date -Format s) model=$Model ==="
    & python -u scripts/api_translit_label.py --split $Split --run-name $RunName --sample $Sample --sample-mode coverage --vertex --vertex-project $Project --vertex-location $Location --model $Model --batch-size $BatchSize --attempts 2 --sleep-between 2 --break-on-fail
    Start-Sleep -Seconds 10
}
Write-Output "=== done $(Get-Date -Format s) ==="
