# Stop MCP Processes Script
# Run this if MCP server is stuck or causing file locks

Write-Host "🔍 Finding MCP-related processes..." -ForegroundColor Yellow

# Find all Python processes in the project directory
$projectPath = Split-Path -Parent $PSScriptRoot
$processes = Get-Process | Where-Object {
    $_.ProcessName -like "*python*" -and
    $_.Path -like "$projectPath*"
}

if ($processes.Count -eq 0) {
    Write-Host "✅ No MCP processes found" -ForegroundColor Green
    exit 0
}

Write-Host "Found $($processes.Count) process(es):" -ForegroundColor Cyan
$processes | Select-Object ProcessName, Id, Path | Format-Table -AutoSize

# Stop processes
Write-Host "🛑 Stopping processes..." -ForegroundColor Yellow
$processes | Stop-Process -Force

Start-Sleep -Seconds 1

# Verify
$remaining = Get-Process | Where-Object {
    $_.ProcessName -like "*python*" -and
    $_.Path -like "$projectPath*"
}

if ($remaining.Count -eq 0) {
    Write-Host "✅ All MCP processes stopped successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some processes still running:" -ForegroundColor Red
    $remaining | Select-Object ProcessName, Id | Format-Table
}
