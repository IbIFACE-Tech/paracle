#!/usr/bin/env python
"""Quick CLI smoke tests for Paracle."""

from click.testing import CliRunner
from paracle_cli.main import cli


def test_cli():
    """Run quick CLI smoke tests."""
    runner = CliRunner()

    tests = [
        ("--version", "Version check"),
        ("--help", "Help command"),
        ("hello", "Installation verification"),
        ("agents list", "List agents"),
        ("tools list", "List tools"),
        ("status", "Show status"),
        ("doctor", "Health check"),
    ]

    print("\nParacle CLI Quick Tests\n" + "=" * 50)

    passed = 0
    failed = 0

    for cmd, desc in tests:
        result = runner.invoke(cli, cmd.split())
        status = "[PASS]" if result.exit_code == 0 else f"[FAIL-{result.exit_code}]"
        print(f"{status:<12} paracle {cmd:<20} ({desc})")

        if result.exit_code == 0:
            passed += 1
        else:
            failed += 1
            print(f"             Error: {result.output[:100]}")

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = test_cli()
    exit(0 if success else 1)
