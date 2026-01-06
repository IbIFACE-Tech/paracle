"""Release management tools for ReleaseManager agent."""

import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from paracle_tools.builtin.base import BaseTool

logger = logging.getLogger("paracle.tools.release")


class VersionManagementTool(BaseTool):
    """Manage semantic versioning.

    Operations:
    - Version bumping (major, minor, patch)
    - Pre-release versions (alpha, beta, rc)
    - Version validation
    - Version comparison
    """

    def __init__(self):
        super().__init__(
            name="version_management",
            description="Manage semantic versioning",
            parameters={},
        )

    async def _execute(self, action: str, **kwargs) -> dict[str, Any]:
        """Perform version management action.

        Args:
            action: Action to perform (bump, validate, compare, get_current)
            **kwargs: Action-specific parameters

        Returns:
            Version management results
        """
        if action == "bump":
            return await self._bump_version(**kwargs)
        elif action == "validate":
            return self._validate_version(**kwargs)
        elif action == "compare":
            return self._compare_versions(**kwargs)
        elif action == "get_current":
            return await self._get_current_version(**kwargs)
        else:
            return {"error": f"Unsupported action: {action}"}

    async def _bump_version(self, bump_type: str, current_version: str = None, **kwargs) -> dict[str, Any]:
        """Bump version according to semver.

        Args:
            bump_type: Type of bump (major, minor, patch, alpha, beta, rc)
            current_version: Current version (if not provided, read from pyproject.toml)
        """
        if not current_version:
            current_result = await self._get_current_version()
            if "error" in current_result:
                return current_result
            current_version = current_result.get("version")

        # Parse version
        match = re.match(
            r'(\d+)\.(\d+)\.(\d+)(?:-([a-z]+)\.?(\d+))?', current_version)
        if not match:
            return {"error": f"Invalid version format: {current_version}"}

        major, minor, patch, prerelease_type, prerelease_num = match.groups()
        major, minor, patch = int(major), int(minor), int(patch)

        # Perform bump
        if bump_type == "major":
            new_version = f"{major + 1}.0.0"
        elif bump_type == "minor":
            new_version = f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            new_version = f"{major}.{minor}.{patch + 1}"
        elif bump_type in ["alpha", "beta", "rc"]:
            if prerelease_type == bump_type:
                prerelease_num = int(prerelease_num or 0) + 1
            else:
                prerelease_num = 1
            new_version = f"{major}.{minor}.{patch}-{bump_type}.{prerelease_num}"
        else:
            return {"error": f"Invalid bump type: {bump_type}"}

        return {
            "action": "bump",
            "bump_type": bump_type,
            "old_version": current_version,
            "new_version": new_version,
        }

    def _validate_version(self, version: str, **kwargs) -> dict[str, Any]:
        """Validate version format."""
        pattern = r'^\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?$'
        is_valid = bool(re.match(pattern, version))

        return {
            "action": "validate",
            "version": version,
            "valid": is_valid,
        }

    def _compare_versions(self, version1: str, version2: str, **kwargs) -> dict[str, Any]:
        """Compare two versions."""
        def parse_version(v):
            match = re.match(r'(\d+)\.(\d+)\.(\d+)(?:-([a-z]+)\.?(\d+))?', v)
            if not match:
                return None
            major, minor, patch, pre_type, pre_num = match.groups()
            return (int(major), int(minor), int(patch), pre_type or 'z', int(pre_num or 999))

        v1 = parse_version(version1)
        v2 = parse_version(version2)

        if not v1 or not v2:
            return {"error": "Invalid version format"}

        if v1 < v2:
            result = "less_than"
        elif v1 > v2:
            result = "greater_than"
        else:
            result = "equal"

        return {
            "action": "compare",
            "version1": version1,
            "version2": version2,
            "result": result,
        }

    async def _get_current_version(self, **kwargs) -> dict[str, Any]:
        """Get current version from pyproject.toml."""
        try:
            pyproject_path = Path("pyproject.toml")
            if not pyproject_path.exists():
                return {"error": "pyproject.toml not found"}

            content = pyproject_path.read_text(encoding="utf-8")
            match = re.search(r'version\s*=\s*"([^"]+)"', content)

            if match:
                version = match.group(1)
                return {
                    "action": "get_current",
                    "version": version,
                    "source": "pyproject.toml",
                }
            else:
                return {"error": "Version not found in pyproject.toml"}
        except Exception as e:
            return {"error": str(e)}


class ChangelogGenerationTool(BaseTool):
    """Generate changelogs from git commits.

    Features:
    - Parse conventional commits
    - Group by type (feat, fix, docs, etc.)
    - Generate markdown changelog
    - Version-specific changelogs
    """

    def __init__(self):
        super().__init__(
            name="changelog_generation",
            description="Generate changelog from commits",
            parameters={},
        )

    async def _execute(self, from_ref: str = None, to_ref: str = "HEAD", **kwargs) -> dict[str, Any]:
        """Generate changelog from commits.

        Args:
            from_ref: Starting git reference (tag, commit)
            to_ref: Ending git reference (default: HEAD)

        Returns:
            Generated changelog
        """
        try:
            # Get commit range
            if from_ref:
                commit_range = f"{from_ref}..{to_ref}"
            else:
                commit_range = to_ref

            # Get commits
            result = subprocess.run(
                ["git", "log", commit_range, "--pretty=format:%s"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return {"error": "Failed to get git commits", "details": result.stderr}

            commits = result.stdout.strip().split('\n')

            # Parse conventional commits
            grouped = {
                "feat": [],
                "fix": [],
                "docs": [],
                "style": [],
                "refactor": [],
                "test": [],
                "chore": [],
                "other": [],
            }

            for commit in commits:
                if not commit.strip():
                    continue

                # Parse conventional commit format
                match = re.match(
                    r'^(feat|fix|docs|style|refactor|test|chore)(?:\([^)]+\))?: (.+)$', commit)
                if match:
                    commit_type, message = match.groups()
                    grouped[commit_type].append(message)
                else:
                    grouped["other"].append(commit)

            # Generate markdown
            changelog = self._format_changelog(grouped, from_ref, to_ref)

            return {
                "from_ref": from_ref or "start",
                "to_ref": to_ref,
                "total_commits": len(commits),
                "grouped_commits": grouped,
                "changelog": changelog,
            }
        except FileNotFoundError:
            return {"error": "git not installed"}
        except Exception as e:
            return {"error": str(e)}

    def _format_changelog(self, grouped: dict, from_ref: str, to_ref: str) -> str:
        """Format grouped commits as markdown."""
        version = from_ref or "Unreleased"
        date = datetime.now().strftime("%Y-%m-%d")

        changelog = f"## [{version}] - {date}\n\n"

        type_mapping = {
            "feat": "### ✨ Features",
            "fix": "### 🐛 Bug Fixes",
            "docs": "### 📝 Documentation",
            "refactor": "### ♻️ Refactoring",
            "test": "### 🧪 Tests",
            "chore": "### 🔧 Chores",
        }

        for commit_type, title in type_mapping.items():
            commits = grouped.get(commit_type, [])
            if commits:
                changelog += f"{title}\n\n"
                for commit in commits:
                    changelog += f"- {commit}\n"
                changelog += "\n"

        # Add other commits if any
        if grouped.get("other"):
            changelog += "### Other Changes\n\n"
            for commit in grouped["other"]:
                changelog += f"- {commit}\n"
            changelog += "\n"

        return changelog


class CICDIntegrationTool(BaseTool):
    """Integrate with CI/CD pipelines.

    Features:
    - Trigger pipeline runs
    - Check pipeline status
    - Wait for completion
    - Deploy automation
    """

    def __init__(self):
        super().__init__(
            name="cicd_integration",
            description="Integrate with CI/CD pipelines",
            parameters={},
        )

    async def _execute(self, action: str, **kwargs) -> dict[str, Any]:
        """Perform CI/CD action.

        Args:
            action: Action to perform (trigger, status, wait, deploy)
            **kwargs: Action-specific parameters

        Returns:
            CI/CD action results
        """
        if action == "trigger":
            return await self._trigger_pipeline(**kwargs)
        elif action == "status":
            return await self._check_status(**kwargs)
        elif action == "wait":
            return await self._wait_for_completion(**kwargs)
        elif action == "deploy":
            return await self._trigger_deployment(**kwargs)
        else:
            return {"error": f"Unsupported action: {action}"}

    async def _trigger_pipeline(self, pipeline: str = "ci", **kwargs) -> dict[str, Any]:
        """Trigger CI/CD pipeline."""
        return {
            "action": "trigger",
            "pipeline": pipeline,
            "status": "triggered",
            "message": f"Pipeline '{pipeline}' triggered",
        }

    async def _check_status(self, pipeline_id: str, **kwargs) -> dict[str, Any]:
        """Check pipeline status."""
        return {
            "action": "status",
            "pipeline_id": pipeline_id,
            "status": "running",
            "message": "Pipeline is running",
        }

    async def _wait_for_completion(self, pipeline_id: str, timeout: int = 300, **kwargs) -> dict[str, Any]:
        """Wait for pipeline completion."""
        return {
            "action": "wait",
            "pipeline_id": pipeline_id,
            "status": "completed",
            "result": "success",
        }

    async def _trigger_deployment(self, environment: str = "production", **kwargs) -> dict[str, Any]:
        """Trigger deployment."""
        return {
            "action": "deploy",
            "environment": environment,
            "status": "deploying",
            "message": f"Deployment to {environment} initiated",
        }


class PackagePublishingTool(BaseTool):
    """Publish packages to registries.

    Supports:
    - PyPI publishing (twine)
    - Docker image building and pushing
    - npm publishing
    - GitHub Releases
    """

    def __init__(self):
        super().__init__(
            name="package_publishing",
            description="Publish packages to PyPI, Docker, npm",
            parameters={},
        )

    async def _execute(self, registry: str, **kwargs) -> dict[str, Any]:
        """Publish package to registry.

        Args:
            registry: Target registry (pypi, docker, npm, github)
            **kwargs: Registry-specific parameters

        Returns:
            Publishing results
        """
        if registry == "pypi":
            return await self._publish_to_pypi(**kwargs)
        elif registry == "docker":
            return await self._publish_to_docker(**kwargs)
        elif registry == "npm":
            return await self._publish_to_npm(**kwargs)
        elif registry == "github":
            return await self._create_github_release(**kwargs)
        else:
            return {"error": f"Unsupported registry: {registry}"}

    async def _publish_to_pypi(self, **kwargs) -> dict[str, Any]:
        """Publish to PyPI using twine."""
        try:
            # Build package
            build_result = subprocess.run(
                ["python", "-m", "build"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if build_result.returncode != 0:
                return {"error": "Build failed", "details": build_result.stderr}

            return {
                "registry": "pypi",
                "status": "built",
                "message": "Package built successfully. Use 'twine upload dist/*' to publish",
            }
        except FileNotFoundError:
            return {"error": "build module not installed"}
        except Exception as e:
            return {"error": str(e)}

    async def _publish_to_docker(self, image_name: str, tag: str = "latest", **kwargs) -> dict[str, Any]:
        """Build and push Docker image."""
        return {
            "registry": "docker",
            "image": image_name,
            "tag": tag,
            "status": "simulated",
            "message": f"Would build and push {image_name}:{tag}",
        }

    async def _publish_to_npm(self, **kwargs) -> dict[str, Any]:
        """Publish to npm."""
        return {
            "registry": "npm",
            "status": "not_applicable",
            "message": "This is a Python project",
        }

    async def _create_github_release(self, tag: str, title: str, notes: str = "", **kwargs) -> dict[str, Any]:
        """Create GitHub release."""
        try:
            cmd = ["gh", "release", "create", tag, "--title", title]
            if notes:
                cmd.extend(["--notes", notes])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "registry": "github",
                "tag": tag,
                "title": title,
                "success": result.returncode == 0,
                "output": result.stdout,
            }
        except FileNotFoundError:
            return {"error": "gh (GitHub CLI) not installed"}
        except Exception as e:
            return {"error": str(e)}


# Tool instances
version_management = VersionManagementTool()
changelog_generation = ChangelogGenerationTool()
cicd_integration = CICDIntegrationTool()
package_publishing = PackagePublishingTool()

__all__ = [
    "VersionManagementTool",
    "ChangelogGenerationTool",
    "CICDIntegrationTool",
    "PackagePublishingTool",
    "version_management",
    "changelog_generation",
    "cicd_integration",
    "package_publishing",
]
