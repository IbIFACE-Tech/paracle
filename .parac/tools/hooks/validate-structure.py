#!/usr/bin/env python3
"""Pre-commit hook for validating .parac/ structure.

This hook runs before git commit and validates that all files
in the .parac/ directory follow the structure rules defined in
.parac/STRUCTURE.md.

If violations are found:
1. The commit is blocked
2. Violations are displayed with suggested fixes
3. User can auto-fix or manually correct

Installation:
    paracle init --hooks  # Automatic
    OR
    ln -s ../../.parac/tools/hooks/validate-structure.py .git/hooks/pre-commit

Usage:
    This hook runs automatically on `git commit`
    To bypass (not recommended): git commit --no-verify

Exit codes:
    0 - No violations, commit allowed
    1 - Violations found, commit blocked
"""

import sys
from pathlib import Path

# Add project root to Python path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "packages"))

try:
    from paracle_core.governance import ValidationResult, get_compliance_engine
except ImportError as e:
    print(f"❌ Error: Cannot import paracle_core.governance: {e}")
    print("   Make sure Paracle is installed: pip install -e .")
    sys.exit(1)


def get_staged_parac_files() -> list[str]:
    """Get list of .parac/ files that are staged for commit.

    Returns:
        List of file paths relative to repo root
    """
    import subprocess

    try:
        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )

        # Filter for .parac/ files only
        all_files = result.stdout.strip().split("\n")
        parac_files = [f for f in all_files if f.startswith(".parac/") and f != ""]

        return parac_files

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running git: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: git not found in PATH")
        sys.exit(1)


def validate_files(
    files: list[str],
) -> tuple[list[ValidationResult], list[ValidationResult]]:
    """Validate list of files against structure rules.

    Args:
        files: List of file paths to validate

    Returns:
        Tuple of (valid_files, violations)
    """
    engine = get_compliance_engine()

    valid = []
    violations = []

    for file_path in files:
        result = engine.validate_file_path(file_path)

        if result.is_valid:
            valid.append(result)
        else:
            violations.append(result)

    return valid, violations


def display_violations(violations: list[ValidationResult]) -> None:
    """Display violations in user-friendly format.

    Args:
        violations: List of validation results with violations
    """
    print("\n" + "=" * 70)
    print("❌ COMMIT BLOCKED - .parac/ Structure Violations Found")
    print("=" * 70 + "\n")

    for i, v in enumerate(violations, 1):
        print(f"{i}. File: {v.path}")
        print(f"   Category: {v.category.value}")
        print(f"   Issue: {v.error}")
        print(f"   ✅ Fix: Move to {v.suggested_path}")
        print()

    print("=" * 70)
    print(f"Total violations: {len(violations)}")
    print("=" * 70 + "\n")


def display_auto_fix_instructions(violations: list[ValidationResult]) -> None:
    """Display instructions for auto-fixing violations.

    Args:
        violations: List of validation results with violations
    """
    print("To fix these violations:\n")
    print("Option 1: Auto-fix (recommended)")
    print("  paracle validate structure --fix\n")

    print("Option 2: Manual fix")
    for v in violations:
        print(f"  git mv {v.path} {v.suggested_path}")
    print()

    print("Option 3: Bypass (NOT RECOMMENDED)")
    print("  git commit --no-verify")
    print()


def display_summary(valid_count: int, violation_count: int) -> None:
    """Display validation summary.

    Args:
        valid_count: Number of valid files
        violation_count: Number of violations
    """
    print("Validation Summary:")
    print(f"  ✅ Valid files: {valid_count}")
    print(f"  ❌ Violations: {violation_count}")
    print()


def main() -> int:
    """Main pre-commit hook logic.

    Returns:
        0 if no violations (allow commit)
        1 if violations found (block commit)
    """
    # Get staged .parac/ files
    staged_files = get_staged_parac_files()

    if not staged_files:
        # No .parac/ files in commit, allow
        return 0

    print(f"\n🔍 Validating {len(staged_files)} .parac/ file(s)...")

    # Validate files
    valid, violations = validate_files(staged_files)

    # Display results
    if violations:
        display_violations(violations)
        display_auto_fix_instructions(violations)
        display_summary(len(valid), len(violations))

        print("❌ Commit blocked due to structure violations.")
        print("   Fix the issues above and try again.\n")

        return 1
    else:
        print(f"✅ All {len(valid)} file(s) validated successfully!")
        print("   Commit allowed.\n")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n❌ Validation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
