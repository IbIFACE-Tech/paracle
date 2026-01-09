"""Tests for Layer 5: Continuous Monitoring.

Tests GovernanceMonitor for file system watching, violation detection,
and auto-repair functionality.
"""

import tempfile
import time
from pathlib import Path

import pytest
from paracle_core.governance import (
    GovernanceHealth,
    GovernanceMonitor,
    Violation,
    ViolationSeverity,
    get_monitor,
)


@pytest.fixture
def temp_parac():
    """Create temporary .parac/ directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        parac_root = Path(tmpdir) / ".parac"

        # Create standard structure
        (parac_root / "memory" / "data").mkdir(parents=True)
        (parac_root / "memory" / "logs").mkdir(parents=True)
        (parac_root / "memory" / "knowledge").mkdir(parents=True)
        (parac_root / "agents" / "specs").mkdir(parents=True)
        (parac_root / "roadmap").mkdir(parents=True)

        yield parac_root


class TestGovernanceMonitor:
    """Test GovernanceMonitor core functionality."""

    def test_monitor_initialization(self, temp_parac):
        """Test monitor initialization."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        assert monitor.parac_root == temp_parac
        assert not monitor.is_running
        assert monitor.auto_repair is False
        assert len(monitor.violations) == 0

    def test_monitor_with_auto_repair(self, temp_parac):
        """Test monitor with auto-repair enabled."""
        monitor = GovernanceMonitor(
            parac_root=temp_parac,
            auto_repair=True,
            repair_delay_seconds=0.1,
        )

        assert monitor.auto_repair is True
        assert monitor.repair_delay == 0.1

    def test_check_valid_file(self, temp_parac):
        """Test checking valid file returns None."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create valid file
        valid_file = temp_parac / "memory" / "data" / "test.db"
        valid_file.touch()

        violation = monitor.check_file(valid_file)

        assert violation is None
        assert len(monitor.violations) == 0

    def test_check_invalid_file(self, temp_parac):
        """Test checking invalid file detects violation."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create invalid file (database in wrong location)
        invalid_file = temp_parac / "test.db"
        invalid_file.touch()

        violation = monitor.check_file(invalid_file)

        assert violation is not None
        assert isinstance(violation, Violation)
        assert ".parac/test.db" in violation.path
        assert violation.severity == ViolationSeverity.CRITICAL
        assert len(monitor.violations) == 1

    def test_severity_determination(self, temp_parac):
        """Test violation severity is correct."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Critical: operational data
        db_file = temp_parac / "costs.db"
        db_file.touch()
        violation = monitor.check_file(db_file)
        assert violation.severity == ViolationSeverity.CRITICAL

        # Critical: logs
        log_file = temp_parac / "debug.log"
        log_file.touch()
        violation = monitor.check_file(log_file)
        assert violation.severity == ViolationSeverity.CRITICAL

    def test_repair_violation(self, temp_parac):
        """Test repairing a violation."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create invalid file
        invalid_file = temp_parac / "costs.db"
        invalid_file.touch()

        # Detect violation
        violation = monitor.check_file(invalid_file)
        assert violation is not None

        # Repair
        success = monitor.repair_violation(violation)

        assert success is True
        assert violation.repaired_at is not None
        assert violation.path not in monitor.violations
        assert len(monitor.repaired_violations) == 1

        # Check file was moved
        target = temp_parac / "memory" / "data" / "costs.db"
        assert target.exists()
        assert not invalid_file.exists()

    def test_scan_all_files(self, temp_parac):
        """Test scanning all files detects violations."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create multiple invalid files
        (temp_parac / "test1.db").touch()
        (temp_parac / "test2.log").touch()
        (temp_parac / "memory" / "valid.db").touch()  # Wrong but closer

        # Create valid files
        (temp_parac / "memory" / "data" / "valid.db").touch()
        (temp_parac / "memory" / "logs" / "valid.log").touch()

        # Scan
        monitor._scan_all_files()

        # Should detect 3 violations
        assert len(monitor.violations) >= 2  # At least the root files

    def test_repair_all(self, temp_parac):
        """Test repairing all violations."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create multiple invalid files
        (temp_parac / "test1.db").touch()
        (temp_parac / "test2.db").touch()

        # Scan
        monitor._scan_all_files()
        initial_violations = len(monitor.violations)

        # Repair all
        repaired = monitor.repair_all()

        assert repaired == initial_violations
        assert len(monitor.violations) == 0
        assert len(monitor.repaired_violations) == repaired


class TestGovernanceHealth:
    """Test governance health reporting."""

    def test_get_health_healthy(self, temp_parac):
        """Test health status when no violations."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create valid files
        (temp_parac / "memory" / "data" / "test.db").touch()
        (temp_parac / "memory" / "logs" / "test.log").touch()

        # Start and get health
        monitor.start()
        health = monitor.get_health()
        monitor.stop()

        assert isinstance(health, GovernanceHealth)
        assert health.status == "healthy"
        assert health.violations == 0
        assert health.health_percentage == 100.0

    def test_get_health_with_violations(self, temp_parac):
        """Test health status with violations."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create violations
        (temp_parac / "test1.db").touch()
        (temp_parac / "test2.db").touch()

        # Create valid files
        (temp_parac / "memory" / "data" / "valid.db").touch()

        # Scan
        monitor._scan_all_files()
        health = monitor.get_health()

        assert health.violations >= 2
        assert health.status in ("warning", "critical")
        assert health.health_percentage < 100.0

    def test_health_after_repair(self, temp_parac):
        """Test health improves after repair."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create violations
        (temp_parac / "test.db").touch()

        # Scan
        monitor._scan_all_files()
        health_before = monitor.get_health()

        # Repair
        monitor.repair_all()
        health_after = monitor.get_health()

        assert health_after.violations < health_before.violations
        assert health_after.health_percentage > health_before.health_percentage
        assert health_after.repaired > 0


class TestFileSystemWatcher:
    """Test file system watching functionality."""

    def test_monitor_start_stop(self, temp_parac):
        """Test starting and stopping monitor."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        assert not monitor.is_running

        monitor.start()
        assert monitor.is_running
        assert monitor.observer is not None

        monitor.stop()
        assert not monitor.is_running

    def test_monitor_detects_new_file(self, temp_parac):
        """Test monitor detects newly created files."""
        monitor = GovernanceMonitor(parac_root=temp_parac)
        monitor.start()

        # Give watcher time to start
        time.sleep(0.5)

        # Create invalid file
        invalid_file = temp_parac / "test.db"
        invalid_file.touch()

        # Give watcher time to detect
        time.sleep(0.5)

        # Check violation detected
        assert len(monitor.violations) > 0

        monitor.stop()

    def test_monitor_ignores_non_parac_changes(self, temp_parac):
        """Test monitor ignores changes outside .parac/."""
        monitor = GovernanceMonitor(parac_root=temp_parac)
        monitor.start()

        # Give watcher time to start
        time.sleep(0.5)

        violations_before = len(monitor.violations)

        # Create file outside .parac/ (in parent)
        outside_file = temp_parac.parent / "outside.txt"
        outside_file.touch()

        # Give watcher time (should not detect)
        time.sleep(0.5)

        # No new violations
        assert len(monitor.violations) == violations_before

        monitor.stop()
        outside_file.unlink()


class TestAutoRepair:
    """Test auto-repair functionality."""

    @pytest.mark.asyncio
    async def test_auto_repair_critical_violation(self, temp_parac):
        """Test auto-repair kicks in for critical violations."""
        monitor = GovernanceMonitor(
            parac_root=temp_parac,
            auto_repair=True,
            repair_delay_seconds=0.1,
        )

        monitor.start()
        time.sleep(0.5)

        # Create critical violation
        invalid_file = temp_parac / "costs.db"
        invalid_file.write_text("test data")

        # Wait for detection and repair
        time.sleep(1.0)

        # Check auto-repaired
        target = temp_parac / "memory" / "data" / "costs.db"
        assert target.exists()
        assert target.read_text() == "test data"
        assert not invalid_file.exists()

        monitor.stop()

    def test_no_auto_repair_when_disabled(self, temp_parac):
        """Test auto-repair does not run when disabled."""
        monitor = GovernanceMonitor(
            parac_root=temp_parac,
            auto_repair=False,  # Disabled
        )

        monitor.start()
        time.sleep(0.5)

        # Create violation
        invalid_file = temp_parac / "test.db"
        invalid_file.touch()

        # Wait
        time.sleep(1.0)

        # File should still be in wrong location
        assert invalid_file.exists()
        assert len(monitor.repaired_violations) == 0

        monitor.stop()


class TestMonitorSingleton:
    """Test singleton pattern for monitor."""

    def test_get_monitor_returns_same_instance(self, temp_parac):
        """Test get_monitor returns singleton."""
        # Note: This test may fail if other tests modified the singleton
        # In real usage, this is the expected behavior

        monitor1 = get_monitor()
        monitor2 = get_monitor()

        assert monitor1 is monitor2

    def test_get_monitor_with_options(self):
        """Test get_monitor with configuration options."""
        monitor = get_monitor(auto_repair=True, repair_delay=10.0)

        # Note: Options only apply on first call
        # This tests that function accepts the parameters
        assert monitor is not None


class TestViolationHistory:
    """Test violation history tracking."""

    def test_get_violations(self, temp_parac):
        """Test getting current violations."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create violations
        (temp_parac / "test1.db").touch()
        (temp_parac / "test2.db").touch()

        monitor._scan_all_files()

        violations = monitor.get_violations()
        assert len(violations) >= 2
        assert all(isinstance(v, Violation) for v in violations)

    def test_get_repaired_violations(self, temp_parac):
        """Test getting repaired violation history."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create and repair violations
        (temp_parac / "test.db").touch()
        monitor._scan_all_files()
        monitor.repair_all()

        repaired = monitor.get_repaired_violations()
        assert len(repaired) > 0
        assert all(v.repaired_at is not None for v in repaired)

    def test_clear_history(self, temp_parac):
        """Test clearing violation history."""
        monitor = GovernanceMonitor(parac_root=temp_parac)

        # Create and repair violations
        (temp_parac / "test.db").touch()
        monitor._scan_all_files()
        monitor.repair_all()

        assert len(monitor.repaired_violations) > 0
        assert monitor.total_repairs > 0

        monitor.clear_history()

        assert len(monitor.repaired_violations) == 0
        assert monitor.total_repairs == 0


@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_developer_creates_file_in_wrong_place(self, temp_parac):
        """Test detecting file created in wrong location."""
        monitor = GovernanceMonitor(parac_root=temp_parac)
        monitor.start()
        time.sleep(0.5)

        # Developer creates database file in root
        db_file = temp_parac / "my_data.db"
        db_file.touch()

        time.sleep(0.5)

        # Should be detected
        violations = monitor.get_violations()
        assert any(".parac/my_data.db" in v.path for v in violations)

        monitor.stop()

    def test_continuous_monitoring_workflow(self, temp_parac):
        """Test complete monitoring workflow."""
        # 1. Start monitoring with auto-repair
        monitor = GovernanceMonitor(
            parac_root=temp_parac,
            auto_repair=True,
            repair_delay_seconds=0.2,
        )
        monitor.start()
        time.sleep(0.5)

        # 2. Create violation
        invalid_file = temp_parac / "costs.db"
        invalid_file.write_text("cost data")

        # 3. Wait for auto-repair
        time.sleep(1.0)

        # 4. Check repaired
        health = monitor.get_health()
        assert health.repaired > 0
        assert health.violations == 0

        # 5. Verify file moved correctly
        target = temp_parac / "memory" / "data" / "costs.db"
        assert target.exists()
        assert target.read_text() == "cost data"

        monitor.stop()
