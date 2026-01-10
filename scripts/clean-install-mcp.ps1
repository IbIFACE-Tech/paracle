# Clean Install MCP Script
# Run this to cleanly reinstall paracle CLI without file locks

Write-Host "🧹 Cleaning MCP installation..." -ForegroundColor Cyan

# Step 1: Stop all processes
Write-Host "`n1️⃣ Stopping all Python/Paracle processes..." -ForegroundColor Yellow
& "$PSScriptRoot\stop-mcp-processes.ps1"

# Step 2: Remove paracle.exe if exists
$paracleExe = Join-Path $PSScriptRoot "..\\.venv\Scripts\paracle.exe"
if (Test-Path $paracleExe) {
    Write-Host "`n2️⃣ Removing old paracle.exe..." -ForegroundColor Yellow
    Remove-Item $paracleExe -Force -ErrorAction SilentlyContinue
    if ($?) {
        Write-Host "✅ Removed paracle.exe" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not remove paracle.exe (may still be locked)" -ForegroundColor Red
        Write-Host "   Try running this script again" -ForegroundColor Yellow
        exit 1
    }
}

# Step 3: Reinstall with uv
Write-Host "`n3️⃣ Reinstalling paracle CLI..." -ForegroundColor Yellow
Set-Location (Join-Path $PSScriptRoot "..")
uv sync --reinstall

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Clean installation complete!" -ForegroundColor Green
    Write-Host "`nYou can now restart VS Code to use the new MCP configuration" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Installation failed" -ForegroundColor Red
    exit $LASTEXITCODE
}
