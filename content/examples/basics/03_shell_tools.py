"""Example: Using Paracle's built-in shell tool.

This example demonstrates how to use the run_command tool:
- Execute safe shell commands
- Capture stdout and stderr
- Handle command timeouts
- Use command whitelists for security

Run: uv run python examples/03_shell_tools.py
"""

import asyncio
import sys

from paracle_tools import run_command


async def main():
    """Demonstrate shell command tool usage."""
    print("=" * 60)
    print("Paracle Shell Command Tool Example")
    print("=" * 60)

    # =========================================================================
    # 1. SIMPLE COMMANDS
    # =========================================================================
    print("\n1. Running simple commands...")

    # Echo command
    result = await run_command.execute(command="echo Hello from Paracle")

    if result.success:
        print(f"✓ Command executed successfully")
        print(f"  Output: {result.output['stdout'].strip()}")
        print(f"  Return code: {result.output['return_code']}")
    else:
        print(f"✗ Error: {result.error}")

    # List files
    if sys.platform == "win32":
        list_cmd = "dir /B"
    else:
        list_cmd = "ls -1"

    result = await run_command.execute(command=list_cmd)

    if result.success:
        print(f"\n✓ Directory listing:")
        files = result.output["stdout"].strip().split("\n")[:5]
        for f in files:
            print(f"  - {f}")
        if len(result.output["stdout"].strip().split("\n")) > 5:
            print("  ...")

    # =========================================================================
    # 2. GIT COMMANDS
    # =========================================================================
    print("\n2. Git commands...")

    # Git status
    result = await run_command.execute(command="git status --short")

    if result.success:
        print(f"✓ Git status:")
        if result.output["stdout"].strip():
            print(result.output["stdout"].strip())
        else:
            print("  (no changes)")

    # Git log (last 3 commits)
    result = await run_command.execute(command="git log --oneline -3")

    if result.success:
        print(f"\n✓ Recent commits:")
        print(result.output["stdout"].strip())

    # =========================================================================
    # 3. PYTHON COMMANDS
    # =========================================================================
    print("\n3. Python commands...")

    # Python version
    result = await run_command.execute(command="python --version")

    if result.success:
        version = result.output["stdout"].strip() or result.output["stderr"].strip()
        print(f"✓ Python version: {version}")

    # Run Python code
    result = await run_command.execute(
        command="python -c \"import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')\""
    )

    if result.success:
        print(f"✓ Python info: {result.output['stdout'].strip()}")

    # =========================================================================
    # 4. COMMAND WITH STDERR
    # =========================================================================
    print("\n4. Commands with stderr output...")

    # Python writing to stderr
    result = await run_command.execute(
        command="python -c \"import sys; sys.stderr.write('This is stderr\\n')\""
    )

    if result.success:
        print(f"✓ Command executed")
        print(f"  Stdout: '{result.output['stdout'].strip()}'")
        print(f"  Stderr: '{result.output['stderr'].strip()}'")

    # =========================================================================
    # 5. COMMAND WITH NON-ZERO EXIT CODE
    # =========================================================================
    print("\n5. Commands with non-zero exit codes...")

    result = await run_command.execute(command='python -c "import sys; sys.exit(42)"')

    if result.success:  # Tool execution succeeded
        print(f"✓ Tool executed successfully")
        print(f"  Command success: {result.output['success']}")  # But command failed
        print(f"  Return code: {result.output['return_code']}")

    # =========================================================================
    # 6. SECURITY - BLOCKED COMMANDS
    # =========================================================================
    print("\n6. Security - Blocked commands...")

    # Try to run rm (should be blocked)
    result = await run_command.execute(command="rm -rf /")

    print(f"Attempting 'rm -rf /': success={result.success}")
    if not result.success:
        print(f"  ✓ Blocked! Error: {result.error}")

    # Try to run sudo (should be blocked)
    result = await run_command.execute(command="sudo ls")

    print(f"Attempting 'sudo ls': success={result.success}")
    if not result.success:
        print(f"  ✓ Blocked! Error: {result.error}")

    # =========================================================================
    # 7. COMMAND WHITELIST
    # =========================================================================
    print("\n7. Using command whitelists...")

    from paracle_tools.builtin.shell import RunCommandTool

    # Create tool that only allows echo and ls
    restricted_shell = RunCommandTool(allowed_commands=["echo", "ls", "dir"])

    # This will succeed (echo is allowed)
    result = await restricted_shell.execute(command="echo Allowed command")
    print(f"Echo (allowed): success={result.success}")
    if result.success:
        print(f"  Output: {result.output['stdout'].strip()}")

    # This will fail (python not in whitelist)
    result = await restricted_shell.execute(command="python --version")
    print(f"Python (not allowed): success={result.success}")
    if not result.success:
        print(f"  Error: {result.error}")

    # =========================================================================
    # 8. COMMAND TIMEOUT
    # =========================================================================
    print("\n8. Command timeouts...")

    # Create tool with 1-second timeout
    fast_shell = RunCommandTool(timeout=1.0)

    # Fast command (should succeed)
    result = await fast_shell.execute(command="echo Quick command")
    print(f"Quick command: success={result.success}")

    # Slow command (should timeout)
    if sys.platform == "win32":
        slow_cmd = 'python -c "import time; time.sleep(5)"'
    else:
        slow_cmd = "sleep 5"

    result = await fast_shell.execute(command=slow_cmd)
    print(f"Slow command (5s with 1s timeout): success={result.success}")
    if not result.success:
        print(f"  ✓ Timed out! Error: {result.error}")

    # =========================================================================
    # 9. PYTEST EXAMPLE
    # =========================================================================
    print("\n9. Running tests...")

    # Run a specific test
    result = await run_command.execute(
        command="pytest tests/unit/test_builtin_tools_shell.py -v --tb=short"
    )

    if result.success:
        print(f"✓ Tests executed")
        print(f"  Return code: {result.output['return_code']}")
        # Show last few lines
        output_lines = result.output["stdout"].strip().split("\n")
        print("  Last lines:")
        for line in output_lines[-5:]:
            print(f"    {line}")

    # =========================================================================
    # 10. USING THE REGISTRY
    # =========================================================================
    print("\n10. Using BuiltinToolRegistry...")

    from paracle_tools import BuiltinToolRegistry

    # Create registry with custom configuration
    registry = BuiltinToolRegistry(
        allowed_commands=["echo", "git", "python", "ls", "dir"], command_timeout=5.0
    )

    # Execute through registry
    result = await registry.execute_tool("run_command", command="echo Via registry")

    if result.success:
        print(f"✓ Via registry: {result.output['stdout'].strip()}")

    # =========================================================================
    # 11. ERROR HANDLING
    # =========================================================================
    print("\n11. Error handling...")

    # Non-existent command
    from paracle_tools.builtin.shell import RunCommandTool

    shell = RunCommandTool(allowed_commands=["nonexistentcommand12345"])
    result = await shell.execute(command="nonexistentcommand12345")

    print(f"Non-existent command: success={result.success}")
    if not result.success:
        print(f"  Error: {result.error}")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print("\nSecurity notes:")
    print("- Dangerous commands (rm, sudo, etc.) are blocked by default")
    print("- Use allowed_commands whitelist for production")
    print("- Set appropriate timeouts to prevent hung processes")
    print("- Always validate command inputs from untrusted sources")


if __name__ == "__main__":
    asyncio.run(main())
