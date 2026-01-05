# PowerShell script to install git hooks for Windows

$ErrorActionPreference = "Stop"

$gitRoot = git rev-parse --show-toplevel
if (-not $?) {
    Write-Error "Not a git repository"
    exit 1
}

$hooksDir = Join-Path $gitRoot ".git" "hooks"
$sourceHook = Join-Path $gitRoot ".parac" "tools" "hooks" "pre-commit"

Write-Host "📦 Installing PARACLE git hooks..." -ForegroundColor Cyan

# Check if source hook exists
if (-not (Test-Path $sourceHook)) {
    Write-Error "Source hook not found: $sourceHook"
    exit 1
}

# Copy the unified pre-commit hook
$preCommitPath = Join-Path $hooksDir "pre-commit"
Copy-Item -Path $sourceHook -Destination $preCommitPath -Force

Write-Host "✅ Installed unified pre-commit hook" -ForegroundColor Green
Write-Host ""
Write-Host "The .parac/ workspace will now be automatically maintained:" -ForegroundColor Cyan
Write-Host "  - Agent manifest regeneration when agent specs change" -ForegroundColor White
Write-Host "  - Project state updates when code/docs change" -ForegroundColor White

Write-Host ""
Write-Host "🎉 Git hooks installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The manifest will now be automatically regenerated when you commit agent changes." -ForegroundColor Cyan
