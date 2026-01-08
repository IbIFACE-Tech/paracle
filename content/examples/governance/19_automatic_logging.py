"""Example: Automatic Logging with Decorators.

This example demonstrates the automatic logging system.
No manual logging required!
"""

import asyncio

from paracle_core.governance.auto_logger import (
    agent_operation,
    async_agent_operation,
    log_agent_action,
)
from paracle_core.governance.logger import get_governance_logger
from paracle_core.governance.state_manager import get_state_manager

# =============================================================================
# Example 1: Automatic Function Logging
# =============================================================================


@log_agent_action("CoderAgent", "IMPLEMENTATION")
async def implement_authentication() -> dict:
    """Implement JWT authentication system."""
    print("Implementing authentication...")
    await asyncio.sleep(0.1)  # Simulate work

    return {
        "files_created": ["auth.py", "jwt.py"],
        "tests_added": 15,
        "lines_of_code": 350,
    }


@log_agent_action("TesterAgent", "TEST")
async def run_test_suite(test_path: str) -> dict:
    """Run test suite and return results."""
    print(f"Running tests in {test_path}...")
    await asyncio.sleep(0.2)

    return {
        "total": 100,
        "passed": 98,
        "failed": 2,
        "coverage": "94.5%",
    }


@log_agent_action("ReviewerAgent", "REVIEW")
def review_code(file_path: str) -> dict:
    """Review code for quality and security."""
    print(f"Reviewing {file_path}...")

    return {
        "issues_found": 3,
        "severity": "medium",
        "suggestions": ["Add docstrings", "Improve error handling"],
    }


# =============================================================================
# Example 2: Automatic Operation Logging (Context Managers)
# =============================================================================


async def feature_development_with_context():
    """Develop feature using context managers for automatic logging."""

    # Synchronous operation
    with agent_operation("CoderAgent", "Implementing user authentication"):
        print("Creating auth module...")
        await asyncio.sleep(0.1)
        print("Adding JWT support...")

    # Async operation
    async with async_agent_operation("TesterAgent", "Running authentication tests"):
        print("Running unit tests...")
        await asyncio.sleep(0.1)
        print("Running integration tests...")


# =============================================================================
# Example 3: Automatic State Management
# =============================================================================


async def complete_deliverable_automatically():
    """Complete a deliverable - state auto-updates!"""

    # Get state manager
    state_manager = get_state_manager()

    # Simulate completing a deliverable
    print("\n--- Completing deliverable: conditional_retry ---")

    await state_manager.on_deliverable_completed(
        deliverable_id="conditional_retry",
        agent="CoderAgent",
        phase="phase_9",
        description="Retry system with exponential backoff and custom conditions",
    )

    print("✅ State automatically updated!")
    print("  - Deliverable marked complete")
    print("  - Progress recalculated")
    print("  - Recent update added")
    print("  - No manual editing required!")


# =============================================================================
# Example 4: Error Handling (Automatic Failure Logging)
# =============================================================================


@log_agent_action("CoderAgent", "BUGFIX")
async def bugfix_with_error():
    """Example of automatic error logging."""
    print("Attempting to fix bug...")
    await asyncio.sleep(0.1)

    # This error will be automatically logged
    raise ValueError("Database connection failed")


# =============================================================================
# Example 5: Check Logs
# =============================================================================


def view_recent_logs():
    """View recent log entries."""
    logger = get_governance_logger()

    print("\n--- Recent Log Entries ---")

    # Read last 10 lines from log file
    log_file = logger.actions_log

    if log_file.exists():
        with open(log_file) as f:
            lines = f.readlines()
            recent = lines[-10:]

            for line in recent:
                print(line.strip())
    else:
        print("Log file not found")


# =============================================================================
# Main Demo
# =============================================================================


async def main():
    """Run all examples."""

    print("=" * 70)
    print("AUTOMATIC LOGGING DEMO")
    print("=" * 70)

    # Example 1: Decorated functions
    print("\n1. Decorated Functions (Auto-logged)")
    print("-" * 70)

    result1 = await implement_authentication()
    print(f"Result: {result1}")

    result2 = await run_test_suite("tests/")
    print(f"Result: {result2}")

    result3 = review_code("src/auth.py")
    print(f"Result: {result3}")

    # Example 2: Context managers
    print("\n2. Context Managers (Auto-logged)")
    print("-" * 70)

    await feature_development_with_context()

    # Example 3: Automatic state management
    print("\n3. Automatic State Management")
    print("-" * 70)

    try:
        await complete_deliverable_automatically()
    except FileNotFoundError as e:
        print(f"Note: {e}")
        print("(State manager needs .parac/ directory)")

    # Example 4: Error handling
    print("\n4. Error Handling (Auto-logged)")
    print("-" * 70)

    try:
        await bugfix_with_error()
    except ValueError as e:
        print(f"Error caught: {e}")
        print("✅ Error automatically logged!")

    # Example 5: View logs
    print("\n5. View Recent Logs")
    print("-" * 70)

    view_recent_logs()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Points:")
    print("  ✅ No manual logging required")
    print("  ✅ All actions automatically logged")
    print("  ✅ Success and failure both captured")
    print("  ✅ State updates automatically")
    print("  ✅ Zero maintenance overhead")


if __name__ == "__main__":
    asyncio.run(main())
