"""Fix all tool files to use super().__init__() properly."""

import re
from pathlib import Path

# Define all tool files and their tool class names
TOOL_FILES = {
    "packages/paracle_tools/architect_tools.py": [
        ("CodeAnalysisTool", "code_analysis",
         "Analyze code structure, dependencies, and complexity metrics"),
        ("DiagramGenerationTool", "diagram_generation",
         "Generate architecture and design diagrams"),
        ("PatternMatchingTool", "pattern_matching",
         "Detect design patterns and anti-patterns in code"),
    ],
    "packages/paracle_tools/coder_tools.py": [
        ("CodeGenerationTool", "code_generation",
         "Generate code from templates or specifications"),
        ("RefactoringTool", "refactoring",
         "Refactor code with extract method, rename, and formatting"),
        ("TestingTool", "testing", "Run pytest tests and analyze coverage"),
    ],
    "packages/paracle_tools/reviewer_tools.py": [
        ("StaticAnalysisTool", "static_analysis",
         "Run static analysis with ruff, mypy, or pylint"),
        ("SecurityScanTool", "security_scan",
         "Scan for security vulnerabilities with bandit and safety"),
        ("CodeReviewTool", "code_review", "Review code quality and style"),
    ],
    "packages/paracle_tools/tester_tools.py": [
        ("TestGenerationTool", "test_generation", "Generate test cases for code"),
        ("TestExecutionTool", "test_execution",
         "Execute pytest tests with options"),
        ("CoverageAnalysisTool", "coverage_analysis",
         "Analyze test coverage with pytest-cov"),
    ],
    "packages/paracle_tools/pm_tools.py": [
        ("TaskTrackingTool", "task_tracking", "Track and manage tasks"),
        ("MilestoneManagementTool", "milestone_management",
         "Manage project milestones and roadmap"),
        ("TeamCoordinationTool", "team_coordination",
         "Coordinate team activities and assignments"),
    ],
    "packages/paracle_tools/documenter_tools.py": [
        ("MarkdownGenerationTool", "markdown_generation",
         "Generate markdown documentation"),
        ("ApiDocGenerationTool", "api_doc_generation", "Generate API documentation"),
        ("DiagramCreationTool", "diagram_creation",
         "Create diagrams for documentation"),
    ],
    "packages/paracle_tools/release_tools.py": [
        ("VersionManagementTool", "version_management", "Manage semantic versioning"),
        ("ChangelogGenerationTool", "changelog_generation",
         "Generate changelog from commits"),
        ("CICDIntegrationTool", "cicd_integration",
         "Integrate with CI/CD pipelines"),
        ("PackagePublishingTool", "package_publishing",
         "Publish packages to PyPI, Docker, npm"),
        ("GitHubCLITool", "github_cli",
         "Execute GitHub CLI operations"),
    ],
}


def fix_tool_class(content: str, class_name: str, tool_name: str, description: str) -> str:
    """Fix a single tool class to use super().__init__()."""

    # Pattern to match class definition with name/description attributes
    pattern = rf'(class {class_name}\(BaseTool\):.*?""".*?""")\s+name = "[^"]+"\s+description = "[^"]+"'

    # Replacement with __init__ method
    replacement = rf'\1\n\n    def __init__(self):\n        super().__init__(\n            name="{tool_name}",\n            description="{description}",\n            parameters={{}},\n        )'

    # Use DOTALL to match across newlines
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    return new_content


def main():
    """Fix all tool files."""
    root = Path(__file__).parent.parent

    for file_path, tools in TOOL_FILES.items():
        full_path = root / file_path
        print(f"Fixing {file_path}...")

        content = full_path.read_text(encoding="utf-8")

        for class_name, tool_name, description in tools:
            print(f"  - {class_name}")
            content = fix_tool_class(
                content, class_name, tool_name, description)

        full_path.write_text(content, encoding="utf-8")
        print(f"  ✓ Fixed {len(tools)} tools\n")

    print("All tool files fixed!")


if __name__ == "__main__":
    main()
