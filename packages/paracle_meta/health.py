"""Health check utilities for paracle_meta.

Provides comprehensive health monitoring for:
- Database connectivity
- Provider availability
- Learning engine status
- Cost budget status
- System resources

Usage:
    from paracle_meta.health import HealthChecker, check_health

    # Quick health check
    result = await check_health()
    print(result.status)  # "healthy", "degraded", "unhealthy"

    # Detailed check
    checker = HealthChecker(config)
    result = await checker.full_check()
    print(result.model_dump_json(indent=2))
"""

from __future__ import annotations

import time
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

import httpx
from paracle_core.logging import get_logger
from pydantic import BaseModel, Field
from sqlalchemy import text

if TYPE_CHECKING:
    from paracle_meta.config import MetaEngineConfig
    from paracle_meta.database import MetaDatabase

logger = get_logger(__name__)

# Module start time for uptime tracking
_start_time = time.time()


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a single component."""

    name: str
    status: HealthStatus
    message: str | None = None
    latency_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class HealthCheck(BaseModel):
    """Complete health check result."""

    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.8.0"
    uptime_seconds: float = Field(default_factory=lambda: time.time() - _start_time)

    # Component statuses
    database: ComponentHealth
    providers: dict[str, ComponentHealth] = Field(default_factory=dict)
    learning_engine: ComponentHealth | None = None
    cost_tracker: ComponentHealth | None = None

    # Summary metrics
    total_components: int = 0
    healthy_components: int = 0
    degraded_components: int = 0
    unhealthy_components: int = 0

    def compute_summary(self) -> None:
        """Compute summary metrics from component statuses."""
        components = [self.database]

        if self.learning_engine:
            components.append(self.learning_engine)
        if self.cost_tracker:
            components.append(self.cost_tracker)

        components.extend(self.providers.values())

        self.total_components = len(components)
        self.healthy_components = sum(
            1 for c in components if c.status == HealthStatus.HEALTHY
        )
        self.degraded_components = sum(
            1 for c in components if c.status == HealthStatus.DEGRADED
        )
        self.unhealthy_components = sum(
            1 for c in components if c.status == HealthStatus.UNHEALTHY
        )

        # Overall status is the worst of all components
        if self.unhealthy_components > 0:
            self.status = HealthStatus.UNHEALTHY
        elif self.degraded_components > 0:
            self.status = HealthStatus.DEGRADED
        else:
            self.status = HealthStatus.HEALTHY


class HealthChecker:
    """Health checker for paracle_meta components."""

    def __init__(
        self,
        config: MetaEngineConfig | None = None,
        db: MetaDatabase | None = None,
    ) -> None:
        """Initialize health checker.

        Args:
            config: Meta engine configuration.
            db: Database instance.
        """
        self._config = config
        self._db = db

    async def full_check(self) -> HealthCheck:
        """Perform full health check of all components.

        Returns:
            Complete health check result.
        """
        # Check database
        db_health = await self._check_database()

        # Check providers
        provider_health = await self._check_providers()

        # Check learning engine
        learning_health = await self._check_learning_engine()

        # Check cost tracker
        cost_health = await self._check_cost_tracker()

        # Build result
        result = HealthCheck(
            status=HealthStatus.HEALTHY,  # Will be computed
            database=db_health,
            providers=provider_health,
            learning_engine=learning_health,
            cost_tracker=cost_health,
        )

        result.compute_summary()
        return result

    async def quick_check(self) -> HealthStatus:
        """Perform quick health check (database only).

        Returns:
            Overall health status.
        """
        db_health = await self._check_database()
        return db_health.status

    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        start = time.time()

        try:
            if self._db is None:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="Database not configured",
                )

            # Try to connect
            if not self._db.is_connected:
                self._db.connect()

            # Execute simple query
            with self._db.session() as session:
                session.execute(text("SELECT 1"))

            latency = (time.time() - start) * 1000

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Connected",
                latency_ms=round(latency, 2),
                details={
                    "backend": "postgresql" if self._db.is_postgres else "sqlite",
                    "vectors_enabled": self._db.has_vectors,
                },
            )

        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.error(f"Database health check failed: {e}")

            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=round(latency, 2),
            )

    async def _check_providers(self) -> dict[str, ComponentHealth]:
        """Check LLM provider availability."""
        results: dict[str, ComponentHealth] = {}

        if self._config is None:
            return results

        for provider_config in self._config.providers:
            health = await self._check_single_provider(provider_config.name)
            results[provider_config.name] = health

        # Also check default provider if not in list
        if self._config.default_provider not in results:
            health = await self._check_single_provider(self._config.default_provider)
            results[self._config.default_provider] = health

        return results

    async def _check_single_provider(self, provider_name: str) -> ComponentHealth:
        """Check a single provider's availability."""
        start = time.time()

        try:
            if provider_name == "ollama":
                # Check Ollama server
                health = await self._check_ollama()
            elif provider_name in ("openai", "anthropic", "azure", "groq", "mistral"):
                # For cloud providers, check if API key is configured
                health = self._check_cloud_provider(provider_name)
            else:
                health = ComponentHealth(
                    name=provider_name,
                    status=HealthStatus.DEGRADED,
                    message="Unknown provider",
                )

            health.latency_ms = round((time.time() - start) * 1000, 2)
            return health

        except Exception as e:
            return ComponentHealth(
                name=provider_name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=round((time.time() - start) * 1000, 2),
            )

    async def _check_ollama(self) -> ComponentHealth:
        """Check Ollama server availability."""
        base_url = "http://localhost:11434"

        if self._config:
            provider = self._config.get_provider_config("ollama")
            if provider and provider.base_url:
                base_url = provider.base_url

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]

                    return ComponentHealth(
                        name="ollama",
                        status=HealthStatus.HEALTHY,
                        message=f"Running with {len(models)} models",
                        details={"models": models[:5]},  # First 5 models
                    )
                else:
                    return ComponentHealth(
                        name="ollama",
                        status=HealthStatus.UNHEALTHY,
                        message=f"HTTP {response.status_code}",
                    )

        except httpx.ConnectError:
            return ComponentHealth(
                name="ollama",
                status=HealthStatus.UNHEALTHY,
                message="Connection refused - is Ollama running?",
            )
        except Exception as e:
            return ComponentHealth(
                name="ollama",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )

    def _check_cloud_provider(self, provider_name: str) -> ComponentHealth:
        """Check cloud provider configuration."""
        import os

        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "mistral": "MISTRAL_API_KEY",
        }

        env_var = env_var_map.get(provider_name)

        # Check config first
        if self._config:
            provider = self._config.get_provider_config(provider_name)
            if provider and provider.api_key:
                return ComponentHealth(
                    name=provider_name,
                    status=HealthStatus.HEALTHY,
                    message="API key configured",
                )

        # Check environment variable
        if env_var and os.environ.get(env_var):
            return ComponentHealth(
                name=provider_name,
                status=HealthStatus.HEALTHY,
                message=f"API key from {env_var}",
            )

        return ComponentHealth(
            name=provider_name,
            status=HealthStatus.DEGRADED,
            message=f"No API key (set {env_var})",
        )

    async def _check_learning_engine(self) -> ComponentHealth | None:
        """Check learning engine status."""
        if self._config is None:
            return None

        if not self._config.learning.enabled:
            return ComponentHealth(
                name="learning_engine",
                status=HealthStatus.HEALTHY,
                message="Disabled by configuration",
            )

        try:
            from paracle_meta.learning import LearningEngine

            # Create engine to check database
            if self._db:
                engine = LearningEngine.with_repositories(
                    self._db,
                    enabled=True,
                )
                return ComponentHealth(
                    name="learning_engine",
                    status=HealthStatus.HEALTHY,
                    message="Repository mode",
                    details={"mode": "repositories"},
                )
            else:
                # Legacy mode
                engine = LearningEngine(enabled=True)
                return ComponentHealth(
                    name="learning_engine",
                    status=HealthStatus.HEALTHY,
                    message="Legacy SQLite mode",
                    details={"mode": "sqlite"},
                )

        except Exception as e:
            return ComponentHealth(
                name="learning_engine",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )

    async def _check_cost_tracker(self) -> ComponentHealth | None:
        """Check cost tracking status."""
        if self._config is None:
            return None

        if not self._config.cost.enabled:
            return ComponentHealth(
                name="cost_tracker",
                status=HealthStatus.HEALTHY,
                message="Disabled by configuration",
            )

        try:
            if self._db:
                from paracle_meta.repositories import CostRepository

                repo = CostRepository(self._db)
                daily_cost = repo.get_period_cost("1d")
                monthly_cost = repo.get_period_cost("30d")

                # Check against limits
                daily_pct = daily_cost / self._config.cost.max_daily_budget * 100
                monthly_pct = monthly_cost / self._config.cost.max_monthly_budget * 100

                status = HealthStatus.HEALTHY
                message = "Within budget"

                if daily_pct >= 100 or monthly_pct >= 100:
                    status = HealthStatus.UNHEALTHY
                    message = "Budget exceeded!"
                elif daily_pct >= self._config.cost.warning_threshold * 100:
                    status = HealthStatus.DEGRADED
                    message = f"Approaching daily limit ({daily_pct:.0f}%)"
                elif monthly_pct >= self._config.cost.warning_threshold * 100:
                    status = HealthStatus.DEGRADED
                    message = f"Approaching monthly limit ({monthly_pct:.0f}%)"

                return ComponentHealth(
                    name="cost_tracker",
                    status=status,
                    message=message,
                    details={
                        "daily_cost": round(daily_cost, 2),
                        "daily_limit": self._config.cost.max_daily_budget,
                        "daily_pct": round(daily_pct, 1),
                        "monthly_cost": round(monthly_cost, 2),
                        "monthly_limit": self._config.cost.max_monthly_budget,
                        "monthly_pct": round(monthly_pct, 1),
                    },
                )
            else:
                return ComponentHealth(
                    name="cost_tracker",
                    status=HealthStatus.DEGRADED,
                    message="Database not available",
                )

        except Exception as e:
            return ComponentHealth(
                name="cost_tracker",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )


async def check_health(
    config: MetaEngineConfig | None = None,
    db: MetaDatabase | None = None,
) -> HealthCheck:
    """Quick health check function.

    Args:
        config: Optional configuration.
        db: Optional database instance.

    Returns:
        Health check result.
    """
    checker = HealthChecker(config, db)
    return await checker.full_check()


def format_health_report(health: HealthCheck) -> str:
    """Format health check result for display.

    Args:
        health: Health check result.

    Returns:
        Formatted string for CLI output.
    """
    lines = []

    # Header - use ASCII-safe symbols for Windows compatibility
    status_emoji = {
        HealthStatus.HEALTHY: "[OK]",
        HealthStatus.DEGRADED: "[!]",
        HealthStatus.UNHEALTHY: "[X]",
    }

    lines.append(
        f"Paracle Meta Health: {status_emoji[health.status]} {health.status.value.upper()}"
    )
    lines.append(f"Version: {health.version}")
    lines.append(f"Uptime: {health.uptime_seconds:.0f}s")
    lines.append("")

    # Components
    lines.append("Components:")
    lines.append(f"  Total: {health.total_components}")
    lines.append(f"  Healthy: {health.healthy_components}")
    if health.degraded_components > 0:
        lines.append(f"  Degraded: {health.degraded_components}")
    if health.unhealthy_components > 0:
        lines.append(f"  Unhealthy: {health.unhealthy_components}")
    lines.append("")

    # Database
    lines.append(
        f"Database: {status_emoji[health.database.status]} {health.database.status.value}"
    )
    if health.database.message:
        lines.append(f"  {health.database.message}")
    if health.database.latency_ms:
        lines.append(f"  Latency: {health.database.latency_ms}ms")
    if health.database.details:
        for key, value in health.database.details.items():
            lines.append(f"  {key}: {value}")
    lines.append("")

    # Providers
    if health.providers:
        lines.append("Providers:")
        for name, provider_health in health.providers.items():
            lines.append(
                f"  {name}: {status_emoji[provider_health.status]} {provider_health.status.value}"
            )
            if provider_health.message:
                lines.append(f"    {provider_health.message}")
        lines.append("")

    # Learning Engine
    if health.learning_engine:
        lines.append(
            f"Learning Engine: {status_emoji[health.learning_engine.status]} {health.learning_engine.status.value}"
        )
        if health.learning_engine.message:
            lines.append(f"  {health.learning_engine.message}")
        lines.append("")

    # Cost Tracker
    if health.cost_tracker:
        lines.append(
            f"Cost Tracker: {status_emoji[health.cost_tracker.status]} {health.cost_tracker.status.value}"
        )
        if health.cost_tracker.message:
            lines.append(f"  {health.cost_tracker.message}")
        if health.cost_tracker.details:
            daily = health.cost_tracker.details.get("daily_cost", 0)
            daily_limit = health.cost_tracker.details.get("daily_limit", 0)
            monthly = health.cost_tracker.details.get("monthly_cost", 0)
            monthly_limit = health.cost_tracker.details.get("monthly_limit", 0)
            lines.append(f"  Daily: ${daily:.2f} / ${daily_limit:.2f}")
            lines.append(f"  Monthly: ${monthly:.2f} / ${monthly_limit:.2f}")

    return "\n".join(lines)
