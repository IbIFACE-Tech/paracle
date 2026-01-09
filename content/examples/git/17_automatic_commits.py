"""Example: Automatic Git Commits for Agent Changes.

This example demonstrates how to use automatic commit functionality
when agents make changes to the codebase.
"""

from pathlib import Path

from paracle_git import AutoCommitManager, CommitConfig, CommitType


def main():
    """Run the automatic commit example."""
    print("=== Paracle Automatic Commits Example ===\n")

    # 1. Configure automatic commits
    print("1. Configuring automatic commits...")
    config = CommitConfig(
        enabled=True,
        require_approval=False,  # Auto-commit without approval
        conventional_commits=True,
        sign_commits=False,
        prefix_agent_name=True,
        include_metadata=True,
    )
    print(
        f"   [OK] Config: approval={config.require_approval}, conventional={config.conventional_commits}\n"
    )

    # 2. Initialize manager
    print("2. Initializing AutoCommitManager...")
    repo_path = Path(".")
    manager = AutoCommitManager(repo_path, config=config)

    if not manager.is_git_repo():
        print("   [WARNING] Not a git repository - commits will not be created\n")
        print("   To test this example in a real repo:")
        print("   1. git init")
        print("   2. Make some file changes")
        print("   3. Run this example again\n")
        return

    print(f"   [OK] Repository: {repo_path.absolute()}\n")

    # 3. Check for changes
    print("3. Detecting changes...")
    changes = manager.get_changed_files()

    if not changes:
        print("   [INFO] No changes detected\n")
        print("   To see this in action:")
        print("   1. Make some file changes")
        print("   2. Run this example again\n")
        return

    print(f"   [OK] Found {len(changes)} changed file(s):")
    for change in changes:
        print(f"      - {change.file_path} ({change.change_type})")
    print()

    # 4. Create automatic commit
    print("4. Creating automatic commit...")
    success = manager.commit_agent_changes(
        agent_name="coder_agent",
        changes=changes,
        commit_type=CommitType.FEAT,
        description="Implement automatic git commits",
        scope="git",
        body="Added AutoCommitManager for tracking and committing agent changes",
    )

    if success:
        print("   [OK] Commit created successfully\n")
    else:
        print("   [ERROR] Failed to create commit\n")
        return

    # 5. Show recent commits
    print("5. Recent commit history:")
    commits = manager.get_commit_history(limit=5)
    for commit in commits:
        print(f"   {commit}")
    print()

    # 6. Example with different commit types
    print("6. Example commit messages (not executed):\n")

    examples = [
        (CommitType.FEAT, "agent", "Add new agent skill for code review", None),
        (CommitType.FIX, "api", "Fix authentication timeout issue", None),
        (CommitType.DOCS, "readme", "Update installation instructions", None),
        (CommitType.REFACTOR, "core", "Restructure agent inheritance", None),
        (CommitType.TEST, "agent", "Add unit tests for agent factory", None),
    ]

    for commit_type, scope, description, body in examples:
        from paracle_git.conventional import create_commit_message

        msg = create_commit_message(
            type=commit_type,
            scope=scope,
            description=description,
            body=body,
        )
        first_line = msg.split("\n")[0]
        print(f"   {first_line}")

    print("\n=== CLI Usage Examples ===\n")
    print("# Show current status")
    print("paracle git status\n")

    print("# Configure auto-commit")
    print("paracle git config --enable --approval --conventional\n")

    print("# Create a commit")
    print(
        "paracle git commit 'Implement feature X' --type feat --scope api --agent coder\n"
    )

    print("# Show commit history")
    print("paracle git log --limit 10\n")

    print("=== Integration with Agents ===\n")
    print("You can integrate auto-commit into agent workflows:")
    print("1. Agent makes file changes")
    print("2. AutoCommitManager detects changes")
    print("3. Creates conventional commit with agent metadata")
    print("4. Commit includes agent name, timestamp, and file list")
    print("\nThis provides full traceability of agent actions!")


if __name__ == "__main__":
    main()
