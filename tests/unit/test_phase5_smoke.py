"""
Basic smoke tests for Phase 5 components.

These tests verify that:
1. Modules can be imported successfully
2. Core classes can be instantiated
3. Basic configurations are valid

For comprehensive testing, see tests/unit/test_sandbox.py, etc.
"""

import pytest


class TestPhase5Imports:
    """Test that Phase 5 packages can be imported."""

    def test_import_sandbox(self):
        """Test sandbox package imports."""
        from paracle_sandbox import SandboxConfig, SandboxManager
        from paracle_sandbox.docker_sandbox import DockerSandbox
        from paracle_sandbox.monitor import SandboxMonitor

        assert SandboxConfig is not None
        assert SandboxManager is not None
        assert DockerSandbox is not None
        assert SandboxMonitor is not None

    def test_import_isolation(self):
        """Test isolation package imports."""
        from paracle_isolation import NetworkConfig, NetworkIsolator, NetworkPolicy

        assert NetworkConfig is not None
        assert NetworkIsolator is not None
        assert NetworkPolicy is not None

    def test_import_rollback(self):
        """Test rollback package imports."""
        from paracle_rollback import RollbackConfig, RollbackManager
        from paracle_rollback.snapshot import TarballSnapshotStrategy, VolumeSnapshot

        assert RollbackConfig is not None
        assert RollbackManager is not None
        assert TarballSnapshotStrategy is not None
        assert VolumeSnapshot is not None

    def test_import_review(self):
        """Test review package imports."""
        from paracle_review import ReviewConfig, ReviewManager
        from paracle_review.models import ArtifactReview, ReviewDecision, ReviewStatus

        assert ReviewConfig is not None
        assert ReviewManager is not None
        assert ArtifactReview is not None
        assert ReviewDecision is not None
        assert ReviewStatus is not None


class TestPhase5Configuration:
    """Test Phase 5 configuration models."""

    def test_sandbox_config(self):
        """Test SandboxConfig creation."""
        from paracle_sandbox import SandboxConfig

        config = SandboxConfig(
            base_image="python:3.11-slim",
            cpu_cores=1.0,
            memory_mb=512,
        )

        assert config.base_image == "python:3.11-slim"
        assert config.cpu_cores == 1.0
        assert config.memory_mb == 512

    def test_network_config(self):
        """Test NetworkConfig creation."""
        from paracle_isolation import NetworkConfig, NetworkPolicy

        config = NetworkConfig(
            driver="bridge",
            internal=True,
        )

        assert config.driver == "bridge"
        assert config.internal is True

        policy = NetworkPolicy(
            allow_internet=False,
            allowed_ports=[80, 443],
        )

        assert policy.allow_internet is False
        assert policy.allowed_ports == [80, 443]

    def test_rollback_config(self):
        """Test RollbackConfig creation."""
        from paracle_rollback import RollbackConfig, RollbackPolicy

        config = RollbackConfig(
            policy=RollbackPolicy(
                enabled=True,
                triggers=["on_error"],
                max_snapshots=3,
            )
        )

        assert config.policy.enabled is True
        assert "on_error" in config.policy.triggers
        assert config.policy.max_snapshots == 3

    def test_review_config(self):
        """Test ReviewConfig creation."""
        from paracle_review import ReviewConfig, ReviewPolicy

        config = ReviewConfig(
            policy=ReviewPolicy(
                enabled=True,
                auto_approve_low_risk=True,
                min_approvals=2,
            )
        )

        assert config.policy.enabled is True
        assert config.policy.auto_approve_low_risk is True
        assert config.policy.min_approvals == 2


class TestPhase5Exceptions:
    """Test Phase 5 exception classes."""

    def test_sandbox_exceptions(self):
        """Test sandbox exception hierarchy."""
        from paracle_sandbox.exceptions import (
            DockerNotAvailableError,
            ResourceLimitExceededError,
            SandboxError,
            SandboxTimeoutError,
        )

        # All should be Exception subclasses
        assert issubclass(SandboxError, Exception)
        assert issubclass(DockerNotAvailableError, SandboxError)
        assert issubclass(ResourceLimitExceededError, SandboxError)
        assert issubclass(SandboxTimeoutError, SandboxError)

    def test_isolation_exceptions(self):
        """Test isolation exception hierarchy."""
        from paracle_isolation.exceptions import (
            IsolationError,
            NetworkCreationError,
            NetworkNotFoundError,
        )

        assert issubclass(IsolationError, Exception)
        assert issubclass(NetworkCreationError, IsolationError)
        assert issubclass(NetworkNotFoundError, IsolationError)

    def test_rollback_exceptions(self):
        """Test rollback exception hierarchy."""
        from paracle_rollback.exceptions import (
            RollbackError,
            RollbackFailedError,
            SnapshotCreationError,
            SnapshotNotFoundError,
        )

        assert issubclass(RollbackError, Exception)
        assert issubclass(SnapshotCreationError, RollbackError)
        assert issubclass(SnapshotNotFoundError, RollbackError)
        assert issubclass(RollbackFailedError, RollbackError)

    def test_review_exceptions(self):
        """Test review exception hierarchy."""
        from paracle_review.exceptions import (
            ReviewAlreadyDecidedError,
            ReviewError,
            ReviewNotFoundError,
            ReviewTimeoutError,
        )

        assert issubclass(ReviewError, Exception)
        assert issubclass(ReviewNotFoundError, ReviewError)
        assert issubclass(ReviewAlreadyDecidedError, ReviewError)
        assert issubclass(ReviewTimeoutError, ReviewError)


class TestPhase5Models:
    """Test Phase 5 data models."""

    def test_review_status_enum(self):
        """Test ReviewStatus enum values."""
        from paracle_review.models import ReviewStatus

        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewStatus.APPROVED.value == "approved"
        assert ReviewStatus.REJECTED.value == "rejected"
        assert ReviewStatus.TIMEOUT.value == "timeout"
        assert ReviewStatus.CANCELLED.value == "cancelled"

    def test_volume_snapshot_dataclass(self):
        """Test VolumeSnapshot dataclass."""
        from datetime import datetime

        from paracle_rollback.snapshot import VolumeSnapshot

        snapshot = VolumeSnapshot(
            snapshot_id="test-123",
            container_id="container-456",
            timestamp=datetime.now(),
            size_bytes=1024,
            storage_path="/tmp/snapshot.tar.gz",
        )

        assert snapshot.snapshot_id == "test-123"
        assert snapshot.container_id == "container-456"
        assert snapshot.size_bytes == 1024

    def test_artifact_review_model(self):
        """Test ArtifactReview model."""
        from datetime import datetime

        from paracle_review.models import ArtifactReview, ReviewStatus

        review = ArtifactReview(
            review_id="review-001",
            artifact_id="artifact-001",
            artifact_type="file_change",
            sandbox_id="sandbox-001",
            status=ReviewStatus.PENDING,
            risk_level="low",
            created_at=datetime.now(),
        )

        assert review.review_id == "review-001"
        assert review.status == ReviewStatus.PENDING
        assert review.risk_level == "low"
        assert review.approval_count() == 0
        assert review.rejection_count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
