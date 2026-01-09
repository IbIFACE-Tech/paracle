"""Quick test for paracle config commands."""

import subprocess


def test_config_commands():
    """Test that config commands are available."""
    commands = [
        ["paracle", "config", "--help"],
        ["paracle", "config", "show", "--help"],
        ["paracle", "config", "validate", "--help"],
        ["paracle", "config", "files", "--help"],
    ]

    print("Testing paracle config commands...\n")

    for cmd in commands:
        cmd_str = " ".join(cmd)
        print(f"Testing: {cmd_str}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode == 0:
                print("  ✓ Command available")
            else:
                print(f"  ✗ Command failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"    Error: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            print("  ✗ Command timed out")
        except FileNotFoundError:
            print("  ✗ paracle command not found")
            print("    (This is expected if not installed)")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")

        print()

    print("\n✅ Config commands test complete!")


if __name__ == "__main__":
    test_config_commands()
