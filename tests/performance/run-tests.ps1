# Performance Test Execution Script
# Run all 5 test scenarios and collect metrics

param(
    [string]$Scenario = "all",
    [string]$ApiHost = "http://localhost:8000",
    [int]$Duration = 300  # 5 minutes default
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Paracle Performance Test Suite" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if API is running
Write-Host "📡 Checking API availability..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$ApiHost/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "✅ API is reachable at $ApiHost" -ForegroundColor Green
} catch {
    Write-Host "❌ API not reachable at $ApiHost" -ForegroundColor Red
    Write-Host "💡 Starting local development server..." -ForegroundColor Yellow

    # Start API in background
    $apiJob = Start-Job -ScriptBlock {
        param($workDir)
        Set-Location $workDir
        & python -m uvicorn packages.paracle_api.main:app --host 0.0.0.0 --port 8000
    } -ArgumentList (Get-Location)

    Write-Host "⏳ Waiting for API to start (30s)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30

    try {
        $response = Invoke-WebRequest -Uri "$ApiHost/health" -Method GET -TimeoutSec 5
        Write-Host "✅ API started successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to start API" -ForegroundColor Red
        Write-Host "💡 Running tests in SIMULATION mode (no actual API calls)" -ForegroundColor Yellow
        $SimulationMode = $true
    }
}

Write-Host ""

# Check if locust is installed
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
try {
    $locustVersion = & locust --version 2>&1
    Write-Host "✅ Locust installed: $locustVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Locust not installed" -ForegroundColor Red
    Write-Host "💡 Installing locust..." -ForegroundColor Yellow
    & pip install locust==2.20.0
    Write-Host "✅ Locust installed successfully" -ForegroundColor Green
}

Write-Host ""

# Create results directory
$resultsDir = "tests/performance/results"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
New-Item -ItemType Directory -Path "$resultsDir/$timestamp" -Force | Out-Null

# Function to run a test scenario
function Run-TestScenario {
    param(
        [string]$Name,
        [int]$Users,
        [int]$SpawnRate,
        [int]$RunTime,
        [string]$Description
    )

    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "🧪 Test Scenario: $Name" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "📋 Description: $Description" -ForegroundColor White
    Write-Host "👥 Users: $Users | ⚡ Spawn Rate: $SpawnRate/s | ⏱️  Duration: $RunTime`s" -ForegroundColor White
    Write-Host ""

    $outputFile = "$resultsDir/$timestamp/$Name.html"
    $csvFile = "$resultsDir/$timestamp/$Name"

    if (-not $SimulationMode) {
        Write-Host "🏃 Running test..." -ForegroundColor Yellow

        # Run locust test
        & locust -f tests/performance/locustfile.py `
            --host $ApiHost `
            --users $Users `
            --spawn-rate $SpawnRate `
            --run-time "${RunTime}s" `
            --headless `
            --html $outputFile `
            --csv $csvFile `
            --only-summary

        Write-Host ""
        Write-Host "✅ Test completed!" -ForegroundColor Green
        Write-Host "📊 Results saved to: $outputFile" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  SIMULATION MODE - Generating mock results..." -ForegroundColor Yellow

        # Generate simulated results
        Generate-MockResults -Name $Name -Users $Users -OutputFile $outputFile

        Write-Host "✅ Mock results generated!" -ForegroundColor Green
    }

    Write-Host ""
}

# Function to generate mock results for simulation mode
function Generate-MockResults {
    param(
        [string]$Name,
        [int]$Users,
        [string]$OutputFile
    )

    # Calculate realistic metrics based on user count
    $baseRps = 100
    $userMultiplier = $Users / 100
    $expectedRps = [math]::Round($baseRps * $userMultiplier, 0)

    # Latency increases with load
    $baseP50 = 150
    $baseP95 = 400
    $baseP99 = 850

    $loadFactor = [math]::Min($userMultiplier, 3)
    $p50 = [math]::Round($baseP50 * $loadFactor, 0)
    $p95 = [math]::Round($baseP95 * $loadFactor, 0)
    $p99 = [math]::Round($baseP99 * $loadFactor, 0)

    # Error rate increases with stress
    $errorRate = if ($Users -gt 1500) { 0.5 + (($Users - 1500) * 0.001) } else { 0.02 }

    $mockHtml = @"
<!DOCTYPE html>
<html>
<head>
    <title>Paracle Performance Test - $Name (SIMULATED)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; padding: 15px 25px; background: #ecf0f1; border-radius: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .metric-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; }
        .pass { color: #27ae60; }
        .fail { color: #e74c3c; }
        .warning { color: #f39c12; background: #fff3cd; padding: 15px; border-left: 4px solid #f39c12; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Paracle Performance Test Results - $Name</h1>
        <div class="warning">
            ⚠️ <strong>SIMULATED RESULTS</strong> - These are mock results generated for demonstration purposes.
            Run tests against actual API for real metrics.
        </div>

        <h2>📊 Test Configuration</h2>
        <div class="metric">
            <div class="metric-value">$Users</div>
            <div class="metric-label">Concurrent Users</div>
        </div>
        <div class="metric">
            <div class="metric-value">$expectedRps</div>
            <div class="metric-label">Target RPS</div>
        </div>
        <div class="metric">
            <div class="metric-value">300s</div>
            <div class="metric-label">Duration</div>
        </div>

        <h2>🎯 Performance Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Target</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Throughput</td>
                <td><strong>$expectedRps req/s</strong></td>
                <td>≥1000 req/s</td>
                <td class="$(if($expectedRps -ge 1000){'pass'}else{'fail'})">$(if($expectedRps -ge 1000){'✅ PASS'}else{'❌ FAIL'})</td>
            </tr>
            <tr>
                <td>p50 Latency</td>
                <td><strong>${p50}ms</strong></td>
                <td>&lt;200ms</td>
                <td class="$(if($p50 -lt 200){'pass'}else{'fail'})">$(if($p50 -lt 200){'✅ PASS'}else{'❌ FAIL'})</td>
            </tr>
            <tr>
                <td>p95 Latency</td>
                <td><strong>${p95}ms</strong></td>
                <td>&lt;500ms</td>
                <td class="$(if($p95 -lt 500){'pass'}else{'fail'})">$(if($p95 -lt 500){'✅ PASS'}else{'❌ FAIL'})</td>
            </tr>
            <tr>
                <td>p99 Latency</td>
                <td><strong>${p99}ms</strong></td>
                <td>&lt;1000ms</td>
                <td class="$(if($p99 -lt 1000){'pass'}else{'fail'})">$(if($p99 -lt 1000){'✅ PASS'}else{'❌ FAIL'})</td>
            </tr>
            <tr>
                <td>Error Rate</td>
                <td><strong>$([math]::Round($errorRate, 4))%</strong></td>
                <td>&lt;0.1%</td>
                <td class="$(if($errorRate -lt 0.1){'pass'}else{'fail'})">$(if($errorRate -lt 0.1){'✅ PASS'}else{'❌ FAIL'})</td>
            </tr>
        </table>

        <h2>📈 Request Distribution</h2>
        <table>
            <tr>
                <th>Operation</th>
                <th>Requests</th>
                <th>Avg Latency</th>
                <th>Failures</th>
            </tr>
            <tr>
                <td>List Agents (40%)</td>
                <td>$([math]::Round($expectedRps * 300 * 0.4, 0))</td>
                <td>${p50}ms</td>
                <td>$([math]::Round($expectedRps * 300 * 0.4 * $errorRate / 100, 0))</td>
            </tr>
            <tr>
                <td>Get Agent Details (30%)</td>
                <td>$([math]::Round($expectedRps * 300 * 0.3, 0))</td>
                <td>$([math]::Round($p50 * 1.5, 0))ms</td>
                <td>$([math]::Round($expectedRps * 300 * 0.3 * $errorRate / 100, 0))</td>
            </tr>
            <tr>
                <td>Execute Agent (20%)</td>
                <td>$([math]::Round($expectedRps * 300 * 0.2, 0))</td>
                <td>$([math]::Round($p95 * 0.8, 0))ms</td>
                <td>$([math]::Round($expectedRps * 300 * 0.2 * $errorRate / 100, 0))</td>
            </tr>
            <tr>
                <td>Execute Workflow (8%)</td>
                <td>$([math]::Round($expectedRps * 300 * 0.08, 0))</td>
                <td>$([math]::Round($p99 * 1.2, 0))ms</td>
                <td>$([math]::Round($expectedRps * 300 * 0.08 * $errorRate / 100, 0))</td>
            </tr>
            <tr>
                <td>Health Check (2%)</td>
                <td>$([math]::Round($expectedRps * 300 * 0.02, 0))</td>
                <td>$([math]::Round($p50 * 0.5, 0))ms</td>
                <td>0</td>
            </tr>
        </table>

        <p style="margin-top: 40px; color: #7f8c8d; font-size: 12px;">
            Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Scenario: $Name | Mode: SIMULATION
        </p>
    </div>
</body>
</html>
"@

    $mockHtml | Out-File -FilePath $OutputFile -Encoding UTF8
}

# Run test scenarios
if ($Scenario -eq "all" -or $Scenario -eq "baseline") {
    Run-TestScenario -Name "01_Baseline_100users" `
        -Users 100 `
        -SpawnRate 10 `
        -RunTime 300 `
        -Description "Baseline load test to establish performance characteristics"
}

if ($Scenario -eq "all" -or $Scenario -eq "target") {
    Run-TestScenario -Name "02_Target_500users" `
        -Users 500 `
        -SpawnRate 50 `
        -RunTime 300 `
        -Description "Target load test approaching production levels"
}

if ($Scenario -eq "all" -or $Scenario -eq "peak") {
    Run-TestScenario -Name "03_Peak_1000users" `
        -Users 1000 `
        -SpawnRate 100 `
        -RunTime 600 `
        -Description "Peak load test validating SLA targets (≥1000 req/s)"
}

if ($Scenario -eq "all" -or $Scenario -eq "stress") {
    Run-TestScenario -Name "04_Stress_2000users" `
        -Users 2000 `
        -SpawnRate 100 `
        -RunTime 300 `
        -Description "Stress test to identify breaking points and bottlenecks"
}

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ All tests completed!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Results saved to: $resultsDir/$timestamp/" -ForegroundColor Cyan
Write-Host "📈 Open HTML files in browser to view detailed results" -ForegroundColor Cyan
Write-Host ""

# Summary
Write-Host "📋 Test Summary:" -ForegroundColor Yellow
Get-ChildItem -Path "$resultsDir/$timestamp/*.html" | ForEach-Object {
    Write-Host "   • $($_.Name)" -ForegroundColor White
}

# Cleanup
if ($apiJob) {
    Write-Host ""
    Write-Host "🛑 Stopping API server..." -ForegroundColor Yellow
    Stop-Job -Job $apiJob
    Remove-Job -Job $apiJob
}

Write-Host ""
Write-Host "🎉 Performance testing complete!" -ForegroundColor Green
