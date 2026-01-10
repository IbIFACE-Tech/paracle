#!/bin/bash
# Stop MCP Processes Script (Bash version)
# Run this if MCP server is stuck or causing file locks

echo "🔍 Finding MCP-related processes..."

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Find Python processes in project directory
pids=$(ps aux | grep python | grep "$PROJECT_DIR" | grep -v grep | awk '{print $2}')

if [ -z "$pids" ]; then
    echo "✅ No MCP processes found"
    exit 0
fi

echo "Found processes:"
ps aux | grep python | grep "$PROJECT_DIR" | grep -v grep

echo "🛑 Stopping processes..."
echo "$pids" | xargs kill -9

sleep 1

# Verify
remaining=$(ps aux | grep python | grep "$PROJECT_DIR" | grep -v grep | awk '{print $2}')
if [ -z "$remaining" ]; then
    echo "✅ All MCP processes stopped successfully"
else
    echo "⚠️  Some processes still running:"
    ps aux | grep python | grep "$PROJECT_DIR" | grep -v grep
fi
