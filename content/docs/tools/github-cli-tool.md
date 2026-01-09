# GitHub CLI Tool - Quick Reference

**Tool**: `github_cli` (ReleaseManager Agent)

**Description**: Comprehensive GitHub CLI integration for PR, release, workflow, and repository management.

## Prerequisites

```bash
# Install GitHub CLI
winget install --id GitHub.cli  # Windows
brew install gh                 # macOS

# Authenticate
gh auth login
```

## Pull Request Operations

### List PRs

```python
from paracle_tools.release_tools import github_cli

# List open PRs
result = await github_cli.execute(action="pr_list", state="open", limit=10)

# List all PRs (open, closed, merged)
result = await github_cli.execute(action="pr_list", state="all", limit=30)
```

### Create PR

```python
result = await github_cli.execute(
    action="pr_create",
    title="feat: Add new feature X",
    body="This PR implements feature X with improvements Y and Z",
    base="main",
    head="feature/new-feature",
    draft=False
)
```

### View PR Details

```python
result = await github_cli.execute(action="pr_view", pr_number=123)
```

### Review PR

```python
# Approve PR
result = await github_cli.execute(
    action="pr_review",
    pr_number=123,
    approve=True,
    comment="LGTM! 🚀"
)

# Request changes
result = await github_cli.execute(
    action="pr_review",
    pr_number=123,
    request_changes=True,
    comment="Please address the following issues..."
)
```

### Check PR Status

```python
# View CI checks status
result = await github_cli.execute(action="pr_checks", pr_number=123)
```

### View PR Diff

```python
result = await github_cli.execute(action="pr_diff", pr_number=123)
```

### Merge PR

```python
# Merge with merge commit
result = await github_cli.execute(
    action="pr_merge",
    pr_number=123,
    merge_method="merge",
    delete_branch=True
)

# Squash and merge
result = await github_cli.execute(
    action="pr_merge",
    pr_number=123,
    merge_method="squash",
    delete_branch=True
)

# Rebase and merge
result = await github_cli.execute(
    action="pr_merge",
    pr_number=123,
    merge_method="rebase",
    delete_branch=True
)

# Auto-merge when checks pass
result = await github_cli.execute(
    action="pr_merge",
    pr_number=123,
    auto_merge=True,
    merge_method="squash"
)
```

## Release Operations

### List Releases

```python
result = await github_cli.execute(action="release_list", limit=10)
```

### Create Release

```python
# Create release with auto-generated notes
result = await github_cli.execute(
    action="release_create",
    tag="v1.0.0",
    title="Production Release v1.0.0",
    generate_notes=True
)

# Create release with custom notes
result = await github_cli.execute(
    action="release_create",
    tag="v1.0.0",
    title="Production Release v1.0.0",
    notes="""
    ## What's New
    - Phase 7 Observability complete
    - Phase 8 Error Management
    - Phase 10 Security Audit (100/100)

    ## Breaking Changes
    None

    ## Bug Fixes
    - Fixed authentication issue
    """,
    generate_notes=False
)

# Create draft release
result = await github_cli.execute(
    action="release_create",
    tag="v1.0.0",
    title="Draft v1.0.0",
    draft=True
)

# Create pre-release
result = await github_cli.execute(
    action="release_create",
    tag="v0.2.0-beta.1",
    title="Beta Release v0.2.0-beta.1",
    prerelease=True,
    generate_notes=True
)
```

### View Release

```python
result = await github_cli.execute(action="release_view", tag="v1.0.0")
```

### Delete Release

```python
result = await github_cli.execute(action="release_delete", tag="v0.1.0-alpha.1")
```

## Workflow Operations

### List Workflows

```python
result = await github_cli.execute(action="workflow_list")
```

### Trigger Workflow

```python
result = await github_cli.execute(action="workflow_run", workflow="CI Pipeline")
```

## Repository Operations

### View Repository Info

```python
result = await github_cli.execute(action="repo_view")
```

## Issue Operations

### List Issues

```python
# List open issues
result = await github_cli.execute(action="issue_list", state="open", limit=10)

# List all issues
result = await github_cli.execute(action="issue_list", state="all", limit=50)
```

### Create Issue

```python
result = await github_cli.execute(
    action="issue_create",
    title="Bug: Authentication fails",
    body="Description of the bug and steps to reproduce..."
)
```

## Return Format

All operations return a dictionary with:

```python
{
    "action": "pr_list",           # Action performed
    "command": "gh pr list...",    # Actual gh command executed
    "stdout": "...",               # Command output
    "stderr": "...",               # Error output (if any)
    "returncode": 0,               # Exit code
    "success": True                # True if returncode == 0
}
```

On error:

```python
{
    "error": "Error message",
    "action": "pr_create"
}
```

## Complete Release Workflow Example

```python
from paracle_tools.release_tools import github_cli
import asyncio

async def release_workflow():
    # 1. Create PR from develop to main
    print("Creating release PR...")
    pr_result = await github_cli.execute(
        action="pr_create",
        title="Release v1.0.0",
        body="Production release v1.0.0 with all features complete.",
        base="main",
        head="release/v1.0.0"
    )

    if not pr_result.get("success"):
        print(f"Error creating PR: {pr_result.get('stderr')}")
        return

    # Extract PR number from output
    pr_number = 123  # Parse from pr_result['stdout']

    # 2. Check PR status
    print("Checking PR status...")
    checks_result = await github_cli.execute(action="pr_checks", pr_number=pr_number)
    print(checks_result['stdout'])

    # 3. Wait for reviews (manual step)
    input("Press Enter after PR is reviewed...")

    # 4. Merge PR
    print("Merging PR...")
    merge_result = await github_cli.execute(
        action="pr_merge",
        pr_number=pr_number,
        merge_method="squash",
        delete_branch=True
    )

    if not merge_result.get("success"):
        print(f"Error merging PR: {merge_result.get('stderr')}")
        return

    # 5. Create GitHub release
    print("Creating GitHub release...")
    release_result = await github_cli.execute(
        action="release_create",
        tag="v1.0.0",
        title="Production Release v1.0.0",
        generate_notes=True
    )

    if release_result.get("success"):
        print("✅ Release v1.0.0 created successfully!")
        print(release_result['stdout'])
    else:
        print(f"Error creating release: {release_result.get('stderr')}")

# Run workflow
asyncio.run(release_workflow())
```

## Best Practices

1. **Always check return status**:
   ```python
   if result.get("success"):
       # Handle success
   else:
       # Handle error
       print(result.get("stderr"))
   ```

2. **Use auto-generated release notes** when possible:
   ```python
   result = await github_cli.execute(
       action="release_create",
       tag="v1.0.0",
       generate_notes=True  # Auto-generates from PRs
   )
   ```

3. **Check PR status before merging**:
   ```python
   checks = await github_cli.execute(action="pr_checks", pr_number=123)
   # Verify all checks pass before merging
   ```

4. **Use draft PRs** for work-in-progress:
   ```python
   result = await github_cli.execute(
       action="pr_create",
       title="WIP: Feature X",
       draft=True  # Marks as draft
   )
   ```

5. **Delete branches after merge** to keep repo clean:
   ```python
   result = await github_cli.execute(
       action="pr_merge",
       pr_number=123,
       delete_branch=True  # Auto-delete after merge
   )
   ```

## See Also

- [Release Automation Skill](../.parac/agents/skills/release-automation/SKILL.md)
- [ReleaseManager Agent Spec](../.parac/agents/specs/releasemanager.md)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

## Notes

- GitHub CLI (`gh`) must be installed and authenticated
- Repository must be hosted on GitHub (not GitLab/Bitbucket)
- Some operations require specific permissions (e.g., merge requires write access)
- Rate limits apply based on GitHub API limits
