#!/bin/bash
# Bash script to install git hooks for Unix/Linux/Mac

set -e

GIT_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$GIT_ROOT/.git/hooks"
SOURCE_HOOK="$GIT_ROOT/.parac/tools/hooks/pre-commit"

echo "📦 Installing PARACLE git hooks..."

# Check if source hook exists
if [ ! -f "$SOURCE_HOOK" ]; then
    echo "❌ Error: Source hook not found: $SOURCE_HOOK"
    exit 1
fi

# Copy the unified pre-commit hook
cp "$SOURCE_HOOK" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Git hooks installed successfully!"
echo ""
echo "The .parac/ workspace will now be automatically maintained:"
echo "  - Agent manifest regeneration when agent specs change"
echo "  - Project state updates when code/docs change"
