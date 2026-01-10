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
- Paracle framework integration (API, tools, MCP)
- Multi-language code execution (Python, JS/TS, Go, Rust, C/C++, etc.)
- Image processing (vision, generation, editing, OCR)
- Audio processing (transcription, TTS, conversion)
- Database operations (SQL, NoSQL - PostgreSQL, MongoDB, Redis)
- Notifications (email, Slack, Discord, Teams, SMS, webhooks)
- Task scheduling (cron-based, delayed execution)
- Container management (Docker, Podman)
- Cloud services (AWS, GCP, Azure - storage, functions, secrets)
- Document processing (PDF, Excel, CSV, Markdown)
- Browser automation (Playwright - navigation, scraping, screenshots)
- Polyglot extensions (Go, Rust, JS/TS, WASM - multi-language plugins)

These capabilities allow the MetaAgent to autonomously perform
complex tasks beyond simple artifact generation.

Hybrid Architecture:
- Native capabilities for lightweight, self-contained operations
- Anthropic SDK integration for intelligent, Claude-powered features
- Paracle integration for unified access to framework features
"""

from paracle_meta.capabilities.agent_spawner import (
    AgentPool,
    AgentSpawner,
    AgentStatus,
    AgentType,
    SpawnConfig,
    SpawnedAgent,
)

# New Hybrid Capabilities
from paracle_meta.capabilities.anthropic_integration import (
    AnthropicCapability,
    AnthropicConfig,
    ClaudeModel,
    ConversationContext,
    Message,
    ToolCall,
    ToolDefinition,
    ToolResult,
)
from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)
from paracle_meta.capabilities.code_creation import (
    CodeCreationCapability,
    CodeCreationConfig,
)
from paracle_meta.capabilities.code_execution import (
    CodeExecutionCapability,
    CodeExecutionConfig,
    ExecutionResult,
)
from paracle_meta.capabilities.multi_language_execution import (
    Language,
    MultiLanguageConfig,
    MultiLanguageExecutionCapability,
)
from paracle_meta.capabilities.filesystem import FileSystemCapability, FileSystemConfig
from paracle_meta.capabilities.mcp_integration import MCPCapability, MCPConfig, MCPTool
from paracle_meta.capabilities.memory import MemoryCapability, MemoryConfig, MemoryItem
from paracle_meta.capabilities.paracle_integration import ParacleCapability, ParacleConfig
from paracle_meta.capabilities.shell import ProcessInfo, ShellCapability, ShellConfig

# New Extended Capabilities (v1.8.0)
from paracle_meta.capabilities.image import ImageCapability, ImageConfig
from paracle_meta.capabilities.audio import AudioCapability, AudioConfig
from paracle_meta.capabilities.database import DatabaseCapability, DatabaseConfig, DatabaseType
from paracle_meta.capabilities.notification import NotificationCapability, NotificationConfig, NotificationChannel
from paracle_meta.capabilities.scheduler import SchedulerCapability, SchedulerConfig, ScheduledTask
from paracle_meta.capabilities.container import ContainerCapability, ContainerConfig, ContainerRuntime
from paracle_meta.capabilities.cloud import CloudCapability, CloudConfig, CloudProvider
from paracle_meta.capabilities.document import DocumentCapability, DocumentConfig, DocumentFormat
from paracle_meta.capabilities.browser import BrowserCapability, BrowserConfig, BrowserType
from paracle_meta.capabilities.polyglot import (
    PolyglotCapability,
    PolyglotConfig,
    ExtensionLanguage,
    ExtensionManifest,
    ExtensionInfo,
    Protocol,
)

from paracle_meta.capabilities.task_management import (
    Task,
    TaskConfig,
    TaskManagementCapability,
    TaskPriority,
    TaskStatus,
    Workflow,
)
from paracle_meta.capabilities.web_capabilities import (
    CrawlResult,
    SearchResult,
    WebCapability,
    WebConfig,
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
    # Multi-Language Execution
    "MultiLanguageExecutionCapability",
    "MultiLanguageConfig",
    "Language",
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
    # Paracle Integration
    "ParacleCapability",
    "ParacleConfig",
    # Image Processing
    "ImageCapability",
    "ImageConfig",
    # Audio Processing
    "AudioCapability",
    "AudioConfig",
    # Database Operations
    "DatabaseCapability",
    "DatabaseConfig",
    "DatabaseType",
    # Notifications
    "NotificationCapability",
    "NotificationConfig",
    "NotificationChannel",
    # Task Scheduling
    "SchedulerCapability",
    "SchedulerConfig",
    "ScheduledTask",
    # Container Management
    "ContainerCapability",
    "ContainerConfig",
    "ContainerRuntime",
    # Cloud Services
    "CloudCapability",
    "CloudConfig",
    "CloudProvider",
    # Document Processing
    "DocumentCapability",
    "DocumentConfig",
    "DocumentFormat",
    # Browser Automation
    "BrowserCapability",
    "BrowserConfig",
    "BrowserType",
    # Polyglot Extensions (Go, Rust, JS/TS, WASM)
    "PolyglotCapability",
    "PolyglotConfig",
    "ExtensionLanguage",
    "ExtensionManifest",
    "ExtensionInfo",
    "Protocol",
]
