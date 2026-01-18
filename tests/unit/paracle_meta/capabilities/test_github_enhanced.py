"""Unit tests for GitHubEnhancedCapability."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from paracle_meta.capabilities.github_enhanced import (
    GitHubEnhancedCapability,
    GitHubEnhancedConfig,
    PRStatus,
    ReviewStatus,
)


@pytest.fixture
def github_enhanced():
    """Create GitHubEnhancedCapability instance with mock client."""
    config = GitHubEnhancedConfig(
        token="test-token",
        enable_auto_review=True,
    )
    capability = GitHubEnhancedCapability(config)

    # Mock GitHub client
    capability._client = MagicMock()

    return capability


@pytest.mark.asyncio
async def test_github_enhanced_initialization(github_enhanced):
    """Test GitHubEnhancedCapability initialization."""
    assert github_enhanced.name == "github_enhanced"
    assert github_enhanced.config.enable_auto_review is True


@pytest.mark.asyncio
async def test_add_repository(github_enhanced):
    """Test adding a repository to track."""
    result = await github_enhanced.add_repository(
        owner="test-owner",
        name="test-repo",
        url="https://github.com/test-owner/test-repo",
    )

    assert result.success is True
    assert result.output["owner"] == "test-owner"
    assert result.output["name"] == "test-repo"


@pytest.mark.asyncio
async def test_review_pr(github_enhanced):
    """Test AI-powered PR review."""
    # Mock PR data
    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={
            "number": 123,
            "title": "Add new feature",
            "diff": "+def new_function():\n+    return True",
            "files_changed": 1,
        }
    )

    result = await github_enhanced.review_pr(
        repo="test-owner/test-repo", pr_number=123, auto_comment=False
    )

    assert result.success is True
    assert "quality_score" in result.output
    assert "issues" in result.output
    assert result.output["pr_number"] == 123


@pytest.mark.asyncio
async def test_review_pr_with_auto_comment(github_enhanced):
    """Test PR review with automatic comments."""
    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={
            "number": 123,
            "title": "Fix bug",
            "diff": "-    buggy_code()\n+    fixed_code()",
            "files_changed": 1,
        }
    )

    github_enhanced._client.add_pr_comment = AsyncMock()

    result = await github_enhanced.review_pr(
        repo="test-owner/test-repo", pr_number=123, auto_comment=True
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_review_identifies_security_issues(github_enhanced):
    """Test that review identifies security issues."""
    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={
            "number": 123,
            "title": "Add authentication",
            "diff": '+password = "hardcoded_password"\n+execute_sql(f"SELECT * FROM users WHERE id={user_id}")',
            "files_changed": 1,
        }
    )

    result = await github_enhanced.review_pr(repo="test-owner/test-repo", pr_number=123)

    assert result.success is True
    # Should detect security issues
    assert "security" in result.output
    security_issues = result.output["security"]
    assert len(security_issues) > 0


@pytest.mark.asyncio
async def test_review_checks_performance(github_enhanced):
    """Test that review includes performance analysis."""
    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={
            "number": 123,
            "title": "Optimize loop",
            "diff": "+for i in range(1000000):\n+    slow_operation()",
            "files_changed": 1,
        }
    )

    result = await github_enhanced.review_pr(repo="test-owner/test-repo", pr_number=123)

    assert result.success is True
    assert "performance" in result.output


@pytest.mark.asyncio
async def test_review_checks_style(github_enhanced):
    """Test that review includes style analysis."""
    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={
            "number": 123,
            "title": "Add function",
            "diff": "+def badlyNamed():\n+  return x",  # Bad style
            "files_changed": 1,
        }
    )

    result = await github_enhanced.review_pr(repo="test-owner/test-repo", pr_number=123)

    assert result.success is True
    assert "style" in result.output


@pytest.mark.asyncio
async def test_sync_repos(github_enhanced):
    """Test syncing files across repositories."""
    # Add repositories
    await github_enhanced.add_repository(
        owner="org", name="repo1", url="https://github.com/org/repo1"
    )
    await github_enhanced.add_repository(
        owner="org", name="repo2", url="https://github.com/org/repo2"
    )

    github_enhanced._client.get_file_content = AsyncMock(return_value="File content")
    github_enhanced._client.create_or_update_file = AsyncMock()

    result = await github_enhanced.sync_repos(
        source="org/repo1", targets=["org/repo2"], files=["README.md"]
    )

    assert result.success is True
    assert "synced_count" in result.output


@pytest.mark.asyncio
async def test_create_pr(github_enhanced):
    """Test creating a pull request."""
    github_enhanced._client.create_pull_request = AsyncMock(
        return_value={"number": 456, "url": "https://github.com/..."}
    )

    result = await github_enhanced.create_pr(
        repo="test-owner/test-repo",
        title="New feature",
        body="Description",
        head="feature-branch",
        base="main",
    )

    assert result.success is True
    assert result.output["pr_number"] == 456


@pytest.mark.asyncio
async def test_merge_pr(github_enhanced):
    """Test merging a pull request."""
    github_enhanced._client.merge_pull_request = AsyncMock()

    result = await github_enhanced.merge_pr(
        repo="test-owner/test-repo", pr_number=123, merge_method="squash"
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_list_prs(github_enhanced):
    """Test listing pull requests."""
    github_enhanced._client.list_pull_requests = AsyncMock(
        return_value=[
            {"number": 1, "title": "PR 1", "state": "open"},
            {"number": 2, "title": "PR 2", "state": "open"},
        ]
    )

    result = await github_enhanced.list_prs(repo="test-owner/test-repo", state="open")

    assert result.success is True
    assert len(result.output["pull_requests"]) == 2


@pytest.mark.asyncio
async def test_get_pr_status(github_enhanced):
    """Test getting PR status."""
    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={
            "number": 123,
            "state": "open",
            "mergeable": True,
            "checks": [{"name": "CI", "status": "success"}],
        }
    )

    result = await github_enhanced.get_pr_status(
        repo="test-owner/test-repo", pr_number=123
    )

    assert result.success is True
    assert result.output["pr_number"] == 123
    assert "mergeable" in result.output


@pytest.mark.asyncio
async def test_auto_approve_pr(github_enhanced):
    """Test auto-approving a PR based on criteria."""
    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={
            "number": 123,
            "diff": "+# Minor fix",
            "files_changed": 1,
        }
    )

    github_enhanced._client.approve_pull_request = AsyncMock()

    result = await github_enhanced.auto_approve_pr(
        repo="test-owner/test-repo",
        pr_number=123,
        criteria={"max_files_changed": 5, "min_quality_score": 80},
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_check_ci_status(github_enhanced):
    """Test checking CI status."""
    github_enhanced._client.get_checks = AsyncMock(
        return_value=[
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "completed", "conclusion": "success"},
        ]
    )

    result = await github_enhanced.check_ci_status(
        repo="test-owner/test-repo", pr_number=123
    )

    assert result.success is True
    assert "checks" in result.output
    assert result.output["all_passed"] is True


@pytest.mark.asyncio
async def test_get_repository_stats(github_enhanced):
    """Test getting repository statistics."""
    await github_enhanced.add_repository(
        owner="org", name="repo", url="https://github.com/org/repo"
    )

    github_enhanced._client.get_repository = AsyncMock(
        return_value={
            "stars": 100,
            "forks": 20,
            "open_issues": 5,
        }
    )

    result = await github_enhanced.get_repository_stats(repo="org/repo")

    assert result.success is True
    assert "stars" in result.output


@pytest.mark.asyncio
async def test_create_issue(github_enhanced):
    """Test creating an issue."""
    github_enhanced._client.create_issue = AsyncMock(return_value={"number": 789})

    result = await github_enhanced.create_issue(
        repo="test-owner/test-repo",
        title="Bug report",
        body="Description of the bug",
        labels=["bug"],
    )

    assert result.success is True
    assert result.output["issue_number"] == 789


@pytest.mark.asyncio
async def test_close_stale_prs(github_enhanced):
    """Test closing stale PRs."""
    github_enhanced._client.list_pull_requests = AsyncMock(
        return_value=[
            {"number": 1, "updated_at": "2020-01-01T00:00:00Z"},
            {"number": 2, "updated_at": "2023-12-01T00:00:00Z"},
        ]
    )

    github_enhanced._client.close_pull_request = AsyncMock()

    result = await github_enhanced.close_stale_prs(
        repo="test-owner/test-repo", days_threshold=365
    )

    assert result.success is True
    assert "closed_count" in result.output


@pytest.mark.asyncio
async def test_get_review_stats(github_enhanced):
    """Test getting review statistics."""
    # Review a few PRs
    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={
            "number": 123,
            "diff": "+code",
            "files_changed": 1,
        }
    )

    await github_enhanced.review_pr(repo="test-owner/test-repo", pr_number=123)

    result = await github_enhanced.get_review_stats()

    assert result.success is True
    assert "total_reviews" in result.output


@pytest.mark.asyncio
async def test_batch_review_prs(github_enhanced):
    """Test reviewing multiple PRs in batch."""
    github_enhanced._client.list_pull_requests = AsyncMock(
        return_value=[{"number": 1}, {"number": 2}, {"number": 3}]
    )

    github_enhanced._client.get_pull_request = AsyncMock(
        return_value={"diff": "+code", "files_changed": 1}
    )

    result = await github_enhanced.batch_review(
        repo="test-owner/test-repo", pr_numbers=[1, 2, 3]
    )

    assert result.success is True
    assert len(result.output["reviews"]) == 3


@pytest.mark.asyncio
async def test_compare_branches(github_enhanced):
    """Test comparing two branches."""
    github_enhanced._client.compare_branches = AsyncMock(
        return_value={"ahead_by": 5, "behind_by": 2, "commits": []}
    )

    result = await github_enhanced.compare_branches(
        repo="test-owner/test-repo", base="main", head="develop"
    )

    assert result.success is True
    assert "ahead_by" in result.output


@pytest.mark.asyncio
async def test_list_tracked_repositories(github_enhanced):
    """Test listing all tracked repositories."""
    await github_enhanced.add_repository(
        owner="org", name="repo1", url="https://github.com/org/repo1"
    )
    await github_enhanced.add_repository(
        owner="org", name="repo2", url="https://github.com/org/repo2"
    )

    result = await github_enhanced.list_repositories()

    assert result.success is True
    assert len(result.output["repositories"]) == 2


@pytest.mark.asyncio
async def test_remove_repository(github_enhanced):
    """Test removing a tracked repository."""
    await github_enhanced.add_repository(
        owner="org", name="repo", url="https://github.com/org/repo"
    )

    result = await github_enhanced.remove_repository(repo="org/repo")
    assert result.success is True

    # Verify removal
    list_result = await github_enhanced.list_repositories()
    assert len(list_result.output["repositories"]) == 0
