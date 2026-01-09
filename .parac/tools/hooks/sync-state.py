#!/usr/bin/env python3
"""
Paracle State Synchronizer

Synchronizes current_state.yaml with the actual project state.
Reads from git, tests, and other sources to update metrics.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("⚠️  PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


PARAC_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = PARAC_ROOT.parent
STATE_FILE = PARAC_ROOT / "memory" / "context" / "current_state.yaml"


def run_command(cmd: list[str], cwd: Path = PROJECT_ROOT) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def get_git_info() -> dict:
    """Get current git state."""
    info = {}

    # Current branch
    success, output = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    info["branch"] = output if success else "unknown"

    # Last commit
    success, output = run_command(["git", "log", "-1", "--format=%h %s"])
    info["last_commit"] = output if success else "unknown"

    # Uncommitted changes
    success, output = run_command(["git", "status", "--porcelain"])
    info["has_changes"] = bool(output) if success else False

    return info


def get_test_coverage() -> str:
    """Get test coverage if available."""
    # Try to read from coverage report
    coverage_file = PROJECT_ROOT / ".coverage"
    if coverage_file.exists():
        # Would need coverage library to parse
        return "unknown"

    # Try pytest-cov output
    htmlcov = PROJECT_ROOT / "htmlcov" / "index.html"
    if htmlcov.exists():
        try:
            content = htmlcov.read_text()
            # Parse coverage from HTML (simplified)
            if "%" in content:
                import re

                match = re.search(r"(\d+)%", content)
                if match:
                    return f"{match.group(1)}%"
        except Exception:
            pass

    return "unknown"


def count_files(pattern: str, directory: Path = PROJECT_ROOT) -> int:
    """Count files matching pattern."""
    return len(list(directory.rglob(pattern)))


def update_state(state: dict) -> dict:
    """Update state with current information."""
    # Update snapshot date
    state["snapshot_date"] = datetime.now().strftime("%Y-%m-%d")

    # Update git info
    git_info = get_git_info()
    if "repository" not in state:
        state["repository"] = {}
    state["repository"]["branch"] = git_info["branch"]
    state["repository"]["last_commit"] = git_info["last_commit"]
    state["repository"]["has_uncommitted_changes"] = git_info["has_changes"]

    # Update file counts
    packages_dir = PROJECT_ROOT / "packages"
    tests_dir = PROJECT_ROOT / "tests"

    if packages_dir.exists():
        state.setdefault("metrics", {})["python_files"] = count_files(
            "*.py", packages_dir
        )

    if tests_dir.exists():
        state.setdefault("metrics", {})["test_files"] = count_files(
            "test_*.py", tests_dir
        )

    # Try to get coverage
    coverage = get_test_coverage()
    if coverage != "unknown":
        state.setdefault("metrics", {})["code_coverage"] = coverage

    return state


def main():
    """Synchronize state file."""
    print("=" * 60)
    print("Paracle State Synchronizer")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # Read current state
    print("📖 Reading current state...")
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            state = yaml.safe_load(f)
        print(f"  ✅ Loaded state version {state.get('version', 'unknown')}")
    except Exception as e:
        print(f"  ❌ Error reading state: {e}")
        sys.exit(1)
    print()

    # Update state
    print("🔄 Updating state from project...")
    state = update_state(state)
    print("  ✅ State updated")
    print()

    # Show changes
    print("📊 Current metrics:")
    metrics = state.get("metrics", {})
    for key, value in metrics.items():
        print(f"  - {key}: {value}")
    print()

    print("📂 Repository:")
    repo = state.get("repository", {})
    for key, value in repo.items():
        print(f"  - {key}: {value}")
    print()

    # Write updated state
    print("💾 Writing updated state...")
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            yaml.dump(
                state, f, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
        print("  ✅ State file updated")
    except Exception as e:
        print(f"  ❌ Error writing state: {e}")
        sys.exit(1)
    print()

    print("=" * 60)
    print("✅ Synchronization complete")


if __name__ == "__main__":
    main()
