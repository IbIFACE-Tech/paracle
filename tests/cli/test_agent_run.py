"""Test script for agent run command."""

import subprocess
import sys


def run_command(cmd: list[str], description: str) -> bool:
    """Run CLI command and report results."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main() -> int:
    """Run all agent run tests."""
    print("\n🧪 PARACLE AGENT RUN - TEST SUITE")
    print("=" * 60)

    tests = [
        # 1. Help and validation
        (
            ["paracle", "agent", "run", "--help"],
            "Show help message",
        ),
        # 2. Dry run validation
        (
            [
                "paracle",
                "agent",
                "run",
                "reviewer",
                "--task",
                "Review code quality",
                "--dry-run",
            ],
            "Dry run - validate without executing",
        ),
        # 3. Safe mode (would need mocking for full test)
        (
            [
                "paracle",
                "agent",
                "run",
                "coder",
                "--task",
                "Analyze code structure",
                "--mode",
                "safe",
                "--dry-run",
            ],
            "Safe mode dry run",
        ),
        # 4. YOLO mode dry run
        (
            [
                "paracle",
                "agent",
                "run",
                "coder",
                "--task",
                "Format code",
                "--mode",
                "yolo",
                "--dry-run",
            ],
            "YOLO mode dry run",
        ),
        # 5. Sandbox mode dry run
        (
            [
                "paracle",
                "agent",
                "run",
                "tester",
                "--task",
                "Run tests",
                "--mode",
                "sandbox",
                "--dry-run",
            ],
            "Sandbox mode dry run",
        ),
        # 6. Review mode dry run
        (
            [
                "paracle",
                "agent",
                "run",
                "architect",
                "--task",
                "Design system",
                "--mode",
                "review",
                "--dry-run",
            ],
            "Review mode dry run",
        ),
        # 7. With inputs
        (
            [
                "paracle",
                "agent",
                "run",
                "coder",
                "--task",
                "Implement feature",
                "--input",
                "feature=auth",
                "--input",
                "priority=high",
                "--dry-run",
            ],
            "With input parameters",
        ),
        # 8. With model and provider
        (
            [
                "paracle",
                "agent",
                "run",
                "reviewer",
                "--task",
                "Review code",
                "--model",
                "gpt-4-turbo",
                "--provider",
                "openai",
                "--temperature",
                "0.3",
                "--dry-run",
            ],
            "With custom model and provider",
        ),
        # 9. With cost limit
        (
            [
                "paracle",
                "agent",
                "run",
                "documenter",
                "--task",
                "Generate docs",
                "--cost-limit",
                "2.50",
                "--dry-run",
            ],
            "With cost limit",
        ),
        # 10. With timeout
        (
            [
                "paracle",
                "agent",
                "run",
                "coder",
                "--task",
                "Large refactor",
                "--timeout",
                "600",
                "--dry-run",
            ],
            "With custom timeout",
        ),
        # 11. Verbose mode
        (
            [
                "paracle",
                "agent",
                "run",
                "reviewer",
                "--task",
                "Code review",
                "--verbose",
                "--dry-run",
            ],
            "Verbose output",
        ),
        # 12. Invalid agent (should fail gracefully)
        (
            [
                "paracle",
                "agent",
                "run",
                "nonexistent",
                "--task",
                "Test",
                "--dry-run",
            ],
            "Invalid agent (should handle gracefully)",
        ),
    ]

    passed = 0
    failed = 0

    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    print(f"{'='*60}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
