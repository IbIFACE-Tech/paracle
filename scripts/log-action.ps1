# Quick Action Logger - PowerShell Wrapper
# Usage: .\scripts\log-action.ps1 BUGFIX "Fixed docker import error"

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet(
        "IMPLEMENTATION",
        "BUGFIX",
        "TEST",
        "REVIEW",
        "DOCUMENTATION",
        "DECISION",
        "PLANNING",
        "REFACTORING",
        "UPDATE"
    )]
    [string]$Action,

    [Parameter(Mandatory=$true, Position=1)]
    [string]$Description,

    [Parameter(Mandatory=$false)]
    [string]$Agent = "CoderAgent"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$loggerScript = Join-Path $projectRoot ".parac\tools\hooks\agent-logger.py"

if (-not (Test-Path $loggerScript)) {
    Write-Host "❌ Error: agent-logger.py not found at $loggerScript" -ForegroundColor Red
    exit 1
}

Write-Host "📝 Logging action..." -ForegroundColor Cyan

# Execute agent-logger.py
python $loggerScript $Agent $Action $Description

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Logged: [$Agent] [$Action] $Description" -ForegroundColor Green
} else {
    Write-Host "❌ Error logging action" -ForegroundColor Red
    exit 1
}
