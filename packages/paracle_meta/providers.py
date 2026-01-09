"""Multi-Provider Orchestration for Paracle Meta-Agent.

Supports intelligent provider selection based on:
- Task type (agents, workflows, code, etc.)
- Cost optimization
- Provider availability
- Performance history
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from paracle_core.logging import get_logger
from pydantic import BaseModel, Field

from paracle_meta.exceptions import ProviderNotAvailableError, ProviderSelectionError

logger = get_logger(__name__)


class TaskType(str, Enum):
    """Types of generation tasks."""

    AGENT = "agent"
    WORKFLOW = "workflow"
    SKILL = "skill"
    POLICY = "policy"
    CODE = "code"
    SECURITY = "security"
    ANALYSIS = "analysis"
    SIMPLE = "simple"
    COMPLEX = "complex"


class ProviderConfig(BaseModel):
    """Configuration for a single provider."""

    name: str = Field(..., description="Provider name (openai, anthropic, etc.)")
    model: str = Field(..., description="Model name")
    api_key_env: str | None = Field(
        None, description="Environment variable for API key"
    )
    endpoint: str | None = Field(None, description="Custom endpoint URL")
    use_for: list[str] = Field(
        default_factory=list, description="Task types this provider is suited for"
    )
    priority: int = Field(default=10, description="Priority (lower = preferred)")
    cost_per_1k_tokens: float = Field(
        default=0.01, description="Cost per 1000 tokens in USD"
    )
    max_tokens: int = Field(default=4096, description="Maximum tokens")
    enabled: bool = Field(default=True, description="Whether provider is enabled")


@dataclass
class ProviderSelection:
    """Result of provider selection."""

    provider: str
    model: str
    priority: int
    cost_per_1k: float
    reason: str


class PerformanceMetrics(BaseModel):
    """Performance metrics for a provider."""

    provider: str
    model: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_quality_score: float = 0.0
    avg_latency_ms: float = 0.0
    last_used: datetime | None = None


class ProviderOrchestrator:
    """Orchestrates multiple LLM providers.

    Handles:
    - Provider configuration loading
    - Provider selection based on task type
    - Automatic fallback on failure
    - Performance tracking

    Example:
        >>> orchestrator = ProviderOrchestrator()
        >>> provider = orchestrator.select_provider(task_type="agent")
        >>> print(f"Using {provider.provider}/{provider.model}")
    """

    def __init__(
        self,
        providers: list[str] | None = None,
        config_path: Path | None = None,
    ):
        """Initialize provider orchestrator.

        Args:
            providers: List of provider names to use (None = all configured)
            config_path: Path to meta_agent.yaml config
        """
        self.config_path = config_path or self._default_config_path()
        self._providers: dict[str, ProviderConfig] = {}
        self._performance: dict[str, PerformanceMetrics] = {}
        self._filter_providers = providers

        self._load_config()
        logger.info(
            "ProviderOrchestrator initialized",
            extra={"providers": list(self._providers.keys())},
        )

    @property
    def available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return [name for name, cfg in self._providers.items() if cfg.enabled]

    def select_provider(
        self,
        task_type: str | TaskType = TaskType.SIMPLE,
        complexity: float = 0.5,
        require_local: bool = False,
        max_cost: float | None = None,
    ) -> ProviderSelection:
        """Select best provider for a task.

        Args:
            task_type: Type of task (agent, workflow, etc.)
            complexity: Task complexity 0.0-1.0
            require_local: If True, only use local providers (Ollama)
            max_cost: Maximum cost per request (None = no limit)

        Returns:
            ProviderSelection with provider details

        Raises:
            ProviderSelectionError: If no suitable provider found
        """
        if isinstance(task_type, TaskType):
            task_type = task_type.value

        candidates = self._get_candidates(task_type, require_local, max_cost)

        if not candidates:
            raise ProviderSelectionError(
                reason="No providers available",
                task_type=task_type,
            )

        # Sort by: use_for match > priority > performance
        best = self._rank_candidates(candidates, task_type, complexity)

        return ProviderSelection(
            provider=best.name,
            model=best.model,
            priority=best.priority,
            cost_per_1k=best.cost_per_1k_tokens,
            reason=f"Best match for {task_type} (priority {best.priority})",
        )

    def get_provider_config(self, provider: str) -> ProviderConfig:
        """Get configuration for a specific provider.

        Args:
            provider: Provider name

        Returns:
            ProviderConfig

        Raises:
            ProviderNotAvailableError: If provider not found
        """
        if provider not in self._providers:
            raise ProviderNotAvailableError(
                provider=provider,
                reason="Not configured",
                available_providers=self.available_providers,
            )

        config = self._providers[provider]
        if not config.enabled:
            raise ProviderNotAvailableError(
                provider=provider,
                reason="Provider is disabled",
                available_providers=self.available_providers,
            )

        return config

    def record_request(
        self,
        provider: str,
        model: str,
        tokens: int,
        cost: float,
        quality_score: float,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        """Record a request for performance tracking.

        Args:
            provider: Provider name
            model: Model used
            tokens: Total tokens used
            cost: Cost in USD
            quality_score: Quality score 0-10
            latency_ms: Latency in milliseconds
            success: Whether request was successful
        """
        key = f"{provider}/{model}"

        if key not in self._performance:
            self._performance[key] = PerformanceMetrics(provider=provider, model=model)

        metrics = self._performance[key]
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        metrics.total_tokens += tokens
        metrics.total_cost += cost
        metrics.last_used = datetime.now()

        # Update moving average for quality and latency
        n = metrics.successful_requests
        if n > 0:
            metrics.avg_quality_score = (
                (metrics.avg_quality_score * (n - 1)) + quality_score
            ) / n
            metrics.avg_latency_ms = (
                (metrics.avg_latency_ms * (n - 1)) + latency_ms
            ) / n

    async def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics for all providers.

        Returns:
            Dictionary with performance metrics per provider
        """
        return {
            key: {
                "provider": m.provider,
                "model": m.model,
                "total_requests": m.total_requests,
                "success_rate": (
                    m.successful_requests / m.total_requests
                    if m.total_requests > 0
                    else 0
                ),
                "avg_quality": round(m.avg_quality_score, 2),
                "avg_latency_ms": round(m.avg_latency_ms, 1),
                "total_cost": round(m.total_cost, 4),
            }
            for key, m in self._performance.items()
        }

    def _get_candidates(
        self,
        task_type: str,
        require_local: bool,
        max_cost: float | None,
    ) -> list[ProviderConfig]:
        """Get candidate providers for a task."""
        candidates = []

        for name, config in self._providers.items():
            # Skip disabled
            if not config.enabled:
                continue

            # Skip filtered
            if self._filter_providers and name not in self._filter_providers:
                continue

            # Check local requirement
            if require_local and name != "ollama":
                continue

            # Check cost limit
            if max_cost is not None and config.cost_per_1k_tokens > max_cost:
                continue

            candidates.append(config)

        return candidates

    def _rank_candidates(
        self,
        candidates: list[ProviderConfig],
        task_type: str,
        complexity: float,
    ) -> ProviderConfig:
        """Rank candidates and return best one."""

        def score(config: ProviderConfig) -> tuple[int, int, float]:
            # Primary: task type match (0 if matches, 1 if not)
            type_match = 0 if task_type in config.use_for else 1

            # Secondary: priority
            priority = config.priority

            # Tertiary: cost (prefer cheaper for simple tasks)
            if complexity < 0.3:
                cost_factor = config.cost_per_1k_tokens * 10
            else:
                cost_factor = config.cost_per_1k_tokens

            return (type_match, priority, cost_factor)

        candidates.sort(key=score)
        return candidates[0]

    def _load_config(self) -> None:
        """Load provider configuration from file."""
        if not self.config_path.exists():
            self._load_defaults()
            return

        try:
            with open(self.config_path) as f:
                data = yaml.safe_load(f) or {}

            meta_agent = data.get("meta_agent", {})
            providers_data = meta_agent.get("providers", [])

            for pdata in providers_data:
                config = ProviderConfig(**pdata)
                self._providers[config.name] = config

            if not self._providers:
                self._load_defaults()

        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default provider configurations."""
        defaults = [
            ProviderConfig(
                name="anthropic",
                model="claude-sonnet-4-20250514",
                api_key_env="ANTHROPIC_API_KEY",
                use_for=["agent", "security", "code", "complex"],
                priority=1,
                cost_per_1k_tokens=0.003,
            ),
            ProviderConfig(
                name="openai",
                model="gpt-4o",
                api_key_env="OPENAI_API_KEY",
                use_for=["workflow", "analysis", "complex"],
                priority=2,
                cost_per_1k_tokens=0.0025,
            ),
            ProviderConfig(
                name="google",
                model="gemini-1.5-pro",
                api_key_env="GOOGLE_API_KEY",
                use_for=["analysis", "simple"],
                priority=3,
                cost_per_1k_tokens=0.00125,
            ),
            ProviderConfig(
                name="ollama",
                model="llama3.2",
                endpoint="http://localhost:11434",
                use_for=["simple", "local"],
                priority=4,
                cost_per_1k_tokens=0.0,  # Free
            ),
        ]

        for config in defaults:
            self._providers[config.name] = config

        logger.debug("Loaded default provider configurations")

    def _default_config_path(self) -> Path:
        """Get default config path."""
        return Path.cwd() / ".parac" / "config" / "meta_agent.yaml"


class ProviderSelector:
    """Helper class for provider selection logic.

    Implements intelligent selection based on:
    - Task type affinity
    - Historical performance
    - Cost optimization
    - Availability
    """

    # Task type to provider affinity mapping
    AFFINITY_MAP: dict[str, list[str]] = {
        "agent": ["anthropic", "openai"],
        "workflow": ["openai", "anthropic"],
        "skill": ["anthropic", "openai"],
        "policy": ["anthropic", "openai"],
        "code": ["anthropic", "openai"],
        "security": ["anthropic"],
        "analysis": ["openai", "google"],
        "simple": ["ollama", "google"],
        "complex": ["anthropic", "openai"],
    }

    def __init__(self, orchestrator: ProviderOrchestrator):
        """Initialize provider selector.

        Args:
            orchestrator: ProviderOrchestrator instance
        """
        self.orchestrator = orchestrator

    def select_for_task(
        self,
        task_type: str,
        complexity: float = 0.5,
        budget_remaining: float | None = None,
    ) -> ProviderSelection:
        """Select provider based on task requirements.

        Args:
            task_type: Type of task
            complexity: Task complexity 0.0-1.0
            budget_remaining: Remaining budget (None = no limit)

        Returns:
            ProviderSelection
        """
        # Calculate max cost based on budget
        max_cost = None
        if budget_remaining is not None:
            # Allow up to 10% of remaining budget per request
            max_cost = budget_remaining * 0.1

        return self.orchestrator.select_provider(
            task_type=task_type,
            complexity=complexity,
            max_cost=max_cost,
        )

    def get_fallback_chain(self, task_type: str) -> list[str]:
        """Get fallback provider chain for a task type.

        Args:
            task_type: Type of task

        Returns:
            List of provider names in fallback order
        """
        # Get affinity providers first
        affinity = self.AFFINITY_MAP.get(task_type, [])
        available = set(self.orchestrator.available_providers)

        # Build chain: affinity providers that are available, then others
        chain = [p for p in affinity if p in available]
        chain.extend([p for p in available if p not in chain])

        return chain


__all__ = [
    "TaskType",
    "ProviderConfig",
    "ProviderSelection",
    "PerformanceMetrics",
    "ProviderOrchestrator",
    "ProviderSelector",
]
