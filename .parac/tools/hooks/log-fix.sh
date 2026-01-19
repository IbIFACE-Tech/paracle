#!/bin/bash
# Quick Fix Logging Script for Bash
# Usage: ./log-fix.sh "Description of the fix"

DESCRIPTION="$1"
AGENT="${2:-CoderAgent}"
ACTION="${3:-BUGFIX}"

if [ -z "$DESCRIPTION" ]; then
    echo "❌ Error: Description is required"
    echo "Usage: $0 \"Description\" [Agent] [Action]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGGER_SCRIPT="$SCRIPT_DIR/agent-logger.py"

echo "🔧 Logging fix..."

# Execute agent-logger.py
python "$LOGGER_SCRIPT" "$AGENT" "$ACTION" "$DESCRIPTION"

if [ $? -eq 0 ]; then
    echo "✅ Fix logged successfully!"
else
    echo "❌ Error logging fix"
    exit 1
fi
