# PowerShell script to install git hooks for Windows

$ErrorActionPreference = "Stop"

$gitRoot = git rev-parse --show-toplevel
if (-not $?) {
    Write-Error "Not a git repository"
    exit 1
}

$hooksDir = Join-Path $gitRoot ".git" "hooks"

Write-Host "📦 Installing PARACLE git hooks..." -ForegroundColor Cyan

# Pre-commit hook (PowerShell version for Windows)
$preCommitContent = @'
# Pre-commit hook to regenerate manifest when agents change

# Check if any agent specs were modified
$agentSpecsChanged = git diff --cached --name-only | Where-Object { $_ -match "^\.parac/agents/specs/.*\.md$" }

if ($agentSpecsChanged) {
    Write-Host "🤖 Agent specs modified, regenerating manifest..." -ForegroundColor Yellow

    # Regenerate manifest
    paracle sync --manifest --no-git --no-metrics

    # Add the updated manifest to the commit
    git add .parac/manifest.yaml

    Write-Host "✅ Manifest regenerated and staged" -ForegroundColor Green
}
'@

$preCommitPath = Join-Path $hooksDir "pre-commit.ps1"
Set-Content -Path $preCommitPath -Value $preCommitContent -Encoding UTF8

Write-Host "✅ Created pre-commit.ps1" -ForegroundColor Green

# Create wrapper script that Git can execute
$wrapperContent = @'
#!/bin/sh
# Git hook wrapper for PowerShell script
pwsh -NoProfile -ExecutionPolicy Bypass -File "$(dirname "$0")/pre-commit.ps1"
'@

$wrapperPath = Join-Path $hooksDir "pre-commit"
Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding ASCII -NoNewline

Write-Host "✅ Created pre-commit wrapper" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Git hooks installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The manifest will now be automatically regenerated when you commit agent changes." -ForegroundColor Cyan
