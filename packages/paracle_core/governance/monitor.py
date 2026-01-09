"""Layer 5: Continuous Monitoring - 24/7 Governance Integrity.

This module provides continuous monitoring of .parac/ structure with:
- Background file system watcher
- Automatic violation repair
- Governance health dashboard
- Self-healing capabilities

Usage:
    # Start monitoring
    from paracle_core.governance import GovernanceMonitor

    monitor = GovernanceMonitor()
    monitor.start()

    # Check health
    health = monitor.get_health()

    # Stop monitoring
    monitor.stop()

CLI:
    paracle governance monitor       # Start monitoring
    paracle governance health        # Check health
    paracle governance repair        # Manual repair
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .ai_compliance import FileCategory, ValidationResult, get_compliance_engine

logger = logging.getLogger(__name__)


class ViolationSeverity(Enum):
    """Severity levels for violations."""

    LOW = "low"  # Non-critical, can wait
    MEDIUM = "medium"  # Should be fixed soon
    HIGH = "high"  # Should be fixed immediately
    CRITICAL = "critical"  # Auto-repair immediately


class RepairAction(Enum):
    """Types of repair actions."""

    MOVE = "move"  # Move file to correct location
    DELETE = "delete"  # Delete invalid file
    RENAME = "rename"  # Rename file
    SKIP = "skip"  # Skip repair (manual intervention needed)


@dataclass
class Violation:
    """Represents a governance violation."""

    path: str
    category: FileCategory
    severity: ViolationSeverity
    error: str
    suggested_path: str
    detected_at: datetime = field(default_factory=datetime.now)
    repaired_at: datetime | None = None
    repair_action: RepairAction | None = None


@dataclass
class GovernanceHealth:
    """Overall governance health status."""

    status: str  # "healthy", "warning", "critical"
    total_files: int
    valid_files: int
    violations: int
    repaired: int
    auto_repair_enabled: bool
    uptime_seconds: float
    last_check: datetime
    violation_rate: float  # violations per hour

    @property
    def health_percentage(self) -> float:
        """Calculate health as percentage."""
        if self.total_files == 0:
            return 100.0
        return (self.valid_files / self.total_files) * 100.0


class GovernanceFileHandler(FileSystemEventHandler):
    """File system event handler for .parac/ monitoring."""

    def __init__(self, monitor: "GovernanceMonitor"):
        """Initialize handler.

        Args:
            monitor: Parent monitor instance
        """
        self.monitor = monitor
        self.engine = get_compliance_engine()

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        # Only monitor .parac/ files
        path = Path(event.src_path)
        if not self._is_parac_file(path):
            return

        logger.debug(f"File created: {path}")
        self.monitor.check_file(path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)
        if not self._is_parac_file(dest_path):
            return

        logger.debug(f"File moved to: {dest_path}")
        self.monitor.check_file(dest_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events.

        Args:
            event: File system event
        """
        # We don't validate on modifications, only on creation/move
        pass

    def _is_parac_file(self, path: Path) -> bool:
        """Check if path is a .parac/ file.

        Args:
            path: File path to check

        Returns:
            True if file is in .parac/
        """
        try:
            # Convert to string and normalize separators
            path_str = str(path).replace("\\", "/")
            return ".parac/" in path_str
        except Exception:
            return False


class GovernanceMonitor:
    """Continuous governance monitoring and auto-repair.

    Features:
    - Real-time file system watching
    - Automatic violation detection
    - Auto-repair with configurable policies
    - Health dashboard
    - Violation history and analytics

    Example:
        >>> monitor = GovernanceMonitor(auto_repair=True)
        >>> monitor.start()
        >>> # Monitor runs in background
        >>> health = monitor.get_health()
        >>> print(f"Health: {health.status}")
        >>> monitor.stop()
    """

    def __init__(
        self,
        parac_root: Path | None = None,
        auto_repair: bool = False,
        repair_delay_seconds: float = 5.0,
    ):
        """Initialize governance monitor.

        Args:
            parac_root: Root .parac/ directory (auto-detected if None)
            auto_repair: Enable automatic violation repair
            repair_delay_seconds: Delay before auto-repair (allows undo)
        """
        self.parac_root = parac_root or self._find_parac_root()
        self.auto_repair = auto_repair
        self.repair_delay = repair_delay_seconds

        self.engine = get_compliance_engine()
        self.observer: Observer | None = None
        self.handler: GovernanceFileHandler | None = None

        # State tracking
        self.violations: dict[str, Violation] = {}
        self.repaired_violations: list[Violation] = []
        self.start_time: float | None = None
        self.last_check: datetime | None = None
        self.is_running = False

        # Statistics
        self.total_checks = 0
        self.total_violations = 0
        self.total_repairs = 0

        logger.info(f"GovernanceMonitor initialized for {self.parac_root}")

    def _find_parac_root(self) -> Path:
        """Find .parac/ root directory.

        Returns:
            Path to .parac/ directory

        Raises:
            FileNotFoundError: If .parac/ not found
        """
        current = Path.cwd()

        # Search up to 5 levels
        for _ in range(5):
            parac_dir = current / ".parac"
            if parac_dir.exists() and parac_dir.is_dir():
                return parac_dir

            parent = current.parent
            if parent == current:
                break
            current = parent

        raise FileNotFoundError(
            "Could not find .parac/ directory. "
            "Run 'paracle init' or specify parac_root explicitly."
        )

    def start(self) -> None:
        """Start continuous monitoring.

        Starts background file system watcher that monitors .parac/
        for violations and optionally auto-repairs them.
        """
        if self.is_running:
            logger.warning("Monitor already running")
            return

        logger.info("Starting governance monitor...")

        # Initial scan
        self._scan_all_files()

        # Start file system watcher
        self.handler = GovernanceFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.parac_root), recursive=True)
        self.observer.start()

        self.is_running = True
        self.start_time = time.time()

        mode = "auto-repair enabled" if self.auto_repair else "monitoring only"
        logger.info(f"Monitor started ({mode})")

        # Log initial health
        health = self.get_health()
        logger.info(
            f"Initial health: {health.status} "
            f"({health.health_percentage:.1f}% - "
            f"{health.violations} violations)"
        )

    def stop(self) -> None:
        """Stop monitoring."""
        if not self.is_running:
            logger.warning("Monitor not running")
            return

        logger.info("Stopping governance monitor...")

        if self.observer:
            self.observer.stop()
            self.observer.join()

        self.is_running = False

        # Log final statistics
        uptime = time.time() - (self.start_time or time.time())
        logger.info(
            f"Monitor stopped. "
            f"Uptime: {uptime:.1f}s, "
            f"Checks: {self.total_checks}, "
            f"Violations: {self.total_violations}, "
            f"Repairs: {self.total_repairs}"
        )

    def check_file(self, path: Path) -> Violation | None:
        """Check a single file for violations.

        Args:
            path: File path to check

        Returns:
            Violation if found, None if valid
        """
        self.total_checks += 1
        self.last_check = datetime.now()

        # Get relative path for validation
        try:
            rel_path = path.relative_to(self.parac_root.parent)
        except ValueError:
            # Path not relative to .parac/, skip
            return None

        path_str = str(rel_path).replace("\\", "/")

        # Validate
        result = self.engine.validate_file_path(path_str)

        if result.is_valid:
            # Remove from violations if it was there
            if path_str in self.violations:
                logger.info(f"Violation resolved: {path_str}")
                del self.violations[path_str]
            return None

        # Violation found
        severity = self._determine_severity(result)
        violation = Violation(
            path=path_str,
            category=result.category,
            severity=severity,
            error=result.error,
            suggested_path=result.suggested_path,
        )

        self.violations[path_str] = violation
        self.total_violations += 1

        logger.warning(
            f"Violation detected: {path_str} " f"(severity: {severity.value})"
        )

        # Auto-repair if enabled
        if self.auto_repair and severity == ViolationSeverity.CRITICAL:
            # Use thread-based delay since watchdog runs in threads
            import threading

            repair_thread = threading.Timer(
                self.repair_delay, lambda: self._auto_repair_sync(violation)
            )
            repair_thread.daemon = True
            repair_thread.start()

        return violation

    def _determine_severity(self, result: ValidationResult) -> ViolationSeverity:
        """Determine violation severity.

        Args:
            result: Validation result

        Returns:
            Severity level
        """
        # Critical: operational data and logs (data loss risk)
        if result.category in (FileCategory.OPERATIONAL_DATA, FileCategory.LOGS):
            return ViolationSeverity.CRITICAL

        # High: decisions, agent specs (governance critical)
        if result.category in (FileCategory.DECISIONS, FileCategory.AGENT_SPECS):
            return ViolationSeverity.HIGH

        # Medium: knowledge, context
        if result.category in (FileCategory.KNOWLEDGE, FileCategory.CONTEXT):
            return ViolationSeverity.MEDIUM

        # Low: other
        return ViolationSeverity.LOW

    def _auto_repair_sync(self, violation: Violation) -> None:
        """Auto-repair violation synchronously (thread-safe).

        Args:
            violation: Violation to repair
        """
        # Check if still a violation
        if violation.path not in self.violations:
            return  # Already resolved

        # Perform repair
        self.repair_violation(violation)

    def repair_violation(self, violation: Violation) -> bool:
        """Repair a violation.

        Args:
            violation: Violation to repair

        Returns:
            True if repaired successfully
        """
        logger.info(f"Repairing violation: {violation.path}")

        try:
            # Get actual file path
            source = self.parac_root.parent / violation.path
            target = self.parac_root.parent / violation.suggested_path

            # Create target directory if needed
            target.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            source.rename(target)

            # Update violation
            violation.repaired_at = datetime.now()
            violation.repair_action = RepairAction.MOVE

            # Remove from active violations
            if violation.path in self.violations:
                del self.violations[violation.path]

            # Add to repaired list
            self.repaired_violations.append(violation)
            self.total_repairs += 1

            logger.info(f"✅ Repaired: {violation.path} → {violation.suggested_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to repair {violation.path}: {e}")
            return False

    def repair_all(self) -> int:
        """Repair all current violations.

        Returns:
            Number of violations repaired
        """
        violations = list(self.violations.values())
        repaired_count = 0

        for violation in violations:
            if self.repair_violation(violation):
                repaired_count += 1

        return repaired_count

    def _scan_all_files(self) -> None:
        """Scan all .parac/ files for initial state."""
        logger.info("Performing initial scan...")

        # Get all files in .parac/
        files = list(self.parac_root.rglob("*"))
        file_count = len([f for f in files if f.is_file()])

        logger.info(f"Scanning {file_count} files...")

        for path in files:
            if path.is_file():
                self.check_file(path)

        logger.info(f"Scan complete. " f"Found {len(self.violations)} violations")

    def get_health(self) -> GovernanceHealth:
        """Get current governance health status.

        Returns:
            Health status
        """
        # Count files
        all_files = list(self.parac_root.rglob("*"))
        total_files = len([f for f in all_files if f.is_file()])
        valid_files = total_files - len(self.violations)

        # Calculate violation rate
        uptime = time.time() - (self.start_time or time.time())
        uptime_hours = max(uptime / 3600.0, 0.01)  # Avoid division by zero
        violation_rate = self.total_violations / uptime_hours

        # Determine status
        if len(self.violations) == 0:
            status = "healthy"
        elif len(self.violations) < 5:
            status = "warning"
        else:
            status = "critical"

        return GovernanceHealth(
            status=status,
            total_files=total_files,
            valid_files=valid_files,
            violations=len(self.violations),
            repaired=len(self.repaired_violations),
            auto_repair_enabled=self.auto_repair,
            uptime_seconds=uptime,
            last_check=self.last_check or datetime.now(),
            violation_rate=violation_rate,
        )

    def get_violations(self) -> list[Violation]:
        """Get all current violations.

        Returns:
            List of active violations
        """
        return list(self.violations.values())

    def get_repaired_violations(self) -> list[Violation]:
        """Get all repaired violations.

        Returns:
            List of repaired violations
        """
        return self.repaired_violations.copy()

    def clear_history(self) -> None:
        """Clear violation history."""
        self.repaired_violations.clear()
        self.total_checks = 0
        self.total_violations = 0
        self.total_repairs = 0
        logger.info("History cleared")


# Singleton instance
_monitor_instance: GovernanceMonitor | None = None


def get_monitor(
    auto_repair: bool = False,
    repair_delay: float = 5.0,
) -> GovernanceMonitor:
    """Get singleton governance monitor instance.

    Args:
        auto_repair: Enable automatic repair
        repair_delay: Delay before auto-repair

    Returns:
        Governance monitor instance
    """
    global _monitor_instance

    if _monitor_instance is None:
        _monitor_instance = GovernanceMonitor(
            auto_repair=auto_repair,
            repair_delay_seconds=repair_delay,
        )

    return _monitor_instance
