"""File management configuration models.

Configurable paths and settings for logs, ADRs, and roadmaps.
Loaded from project.yaml file_management section.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# LOG CONFIGURATION MODELS
# =============================================================================


class LogGlobalConfig(BaseModel):
    """Global log settings applied to all log files."""

    # Line/entry limits
    max_line_length: int = 2000
    max_message_length: int = 1000
    max_description_length: int = 500
    max_file_size_mb: int = 100
    max_total_size_mb: int = 1000

    # Timestamp settings
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    timezone: str = "UTC"

    # Rotation settings (defaults)
    default_rotation: Literal["none", "daily", "weekly", "monthly", "size"] = "none"
    default_retention_days: int | None = None
    compress_rotated: bool = True
    backup_count: int = 10

    # Performance
    buffer_size: int = 8192
    flush_interval_seconds: int = 5
    async_logging: bool = True


class LogFileConfig(BaseModel):
    """Configuration for a single log file."""

    enabled: bool = True
    path: str
    format: str = "[{timestamp}] {message}"
    description: str = ""

    # Limits
    max_entries: int | None = None
    max_file_size_mb: int | None = None
    max_line_length: int | None = None

    # Rotation
    rotation: Literal["none", "daily", "weekly", "monthly", "size"] = "none"
    retention_days: int | None = None
    compress_rotated: bool | None = None

    # Fields
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)

    # Type-specific settings
    include_stack_trace: bool = False
    redact_sensitive: bool = False
    sample_rate: float = 1.0
    include_percentiles: bool = False
    min_level: str | None = None


class PredefinedLogsConfig(BaseModel):
    """Pre-defined log categories."""

    actions: LogFileConfig = Field(
        default_factory=lambda: LogFileConfig(
            enabled=True,
            path="agent_actions.log",
            format="[{timestamp}] [{agent}] [{action}] {description}",
            description="Agent actions and activities",
            required_fields=["timestamp", "agent", "action", "description"],
            optional_fields=["details", "context", "duration_ms"],
        )
    )
    decisions: LogFileConfig = Field(
        default_factory=lambda: LogFileConfig(
            enabled=True,
            path="decisions.log",
            format="[{timestamp}] [{agent}] [DECISION] {decision} | {rationale} | {impact}",
            description="Important decisions made by agents",
            required_fields=["timestamp", "agent", "decision"],
            optional_fields=["rationale", "impact", "alternatives", "references"],
        )
    )
    security: LogFileConfig = Field(
        default_factory=lambda: LogFileConfig(
            enabled=False,
            path="security/security.log",
            format="structured_json",
            description="Security events and audit trail",
            rotation="daily",
            retention_days=365,
            required_fields=["timestamp", "level", "event_type", "actor"],
            optional_fields=[
                "resource",
                "action",
                "outcome",
                "ip_address",
                "user_agent",
            ],
            redact_sensitive=True,
        )
    )
    performance: LogFileConfig = Field(
        default_factory=lambda: LogFileConfig(
            enabled=False,
            path="performance/metrics.log",
            format="structured_json",
            description="Performance metrics and timing data",
            rotation="daily",
            retention_days=30,
            required_fields=["timestamp", "metric_name", "value"],
            optional_fields=["unit", "tags", "percentiles", "histogram"],
            include_percentiles=True,
        )
    )
    risk: LogFileConfig = Field(
        default_factory=lambda: LogFileConfig(
            enabled=False,
            path="risk/risk_log.log",
            format="[{timestamp}] [{level}] [{category}] {message}",
            description="Risk assessments and warnings",
            rotation="daily",
            retention_days=90,
            required_fields=["timestamp", "level", "message"],
            optional_fields=["category", "severity", "mitigation", "owner"],
            min_level="LOW",
        )
    )
    errors: LogFileConfig = Field(
        default_factory=lambda: LogFileConfig(
            enabled=True,
            path="errors/error.log",
            format="structured_json",
            description="Error and exception logging",
            rotation="daily",
            retention_days=90,
            required_fields=["timestamp", "level", "message", "error_type"],
            optional_fields=["stack_trace", "context", "request_id", "user_id"],
            include_stack_trace=True,
        )
    )


class CustomLogConfig(BaseModel):
    """Configuration for a custom log file."""

    name: str
    path: str
    format: str = "[{timestamp}] {message}"
    description: str = ""
    enabled: bool = True

    # Limits
    max_file_size_mb: int | None = None
    max_line_length: int | None = None
    max_entries: int | None = None

    # Rotation
    rotation: Literal["none", "daily", "weekly", "monthly", "size"] = "none"
    retention_days: int | None = None
    compress_rotated: bool = True

    # Fields
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)


class LogsConfig(BaseModel):
    """Log management configuration."""

    base_path: str = "memory/logs"
    global_config: LogGlobalConfig = Field(
        default_factory=LogGlobalConfig, alias="global"
    )
    predefined: PredefinedLogsConfig = Field(default_factory=PredefinedLogsConfig)
    custom: list[CustomLogConfig] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# ADR CONFIGURATION MODELS
# =============================================================================


class ADRLimitsConfig(BaseModel):
    """Content limits for ADRs."""

    max_title_length: int = 200
    max_context_length: int = 5000
    max_decision_length: int = 3000
    max_consequences_length: int = 3000
    max_implementation_length: int = 5000
    max_related_length: int = 1000
    max_total_length: int = 20000
    max_adrs: int | None = None


class ADRStatusConfig(BaseModel):
    """Configuration for an ADR status."""

    name: str
    description: str = ""
    color: str = "white"
    transitions: list[str] = Field(default_factory=list)


class ADRDefaultsConfig(BaseModel):
    """Default values for ADR fields."""

    deciders: str = "Core Team"
    implementation: str = "TBD"
    related: str = "None"


class ADRValidationConfig(BaseModel):
    """Validation rules for ADRs."""

    require_context: bool = True
    require_decision: bool = True
    require_consequences: bool = True
    require_deciders: bool = False
    validate_links: bool = True
    warn_empty_sections: bool = True


class ADRConfig(BaseModel):
    """ADR (Architecture Decision Records) management configuration."""

    base_path: str = "roadmap/adr"
    enabled: bool = True
    format: Literal["markdown", "yaml"] = "markdown"

    # File settings
    index_file: str = "index.md"
    file_extension: str = ".md"
    encoding: str = "utf-8"

    # Content limits
    limits: ADRLimitsConfig = Field(default_factory=ADRLimitsConfig)

    # Auto-numbering
    auto_number: bool = True
    number_format: str = "ADR-{:03d}"
    number_start: int = 1
    number_padding: int = 3

    # Status management
    statuses: list[ADRStatusConfig] = Field(
        default_factory=lambda: [
            ADRStatusConfig(
                name="Proposed",
                description="Under discussion, not yet decided",
                color="yellow",
                transitions=["Accepted", "Rejected", "Withdrawn"],
            ),
            ADRStatusConfig(
                name="Accepted",
                description="Approved and should be followed",
                color="green",
                transitions=["Deprecated", "Superseded"],
            ),
            ADRStatusConfig(
                name="Deprecated",
                description="No longer valid, kept for history",
                color="gray",
                transitions=[],
            ),
            ADRStatusConfig(
                name="Superseded",
                description="Replaced by another ADR",
                color="blue",
                transitions=[],
            ),
            ADRStatusConfig(
                name="Rejected",
                description="Considered but not accepted",
                color="red",
                transitions=[],
            ),
            ADRStatusConfig(
                name="Withdrawn",
                description="Withdrawn before decision",
                color="gray",
                transitions=[],
            ),
        ]
    )
    default_status: str = "Proposed"

    # Default values
    defaults: ADRDefaultsConfig = Field(default_factory=ADRDefaultsConfig)

    # Templates
    template: str = Field(
        default="""# {id}: {title}

**Date**: {date}
**Status**: {status}
**Deciders**: {deciders}

## Context

{context}

## Decision

{decision}

## Consequences

{consequences}

## Implementation

{implementation}

## Related Decisions

{related}
"""
    )
    index_template: str | None = None

    # Migration settings
    legacy_file: str | None = "roadmap/decisions.md"
    migrate_on_init: bool = False
    backup_before_migrate: bool = True

    # Validation
    validation: ADRValidationConfig = Field(default_factory=ADRValidationConfig)


# =============================================================================
# ROADMAP CONFIGURATION MODELS
# =============================================================================


class RoadmapLimitsConfig(BaseModel):
    """Content limits for roadmaps."""

    max_phase_name_length: int = 100
    max_phase_description_length: int = 2000
    max_deliverable_name_length: int = 200
    max_phases: int = 50
    max_deliverables_per_phase: int = 100
    max_roadmaps: int = 20


class PhaseStatusConfig(BaseModel):
    """Configuration for a phase status."""

    name: str
    description: str = ""
    color: str = "white"


class PhaseProgressConfig(BaseModel):
    """Progress tracking configuration for phases."""

    min: int = 0
    max: int = 100
    unit: str = "%"
    auto_calculate: bool = False


class PhasesConfig(BaseModel):
    """Phase configuration for roadmaps."""

    statuses: list[PhaseStatusConfig] = Field(
        default_factory=lambda: [
            PhaseStatusConfig(
                name="pending", description="Not yet started", color="gray"
            ),
            PhaseStatusConfig(
                name="in_progress",
                description="Currently being worked on",
                color="yellow",
            ),
            PhaseStatusConfig(
                name="completed", description="Successfully finished", color="green"
            ),
            PhaseStatusConfig(
                name="blocked",
                description="Cannot proceed due to blockers",
                color="red",
            ),
            PhaseStatusConfig(
                name="on_hold", description="Temporarily paused", color="orange"
            ),
            PhaseStatusConfig(
                name="cancelled", description="Will not be completed", color="gray"
            ),
        ]
    )
    default_status: str = "pending"
    progress: PhaseProgressConfig = Field(default_factory=PhaseProgressConfig)


class DeliverablesConfig(BaseModel):
    """Deliverable configuration for roadmaps."""

    statuses: list[str] = Field(
        default_factory=lambda: [
            "pending",
            "in_progress",
            "completed",
            "blocked",
            "cancelled",
        ]
    )
    default_status: str = "pending"
    track_completion_date: bool = True
    require_owner: bool = False


class RoadmapFileConfig(BaseModel):
    """Configuration for a single roadmap file."""

    name: str
    path: str
    description: str = ""
    enabled: bool = True


class RoadmapSyncConfig(BaseModel):
    """Roadmap synchronization settings."""

    enabled: bool = True
    validate_on_sync: bool = True
    auto_update_state: bool = True
    sync_interval_minutes: int | None = None
    conflict_resolution: Literal["roadmap", "state"] = "roadmap"


class RoadmapValidationConfig(BaseModel):
    """Validation rules for roadmaps."""

    require_phase_id: bool = True
    require_phase_name: bool = True
    unique_phase_ids: bool = True
    validate_progress_range: bool = True
    validate_date_order: bool = True
    warn_no_current_phase: bool = True
    warn_multiple_in_progress: bool = True


class RoadmapExportConfig(BaseModel):
    """Export settings for roadmaps."""

    formats: list[str] = Field(
        default_factory=lambda: ["yaml", "json", "markdown", "html"]
    )
    default_format: str = "yaml"
    include_metadata: bool = True


class RoadmapConfig(BaseModel):
    """Roadmap management configuration."""

    base_path: str = "roadmap"

    # Primary roadmap
    primary: str = "roadmap.yaml"
    primary_description: str = "Main project roadmap"

    # Content limits
    limits: RoadmapLimitsConfig = Field(default_factory=RoadmapLimitsConfig)

    # Phase configuration
    phases: PhasesConfig = Field(default_factory=PhasesConfig)

    # Deliverable configuration
    deliverables: DeliverablesConfig = Field(default_factory=DeliverablesConfig)

    # Additional roadmaps
    additional: list[RoadmapFileConfig] = Field(default_factory=list)

    # Synchronization
    sync: RoadmapSyncConfig = Field(default_factory=RoadmapSyncConfig)

    # Validation
    validation: RoadmapValidationConfig = Field(default_factory=RoadmapValidationConfig)

    # Export
    export: RoadmapExportConfig = Field(default_factory=RoadmapExportConfig)


# =============================================================================
# MAIN CONFIGURATION MODEL
# =============================================================================


class FileManagementConfig(BaseModel):
    """Complete file management configuration.

    Loaded from project.yaml file_management section.
    Provides configurable paths for logs, ADRs, and roadmaps.

    Example:
        >>> config = FileManagementConfig.from_project_yaml(parac_root)
        >>> print(config.logs.base_path)
        'memory/logs'
        >>> print(config.adr.enabled)
        True
        >>> print(config.logs.global_config.max_line_length)
        2000
    """

    logs: LogsConfig = Field(default_factory=LogsConfig)
    adr: ADRConfig = Field(default_factory=ADRConfig)
    roadmap: RoadmapConfig = Field(default_factory=RoadmapConfig)

    @classmethod
    def from_project_yaml(cls, parac_root: Path) -> FileManagementConfig:
        """Load configuration from project.yaml with support for includes.

        Supports split configuration via include directive:
        ```yaml
        include:
          - config/logging.yaml
          - config/file-management.yaml
        ```

        Args:
            parac_root: Path to .parac/ directory.

        Returns:
            FileManagementConfig instance.

        Raises:
            FileNotFoundError: If project.yaml doesn't exist.
        """
        project_yaml = parac_root / "project.yaml"

        if not project_yaml.exists():
            return cls.get_defaults()

        # Load main project.yaml
        with open(project_yaml, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Process includes (merge additional config files)
        data = cls._process_includes(parac_root, data)

        file_management = data.get("file_management", {})
        return cls.from_dict(file_management)

    @classmethod
    def _process_includes(
        cls, parac_root: Path, base_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process include directives and merge configurations.

        Args:
            parac_root: Path to .parac/ directory.
            base_data: Base configuration dictionary.

        Returns:
            Merged configuration dictionary.
        """
        includes = base_data.get("include", [])
        if not includes:
            return base_data

        # Start with base data
        merged = base_data.copy()

        # Load and merge each included file
        for include_path in includes:
            include_file = parac_root / include_path

            if not include_file.exists():
                # Skip missing includes (optional configs)
                continue

            try:
                with open(include_file, encoding="utf-8") as f:
                    include_data = yaml.safe_load(f) or {}

                # Deep merge included data
                merged = cls._deep_merge(merged, include_data)
            except Exception:
                # Skip invalid include files
                continue

        return merged

    @classmethod
    def _deep_merge(
        cls, base: dict[str, Any], overlay: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary.
            overlay: Overlay dictionary (takes precedence).

        Returns:
            Merged dictionary.
        """
        result = base.copy()

        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dicts
                result[key] = cls._deep_merge(result[key], value)
            else:
                # Overlay value takes precedence
                result[key] = value

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileManagementConfig:
        """Create config from dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            FileManagementConfig instance.
        """
        if not data:
            return cls.get_defaults()

        # Parse logs config
        logs_data = data.get("logs", {})
        logs_config = cls._parse_logs_config(logs_data)

        # Parse ADR config
        adr_data = data.get("adr", {})
        adr_config = cls._parse_adr_config(adr_data)

        # Parse roadmap config
        roadmap_data = data.get("roadmap", {})
        roadmap_config = cls._parse_roadmap_config(roadmap_data)

        return cls(logs=logs_config, adr=adr_config, roadmap=roadmap_config)

    @classmethod
    def _parse_logs_config(cls, data: dict[str, Any]) -> LogsConfig:
        """Parse logs configuration."""
        if not data:
            return LogsConfig()

        # Parse global config
        global_data = data.get("global", {})
        global_config = (
            LogGlobalConfig(**global_data) if global_data else LogGlobalConfig()
        )

        # Parse predefined logs
        predefined_data = data.get("predefined", {})
        predefined = PredefinedLogsConfig()

        if predefined_data:
            for name in [
                "actions",
                "decisions",
                "security",
                "performance",
                "risk",
                "errors",
            ]:
                if name in predefined_data:
                    setattr(predefined, name, LogFileConfig(**predefined_data[name]))

        # Parse custom logs
        custom_data = data.get("custom", [])
        custom = [CustomLogConfig(**c) for c in custom_data] if custom_data else []

        return LogsConfig(
            base_path=data.get("base_path", "memory/logs"),
            global_config=global_config,
            predefined=predefined,
            custom=custom,
        )

    @classmethod
    def _parse_adr_config(cls, data: dict[str, Any]) -> ADRConfig:
        """Parse ADR configuration."""
        if not data:
            return ADRConfig()

        # Parse nested configs
        limits_data = data.get("limits", {})
        limits = ADRLimitsConfig(**limits_data) if limits_data else ADRLimitsConfig()

        defaults_data = data.get("defaults", {})
        defaults = (
            ADRDefaultsConfig(**defaults_data) if defaults_data else ADRDefaultsConfig()
        )

        validation_data = data.get("validation", {})
        validation = (
            ADRValidationConfig(**validation_data)
            if validation_data
            else ADRValidationConfig()
        )

        # Parse statuses
        statuses_data = data.get("statuses", [])
        if statuses_data:
            statuses = [ADRStatusConfig(**s) for s in statuses_data]
        else:
            statuses = ADRConfig().statuses

        return ADRConfig(
            base_path=data.get("base_path", "roadmap/adr"),
            enabled=data.get("enabled", True),
            format=data.get("format", "markdown"),
            index_file=data.get("index_file", "index.md"),
            file_extension=data.get("file_extension", ".md"),
            encoding=data.get("encoding", "utf-8"),
            limits=limits,
            auto_number=data.get("auto_number", True),
            number_format=data.get("number_format", "ADR-{:03d}"),
            number_start=data.get("number_start", 1),
            number_padding=data.get("number_padding", 3),
            statuses=statuses,
            default_status=data.get("default_status", "Proposed"),
            defaults=defaults,
            template=data.get("template", ADRConfig().template),
            index_template=data.get("index_template"),
            legacy_file=data.get("legacy_file", "roadmap/decisions.md"),
            migrate_on_init=data.get("migrate_on_init", False),
            backup_before_migrate=data.get("backup_before_migrate", True),
            validation=validation,
        )

    @classmethod
    def _parse_roadmap_config(cls, data: dict[str, Any]) -> RoadmapConfig:
        """Parse roadmap configuration."""
        if not data:
            return RoadmapConfig()

        # Parse nested configs
        limits_data = data.get("limits", {})
        limits = (
            RoadmapLimitsConfig(**limits_data) if limits_data else RoadmapLimitsConfig()
        )

        phases_data = data.get("phases", {})
        phases = (
            cls._parse_phases_config(phases_data) if phases_data else PhasesConfig()
        )

        deliverables_data = data.get("deliverables", {})
        deliverables = (
            DeliverablesConfig(**deliverables_data)
            if deliverables_data
            else DeliverablesConfig()
        )

        sync_data = data.get("sync", {})
        sync = RoadmapSyncConfig(**sync_data) if sync_data else RoadmapSyncConfig()

        validation_data = data.get("validation", {})
        validation = (
            RoadmapValidationConfig(**validation_data)
            if validation_data
            else RoadmapValidationConfig()
        )

        export_data = data.get("export", {})
        export = (
            RoadmapExportConfig(**export_data) if export_data else RoadmapExportConfig()
        )

        # Parse additional roadmaps
        additional_data = data.get("additional", [])
        additional = (
            [RoadmapFileConfig(**r) for r in additional_data] if additional_data else []
        )

        return RoadmapConfig(
            base_path=data.get("base_path", "roadmap"),
            primary=data.get("primary", "roadmap.yaml"),
            primary_description=data.get("primary_description", "Main project roadmap"),
            limits=limits,
            phases=phases,
            deliverables=deliverables,
            additional=additional,
            sync=sync,
            validation=validation,
            export=export,
        )

    @classmethod
    def _parse_phases_config(cls, data: dict[str, Any]) -> PhasesConfig:
        """Parse phases configuration."""
        statuses_data = data.get("statuses", [])
        if statuses_data:
            statuses = [PhaseStatusConfig(**s) for s in statuses_data]
        else:
            statuses = PhasesConfig().statuses

        progress_data = data.get("progress", {})
        progress = (
            PhaseProgressConfig(**progress_data)
            if progress_data
            else PhaseProgressConfig()
        )

        return PhasesConfig(
            statuses=statuses,
            default_status=data.get("default_status", "pending"),
            progress=progress,
        )

    @classmethod
    def get_defaults(cls) -> FileManagementConfig:
        """Get default configuration.

        Returns:
            FileManagementConfig with default values.
        """
        return cls()

    def get_log_path(self, parac_root: Path, log_name: str) -> Path | None:
        """Get full path for a log file.

        Args:
            parac_root: Path to .parac/ directory.
            log_name: Name of the log file (e.g., 'actions', 'decisions', or custom name).

        Returns:
            Full path to log file, or None if not found/disabled.
        """
        base = parac_root / self.logs.base_path

        # Check predefined logs
        predefined = self.logs.predefined
        predefined_map = {
            "actions": predefined.actions,
            "decisions": predefined.decisions,
            "security": predefined.security,
            "performance": predefined.performance,
            "risk": predefined.risk,
            "errors": predefined.errors,
        }

        if log_name in predefined_map:
            config = predefined_map[log_name]
            if config.enabled:
                return base / config.path
            return None

        # Check custom logs
        for custom in self.logs.custom:
            if custom.name == log_name:
                return base / custom.path

        return None

    def get_enabled_logs(self, parac_root: Path) -> dict[str, Path]:
        """Get all enabled log files.

        Args:
            parac_root: Path to .parac/ directory.

        Returns:
            Dictionary mapping log names to their full paths.
        """
        logs: dict[str, Path] = {}
        base = parac_root / self.logs.base_path

        # Predefined logs
        predefined = self.logs.predefined
        for name, config in [
            ("actions", predefined.actions),
            ("decisions", predefined.decisions),
            ("security", predefined.security),
            ("performance", predefined.performance),
            ("risk", predefined.risk),
            ("errors", predefined.errors),
        ]:
            if config.enabled:
                logs[name] = base / config.path

        # Custom logs
        for custom in self.logs.custom:
            if custom.enabled:
                logs[custom.name] = base / custom.path

        return logs

    def get_adr_directory(self, parac_root: Path) -> Path:
        """Get ADR directory path.

        Args:
            parac_root: Path to .parac/ directory.

        Returns:
            Full path to ADR directory.
        """
        return parac_root / self.adr.base_path

    def get_roadmap_path(self, parac_root: Path, name: str = "primary") -> Path | None:
        """Get roadmap file path.

        Args:
            parac_root: Path to .parac/ directory.
            name: Roadmap name ('primary' or additional roadmap name).

        Returns:
            Full path to roadmap file, or None if not found.
        """
        base = parac_root / self.roadmap.base_path

        if name == "primary":
            return base / self.roadmap.primary

        for roadmap in self.roadmap.additional:
            if roadmap.name == name:
                return base / roadmap.path

        return None

    def get_all_roadmaps(self, parac_root: Path) -> dict[str, Path]:
        """Get all roadmap files.

        Args:
            parac_root: Path to .parac/ directory.

        Returns:
            Dictionary mapping roadmap names to their full paths.
        """
        roadmaps: dict[str, Path] = {}
        base = parac_root / self.roadmap.base_path

        # Primary roadmap
        roadmaps["primary"] = base / self.roadmap.primary

        # Additional roadmaps
        for roadmap in self.roadmap.additional:
            roadmaps[roadmap.name] = base / roadmap.path

        return roadmaps

    def get_valid_adr_statuses(self) -> list[str]:
        """Get list of valid ADR status names.

        Returns:
            List of valid status names.
        """
        return [s.name for s in self.adr.statuses]

    def get_valid_phase_statuses(self) -> list[str]:
        """Get list of valid phase status names.

        Returns:
            List of valid status names.
        """
        return [s.name for s in self.roadmap.phases.statuses]
