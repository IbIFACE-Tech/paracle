#!/bin/bash
# Paracle Log Management Helper
# Quick access to log analysis, rotation, and cleanup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo "Paracle Log Management"
    echo "======================"
    echo ""
    echo "Usage: bash manage-logs.sh [command]"
    echo ""
    echo "Commands:"
    echo "  analyze  - Analyze current log size and status (default)"
    echo "  rotate   - Manually rotate logs (archive old entries)"
    echo "  cleanup  - Remove archives older than 1 year"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  bash manage-logs.sh                 # Analyze logs"
    echo "  bash manage-logs.sh analyze         # Analyze logs"
    echo "  bash manage-logs.sh rotate          # Rotate logs now"
    echo "  bash manage-logs.sh cleanup         # Clean old archives"
}

COMMAND="${1:-analyze}"

case "$COMMAND" in
    analyze)
        echo "📊 Analyzing logs..."
        python "$SCRIPT_DIR/analyze-logs.py"
        ;;
    rotate)
        echo "🔄 Rotating logs..."
        python "$SCRIPT_DIR/rotate-logs.py"
        ;;
    cleanup)
        echo "🧹 Cleaning up old archives..."
        python "$SCRIPT_DIR/cleanup-logs.py"
        ;;
    help)
        show_help
        ;;
    *)
        show_help
        ;;
esac
