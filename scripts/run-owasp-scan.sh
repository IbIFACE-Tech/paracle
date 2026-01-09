#!/bin/bash
# OWASP Dependency-Check Quick Runner
# Usage: ./run-owasp-scan.sh [output_format]
# Formats: HTML, JSON, XML, CSV, JUNIT, ALL (default: HTML)

set -e

VERSION="12.1.9"
DC_DIR="./dependency-check"
REPORTS_DIR="./reports/owasp"
FORMAT="${1:-HTML}"

echo "🔍 OWASP Dependency-Check v${VERSION}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create reports directory
mkdir -p "${REPORTS_DIR}"

# Download if not present
if [ ! -d "${DC_DIR}" ]; then
    echo "📥 Downloading OWASP Dependency-Check v${VERSION}..."
    wget -q "https://github.com/dependency-check/DependencyCheck/releases/download/v${VERSION}/dependency-check-${VERSION}-release.zip"
    unzip -q "dependency-check-${VERSION}-release.zip" -d dependency-check
    rm "dependency-check-${VERSION}-release.zip"
    echo "✅ Downloaded and extracted"
else
    echo "✅ Using existing installation"
fi

# Run scan
echo ""
echo "🔎 Scanning project for vulnerabilities..."
echo "   Output: ${REPORTS_DIR}"
echo "   Format: ${FORMAT}"
echo ""

"${DC_DIR}/dependency-check/bin/dependency-check.sh" \
    --scan . \
    --format "${FORMAT}" \
    --out "${REPORTS_DIR}" \
    --project "Paracle" \
    --enableExperimental \
    --suppression .github/dependency-check-suppressions.xml \
    --exclude "**/node_modules/**" \
    --exclude "**/venv/**" \
    --exclude "**/.venv/**" \
    --exclude "**/build/**" \
    --exclude "**/dist/**" \
    --exclude "**/__pycache__/**"

echo ""
echo "✅ Scan complete!"
echo ""
echo "📊 Report generated:"
if [ "${FORMAT}" = "HTML" ] || [ "${FORMAT}" = "ALL" ]; then
    echo "   📄 HTML: ${REPORTS_DIR}/dependency-check-report.html"
fi
if [ "${FORMAT}" = "JSON" ] || [ "${FORMAT}" = "ALL" ]; then
    echo "   📄 JSON: ${REPORTS_DIR}/dependency-check-report.json"
fi
echo ""

# Check for vulnerabilities
if [ -f "${REPORTS_DIR}/dependency-check-report.json" ]; then
    echo "🔍 Vulnerability Summary:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Parse JSON for summary
    CRITICAL=$(jq -r '[.dependencies[].vulnerabilities[]? | select(.severity=="CRITICAL")] | length' "${REPORTS_DIR}/dependency-check-report.json" 2>/dev/null || echo "0")
    HIGH=$(jq -r '[.dependencies[].vulnerabilities[]? | select(.severity=="HIGH")] | length' "${REPORTS_DIR}/dependency-check-report.json" 2>/dev/null || echo "0")
    MEDIUM=$(jq -r '[.dependencies[].vulnerabilities[]? | select(.severity=="MEDIUM")] | length' "${REPORTS_DIR}/dependency-check-report.json" 2>/dev/null || echo "0")
    LOW=$(jq -r '[.dependencies[].vulnerabilities[]? | select(.severity=="LOW")] | length' "${REPORTS_DIR}/dependency-check-report.json" 2>/dev/null || echo "0")

    echo "   🔴 Critical: ${CRITICAL}"
    echo "   🟠 High:     ${HIGH}"
    echo "   🟡 Medium:   ${MEDIUM}"
    echo "   🟢 Low:      ${LOW}"
    echo ""

    if [ "${CRITICAL}" -gt 0 ] || [ "${HIGH}" -gt 0 ]; then
        echo "⚠️  Action Required: Critical or High vulnerabilities found!"
        exit 1
    else
        echo "✅ No critical or high vulnerabilities found"
        exit 0
    fi
else
    echo "⚠️  Could not parse summary (JSON report not generated)"
    exit 0
fi
