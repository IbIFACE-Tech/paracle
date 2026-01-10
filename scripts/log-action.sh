#!/bin/bash
# Quick Action Logger - Bash Wrapper
# Usage: ./scripts/log-action.sh BUGFIX "Fixed docker import error"

ACTION="$1"
DESCRIPTION="$2"
AGENT="${3:-CoderAgent}"

# Validate arguments
if [ -z "$ACTION" ] || [ -z "$DESCRIPTION" ]; then
    echo "Usage: $0 <ACTION> <DESCRIPTION> [AGENT]"
    echo ""
    echo "Actions: BUGFIX, IMPLEMENTATION, TEST, REVIEW, DOCUMENTATION, etc."
    echo "Example: ./scripts/log-action.sh BUGFIX 'Fixed import error'"
    exit 1
fi

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOGGER_SCRIPT="$PROJECT_ROOT/.parac/tools/hooks/agent-logger.py"

if [ ! -f "$LOGGER_SCRIPT" ]; then
    echo "❌ Error: agent-logger.py not found at $LOGGER_SCRIPT"
    exit 1
fi

echo "📝 Logging action..."

# Execute agent-logger.py
python "$LOGGER_SCRIPT" "$AGENT" "$ACTION" "$DESCRIPTION"

if [ $? -eq 0 ]; then
    echo "✅ Logged: [$AGENT] [$ACTION] $DESCRIPTION"
else
    echo "❌ Error logging action"
    exit 1
fi
