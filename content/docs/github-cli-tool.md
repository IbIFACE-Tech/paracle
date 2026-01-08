# GitHub CLI Tool for ReleaseManager Agent

## Overview

The GitHub CLI tool provides comprehensive integration with GitHub's CLI (`gh`) for the ReleaseManager agent, enabling automated PR management, release creation, workflow execution, and more.

## Installation

**GitHub CLI is required:**
- **Windows**: `winget install --id GitHub.cli`
- **macOS**: `brew install gh`
- **Linux**: See https://cli.github.com/

**Authentication:**
```bash
gh auth login
```

## Tool Location

- **Implementation**: `packages/paracle_tools/release_tools.py` (GitHubCLITool class)
- **Test Script**: `examples/tools/test_github_cli.py`
- **Documentation**: `.parac/agents/skills/release-automation/SKILL.md`
- **Quick Reference**: `content/docs/github-cli-quickref.md`

## Supported Operations

### Pull Request Operations

| Action      | Description        | Parameters                                                 |
| ----------- | ------------------ | ---------------------------------------------------------- |
| `pr_list`   | List pull requests | `state`, `limit`                                           |
| `pr_create` | Create new PR      | `title`, `body`, `base`, `head`, `draft`                   |
| `pr_view`   | View PR details    | `pr_number`                                                |
| `pr_merge`  | Merge a PR         | `pr_number`, `merge_method`, `delete_branch`, `auto_merge` |
| `pr_review` | Review a PR        | `pr_number`, `approve`, `request_changes`, `comment`       |
| `pr_checks` | Check PR status    | `pr_number`                                                |
| `pr_diff`   | Show PR diff       | `pr_number`                                                |

### Release Operations

| Action           | Description          | Parameters                                                       |
| ---------------- | -------------------- | ---------------------------------------------------------------- |
| `release_list`   | List releases        | `limit`                                                          |
| `release_create` | Create new release   | `tag`, `title`, `notes`, `draft`, `prerelease`, `generate_notes` |
| `release_view`   | View release details | `tag`                                                            |
| `release_delete` | Delete a release     | `tag`                                                            |

### Workflow Operations

| Action          | Description                   | Parameters |
| --------------- | ----------------------------- | ---------- |
| `workflow_list` | List GitHub Actions workflows | -          |
| `workflow_run`  | Trigger workflow run          | `workflow` |

### Repository Operations

| Action      | Description          | Parameters |
| ----------- | -------------------- | ---------- |
| `repo_view` | View repository info | -          |

### Issue Operations

| Action         | Description      | Parameters       |
| -------------- | ---------------- | ---------------- |
| `issue_list`   | List issues      | `state`, `limit` |
| `issue_create` | Create new issue | `title`, `body`  |

## Usage Examples

### Python API

```python
from paracle_tools.release_tools import github_cli

# List open pull requests
result = await github_cli.execute(
    action="pr_list",
    state="open",
    limit=10
)

# Create a pull request
result = await github_cli.execute(
    action="pr_create",
    title="feat: Add new feature",
    body="Detailed description...",
    base="main",
    head="feature-branch",
    draft=False
)

# Create a release
result = await github_cli.execute(
    action="release_create",
    tag="v1.0.0",
    title="Release v1.0.0",
    notes="Release notes...",
    prerelease=False,
    generate_notes=True
)

# Merge a PR
result = await github_cli.execute(
    action="pr_merge",
    pr_number=42,
    merge_method="squash",
    delete_branch=True
)
```

### Command Line (via test script)

```bash
# Run all tests
uv run python examples/tools/test_github_cli.py

# Tests include:
# 1. Check GitHub CLI installation
# 2. List open pull requests
# 3. List releases
# 4. List workflows
```

## Return Format

All operations return a `ToolResult` object with:

```python
class ToolResult:
    success: bool          # Whether operation succeeded
    output: dict          # Operation output
    error: str | None     # Error message if failed
    metadata: dict        # Additional metadata

# Output dict contains:
{
    "action": str,        # Action that was performed
    "command": str,       # gh CLI command that was executed
    "stdout": str,        # Command output
    "stderr": str,        # Error output
    "returncode": int,    # Command exit code
    "success": bool       # Whether command succeeded
}
```

## Error Handling

The tool handles several error conditions:

1. **GitHub CLI not installed**: Returns error with installation instructions
2. **Authentication required**: Command fails with auth prompt
3. **Repository not found**: Returns GraphQL error
4. **Invalid parameters**: Returns validation error
5. **Command execution errors**: Captured in stderr

## Integration with ReleaseManager Agent

The GitHub CLI tool is automatically available to the ReleaseManager agent:

```python
# In agent code
from paracle_tools.release_tools import github_cli

# Agent can use all GitHub CLI operations
result = await github_cli.execute(action="pr_list")
```

## Testing

Run the test suite to verify installation and functionality:

```bash
uv run python examples/tools/test_github_cli.py
```

**Expected Output:**
```
============================================================
Testing GitHub CLI Tool
============================================================

1. Checking GitHub CLI installation...
✅ GitHub CLI is installed

2. Listing open pull requests...
✅ Pull requests listed
  (or: No open pull requests)

3. Listing releases...
✅ Releases listed
  v1.0.0  Release v1.0.0  Latest  Jan 8, 2026

4. Listing GitHub Actions workflows...
✅ Workflows listed
  ci.yml  Active  12345
```

## Common Use Cases

### 1. Automated Release Workflow

```python
# 1. Create release tag
await github_cli.execute(
    action="release_create",
    tag="v1.0.0",
    title="Release v1.0.0",
    generate_notes=True
)

# 2. List to verify
result = await github_cli.execute(action="release_list", limit=1)
```

### 2. PR Review Workflow

```python
# 1. List open PRs
prs = await github_cli.execute(action="pr_list", state="open")

# 2. Check PR status
checks = await github_cli.execute(action="pr_checks", pr_number=42)

# 3. Review and approve
await github_cli.execute(
    action="pr_review",
    pr_number=42,
    approve=True,
    comment="LGTM! ✅"
)

# 4. Merge if approved
await github_cli.execute(
    action="pr_merge",
    pr_number=42,
    merge_method="squash"
)
```

### 3. Workflow Automation

```python
# 1. List workflows
workflows = await github_cli.execute(action="workflow_list")

# 2. Trigger deployment
await github_cli.execute(
    action="workflow_run",
    workflow="deploy.yml"
)
```

## Skill Integration

The GitHub CLI capabilities are documented in the release-automation skill:

**Path**: `.parac/agents/skills/release-automation/SKILL.md`

**Key sections:**
- GitHub CLI Operations (section 6)
- PR Management
- Release Creation
- Workflow Execution
- Issue Management

## Future Enhancements

Potential improvements:

1. **Batch Operations**: Support multiple PRs/releases in one call
2. **Advanced Filtering**: More sophisticated PR/issue queries
3. **Label Management**: Add/remove labels on PRs/issues
4. **Milestone Management**: Associate PRs with milestones
5. **Project Board Integration**: Move cards across project boards
6. **Status Checks**: Detailed CI/CD status reporting
7. **Deployment Tracking**: Monitor deployment status

## Troubleshooting

### GitHub CLI not found
**Problem**: `gh: command not found`
**Solution**: Install GitHub CLI (see Installation section)

### Authentication required
**Problem**: `gh auth login` required
**Solution**: Run `gh auth login` and follow prompts

### Repository not found
**Problem**: GraphQL error about repository not existing
**Solution**:
- Ensure you're in the correct repository directory
- Check repository name/owner in GitHub
- Verify authentication permissions

### Permission denied
**Problem**: `403 Forbidden` or permission errors
**Solution**: Check your GitHub token has required scopes:
- `repo` for private repositories
- `workflow` for GitHub Actions
- `admin:org` for organization operations

## See Also

- [Release Automation Skill](.parac/agents/skills/release-automation/SKILL.md)
- [GitHub CLI Quick Reference](github-cli-quickref.md)
- [ReleaseManager Agent Spec](.parac/agents/specs/releasemanager.md)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

---

**Created**: January 8, 2026
**Author**: CoderAgent
**Status**: Production Ready ✅
