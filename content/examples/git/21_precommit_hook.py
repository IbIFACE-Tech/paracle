"""Example 21: Pre-commit Hook - Layer 4 Validation

This example demonstrates Layer 4 of the governance system:
Pre-commit validation that blocks commits with .parac/ structure violations.

Layer 4 provides a **safety net at commit time**, preventing violations
from entering version control.

What you'll learn:
1. How the pre-commit hook works
2. What happens when violations are detected
3. How to fix violations before committing
4. How to bypass (when absolutely necessary)
5. Integration with developer workflows

Prerequisites:
    pip install paracle-core
    paracle init  # Installs hook automatically
"""


def example_1_hook_automatic_installation():
    """Example 1: Pre-commit hook installed automatically during init."""
    print("=" * 70)
    print("Example 1: Automatic Hook Installation")
    print("=" * 70 + "\n")

    print("When you run 'paracle init', the pre-commit hook is installed:\n")

    print("$ cd my-project")
    print("$ git init")
    print("$ paracle init\n")

    print("✅ Creates .parac/ structure")
    print("✅ Installs pre-commit hook: .git/hooks/pre-commit")
    print("✅ Makes hook executable\n")

    print("The hook runs automatically on every 'git commit'")
    print()


def example_2_valid_commit():
    """Example 2: Commit with valid .parac/ files succeeds."""
    print("=" * 70)
    print("Example 2: Valid Commit Succeeds")
    print("=" * 70 + "\n")

    print("Developer creates file in correct location:\n")

    print("# Create database in correct location")
    print("$ echo 'data' > .parac/memory/data/costs.db")
    print("$ git add .parac/memory/data/costs.db")
    print("$ git commit -m 'Add cost tracking database'\n")

    print("Hook Output:")
    print("─" * 70)
    print("🔍 Validating 1 .parac/ file(s)...")
    print("✅ All 1 file(s) validated successfully!")
    print("   Commit allowed.\n")
    print("─" * 70)

    print("\n✅ Commit succeeds - file is in correct location\n")


def example_3_blocked_commit():
    """Example 3: Commit with invalid .parac/ files is blocked."""
    print("=" * 70)
    print("Example 3: Invalid Commit Blocked")
    print("=" * 70 + "\n")

    print("AI assistant creates file in wrong location:\n")

    print("# Copilot creates database in .parac root (WRONG)")
    print("$ echo 'data' > .parac/costs.db")
    print("$ git add .parac/costs.db")
    print("$ git commit -m 'Add database'\n")

    print("Hook Output:")
    print("─" * 70)
    print("🔍 Validating 1 .parac/ file(s)...")
    print()
    print("=" * 70)
    print("❌ COMMIT BLOCKED - .parac/ Structure Violations Found")
    print("=" * 70)
    print()
    print("1. File: .parac/costs.db")
    print("   Category: OPERATIONAL_DATA")
    print(
        "   Issue: File placement violation: All databases must be in .parac/memory/data/"
    )
    print("   ✅ Fix: Move to .parac/memory/data/costs.db")
    print()
    print("=" * 70)
    print("Total violations: 1")
    print("=" * 70)
    print()
    print("To fix these violations:")
    print()
    print("Option 1: Auto-fix (recommended)")
    print("  paracle validate structure --fix")
    print()
    print("Option 2: Manual fix")
    print("  git mv .parac/costs.db .parac/memory/data/costs.db")
    print()
    print("Option 3: Bypass (NOT RECOMMENDED)")
    print("  git commit --no-verify")
    print()
    print("Validation Summary:")
    print("  ✅ Valid files: 0")
    print("  ❌ Violations: 1")
    print()
    print("❌ Commit blocked due to structure violations.")
    print("   Fix the issues above and try again.")
    print()
    print("─" * 70)

    print("\n❌ Commit blocked - file is in wrong location\n")


def example_4_auto_fix_workflow():
    """Example 4: Using auto-fix to correct violations."""
    print("=" * 70)
    print("Example 4: Auto-Fix Workflow")
    print("=" * 70 + "\n")

    print("After commit is blocked, developer uses auto-fix:\n")

    print("# Commit blocked")
    print("$ git commit -m 'Add database'")
    print("❌ COMMIT BLOCKED\n")

    print("# Use auto-fix")
    print("$ paracle validate structure --fix\n")

    print("Auto-fix Output:")
    print("─" * 70)
    print("🔧 Fixing .parac/ structure violations...")
    print()
    print("Moving files:")
    print("  .parac/costs.db → .parac/memory/data/costs.db ✅")
    print()
    print("✅ Fixed 1 violation(s)")
    print("─" * 70)
    print()

    print("# Now commit succeeds")
    print("$ git add .parac/memory/data/costs.db")
    print("$ git commit -m 'Add cost tracking database'")
    print("✅ All 1 file(s) validated successfully!")
    print("   Commit allowed.\n")

    print("✅ Workflow complete - violation fixed and committed\n")


def example_5_multiple_violations():
    """Example 5: Multiple violations in one commit."""
    print("=" * 70)
    print("Example 5: Multiple Violations")
    print("=" * 70 + "\n")

    print("Developer commits multiple files with violations:\n")

    print("$ git add .parac/")
    print("$ git commit -m 'Add project files'\n")

    print("Hook Output:")
    print("─" * 70)
    print("🔍 Validating 3 .parac/ file(s)...")
    print()
    print("=" * 70)
    print("❌ COMMIT BLOCKED - .parac/ Structure Violations Found")
    print("=" * 70)
    print()
    print("1. File: .parac/costs.db")
    print("   Category: OPERATIONAL_DATA")
    print(
        "   Issue: File placement violation: All databases must be in .parac/memory/data/"
    )
    print("   ✅ Fix: Move to .parac/memory/data/costs.db")
    print()
    print("2. File: .parac/debug.log")
    print("   Category: LOGS")
    print(
        "   Issue: File placement violation: All log files must be in .parac/memory/logs/"
    )
    print("   ✅ Fix: Move to .parac/memory/logs/debug.log")
    print()
    print("3. File: .parac/architecture.md")
    print("   Category: KNOWLEDGE")
    print(
        "   Issue: File placement violation: Knowledge base files must be in .parac/memory/knowledge/"
    )
    print("   ✅ Fix: Move to .parac/memory/knowledge/architecture.md")
    print()
    print("=" * 70)
    print("Total violations: 3")
    print("=" * 70)
    print()
    print("Validation Summary:")
    print("  ✅ Valid files: 0")
    print("  ❌ Violations: 3")
    print()
    print("─" * 70)

    print("\n❌ All violations must be fixed before commit\n")


def example_6_bypass_hook():
    """Example 6: Bypassing the hook (emergency only)."""
    print("=" * 70)
    print("Example 6: Bypassing Hook (Emergency Only)")
    print("=" * 70 + "\n")

    print("⚠️  WARNING: Only use --no-verify in emergencies!\n")

    print("# Emergency commit (not recommended)")
    print("$ git commit -m 'Emergency fix' --no-verify\n")

    print("✅ Commit succeeds (hook bypassed)")
    print()
    print("⚠️  Note: Bypassing the hook:")
    print("   - Creates governance violations in version control")
    print("   - May break CI/CD pipelines")
    print("   - Requires cleanup later")
    print()
    print("Better approach:")
    print("   1. Fix violations properly")
    print("   2. Or use 'git commit --amend' after fixing")
    print()


def example_7_mixed_files():
    """Example 7: Commit with mixed .parac/ and regular files."""
    print("=" * 70)
    print("Example 7: Mixed Files Commit")
    print("=" * 70 + "\n")

    print("Developer commits both .parac/ and application files:\n")

    print("$ git add .")
    print("$ git commit -m 'Feature implementation'\n")

    print("Hook Output:")
    print("─" * 70)
    print("🔍 Validating 2 .parac/ file(s)...")
    print("✅ All 2 file(s) validated successfully!")
    print("   Commit allowed.")
    print("─" * 70)
    print()

    print("Files committed:")
    print("  src/feature.py                        ✅ (not validated)")
    print("  .parac/memory/data/metrics.db         ✅ (validated, correct)")
    print("  .parac/memory/logs/feature.log        ✅ (validated, correct)")
    print("  README.md                             ✅ (not validated)")
    print()
    print("✅ Hook only validates .parac/ files, allows rest through\n")


def example_8_integration_with_ci():
    """Example 8: Integration with CI/CD pipelines."""
    print("=" * 70)
    print("Example 8: CI/CD Integration")
    print("=" * 70 + "\n")

    print("Pre-commit hook works with CI/CD:\n")

    print("# GitHub Actions workflow")
    print("─" * 70)
    print("name: Validate PR")
    print()
    print("on: [pull_request]")
    print()
    print("jobs:")
    print("  validate:")
    print("    runs-on: ubuntu-latest")
    print("    steps:")
    print("      - uses: actions/checkout@v3")
    print("      - name: Validate .parac/ structure")
    print("        run: |")
    print("          python .parac/tools/hooks/validate-structure.py")
    print("─" * 70)
    print()

    print("Benefits:")
    print("  ✅ Catches violations in PRs")
    print("  ✅ Prevents bad commits from merging")
    print("  ✅ Consistent enforcement across team")
    print("  ✅ No manual review needed for structure")
    print()


def main():
    """Run all pre-commit hook examples."""
    print("\n" + "=" * 70)
    print("LAYER 4: PRE-COMMIT VALIDATION")
    print("Git Hook that Blocks Commits with Structure Violations")
    print("=" * 70 + "\n")

    print("Layer 4 adds a safety net at commit time:\n")
    print("  • Validates .parac/ files before commit")
    print("  • Blocks commits with violations")
    print("  • Provides auto-fix suggestions")
    print("  • Integrates with developer workflows")
    print("  • Works with CI/CD pipelines")
    print()

    input("Press Enter to see examples...")
    print()

    # Run examples
    example_1_hook_automatic_installation()
    input("Press Enter to continue...")
    print()

    example_2_valid_commit()
    input("Press Enter to continue...")
    print()

    example_3_blocked_commit()
    input("Press Enter to continue...")
    print()

    example_4_auto_fix_workflow()
    input("Press Enter to continue...")
    print()

    example_5_multiple_violations()
    input("Press Enter to continue...")
    print()

    example_6_bypass_hook()
    input("Press Enter to continue...")
    print()

    example_7_mixed_files()
    input("Press Enter to continue...")
    print()

    example_8_integration_with_ci()

    print("\n" + "=" * 70)
    print("SUMMARY: Layer 4 Pre-commit Validation")
    print("=" * 70 + "\n")

    print("What Layer 4 Provides:\n")
    print("  ✅ Safety net at commit time")
    print("  ✅ Prevents violations from entering version control")
    print("  ✅ Auto-fix suggestions for quick resolution")
    print("  ✅ Seamless developer workflow integration")
    print("  ✅ CI/CD pipeline support")
    print("  ✅ Team-wide consistency enforcement")
    print()

    print("Governance Layers So Far:\n")
    print("  Layer 1: Automatic Action Logging ✅")
    print("  Layer 2: Automatic State Management ✅")
    print("  Layer 3: AI Compliance Engine (real-time blocking) ✅")
    print("  Layer 4: Pre-commit Validation (commit-time blocking) ✅")
    print("  Layer 5: Continuous Monitoring (planned)")
    print()

    print("Complete Protection:")
    print("  • Layer 3 blocks violations during development (AI assistants)")
    print("  • Layer 4 blocks violations at commit time (safety net)")
    print("  • Layer 5 will monitor and auto-repair 24/7")
    print()

    print("Next Steps:")
    print("  1. Install hook: paracle init")
    print("  2. Test with: git commit")
    print("  3. Use auto-fix: paracle validate structure --fix")
    print("  4. Integrate with CI/CD")
    print()


if __name__ == "__main__":
    main()
