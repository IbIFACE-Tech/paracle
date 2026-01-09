"""Test GitHub CLI tool for ReleaseManager agent.

This script demonstrates the new GitHub CLI integration capabilities.

Usage:
    python examples/tools/test_github_cli.py
"""

import asyncio
import sys
from pathlib import Path

from paracle_tools.release_tools import github_cli

# Add packages to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "packages"))


async def test_github_cli():
    """Test GitHub CLI operations."""
    print("=" * 60)
    print("Testing GitHub CLI Tool")
    print("=" * 60)

    # Test 1: Check if gh CLI is installed
    print("\n1. Checking GitHub CLI installation...")
    result = await github_cli.execute(action="repo_view")

    if not result.success or (result.output and "error" in result.output):
        error_msg = result.error or result.output.get("error", "Unknown")
        print(f"❌ Error: {error_msg}")
        print("\nPlease install GitHub CLI:")
        print("  Windows: winget install --id GitHub.cli")
        print("  macOS: brew install gh")
        print("  Linux: See https://cli.github.com/")
        print("\nThen authenticate with: gh auth login")
        return

    print("✅ GitHub CLI is installed")
    if result.output and result.output.get("stdout"):
        stdout = result.output["stdout"][:500]
        print(f"\nRepository Info:\n{stdout}")

    # Test 2: List open pull requests
    print("\n2. Listing open pull requests...")
    pr_result = await github_cli.execute(action="pr_list", state="open", limit=5)

    pr_success = (
        pr_result.success and pr_result.output and pr_result.output.get("success")
    )
    if pr_success:
        print("✅ Pull requests listed")
        if pr_result.output.get("stdout"):
            print(f"\n{pr_result.output['stdout']}")
        else:
            print("  No open pull requests")
    else:
        stderr = pr_result.output.get("stderr", "") if pr_result.output else ""
        error = stderr or pr_result.error or "Unknown error"
        print(f"⚠️  Could not list PRs: {error}")

    # Test 3: List releases
    print("\n3. Listing releases...")
    release_result = await github_cli.execute(action="release_list", limit=5)

    release_success = (
        release_result.success
        and release_result.output
        and release_result.output.get("success")
    )
    if release_success:
        print("✅ Releases listed")
        if release_result.output.get("stdout"):
            print(f"\n{release_result.output['stdout']}")
        else:
            print("  No releases found")
    else:
        stderr = (
            release_result.output.get("stderr", "") if release_result.output else ""
        )
        error = stderr or release_result.error or "Unknown error"
        print(f"⚠️  Could not list releases: {error}")

    # Test 4: List workflows
    print("\n4. Listing GitHub Actions workflows...")
    workflow_result = await github_cli.execute(action="workflow_list")

    workflow_success = (
        workflow_result.success
        and workflow_result.output
        and workflow_result.output.get("success")
    )
    if workflow_success:
        print("✅ Workflows listed")
        if workflow_result.output.get("stdout"):
            print(f"\n{workflow_result.output['stdout']}")
        else:
            print("  No workflows found")
    else:
        stderr = (
            workflow_result.output.get("stderr", "") if workflow_result.output else ""
        )
        error = stderr or workflow_result.error or "Unknown error"
        print(f"⚠️  Could not list workflows: {error}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nAvailable GitHub CLI actions:")
    print("  PR Operations:")
    print("    - pr_list, pr_create, pr_view, pr_merge, pr_review")
    print("    - pr_checks, pr_diff")
    print("  Release Operations:")
    print("    - release_list, release_create, release_view, release_delete")
    print("  Workflow Operations:")
    print("    - workflow_list, workflow_run")
    print("  Repository Operations:")
    print("    - repo_view")
    print("  Issue Operations:")
    print("    - issue_list, issue_create")
    print("\nFor full documentation, see:")
    print("  .parac/agents/skills/release-automation/SKILL.md")


if __name__ == "__main__":
    asyncio.run(test_github_cli())
