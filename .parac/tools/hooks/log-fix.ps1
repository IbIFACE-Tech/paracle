# Quick Fix Logging Script for PowerShell
# Usage: .\log-fix.ps1 "Description of the fix"

param(
    [Parameter(Mandatory=$true)]
    [string]$Description,

    [Parameter(Mandatory=$false)]
    [string]$Agent = "CoderAgent",

    [Parameter(Mandatory=$false)]
    [string]$Action = "BUGFIX"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$loggerScript = Join-Path $scriptDir "agent-logger.py"

Write-Host "🔧 Logging fix..." -ForegroundColor Cyan

# Execute agent-logger.py
python $loggerScript $Agent $Action $Description

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Fix logged successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Error logging fix" -ForegroundColor Red
    exit 1
}
