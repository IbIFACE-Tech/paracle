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
- Vector search (HNSW-based semantic search with quantization)
- Reflexion (learning from experience and self-critique)
- Hook system (pre/post operation hooks for extensibility)
- Semantic memory (hybrid vector + SQL storage)
- HiveMind (multi-agent coordination with Queen architecture)
- Token optimization (intelligent compression, 30%+ reduction)
- RL training (9 algorithms: Q-Learning, DQN, PPO, SAC, etc.)
- GitHub Enhanced (PR review, multi-repo sync, automation)
- Observability (unified metrics, cost tracking, performance monitoring)
- Rate limiting (token bucket algorithm, burst control, quota management)
- Caching (LLM call deduplication, TTL-based, LRU eviction)
- Audit (ISO 42001 compliant audit trail with tamper-evident hash chain)
- Resilience (circuit breaker, retry with backoff, fallback, timeout, bulkhead)
- Streaming (SSE, WebSocket, real-time streaming with backpressure handling)

These capabilities allow the MetaAgent to autonomously perform
complex tasks beyond simple artifact generation.

Hybrid Architecture:
- Native capabilities for lightweight, self-contained operations
- Anthropic SDK integration for intelligent, Claude-powered features
- Paracle integration for unified access to framework features

  Integration Points:
  - paracle_core: Logging, utilities, cost tracking
  - paracle_observability: Business metrics, Prometheus, alerting
  - paracle_store: Persistence (SQLite, PostgreSQL, Redis)
  - paracle_providers: LLM provider orchestration

  This hybrid approach ensures:
  1. Code reuse and DRY principle
  2. Unified observability across paracle ecosystem
  3. Consistent cost tracking and budgeting
  4. Shared infrastructure for scaling
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

# Claude-Flow Inspired Capabilities (v1.9.0)
from paracle_meta.capabilities.vector_search import (
    VectorSearchCapability,
    VectorSearchConfig,
    IndexType,
    DistanceMetric,
    QuantizationType,
)
from paracle_meta.capabilities.reflexion import (
    ReflexionCapability,
    ReflexionConfig,
    ExperienceType,
    ReflectionDepth,
)
from paracle_meta.capabilities.hook_system import (
    HookSystemCapability,
    HookSystemConfig,
    HookType,
    HookContext,
)
from paracle_meta.capabilities.semantic_memory import (
    SemanticMemoryCapability,
    SemanticMemoryConfig,
    Memory,
    ConversationTurn,
)
from paracle_meta.capabilities.hive_mind import (
    HiveMindCapability,
    HiveMindConfig,
    AgentRole,
    HiveTask,
    ConsensusMethod,
)
from paracle_meta.capabilities.token_optimization import (
    TokenOptimizationCapability,
    TokenOptimizationConfig,
    OptimizationLevel,
    ContentType,
)
from paracle_meta.capabilities.rl_training import (
    RLTrainingCapability,
    RLTrainingConfig,
    RLAlgorithm,
    Experience,
)
from paracle_meta.capabilities.github_enhanced import (
    GitHubEnhancedCapability,
    GitHubEnhancedConfig,
    PRStatus,
    ReviewStatus,
)
from paracle_meta.capabilities.observability import (
    ObservabilityCapability,
    ObservabilityConfig,
)
from paracle_meta.capabilities.rate_limit import (
    RateLimitCapability,
    RateLimitConfig,
)
from paracle_meta.capabilities.caching import (
    CachingCapability,
    CachingConfig,
)
from paracle_meta.capabilities.audit import (
    ActionType,
    AuditCapability,
    AuditConfig,
)
from paracle_meta.capabilities.resilience import (
    CircuitBreaker,
    CircuitState,
    ResilienceCapability,
    ResilienceConfig,
    RetryStrategy,
)
from paracle_meta.capabilities.streaming import (
    ChunkType,
    StreamBuffer,
    StreamChunk,
    StreamingCapability,
    StreamingConfig,
    StreamProtocol,
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
    # Vector Search (v1.9.0)
    "VectorSearchCapability",
    "VectorSearchConfig",
    "IndexType",
    "DistanceMetric",
    "QuantizationType",
    # Reflexion (v1.9.0)
    "ReflexionCapability",
    "ReflexionConfig",
    "ExperienceType",
    "ReflectionDepth",
    # Hook System (v1.9.0)
    "HookSystemCapability",
    "HookSystemConfig",
    "HookType",
    "HookContext",
    # Semantic Memory (v1.9.0)
    "SemanticMemoryCapability",
    "SemanticMemoryConfig",
    "Memory",
    "ConversationTurn",
    # HiveMind (v1.9.0)
    "HiveMindCapability",
    "HiveMindConfig",
    "AgentRole",
    "HiveTask",
    "ConsensusMethod",
    # Token Optimization (v1.9.0)
    "TokenOptimizationCapability",
    "TokenOptimizationConfig",
    "OptimizationLevel",
    "ContentType",
    # RL Training (v1.9.0)
    "RLTrainingCapability",
    "RLTrainingConfig",
    "RLAlgorithm",
    "Experience",
    # GitHub Enhanced (v1.9.0)
    "GitHubEnhancedCapability",
    "GitHubEnhancedConfig",
    "PRStatus",
    "ReviewStatus",
    # Observability (v1.9.1)
    "ObservabilityCapability",
    "ObservabilityConfig",
    # Rate Limiting (v1.9.2)
    "RateLimitCapability",
    "RateLimitConfig",
    # Caching (v1.9.2)
    "CachingCapability",
    "CachingConfig",
    # Audit (v1.9.3)
    "AuditCapability",
    "AuditConfig",
    "ActionType",
    # Resilience (v1.9.4)
    "ResilienceCapability",
    "ResilienceConfig",
    "CircuitBreaker",
    "CircuitState",
    "RetryStrategy",
    # Streaming (v1.9.5)
    "StreamingCapability",
    "StreamingConfig",
    "StreamChunk",
    "StreamBuffer",
    "StreamProtocol",
    "ChunkType",
]
