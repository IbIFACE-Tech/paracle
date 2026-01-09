"""Cost configuration management.

Loads cost settings from project.yaml and environment variables.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class BudgetConfig(BaseModel):
    """Budget limit configuration."""

    enabled: bool = Field(default=False, description="Enable budget enforcement")

    # Budget limits in USD
    daily_limit: float | None = Field(
        default=None, ge=0.0, description="Daily budget limit"
    )
    monthly_limit: float | None = Field(
        default=None, ge=0.0, description="Monthly budget limit"
    )
    workflow_limit: float | None = Field(
        default=None, ge=0.0, description="Per-workflow budget limit"
    )
    total_limit: float | None = Field(
        default=None, ge=0.0, description="Total budget limit"
    )

    # Alert thresholds (percentage of budget)
    warning_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Warning alert at this % of budget"
    )
    critical_threshold: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Critical alert at this % of budget"
    )

    # Actions
    block_on_exceed: bool = Field(
        default=False, description="Block execution when budget exceeded"
    )


class AlertConfig(BaseModel):
    """Alert configuration for cost events."""

    enabled: bool = Field(default=True, description="Enable cost alerts")

    # Alert channels
    log_alerts: bool = Field(default=True, description="Log alerts to console/file")
    webhook_url: str | None = Field(
        default=None, description="Webhook URL for alert notifications"
    )
    email: str | None = Field(default=None, description="Email for alert notifications")

    # Alert frequency
    min_interval_minutes: int = Field(
        default=15, ge=1, description="Minimum interval between alerts of same type"
    )


class TrackingConfig(BaseModel):
    """Cost tracking configuration."""

    enabled: bool = Field(default=True, description="Enable cost tracking")

    # Persistence
    persist_to_db: bool = Field(
        default=True, description="Persist cost records to database"
    )
    db_path: str | None = Field(
        default=None,
        description="Path to cost database. Relative paths are resolved from .parac/ directory (default: .parac/memory/data/costs.db)",
    )

    # Retention
    retention_days: int = Field(
        default=90, ge=1, description="Days to retain cost records"
    )

    # Aggregation
    aggregate_by_minute: bool = Field(
        default=False, description="Aggregate costs by minute for high-volume"
    )


class CostConfig(BaseModel):
    """Complete cost management configuration."""

    # Sub-configurations
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    alerts: AlertConfig = Field(default_factory=AlertConfig)

    # Default model pricing (fallback if not in provider catalog)
    # Prices are per million tokens in USD
    # Structure: {provider: {model: {input: price, output: price}}}
    default_pricing: dict[str, dict[str, dict[str, float]]] = Field(
        default_factory=lambda: {
            "openai": {
                "gpt-4": {"input": 30.0, "output": 60.0},
                "gpt-4-turbo": {"input": 10.0, "output": 30.0},
                "gpt-4o": {"input": 2.5, "output": 10.0},
                "gpt-4o-mini": {"input": 0.15, "output": 0.60},
                "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            },
            "anthropic": {
                "claude-3-opus": {"input": 15.0, "output": 75.0},
                "claude-3-sonnet": {"input": 3.0, "output": 15.0},
                "claude-3-haiku": {"input": 0.25, "output": 1.25},
                "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
            },
            "together": {
                "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo": {
                    "input": 3.5,
                    "output": 3.5,
                },
                "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": {
                    "input": 0.88,
                    "output": 0.88,
                },
            },
        }
    )

    # Cost display settings
    currency: str = Field(default="USD", description="Currency for display")
    decimal_places: int = Field(default=4, ge=0, le=8, description="Decimal places")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CostConfig":
        """Create config from dictionary.

        Args:
            data: Configuration dictionary (typically from project.yaml)

        Returns:
            CostConfig instance
        """
        return cls(**data)

    @classmethod
    def from_project_yaml(cls, project_path: Path | None = None) -> "CostConfig":
        """Load configuration from project.yaml.

        Args:
            project_path: Path to project.yaml or .parac/ directory

        Returns:
            CostConfig instance
        """
        # Find project.yaml
        if project_path is None:
            project_path = cls._find_project_yaml()
        elif project_path.is_dir():
            project_path = project_path / "project.yaml"

        if not project_path or not project_path.exists():
            return cls()  # Return defaults

        # Remember the .parac/ directory for relative path resolution
        parac_dir = project_path.parent

        with open(project_path) as f:
            data = yaml.safe_load(f) or {}

        cost_data = data.get("cost", {})

        # Resolve db_path relative to .parac/ directory if specified
        if "tracking" in cost_data and "db_path" in cost_data["tracking"]:
            db_path = cost_data["tracking"]["db_path"]
            if db_path and not Path(db_path).is_absolute():
                # Resolve relative paths relative to .parac/ directory
                cost_data["tracking"]["db_path"] = str(parac_dir / db_path)

        # Apply environment variable overrides
        cost_data = cls._apply_env_overrides(cost_data)

        return cls.from_dict(cost_data)

    @classmethod
    def from_env(cls) -> "CostConfig":
        """Load configuration from environment variables.

        Environment variables:
            PARACLE_COST_ENABLED: Enable cost tracking (true/false)
            PARACLE_COST_DAILY_LIMIT: Daily budget limit in USD
            PARACLE_COST_MONTHLY_LIMIT: Monthly budget limit in USD
            PARACLE_COST_WORKFLOW_LIMIT: Per-workflow limit in USD
            PARACLE_COST_BLOCK_ON_EXCEED: Block when budget exceeded (true/false)
            PARACLE_COST_WARNING_THRESHOLD: Warning threshold (0.0-1.0)
            PARACLE_COST_CRITICAL_THRESHOLD: Critical threshold (0.0-1.0)
            PARACLE_COST_WEBHOOK_URL: Webhook URL for alerts
            PARACLE_COST_DB_PATH: Path to cost database

        Returns:
            CostConfig instance
        """
        config_data: dict[str, Any] = {}

        # Tracking config
        tracking_enabled = os.getenv("PARACLE_COST_ENABLED", "").lower()
        if tracking_enabled:
            config_data.setdefault("tracking", {})["enabled"] = (
                tracking_enabled == "true"
            )

        db_path = os.getenv("PARACLE_COST_DB_PATH")
        if db_path:
            config_data.setdefault("tracking", {})["db_path"] = db_path

        # Budget config
        daily_limit = os.getenv("PARACLE_COST_DAILY_LIMIT")
        if daily_limit:
            config_data.setdefault("budget", {})["daily_limit"] = float(daily_limit)
            config_data.setdefault("budget", {})["enabled"] = True

        monthly_limit = os.getenv("PARACLE_COST_MONTHLY_LIMIT")
        if monthly_limit:
            config_data.setdefault("budget", {})["monthly_limit"] = float(monthly_limit)
            config_data.setdefault("budget", {})["enabled"] = True

        workflow_limit = os.getenv("PARACLE_COST_WORKFLOW_LIMIT")
        if workflow_limit:
            config_data.setdefault("budget", {})["workflow_limit"] = float(
                workflow_limit
            )

        block_on_exceed = os.getenv("PARACLE_COST_BLOCK_ON_EXCEED", "").lower()
        if block_on_exceed:
            config_data.setdefault("budget", {})["block_on_exceed"] = (
                block_on_exceed == "true"
            )

        warning_threshold = os.getenv("PARACLE_COST_WARNING_THRESHOLD")
        if warning_threshold:
            config_data.setdefault("budget", {})["warning_threshold"] = float(
                warning_threshold
            )

        critical_threshold = os.getenv("PARACLE_COST_CRITICAL_THRESHOLD")
        if critical_threshold:
            config_data.setdefault("budget", {})["critical_threshold"] = float(
                critical_threshold
            )

        # Alert config
        webhook_url = os.getenv("PARACLE_COST_WEBHOOK_URL")
        if webhook_url:
            config_data.setdefault("alerts", {})["webhook_url"] = webhook_url

        return cls.from_dict(config_data)

    @classmethod
    def _find_project_yaml(cls) -> Path | None:
        """Find project.yaml by searching upward from cwd."""
        current = Path.cwd()
        for parent in [current, *current.parents]:
            parac_dir = parent / ".parac"
            if parac_dir.is_dir():
                project_yaml = parac_dir / "project.yaml"
                if project_yaml.exists():
                    return project_yaml
        return None

    @classmethod
    def _apply_env_overrides(cls, config_data: dict[str, Any]) -> dict[str, Any]:
        """Apply environment variable overrides to config data."""
        env_config = cls.from_env()
        env_dict = env_config.model_dump()

        # Deep merge env overrides into config_data
        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                elif value is not None:
                    # Only override if value is not None/default
                    result[key] = value
            return result

        return deep_merge(config_data, env_dict)

    def get_model_pricing(
        self, provider: str, model: str
    ) -> tuple[float, float] | None:
        """Get pricing for a specific model.

        Args:
            provider: Provider name (e.g., "openai")
            model: Model name (e.g., "gpt-4")

        Returns:
            Tuple of (input_cost_per_million, output_cost_per_million) or None
        """
        provider_pricing = self.default_pricing.get(provider, {})

        # Try exact match first
        if model in provider_pricing:
            pricing = provider_pricing[model]
            return (pricing["input"], pricing["output"])

        # Try prefix match for model variants
        for model_name, pricing in provider_pricing.items():
            if model.startswith(model_name) or model_name.startswith(model):
                return (pricing["input"], pricing["output"])

        return None
