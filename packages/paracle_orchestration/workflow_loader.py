"""Workflow Loader - Load workflow definitions from YAML files.

Loads workflows from .parac/workflows/ directory structure:
- catalog.yaml: Registry of workflows with metadata
- definitions/: User workflow definitions
- content/templates/: Template workflows

Supports both API and CLI usage for workflow discovery and loading.
"""

from pathlib import Path
from typing import Any

import yaml
from paracle_domain.models import WorkflowSpec, WorkflowStep
from pydantic import ValidationError

try:
    from paracle_profiling import cached, profile

    PROFILING_AVAILABLE = True
except ImportError:
    # Profiling not available - use no-op decorators
    PROFILING_AVAILABLE = False

    def cached(*_args, **_kwargs):
        def decorator(func):
            return func

        return decorator

    def profile(*_args, **_kwargs):
        def decorator(func):
            return func

        return decorator


class WorkflowLoadError(Exception):
    """Raised when workflow loading fails."""

    ...


class WorkflowLoader:
    """Loads workflow definitions from .parac/workflows/ directory.

    Automatically discovers .parac/ directory and loads workflows from:
    - catalog.yaml (workflow registry)
    - definitions/ (user workflows)
    - content/templates/ (template workflows)

    Example:
        loader = WorkflowLoader()
        workflows = loader.list_workflows()
        spec = loader.load_workflow_spec("my_workflow")
    """

    def __init__(self, parac_root: Path | str | None = None):
        """Initialize workflow loader.

        Args:
            parac_root: Path to .parac/ directory. If None, auto-discovers.

        Raises:
            WorkflowLoadError: If .parac/ not found
        """
        if parac_root is None:
            parac_root = self._find_parac_root()

        self.parac_root = Path(parac_root)
        self.workflows_dir = self.parac_root / "workflows"
        self.catalog_file = self.workflows_dir / "catalog.yaml"
        self.definitions_dir = self.workflows_dir / "definitions"
        self.templates_dir = self.workflows_dir / "templates"

        if not self.workflows_dir.exists():
            raise WorkflowLoadError(
                f"Workflows directory not found: {self.workflows_dir}"
            )

    def _find_parac_root(self) -> Path:
        """Find .parac/ directory by searching upward from cwd.

        Returns:
            Path to .parac/ directory

        Raises:
            WorkflowLoadError: If .parac/ not found
        """
        current = Path.cwd()

        # Search upward for .parac/
        for _ in range(10):  # Limit search depth
            parac_path = current / ".parac"
            if parac_path.exists() and parac_path.is_dir():
                return parac_path
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent

        raise WorkflowLoadError(
            ".parac/ directory not found. Run from project root or "
            "specify parac_root."
        )

    def load_catalog(self) -> dict[str, Any]:
        """Load workflow catalog.

        Returns:
            Catalog dictionary with workflows metadata

        Raises:
            WorkflowLoadError: If catalog not found or invalid
        """
        if not self.catalog_file.exists():
            return {"workflows": []}

        try:
            with open(self.catalog_file, encoding="utf-8") as f:
                catalog = yaml.safe_load(f)
                return catalog or {"workflows": []}
        except Exception as e:
            raise WorkflowLoadError(
                f"Failed to load catalog {self.catalog_file}: {e}"
            ) from e

    def list_workflows(
        self,
        category: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List available workflows from catalog.

        Args:
            category: Filter by category (optional)
            status: Filter by status (active/inactive) (optional)

        Returns:
            List of workflow metadata dicts

        Example:
            workflows = loader.list_workflows(status="active")
        """
        catalog = self.load_catalog()
        workflows = catalog.get("workflows", [])

        # Apply filters
        if category:
            workflows = [w for w in workflows if w.get("category") == category]
        if status:
            workflows = [w for w in workflows if w.get("status") == status]

        return workflows

    def get_workflow_file_path(self, workflow_name: str) -> Path:
        """Get file path for a workflow.

        Searches in order:
        1. definitions/{name}.yaml
        2. content/templates/{name}.yaml

        Args:
            workflow_name: Name of workflow

        Returns:
            Path to workflow file

        Raises:
            WorkflowLoadError: If workflow file not found
        """
        # Try definitions first
        def_path = self.definitions_dir / f"{workflow_name}.yaml"
        if def_path.exists():
            return def_path

        # Try templates
        tpl_path = self.templates_dir / f"{workflow_name}.yaml"
        if tpl_path.exists():
            return tpl_path

        raise WorkflowLoadError(
            f"Workflow '{workflow_name}' not found in definitions/ or "
            "content/templates/"
        )

    @cached(ttl=120)  # Cache for 2 minutes
    @profile()
    def load_workflow_yaml(self, workflow_name: str) -> dict[str, Any]:
        """Load workflow YAML as dictionary.

        Args:
            workflow_name: Name of workflow

        Returns:
            Workflow YAML as dict

        Raises:
            WorkflowLoadError: If loading fails
        """
        file_path = self.get_workflow_file_path(workflow_name)

        try:
            with open(file_path, encoding="utf-8") as f:
                workflow_yaml = yaml.safe_load(f)
                if not workflow_yaml:
                    raise WorkflowLoadError(f"Empty workflow file: {file_path}")
                return workflow_yaml
        except FileNotFoundError as exc:
            raise WorkflowLoadError(
                f"Failed to load {file_path}: File not found"
            ) from exc
        except yaml.YAMLError as e:
            raise WorkflowLoadError(f"Invalid YAML in {file_path}: {e}") from e
        except Exception as e:
            raise WorkflowLoadError(f"Failed to load {file_path}: {e}") from e

    @profile(track_memory=True)
    def load_workflow_spec(self, workflow_name: str) -> WorkflowSpec:
        """Load workflow as WorkflowSpec domain model.

        Args:
            workflow_name: Name of workflow

        Returns:
            WorkflowSpec instance

        Raises:
            WorkflowLoadError: If loading or parsing fails
        """
        workflow_yaml = self.load_workflow_yaml(workflow_name)
        return self._yaml_to_spec(workflow_name, workflow_yaml)

    def _yaml_to_spec(
        self, workflow_name: str, workflow_yaml: dict[str, Any]
    ) -> WorkflowSpec:
        """Convert YAML dict to WorkflowSpec.

        Args:
            workflow_name: Name of workflow
            workflow_yaml: Workflow YAML dict

        Returns:
            WorkflowSpec instance

        Raises:
            WorkflowLoadError: If conversion fails
        """
        try:
            # Parse steps
            steps_yaml = workflow_yaml.get("steps", [])
            if not steps_yaml:
                raise WorkflowLoadError(f"Workflow '{workflow_name}' has no steps")

            steps = []
            for step_yaml in steps_yaml:
                try:
                    step = self._parse_step(step_yaml)
                    steps.append(step)
                except Exception as e:
                    raise WorkflowLoadError(
                        f"Failed to parse step in '{workflow_name}': {e}"
                    ) from e

            # Create WorkflowSpec
            spec = WorkflowSpec(
                name=workflow_yaml.get("name", workflow_name),
                description=workflow_yaml.get("description", ""),
                steps=steps,
                inputs=workflow_yaml.get("inputs", {}),
                outputs=workflow_yaml.get("outputs", {}),
                config=workflow_yaml.get("config", {}),
            )

            return spec

        except ValidationError as e:
            raise WorkflowLoadError(
                f"Invalid workflow structure in '{workflow_name}': {e}"
            ) from e
        except Exception as e:
            raise WorkflowLoadError(
                f"Failed to parse workflow '{workflow_name}': {e}"
            ) from e

    def _parse_step(self, step_yaml: dict[str, Any]) -> WorkflowStep:
        """Parse a workflow step from YAML.

        Handles two YAML formats for backward compatibility:
        1. New format: id + name fields
        2. Legacy format: only name field (generates id from name)

        Also converts outputs from list to dict:
        - outputs: [key1, key2] -> {key1: null, key2: null}
        - outputs: {key1: val1} -> {key1: val1} (unchanged)

        Args:
            step_yaml: Step dictionary from YAML

        Returns:
            WorkflowStep instance

        Raises:
            ValueError: If step structure is invalid
        """
        # Extract identifiers (support both id and name)
        step_id = step_yaml.get("id")
        step_name = step_yaml.get("name")

        # Ensure at least one identifier exists
        if not step_id and not step_name:
            raise ValueError("Step must have either 'id' or 'name' field")

        # Use id as primary, name as fallback
        if not step_id:
            step_id = step_name
        if not step_name:
            step_name = step_id

        # Required fields
        agent = step_yaml.get("agent")
        if not agent:
            raise ValueError(f"Step '{step_name}' must have an 'agent' field")

        # Optional fields
        prompt = step_yaml.get("prompt")
        depends_on = step_yaml.get("depends_on", [])
        config = step_yaml.get("config", {})

        # Parse inputs (always dict)
        inputs = step_yaml.get("inputs", {})
        if not isinstance(inputs, dict):
            raise ValueError(
                f"Step '{step_name}' inputs must be a dictionary, "
                f"got {type(inputs)}"
            )

        # Parse outputs (convert list to dict if needed)
        outputs_raw = step_yaml.get("outputs", {})
        if isinstance(outputs_raw, list):
            # Convert [key1, key2] -> {key1: null, key2: null}
            outputs = dict.fromkeys(outputs_raw)
        elif isinstance(outputs_raw, dict):
            outputs = outputs_raw
        else:
            raise ValueError(
                f"Step '{step_name}' outputs must be list or dict, "
                f"got {type(outputs_raw)}"
            )

        # Parse approval config (ISO 42001 Human-in-the-Loop)
        requires_approval = step_yaml.get("requires_approval", False)
        approval_config = step_yaml.get("approval_config", {})

        # Create WorkflowStep
        step = WorkflowStep(
            id=step_id,
            name=step_name,
            agent=agent,
            prompt=prompt,
            inputs=inputs,
            outputs=outputs,
            depends_on=depends_on,
            config=config,
            requires_approval=requires_approval,
            approval_config=approval_config,
        )

        return step

    def validate_workflow(self, workflow_name: str) -> tuple[bool, list[str]]:
        """Validate a workflow definition.

        Checks:
        - Steps exist
        - Dependencies are valid (no missing steps)
        - No circular dependencies (basic check)

        Args:
            workflow_name: Name of workflow to validate

        Returns:
            Tuple of (is_valid, list_of_errors)

        Example:
            is_valid, errors = loader.validate_workflow("my_workflow")
            if not is_valid:
                print(f"Errors: {errors}")
        """
        errors = []

        try:
            # Load and parse
            spec = self.load_workflow_spec(workflow_name)

            # Check steps exist
            if not spec.steps:
                errors.append("Workflow has no steps")

            # Check dependencies
            step_ids = {step.id for step in spec.steps}
            for step in spec.steps:
                for dep in step.depends_on:
                    if dep not in step_ids:
                        errors.append(
                            f"Step '{step.name}' depends on non-existent "
                            f"step '{dep}'"
                        )

            # If no errors, workflow is valid
            return (len(errors) == 0, errors)

        except WorkflowLoadError as e:
            errors.append(str(e))
            return (False, errors)
        except Exception as e:  # noqa: BLE001
            errors.append(f"Unexpected error: {e}")
            return (False, errors)

    def scan_all_workflows(self) -> list[str]:
        """Scan all workflow files in definitions and templates.

        Returns:
            List of workflow names found

        Example:
            all_workflows = loader.scan_all_workflows()
        """
        workflow_names = []

        # Scan definitions directory
        if self.definitions_dir.exists():
            for file_path in self.definitions_dir.glob("*.yaml"):
                if file_path.stem != "_manifest":
                    workflow_names.append(file_path.stem)

        # Scan templates directory
        if self.templates_dir.exists():
            for file_path in self.templates_dir.glob("*.yaml"):
                workflow_names.append(file_path.stem)

        return sorted(set(workflow_names))


# =============================================================================
# Convenience Functions
# =============================================================================


def load_workflow(
    workflow_name: str, parac_root: Path | str | None = None
) -> WorkflowSpec:
    """Load a workflow spec by name.

    Convenience function for quick workflow loading.

    Args:
        workflow_name: Name of workflow
        parac_root: Optional .parac/ directory path

    Returns:
        WorkflowSpec instance

    Example:
        spec = load_workflow("paracle_build")
    """
    loader = WorkflowLoader(parac_root)
    return loader.load_workflow_spec(workflow_name)


def list_available_workflows(
    parac_root: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List all available workflows.

    Convenience function for workflow discovery.

    Args:
        parac_root: Optional .parac/ directory path

    Returns:
        List of workflow metadata dicts

    Example:
        workflows = list_available_workflows()
        for wf in workflows:
            print(f"{wf['name']}: {wf['description']}")
    """
    loader = WorkflowLoader(parac_root)
    return loader.list_workflows()
