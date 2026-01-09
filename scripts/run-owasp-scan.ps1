# OWASP Dependency-Check Quick Runner (PowerShell)
# Usage: .\run-owasp-scan.ps1 [-Format "HTML"]
# Formats: HTML, JSON, XML, CSV, JUNIT, ALL (default: HTML)

param(
    [string]$Format = "HTML"
)

$VERSION = "12.1.9"
$DC_DIR = ".\dependency-check"
$REPORTS_DIR = ".\reports\owasp"

Write-Host "🔍 OWASP Dependency-Check v$VERSION" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Create reports directory
New-Item -ItemType Directory -Force -Path $REPORTS_DIR | Out-Null

# Download if not present
if (-not (Test-Path $DC_DIR)) {
    Write-Host "📥 Downloading OWASP Dependency-Check v$VERSION..." -ForegroundColor Yellow

    $url = "https://github.com/dependency-check/DependencyCheck/releases/download/v$VERSION/dependency-check-$VERSION-release.zip"
    $zipFile = "dependency-check-$VERSION-release.zip"

    Invoke-WebRequest -Uri $url -OutFile $zipFile
    Expand-Archive -Path $zipFile -DestinationPath "dependency-check" -Force
    Remove-Item $zipFile

    Write-Host "✅ Downloaded and extracted" -ForegroundColor Green
} else {
    Write-Host "✅ Using existing installation" -ForegroundColor Green
}

# Run scan
Write-Host ""
Write-Host "🔎 Scanning project for vulnerabilities..." -ForegroundColor Cyan
Write-Host "   Output: $REPORTS_DIR"
Write-Host "   Format: $Format"
Write-Host ""

& "$DC_DIR\dependency-check\bin\dependency-check.bat" `
    --scan . `
    --format $Format `
    --out $REPORTS_DIR `
    --project "Paracle" `
    --enableExperimental `
    --suppression .github\dependency-check-suppressions.xml `
    --exclude "**/node_modules/**" `
    --exclude "**/venv/**" `
    --exclude "**/.venv/**" `
    --exclude "**/build/**" `
    --exclude "**/dist/**" `
    --exclude "**/__pycache__/**"

Write-Host ""
Write-Host "✅ Scan complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Report generated:" -ForegroundColor Cyan

if ($Format -eq "HTML" -or $Format -eq "ALL") {
    Write-Host "   📄 HTML: $REPORTS_DIR\dependency-check-report.html"
}
if ($Format -eq "JSON" -or $Format -eq "ALL") {
    Write-Host "   📄 JSON: $REPORTS_DIR\dependency-check-report.json"
}
Write-Host ""

# Check for vulnerabilities
$jsonReport = "$REPORTS_DIR\dependency-check-report.json"
if (Test-Path $jsonReport) {
    Write-Host "🔍 Vulnerability Summary:" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

    try {
        $report = Get-Content $jsonReport | ConvertFrom-Json
        $critical = ($report.dependencies.vulnerabilities | Where-Object { $_.severity -eq "CRITICAL" }).Count
        $high = ($report.dependencies.vulnerabilities | Where-Object { $_.severity -eq "HIGH" }).Count
        $medium = ($report.dependencies.vulnerabilities | Where-Object { $_.severity -eq "MEDIUM" }).Count
        $low = ($report.dependencies.vulnerabilities | Where-Object { $_.severity -eq "LOW" }).Count

        Write-Host "   🔴 Critical: $critical" -ForegroundColor Red
        Write-Host "   🟠 High:     $high" -ForegroundColor DarkYellow
        Write-Host "   🟡 Medium:   $medium" -ForegroundColor Yellow
        Write-Host "   🟢 Low:      $low" -ForegroundColor Green
        Write-Host ""

        if ($critical -gt 0 -or $high -gt 0) {
            Write-Host "⚠️  Action Required: Critical or High vulnerabilities found!" -ForegroundColor Red
            exit 1
        } else {
            Write-Host "✅ No critical or high vulnerabilities found" -ForegroundColor Green
            exit 0
        }
    } catch {
        Write-Host "⚠️  Could not parse summary (JSON report may be invalid)" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "⚠️  JSON report not found (generate with -Format JSON)" -ForegroundColor Yellow
    exit 0
}
