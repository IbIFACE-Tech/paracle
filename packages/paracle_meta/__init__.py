"""Paracle Meta-Agent Engine.

Intelligent AI-powered generation system that creates Paracle artifacts
(agents, workflows, skills, policies) from natural language descriptions.

Features:
- Multi-provider LLM support (OpenAI, Anthropic, Google, Ollama, Azure, etc.)
- Learning and continuous improvement
- Cost optimization
- Quality scoring
- Template evolution
- Best practices knowledge base
- Web search and crawling capabilities
- Code execution and testing
- MCP integration for external tools
- Task/workflow management
- Autonomous agent spawning for high load

Hybrid Capabilities (v1.3.0):
- Anthropic Claude SDK integration with tool use
- FileSystem operations (read, write, search, git)
- LLM-powered code creation and refactoring
- Persistent memory and context management
- Shell command execution with safety features

New in v1.4.0:
- Provider abstraction layer with fallback strategies
- Chat mode for interactive conversations with tools
- Plan mode for structured task decomposition
- Capability registry with lazy loading
- Circuit breaker pattern for provider resilience

New in v1.8.0:
- Image processing (vision, generation, editing, OCR)
- Audio processing (transcription, TTS, conversion)
- Database operations (SQL, NoSQL - PostgreSQL, MongoDB, Redis)
- Multi-channel notifications (email, Slack, Discord, Teams, SMS)
- Task scheduling (cron-based, delayed execution)
- Container management (Docker, Podman)
- Cloud services (AWS, GCP, Azure - storage, functions, secrets)
- Document processing (PDF, Excel, CSV, Markdown)
- Browser automation (Playwright - navigation, scraping, screenshots)

Example:
    >>> from paracle_meta import MetaAgent
    >>>
    >>> async with MetaAgent() as meta:
    ...     # Generate an agent
    ...     agent = await meta.generate_agent(
    ...         name="SecurityAuditor",
    ...         description="Reviews Python code for security vulnerabilities"
    ...     )
    ...
    ...     # Use enhanced capabilities
    ...     search = await meta.web_search("Python security best practices")
    ...     code_result = await meta.run_code("print('Hello!')")
    ...
    ...     # Hybrid capabilities (v1.3.0)
    ...     claude = await meta.claude_complete("Explain Python decorators")
    ...     code = await meta.create_function("calculate_sum", "Add two numbers")
    ...     await meta.remember("api_key", "sk-...")
    ...     result = await meta.run_shell("ls -la")
    ...
    ...     # Spawn specialized agent for heavy work
    ...     spawned = await meta.spawn_agent("Researcher", agent_type="researcher")
    ...
    ...     # Learn from feedback
    ...     await meta.record_feedback(agent.id, rating=5)

Interactive Sessions (v1.4.0):
    >>> from paracle_meta import ChatSession, PlanSession
    >>> from paracle_meta.capabilities.providers import AnthropicProvider
    >>> from paracle_meta.registry import CapabilityRegistry
    >>>
    >>> # Chat mode with tools
    >>> provider = AnthropicProvider()
    >>> registry = CapabilityRegistry()
    >>> async with ChatSession(provider, registry) as chat:
    ...     response = await chat.send("Read the config.py file")
    ...     print(response.content)
    >>>
    >>> # Plan mode for complex tasks
    >>> async with PlanSession(provider, registry) as planner:
    ...     plan = await planner.create_plan("Build a REST API")
    ...     await planner.execute_plan(plan)
"""

# Capabilities
from paracle_meta.capabilities import (  # Hybrid capabilities (native + Anthropic SDK)
    AgentSpawner,
    AnthropicCapability,
    AnthropicConfig,
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
    ClaudeModel,
    CodeCreationCapability,
    CodeCreationConfig,
    CodeExecutionCapability,
    CodeExecutionConfig,
    FileSystemCapability,
    FileSystemConfig,
    MCPCapability,
    MCPConfig,
    MemoryCapability,
    MemoryConfig,
    MemoryItem,
    ShellCapability,
    ShellConfig,
    SpawnConfig,
    SpawnedAgent,
    TaskConfig,
    TaskManagementCapability,
    ToolDefinition,
    WebCapability,
    WebConfig,
)
from paracle_meta.capabilities.provider_chain import (
    CircuitBreaker,
    FallbackStrategy,
    ProviderChain,
    ProviderChainError,
    ProviderMetrics,
)

# Provider abstraction (v1.4.0)
from paracle_meta.capabilities.provider_protocol import (
    CapabilityProvider,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ProviderError,
    ProviderStatus,
    StreamChunk,
    ToolCallRequest,
    ToolCallResult,
    ToolDefinitionSchema,
)
from paracle_meta.capabilities.providers import (
    AnthropicProvider,
    MockProvider,
    OllamaProvider,
    OpenAIProvider,
)
from paracle_meta.engine import MetaAgent
from paracle_meta.generators import (
    AgentGenerator,
    PolicyGenerator,
    SkillGenerator,
    WorkflowGenerator,
)
from paracle_meta.generators.base import GenerationRequest, GenerationResult
from paracle_meta.knowledge import BestPracticesDatabase
from paracle_meta.learning import FeedbackCollector, LearningEngine
from paracle_meta.optimizer import CostOptimizer, QualityScorer
from paracle_meta.providers import ProviderOrchestrator, ProviderSelector

# Registry (v1.4.0)
from paracle_meta.registry import (
    CapabilityFacade,
    CapabilityRegistry,
    CapabilityStatus,
    RegistryConfig,
)

# Sessions (v1.4.0)
from paracle_meta.sessions import (
    ChatConfig,
    ChatSession,
    EditBatch,
    EditConfig,
    EditOperation,
    EditSession,
    EditStatus,
    EditType,
    Plan,
    PlanConfig,
    PlanSession,
    PlanStep,
    Session,
    SessionConfig,
    SessionMessage,
)
from paracle_meta.templates import TemplateEvolution, TemplateLibrary

# Database and repositories (v1.5.0) - Optional, requires sqlalchemy
# These are imported lazily to allow basic usage without sqlalchemy
try:
    from paracle_meta.database import (
        MetaDatabase,
        MetaDatabaseConfig,
        get_meta_database,
        get_system_data_path,
    )
    from paracle_meta.health import (
        HealthCheck,
        HealthChecker,
        HealthStatus,
        check_health,
        format_health_report,
    )
    from paracle_meta.repositories import (
        BestPractice,
        BestPracticesRepository,
        ContextRepository,
        CostEntry,
        CostReport,
        CostRepository,
        Feedback,
        FeedbackRepository,
        GenerationRepository,
        MemoryEntry,
        MemoryRepository,
        TemplateRepository,
        TemplateSpec,
    )
    from paracle_meta.repositories import GenerationResult as RepoGenerationResult

    _HAS_DATABASE = True
except ImportError:
    # SQLAlchemy not installed - database features unavailable
    _HAS_DATABASE = False
    MetaDatabase = None  # type: ignore
    MetaDatabaseConfig = None  # type: ignore
    get_meta_database = None  # type: ignore
    get_system_data_path = None  # type: ignore
    BestPractice = None  # type: ignore
    BestPracticesRepository = None  # type: ignore
    CostEntry = None  # type: ignore
    CostReport = None  # type: ignore
    CostRepository = None  # type: ignore
    ContextRepository = None  # type: ignore
    Feedback = None  # type: ignore
    FeedbackRepository = None  # type: ignore
    GenerationRepository = None  # type: ignore
    RepoGenerationResult = None  # type: ignore
    MemoryEntry = None  # type: ignore
    MemoryRepository = None  # type: ignore
    TemplateRepository = None  # type: ignore
    TemplateSpec = None  # type: ignore
    HealthCheck = None  # type: ignore
    HealthChecker = None  # type: ignore
    HealthStatus = None  # type: ignore
    check_health = None  # type: ignore
    format_health_report = None  # type: ignore

# Embeddings - Optional, requires httpx for Ollama, openai for OpenAI
try:
    from paracle_meta.embeddings import (
        CachedEmbeddingProvider,
        EmbeddingCache,
        EmbeddingConfig,
        EmbeddingProvider,
        MockEmbeddings,
        OllamaEmbeddings,
        OpenAIEmbeddings,
        get_embedding_provider,
    )

    _HAS_EMBEDDINGS = True
except ImportError:
    _HAS_EMBEDDINGS = False
    CachedEmbeddingProvider = None  # type: ignore
    EmbeddingCache = None  # type: ignore
    EmbeddingConfig = None  # type: ignore
    EmbeddingProvider = None  # type: ignore
    MockEmbeddings = None  # type: ignore
    OllamaEmbeddings = None  # type: ignore
    OpenAIEmbeddings = None  # type: ignore
    get_embedding_provider = None  # type: ignore

# Configuration - Always available (uses pydantic)
from paracle_meta.config import MetaEngineConfig, load_config, validate_config

__version__ = "1.8.0"

__all__ = [
    # Core
    "MetaAgent",
    "GenerationRequest",
    "GenerationResult",
    # Learning
    "LearningEngine",
    "FeedbackCollector",
    # Providers
    "ProviderOrchestrator",
    "ProviderSelector",
    # Generators
    "AgentGenerator",
    "WorkflowGenerator",
    "SkillGenerator",
    "PolicyGenerator",
    # Optimization
    "CostOptimizer",
    "QualityScorer",
    # Templates & Knowledge
    "TemplateLibrary",
    "TemplateEvolution",
    "BestPracticesDatabase",
    # Capabilities
    "BaseCapability",
    "CapabilityConfig",
    "CapabilityResult",
    "WebCapability",
    "WebConfig",
    "CodeExecutionCapability",
    "CodeExecutionConfig",
    "MCPCapability",
    "MCPConfig",
    "TaskManagementCapability",
    "TaskConfig",
    "AgentSpawner",
    "SpawnConfig",
    "SpawnedAgent",
    # Hybrid capabilities
    "AnthropicCapability",
    "AnthropicConfig",
    "ClaudeModel",
    "ToolDefinition",
    "FileSystemCapability",
    "FileSystemConfig",
    "CodeCreationCapability",
    "CodeCreationConfig",
    "MemoryCapability",
    "MemoryConfig",
    "MemoryItem",
    "ShellCapability",
    "ShellConfig",
    # Provider abstraction (v1.4.0)
    "CapabilityProvider",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "LLMUsage",
    "ProviderError",
    "ProviderStatus",
    "StreamChunk",
    "ToolCallRequest",
    "ToolCallResult",
    "ToolDefinitionSchema",
    "CircuitBreaker",
    "FallbackStrategy",
    "ProviderChain",
    "ProviderChainError",
    "ProviderMetrics",
    "AnthropicProvider",
    "MockProvider",
    "OllamaProvider",
    "OpenAIProvider",
    # Registry (v1.4.0)
    "CapabilityFacade",
    "CapabilityRegistry",
    "CapabilityStatus",
    "RegistryConfig",
    # Sessions (v1.4.0)
    "ChatConfig",
    "ChatSession",
    "EditBatch",
    "EditConfig",
    "EditOperation",
    "EditSession",
    "EditStatus",
    "EditType",
    "Plan",
    "PlanConfig",
    "PlanSession",
    "PlanStep",
    "Session",
    "SessionConfig",
    "SessionMessage",
    # Database and repositories (v1.5.0)
    "MetaDatabase",
    "MetaDatabaseConfig",
    "get_meta_database",
    "get_system_data_path",
    "BestPractice",
    "BestPracticesRepository",
    "CostEntry",
    "CostReport",
    "CostRepository",
    "ContextRepository",
    "Feedback",
    "FeedbackRepository",
    "GenerationRepository",
    "RepoGenerationResult",
    "MemoryEntry",
    "MemoryRepository",
    "TemplateRepository",
    "TemplateSpec",
    # Embeddings (v1.5.0)
    "CachedEmbeddingProvider",
    "EmbeddingCache",
    "EmbeddingConfig",
    "EmbeddingProvider",
    "MockEmbeddings",
    "OllamaEmbeddings",
    "OpenAIEmbeddings",
    "get_embedding_provider",
    # Configuration (v1.5.0)
    "MetaEngineConfig",
    "load_config",
    "validate_config",
    # Health checks (v1.5.0)
    "HealthCheck",
    "HealthChecker",
    "HealthStatus",
    "check_health",
    "format_health_report",
    # Feature flags
    "_HAS_DATABASE",
    "_HAS_EMBEDDINGS",
]
