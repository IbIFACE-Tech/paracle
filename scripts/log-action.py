#!/usr/bin/env python3
"""
Quick Action Logger - Wrapper for agent-logger.py

Usage:
    python scripts/log-action.py BUGFIX "Fixed docker import error"
    python scripts/log-action.py IMPLEMENTATION "Added new feature"
    python scripts/log-action.py TEST "Added unit tests"

This is a convenience wrapper that calls the main agent-logger.py
from .parac/tools/hooks/ with sensible defaults.
"""

from hooks.agent_logger import AgentLogger
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / ".parac" / "tools"))


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: log-action.py <ACTION> <DESCRIPTION> [AGENT]")
        print("")
        print("Actions: BUGFIX, IMPLEMENTATION, TEST, REVIEW, DOCUMENTATION, etc.")
        print("Example: python scripts/log-action.py BUGFIX 'Fixed import error'")
        sys.exit(1)

    action = sys.argv[1].upper()
    description = sys.argv[2]
    agent = sys.argv[3] if len(sys.argv) > 3 else "CoderAgent"

    # Validate action type
    valid_actions = [
        "IMPLEMENTATION",
        "BUGFIX",
        "TEST",
        "REVIEW",
        "DOCUMENTATION",
        "DECISION",
        "PLANNING",
        "REFACTORING",
        "UPDATE",
    ]

    if action not in valid_actions:
        print(f"⚠️  Warning: '{action}' is not a standard action type")
        print(f"Valid types: {', '.join(valid_actions)}")
        response = input("Continue anyway? [y/N] ")
        if response.lower() != "y":
            sys.exit(1)

    try:
        logger = AgentLogger()
        logger.log_action(agent, action, description)
        print(f"✅ Logged: [{agent}] [{action}] {description}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
