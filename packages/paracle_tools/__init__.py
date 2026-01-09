"""
Tool management and Model Context Protocol (MCP) integration.

This package provides:
- Built-in tools: filesystem, HTTP, shell operations (with security controls)
- MCP client for discovering and calling MCP-compatible tools
- Tool registry for managing available tools
- Tool integration with Paracle agents

SECURITY NOTE: Default tool instances have been REMOVED for security.
All filesystem/shell tools now require explicit configuration.
Use factory functions to create properly configured tools.
"""

__version__ = "1.0.1"

# MCP tools
# Built-in tools
from paracle_mcp import MCPClient, MCPToolRegistry

# Agent-specific tools
from paracle_tools.architect_tools import (
    CodeAnalysisTool,
    DiagramGenerationTool,
    PatternMatchingTool,
    code_analysis,
    diagram_generation,
    pattern_matching,
)
from paracle_tools.builtin import (  # Base classes; Filesystem tool classes (require allowed_paths); Shell tool classes (require allowed_commands); HTTP tools
    DEVELOPMENT_COMMANDS,
    READONLY_COMMANDS,
    BaseTool,
    BuiltinToolRegistry,
    DeleteFileTool,
    ListDirectoryTool,
    PermissionError,
    ReadFileTool,
    RunCommandTool,
    Tool,
    ToolError,  # Builtin tool error
    ToolResult,
    WriteFileTool,
    create_command_tool,
    create_development_command_tool,
    create_readonly_command_tool,
    create_sandboxed_filesystem_tools,
    http_delete,
    http_get,
    http_post,
    http_put,
)
from paracle_tools.coder_tools import (
    CodeGenerationTool,
    RefactoringTool,
    TestingTool,
    code_generation,
    refactoring,
    testing,
)
from paracle_tools.documenter_tools import (
    ApiDocGenerationTool,
    DiagramCreationTool,
    MarkdownGenerationTool,
    api_doc_generation,
    diagram_creation,
    markdown_generation,
)

# Tool exceptions (import with alias to avoid conflict with builtin.ToolError)
from paracle_tools.exceptions import (
    ToolConfigurationError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionError,
    ToolRegistrationError,
    ToolResourceError,
    ToolTimeoutError,
    ToolValidationError,
)
from paracle_tools.exceptions import ToolError as ParacleToolError
from paracle_tools.git_tools import (
    GitAddTool,
    GitBranchTool,
    GitCheckoutTool,
    GitCommitTool,
    GitDiffTool,
    GitFetchTool,
    GitLogTool,
    GitMergeTool,
    GitPullTool,
    GitPushTool,
    GitRemoteTool,
    GitResetTool,
    GitStashTool,
    GitStatusTool,
    GitTagTool,
    git_add,
    git_branch,
    git_checkout,
    git_commit,
    git_diff,
    git_fetch,
    git_log,
    git_merge,
    git_pull,
    git_push,
    git_remote,
    git_reset,
    git_stash,
    git_status,
    git_tag,
)
from paracle_tools.pm_tools import (
    MilestoneManagementTool,
    TaskTrackingTool,
    TeamCoordinationTool,
    milestone_management,
    task_tracking,
    team_coordination,
)
from paracle_tools.release_tools import (
    ChangelogGenerationTool,
    CICDIntegrationTool,
    GitHubCLITool,
    PackagePublishingTool,
    VersionManagementTool,
    changelog_generation,
    cicd_integration,
    github_cli,
    package_publishing,
    version_management,
)
from paracle_tools.reviewer_tools import (
    CodeReviewTool,
    SecurityScanTool,
    StaticAnalysisTool,
    code_review,
    security_scan,
    static_analysis,
)
from paracle_tools.terminal_tools import (
    TerminalExecuteTool,
    TerminalInfoTool,
    TerminalInteractiveTool,
    TerminalWhichTool,
    terminal_execute,
    terminal_info,
    terminal_interactive,
    terminal_which,
)
from paracle_tools.tester_tools import (
    CoverageAnalysisTool,
    TestExecutionTool,
    TestGenerationTool,
    coverage_analysis,
    test_execution,
    test_generation,
)

__all__ = [
    # Paracle exceptions (framework-level)
    "ParacleToolError",
    "ToolConfigurationError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolPermissionError",
    "ToolRegistrationError",
    "ToolResourceError",
    "ToolTimeoutError",
    "ToolValidationError",
    # MCP
    "MCPClient",
    "MCPToolRegistry",
    # Built-in base (legacy ToolError from builtin)
    "BaseTool",
    "Tool",
    "ToolResult",
    "ToolError",
    "PermissionError",
    "BuiltinToolRegistry",
    # Filesystem tool classes (require allowed_paths)
    "ReadFileTool",
    "WriteFileTool",
    "ListDirectoryTool",
    "DeleteFileTool",
    "create_sandboxed_filesystem_tools",
    # HTTP tools
    "http_get",
    "http_post",
    "http_put",
    "http_delete",
    # Shell tool classes (require allowed_commands)
    "RunCommandTool",
    "create_command_tool",
    "create_readonly_command_tool",
    "create_development_command_tool",
    "READONLY_COMMANDS",
    "DEVELOPMENT_COMMANDS",
    # Git tools
    "GitAddTool",
    "GitBranchTool",
    "GitCheckoutTool",
    "GitCommitTool",
    "GitDiffTool",
    "GitFetchTool",
    "GitLogTool",
    "GitMergeTool",
    "GitPullTool",
    "GitPushTool",
    "GitRemoteTool",
    "GitResetTool",
    "GitStashTool",
    "GitStatusTool",
    "GitTagTool",
    "git_add",
    "git_branch",
    "git_checkout",
    "git_commit",
    "git_diff",
    "git_fetch",
    "git_log",
    "git_merge",
    "git_pull",
    "git_push",
    "git_remote",
    "git_reset",
    "git_stash",
    "git_status",
    "git_tag",
    # Terminal tools
    "TerminalExecuteTool",
    "TerminalInfoTool",
    "TerminalInteractiveTool",
    "TerminalWhichTool",
    "terminal_execute",
    "terminal_info",
    "terminal_interactive",
    "terminal_which",
    # Architect tools
    "CodeAnalysisTool",
    "DiagramGenerationTool",
    "PatternMatchingTool",
    "code_analysis",
    "diagram_generation",
    "pattern_matching",
    # Coder tools
    "CodeGenerationTool",
    "RefactoringTool",
    "TestingTool",
    "code_generation",
    "refactoring",
    "testing",
    # Reviewer tools
    "StaticAnalysisTool",
    "SecurityScanTool",
    "CodeReviewTool",
    "static_analysis",
    "security_scan",
    "code_review",
    # Tester tools
    "TestGenerationTool",
    "TestExecutionTool",
    "CoverageAnalysisTool",
    "test_generation",
    "test_execution",
    "coverage_analysis",
    # PM tools
    "TaskTrackingTool",
    "MilestoneManagementTool",
    "TeamCoordinationTool",
    "task_tracking",
    "milestone_management",
    "team_coordination",
    # Documenter tools
    "MarkdownGenerationTool",
    "ApiDocGenerationTool",
    "DiagramCreationTool",
    "markdown_generation",
    "api_doc_generation",
    "diagram_creation",
    # Release Manager tools
    "VersionManagementTool",
    "ChangelogGenerationTool",
    "CICDIntegrationTool",
    "PackagePublishingTool",
    "version_management",
    "changelog_generation",
    "cicd_integration",
    "package_publishing",
]
