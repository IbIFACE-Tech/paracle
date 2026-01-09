"""Workflow repository implementation.

Specialized repository for Workflow entities with additional query methods.
"""

from __future__ import annotations

from paracle_domain.models import EntityStatus, Workflow, WorkflowSpec

from paracle_store.repository import InMemoryRepository


class WorkflowRepository(InMemoryRepository[Workflow]):
    """Repository for Workflow entities."""

    def __init__(self) -> None:
        """Initialize workflow repository."""
        super().__init__(
            entity_type="Workflow",
            id_getter=lambda w: w.id,
        )
        self._specs: dict[str, WorkflowSpec] = {}

    def register_spec(self, spec: WorkflowSpec) -> WorkflowSpec:
        """Register a workflow spec.

        Args:
            spec: Workflow specification to register

        Returns:
            Registered spec
        """
        self._specs[spec.name] = spec
        return spec

    def get_spec(self, name: str) -> WorkflowSpec | None:
        """Get a workflow spec by name.

        Args:
            name: Spec name

        Returns:
            WorkflowSpec if found, None otherwise
        """
        return self._specs.get(name)

    def list_specs(self) -> list[WorkflowSpec]:
        """List all registered specs.

        Returns:
            List of all workflow specs
        """
        return list(self._specs.values())

    def remove_spec(self, name: str) -> bool:
        """Remove a workflow spec.

        Args:
            name: Spec name to remove

        Returns:
            True if removed, False if not found
        """
        if name not in self._specs:
            return False
        del self._specs[name]
        return True

    def create_from_spec(self, spec_name: str) -> Workflow:
        """Create a workflow from a registered spec.

        Args:
            spec_name: Name of the spec to use

        Returns:
            Created workflow

        Raises:
            ValueError: If spec not found
        """
        spec = self.get_spec(spec_name)
        if spec is None:
            raise ValueError(f"Spec '{spec_name}' not found")

        workflow = Workflow(spec=spec)
        return self.add(workflow)

    def find_by_status(self, status: EntityStatus) -> list[Workflow]:
        """Find workflows by status.

        Args:
            status: Status to filter by

        Returns:
            List of matching workflows
        """
        return self.find_by(lambda w: w.status.phase == status)

    def find_running(self) -> list[Workflow]:
        """Find all running workflows.

        Returns:
            List of running workflows
        """
        return self.find_by_status(EntityStatus.RUNNING)

    def find_completed(self) -> list[Workflow]:
        """Find all completed workflows.

        Returns:
            List of completed workflows
        """
        return self.find_by(
            lambda w: w.status.phase in (EntityStatus.SUCCEEDED, EntityStatus.FAILED)
        )

    def find_by_spec_name(self, spec_name: str) -> list[Workflow]:
        """Find workflows by spec name.

        Args:
            spec_name: Spec name to filter by

        Returns:
            List of matching workflows
        """
        return self.find_by(lambda w: w.spec.name == spec_name)
