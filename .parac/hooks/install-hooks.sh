#!/bin/bash
# Bash script to install git hooks for Unix/Linux/Mac

set -e

GIT_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$GIT_ROOT/.git/hooks"

echo "📦 Installing PARACLE git hooks..."

# Pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook to regenerate manifest when agents change

# Check if any agent specs were modified
AGENT_SPECS_CHANGED=$(git diff --cached --name-only | grep -c "^\.parac/agents/specs/.*\.md$" || true)

if [ $AGENT_SPECS_CHANGED -gt 0 ]; then
    echo "🤖 Agent specs modified, regenerating manifest..."

    # Regenerate manifest
    paracle sync --manifest --no-git --no-metrics

    # Add the updated manifest to the commit
    git add .parac/manifest.yaml

    echo "✅ Manifest regenerated and staged"
fi
EOF

chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Git hooks installed successfully!"
echo ""
echo "The manifest will now be automatically regenerated when you commit agent changes."
