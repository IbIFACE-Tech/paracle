"""Paracle Meta Capabilities Module.

Provides powerful integrated capabilities for the MetaAgent:
- Web search and crawling
- Code execution and testing
- MCP (Model Context Protocol) integration
- Task/workflow management
- Autonomous agent spawning
- Anthropic Claude SDK integration
- FileSystem operations
- LLM-powered code creation
- Persistent memory and context
- Shell command execution

These capabilities allow the MetaAgent to autonomously perform
complex tasks beyond simple artifact generation.

Hybrid Architecture:
- Native capabilities for lightweight, self-contained operations
- Anthropic SDK integration for intelligent, Claude-powered features
"""

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)
from paracle_meta.capabilities.code_execution import (
    CodeExecutionCapability,
    CodeExecutionConfig,
    ExecutionResult,
)
from paracle_meta.capabilities.mcp_integration import (
    MCPCapability,
    MCPConfig,
    MCPTool,
)
from paracle_meta.capabilities.task_management import (
    TaskManagementCapability,
    TaskConfig,
    Task,
    TaskStatus,
    TaskPriority,
    Workflow,
)
from paracle_meta.capabilities.web_capabilities import (
    WebCapability,
    WebConfig,
    SearchResult,
    CrawlResult,
)
from paracle_meta.capabilities.agent_spawner import (
    AgentSpawner,
    SpawnConfig,
    SpawnedAgent,
    AgentType,
    AgentStatus,
    AgentPool,
)

# New Hybrid Capabilities
from paracle_meta.capabilities.anthropic_integration import (
    AnthropicCapability,
    AnthropicConfig,
    ClaudeModel,
    ToolDefinition,
    ToolCall,
    ToolResult,
    Message,
    ConversationContext,
)
from paracle_meta.capabilities.filesystem import (
    FileSystemCapability,
    FileSystemConfig,
)
from paracle_meta.capabilities.code_creation import (
    CodeCreationCapability,
    CodeCreationConfig,
)
from paracle_meta.capabilities.memory import (
    MemoryCapability,
    MemoryConfig,
    MemoryItem,
)
from paracle_meta.capabilities.shell import (
    ShellCapability,
    ShellConfig,
    ProcessInfo,
)

__all__ = [
    # Base
    "BaseCapability",
    "CapabilityConfig",
    "CapabilityResult",
    # Web
    "WebCapability",
    "WebConfig",
    "SearchResult",
    "CrawlResult",
    # Code Execution
    "CodeExecutionCapability",
    "CodeExecutionConfig",
    "ExecutionResult",
    # MCP
    "MCPCapability",
    "MCPConfig",
    "MCPTool",
    # Tasks
    "TaskManagementCapability",
    "TaskConfig",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "Workflow",
    # Agent Spawning
    "AgentSpawner",
    "SpawnConfig",
    "SpawnedAgent",
    "AgentType",
    "AgentStatus",
    "AgentPool",
    # Anthropic Integration
    "AnthropicCapability",
    "AnthropicConfig",
    "ClaudeModel",
    "ToolDefinition",
    "ToolCall",
    "ToolResult",
    "Message",
    "ConversationContext",
    # FileSystem
    "FileSystemCapability",
    "FileSystemConfig",
    # Code Creation
    "CodeCreationCapability",
    "CodeCreationConfig",
    # Memory
    "MemoryCapability",
    "MemoryConfig",
    "MemoryItem",
    # Shell
    "ShellCapability",
    "ShellConfig",
    "ProcessInfo",
]
