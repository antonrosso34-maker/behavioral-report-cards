param(
    [int]$Port = 8140,
    [string]$Branch = "agent-04-routing-v6-kv8",
    [switch]$Resume
)

$ErrorActionPreference = "Stop"

# Absolute main-workspace paths: the model, tools, and runner live there.
$Main = "C:\Users\Anton\.lmstudio\apps\bionic\projects\d49037d8-47f4-5808-9028-c707de117f8f\workspace\LLM intagration"
$Model = Join-Path $Main "harness\models\Qwen2.5-Coder-1.5B-Instruct\quants\q3km_code.gguf"
$Splits = Join-Path $Main "harness\data\splits.json"
$RunEval = Join-Path $Main "harness\scripts\run_eval.py"
$LockCli = Join-Path $Main "harness\team\scripts\eval_lock.py"
$OutDir = Join-Path $Main "harness\results\v6"
$LogPath = Join-Path $PSScriptRoot "v6_kv8_run.log"

$ModelSha = "fbc80466f48cffb16a1c869bd6a7789895af98b17f176b35f1630b26ce512ceb"
$SplitsSha = "dd5cd10676843ac3e8ebf2a7ed7190db0421aa3ee1c821ea4009824e8624d12d"

function Assert-File([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label not found: $Path"
    }
}

function Get-Sha([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Invoke-BelowNormal {
    param([string[]]$ArgList)
    $p = Start-Process -FilePath "python" -ArgumentList $ArgList -PassThru -NoNewWindow
    try {
        $p.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
    } catch {
        Write-Warning "could not set below-normal priority: $($_.Exception.Message)"
    }
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) {
        throw "run_eval failed with exit code $($p.ExitCode)"
    }
}

Assert-File $Model "model"
Assert-File $Splits "splits"
Assert-File $RunEval "run_eval.py"
Assert-File $LockCli "eval_lock.py"

$modelShaActual = Get-Sha $Model
if ($modelShaActual -ne $ModelSha) {
    throw "model SHA mismatch: expected $ModelSha, got $modelShaActual"
}
$splitsShaActual = Get-Sha $Splits
if ($splitsShaActual -ne $SplitsSha) {
    throw "splits SHA mismatch: expected $SplitsSha, got $splitsShaActual"
}

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$heOut = Join-Path $OutDir "v6_kv8_he_dev.jsonl"
$mbOut = Join-Path $OutDir "v6_kv8_mbpp_dev.jsonl"
foreach ($f in @($heOut, $mbOut)) {
    if (Test-Path -LiteralPath $f) {
        Write-Warning "output exists: $f; run_eval will truncate unless -Resume is used"
    }
}

Start-Transcript -Path $LogPath -Force | Out-Null
$acquired = $false
try {
    Write-Host "V6 KV8 80-generation run"
    Write-Host "model: $Model"
    Write-Host "model SHA256: $modelShaActual"
    Write-Host "splits: $Splits"
    Write-Host "splits SHA256: $splitsShaActual"
    Write-Host "port: $Port; branch: $Branch; resume: $Resume"

    $lockStatus = (& python $LockCli status 2>&1) -join "`n"
    if ($lockStatus -notmatch "LOCK FREE") {
        throw "eval lock is not free: $lockStatus"
    }
    & python $LockCli acquire --branch $Branch --port $Port --timeout 3600
    if ($LASTEXITCODE -ne 0) {
        throw "eval lock acquire failed with exit code $LASTEXITCODE"
    }
    $acquired = $true

    $heArgs = @(
        "`"$RunEval`"",
        "--model", "`"$Model`"",
        "--label", "v6_kv8_he_dev",
        "--backend", "cpu",
        "--threads", "6",
        "--context", "2048",
        "--kv-cache", "q8_0",
        "--dataset", "humaneval",
        "--split", "dev",
        "--max-tokens", "512",
        "--temperature", "0.0",
        "--request-timeout", "600",
        "--test-timeout", "30",
        "--port", "$Port",
        "--output", "`"$heOut`""
    )
    if ($Resume) { $heArgs += "--resume" }
    Invoke-BelowNormal -ArgList $heArgs

    $mbArgs = @(
        "`"$RunEval`"",
        "--model", "`"$Model`"",
        "--label", "v6_kv8_mbpp_dev",
        "--backend", "cpu",
        "--threads", "6",
        "--context", "2048",
        "--kv-cache", "q8_0",
        "--dataset", "mbpp",
        "--split", "dev",
        "--max-tokens", "512",
        "--temperature", "0.0",
        "--request-timeout", "600",
        "--test-timeout", "30",
        "--port", "$Port",
        "--output", "`"$mbOut`""
    )
    if ($Resume) { $mbArgs += "--resume" }
    Invoke-BelowNormal -ArgList $mbArgs

    Write-Host "V6 KV8 run complete."
    Write-Host "HE dev output: $heOut"
    Write-Host "MBPP dev output: $mbOut"
} finally {
    if ($acquired) {
        & python $LockCli release --branch $Branch
    }
    Stop-Transcript | Out-Null
}
