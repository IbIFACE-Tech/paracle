"""
Example 21: Git Workflow Management

Demonstrates branch-per-execution isolation for safe operations:
- BranchManager: Low-level git operations
- ExecutionManager: High-level execution lifecycle
- Integration with agent execution

Requirements:
    - Git repository initialized
    - Clean working directory recommended
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from paracle_git_workflows import BranchManager, ExecutionConfig, ExecutionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# EXAMPLE 1: BranchManager (Low-Level Operations)
# =============================================================================


def example_branch_manager():
    """Example: Using BranchManager for low-level git operations."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: BranchManager - Low-Level Git Operations")
    print("=" * 60)

    # Initialize manager
    repo_path = Path(".")
    manager = BranchManager(repo_path)

    # Get current branch
    current_branch = manager.get_current_branch()
    print(f"\nCurrent branch: {current_branch}")

    # Create execution branch
    print("\n1. Creating execution branch...")
    branch_info = manager.create_execution_branch(
        execution_id="demo-001", base_branch=current_branch
    )
    print(f"   ✓ Created: {branch_info.name}")
    print(f"   Base: {branch_info.base_branch}")
    print(f"   Execution ID: {branch_info.execution_id}")

    # List execution branches
    print("\n2. Listing execution branches...")
    branches = manager.list_execution_branches()
    print(f"   Found {len(branches)} execution branches:")
    for branch in branches[:5]:  # Show first 5
        print(f"   - {branch.name} ({branch.commit_count} commits)")

    # Switch back to original branch
    print(f"\n3. Switching back to {current_branch}...")
    manager.switch_branch(current_branch)
    print(f"   ✓ On branch: {manager.get_current_branch()}")

    # Merge execution branch (if you want to keep changes)
    merge_choice = input("\n   Merge demo branch? (y/N): ").lower()
    if merge_choice == "y":
        print(f"\n4. Merging {branch_info.name}...")
        try:
            manager.merge_execution_branch(
                branch_name=branch_info.name, target_branch=current_branch
            )
            print("   ✓ Merged successfully")
        except RuntimeError as e:
            print(f"   ✗ Merge failed: {e}")

    # Delete execution branch
    delete_choice = input("\n   Delete demo branch? (y/N): ").lower()
    if delete_choice == "y":
        print(f"\n5. Deleting {branch_info.name}...")
        manager.delete_execution_branch(branch_name=branch_info.name, force=False)
        print("   ✓ Deleted")
    else:
        print(
            f"\n   Branch {branch_info.name} kept "
            f"(delete manually with: git branch -d {branch_info.name})"
        )

    print("\n✓ BranchManager example complete")


# =============================================================================
# EXAMPLE 2: ExecutionManager (High-Level Lifecycle)
# =============================================================================


async def example_execution_manager():
    """Example: Using ExecutionManager for execution lifecycle."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: ExecutionManager - Execution Lifecycle")
    print("=" * 60)

    # Configure execution manager
    config = ExecutionConfig(
        enable_branching=True,
        auto_commit=True,
        auto_merge=False,  # Manual merge for demo
        auto_cleanup=False,  # Manual cleanup for demo
        base_branch="main",
    )

    manager = ExecutionManager(config=config, repo_path=".")

    # Start execution
    execution_id = f"demo-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    print(f"\n1. Starting execution: {execution_id}")

    info = manager.start_execution(execution_id)
    print(f"   ✓ Created branch: {info['branch_name']}")

    # Simulate work and commits
    print("\n2. Simulating work with auto-commits...")

    # Step 1: Add a file
    test_file = Path("demo_file.txt")
    test_file.write_text("Step 1: Initial content\n")
    print("   - Created demo_file.txt")

    manager.commit_changes(
        execution_id=execution_id,
        message="feat: Add demo file (step 1)",
        files=["demo_file.txt"],
    )
    print("   ✓ Committed step 1")

    # Step 2: Modify file
    test_file.write_text(test_file.read_text() + "Step 2: Additional content\n")
    print("   - Modified demo_file.txt")

    manager.commit_changes(
        execution_id=execution_id,
        message="feat: Update demo file (step 2)",
        files=["demo_file.txt"],
    )
    print("   ✓ Committed step 2")

    # List active executions
    print("\n3. Listing active executions...")
    active = manager.list_active_executions()
    for exec_id, branch_info in active.items():
        print(f"   - {exec_id}: {branch_info.name}")

    # Complete execution
    print(f"\n4. Completing execution: {execution_id}")

    success_choice = input("   Mark as successful? (Y/n): ").lower()
    success = success_choice != "n"

    manager.complete_execution(execution_id, success=success)

    if success and config.auto_merge:
        print("   ✓ Merged to main (auto)")
    else:
        print("   ✓ Execution completed (branch kept)")
        print(f"   To merge: paracle git merge {info['branch_name']}")

    # Cleanup test file
    test_file.unlink(missing_ok=True)

    print("\n✓ ExecutionManager example complete")


# =============================================================================
# EXAMPLE 3: Integration with Agent Execution
# =============================================================================


async def example_agent_integration():
    """Example: Git workflows with agent execution."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Git Workflows + Agent Execution")
    print("=" * 60)

    # Configure for agent executions
    config = ExecutionConfig(
        enable_branching=True,
        auto_commit=True,
        auto_merge=True,  # Auto-merge on success
        auto_cleanup=True,  # Auto-cleanup merged branches
        base_branch="main",
    )

    git_manager = ExecutionManager(config=config, repo_path=".")

    # Simulate agent execution
    execution_id = "agent-demo-001"
    print(f"\n1. Starting agent execution: {execution_id}")

    try:
        # Start execution (creates branch)
        info = git_manager.start_execution(execution_id)
        print(f"   ✓ Branch: {info['branch_name']}")

        # Simulate agent work
        print("\n2. Agent working...")

        # Step 1: Agent analyzes code
        print("   - Analyzing code...")
        await asyncio.sleep(0.5)  # Simulate work
        git_manager.commit_changes(
            execution_id=execution_id,
            message="refactor: Analyze codebase structure",
            files=[],  # No files for this step
        )
        print("   ✓ Analysis complete")

        # Step 2: Agent implements changes
        print("   - Implementing changes...")
        await asyncio.sleep(0.5)

        # Create a demo file
        demo_file = Path("agent_output.txt")
        demo_file.write_text("Agent implementation:\n- Feature X\n")

        git_manager.commit_changes(
            execution_id=execution_id,
            message="feat: Implement feature X",
            files=["agent_output.txt"],
        )
        print("   ✓ Implementation complete")

        # Step 3: Agent runs tests
        print("   - Running tests...")
        await asyncio.sleep(0.5)

        demo_file.write_text(demo_file.read_text() + "- Tests: PASSED\n")

        git_manager.commit_changes(
            execution_id=execution_id,
            message="test: Add tests for feature X",
            files=["agent_output.txt"],
        )
        print("   ✓ Tests passed")

        # Complete successfully
        print("\n3. Completing execution: SUCCESS")
        git_manager.complete_execution(execution_id, success=True)
        print("   ✓ Merged to main")
        print("   ✓ Branch cleaned up")

        # Cleanup demo file
        demo_file.unlink(missing_ok=True)

    except Exception as e:
        # Failed execution
        print(f"\n3. Execution FAILED: {e}")
        git_manager.complete_execution(execution_id, success=False)
        print("   ✓ Branch kept for debugging")
        print(f"   Debug: git checkout {info['branch_name']}")

    print("\n✓ Agent integration example complete")


# =============================================================================
# EXAMPLE 4: Cleanup and Maintenance
# =============================================================================


def example_cleanup():
    """Example: Cleanup old and merged branches."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Cleanup and Maintenance")
    print("=" * 60)

    manager = BranchManager(Path("."))

    # List all execution branches
    print("\n1. Listing all execution branches...")
    branches = manager.list_execution_branches()
    print(f"   Found {len(branches)} execution branches")

    if branches:
        print("\n   Recent branches:")
        for branch in branches[:5]:
            print(f"   - {branch.name} ({branch.created_at})")

    # Cleanup merged branches
    print("\n2. Cleaning up merged branches...")
    cleanup_choice = input("   Proceed with cleanup? (y/N): ").lower()

    if cleanup_choice == "y":
        count = manager.cleanup_merged_branches(target_branch="main")
        print(f"   ✓ Cleaned up {count} merged branches")
    else:
        print("   Skipped cleanup")

    # Show remaining branches
    remaining = manager.list_execution_branches()
    print(f"\n3. Remaining execution branches: {len(remaining)}")

    if remaining:
        print("\n   To cleanup manually:")
        print("   - Merged: paracle git cleanup --target main")
        print("   - All: git branch -D exec/*")

    print("\n✓ Cleanup example complete")


# =============================================================================
# MAIN
# =============================================================================


async def main():
    """Run all git workflow examples."""
    print("\n" + "=" * 60)
    print("GIT WORKFLOW MANAGEMENT EXAMPLES")
    print("=" * 60)

    # Check git repository
    if not Path(".git").exists():
        print("\n⚠ Not a git repository!")
        print("Initialize with: git init")
        return

    try:
        # Example 1: BranchManager (low-level)
        example_branch_manager()

        # Example 2: ExecutionManager (high-level)
        await example_execution_manager()

        # Example 3: Agent integration
        await example_agent_integration()

        # Example 4: Cleanup
        example_cleanup()

        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Use with agents: See example_agent_integration()")
        print("2. Configure auto-merge: ExecutionConfig(auto_merge=True)")
        print("3. Cleanup old branches: paracle git cleanup")
        print("4. Create PRs: paracle git pr-create <exec_id> 'Title'")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
