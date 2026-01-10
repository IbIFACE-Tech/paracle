# Paracle Log Management Helper
# Quick access to log analysis, rotation, and cleanup

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('analyze', 'rotate', 'cleanup', 'help')]
    [string]$Command = 'analyze'
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Show-Help {
    Write-Host "Paracle Log Management" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\manage-logs.ps1 [command]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  analyze  - Analyze current log size and status (default)"
    Write-Host "  rotate   - Manually rotate logs (archive old entries)"
    Write-Host "  cleanup  - Remove archives older than 1 year"
    Write-Host "  help     - Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\manage-logs.ps1                 # Analyze logs"
    Write-Host "  .\manage-logs.ps1 analyze         # Analyze logs"
    Write-Host "  .\manage-logs.ps1 rotate          # Rotate logs now"
    Write-Host "  .\manage-logs.ps1 cleanup         # Clean old archives"
}

switch ($Command) {
    'analyze' {
        Write-Host "📊 Analyzing logs..." -ForegroundColor Cyan
        python (Join-Path $scriptDir "analyze-logs.py")
    }
    'rotate' {
        Write-Host "🔄 Rotating logs..." -ForegroundColor Cyan
        python (Join-Path $scriptDir "rotate-logs.py")
    }
    'cleanup' {
        Write-Host "🧹 Cleaning up old archives..." -ForegroundColor Cyan
        python (Join-Path $scriptDir "cleanup-logs.py")
    }
    'help' {
        Show-Help
    }
    default {
        Show-Help
    }
}
