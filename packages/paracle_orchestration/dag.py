"""DAG (Directed Acyclic Graph) utilities for workflow orchestration."""

from collections import defaultdict, deque

from paracle_domain.models import WorkflowStep

from paracle_orchestration.exceptions import (
    CircularDependencyError,
    InvalidWorkflowError,
)


class DAG:
    """Directed Acyclic Graph for workflow step dependencies.

    Provides validation and topological sorting for workflow steps
    based on their dependencies.

    Example:
        >>> steps = [
        ...     WorkflowStep(name="step1", agent="agent1"),
        ...     WorkflowStep(name="step2", agent="agent2", depends_on=["step1"]),
        ...     WorkflowStep(name="step3", agent="agent3", depends_on=["step1"]),
        ... ]
        >>> dag = DAG(steps)
        >>> dag.validate()  # Raises if circular dependencies
        >>> levels = dag.get_execution_levels()  # [[step1], [step2, step3]]
    """

    def __init__(self, steps: list[WorkflowStep]) -> None:
        """Initialize DAG with workflow steps.

        Args:
            steps: List of workflow steps with dependencies
        """
        self.steps = {step.id: step for step in steps}
        self.graph = self._build_graph()
        self.reverse_graph = self._build_reverse_graph()

    def _build_graph(self) -> dict[str, list[str]]:
        """Build adjacency list representation of the graph.

        Returns:
            Dictionary mapping step IDs to their dependencies
        """
        graph: dict[str, list[str]] = defaultdict(list)
        for step in self.steps.values():
            graph[step.id] = list(step.depends_on) if step.depends_on else []
        return dict(graph)

    def _build_reverse_graph(self) -> dict[str, list[str]]:
        """Build reverse adjacency list (dependents).

        Returns:
            Dictionary mapping step IDs to steps that depend on them
        """
        reverse: dict[str, list[str]] = defaultdict(list)
        for step_id, deps in self.graph.items():
            for dep in deps:
                reverse[dep].append(step_id)
        return dict(reverse)

    def validate(self) -> None:
        """Validate the DAG for correctness.

        Checks for:
        - All referenced dependencies exist
        - No circular dependencies

        Raises:
            InvalidWorkflowError: If dependencies reference non-existent steps
            CircularDependencyError: If circular dependency is detected
        """
        # Check all dependencies exist
        for step_id, deps in self.graph.items():
            for dep in deps:
                if dep not in self.steps:
                    raise InvalidWorkflowError(
                        f"Step '{step_id}' depends on " f"non-existent step '{dep}'"
                    )

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node: str, path: list[str]) -> list[str] | None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Check all neighbors
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    cycle = has_cycle(neighbor, path.copy())
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            return None

        for step_name in self.steps:
            if step_name not in visited:
                cycle = has_cycle(step_name, [])
                if cycle:
                    raise CircularDependencyError(cycle)

    def topological_sort(self) -> list[str]:
        """Perform topological sort using Kahn's algorithm.

        Returns:
            List of step names in topological order

        Raises:
            CircularDependencyError: If the graph has cycles
        """
        # Calculate in-degree for each node (number of dependencies)
        in_degree = {step: len(self.graph[step]) for step in self.steps}

        # Queue of nodes with in-degree 0 (no dependencies)
        queue = deque([step for step, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Reduce in-degree for dependents
            for dependent in self.reverse_graph.get(node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self.steps):
            # Some nodes couldn't be sorted - there's a cycle
            remaining = [s for s in self.steps if s not in result]
            raise CircularDependencyError(remaining)

        return result

    def get_execution_levels(self) -> list[list[str]]:
        """Get execution levels for parallel execution.

        Groups steps into levels where all steps in a level can be
        executed in parallel (no dependencies between them).

        Returns:
            List of levels, each level is a list of step names that
            can be executed in parallel

        Example:
            >>> # step1 (no deps)
            >>> # step2, step3 (both depend on step1)
            >>> # step4 (depends on step2, step3)
            >>> levels = dag.get_execution_levels()
            >>> # [[step1], [step2, step3], [step4]]
        """
        # Calculate in-degree
        in_degree = {step: len(self.graph[step]) for step in self.steps}

        levels: list[list[str]] = []
        remaining = set(self.steps.keys())

        while remaining:
            # Find all nodes with in-degree 0 in remaining set
            current_level = [step for step in remaining if in_degree[step] == 0]

            if not current_level:
                # No nodes with in-degree 0 - there's a cycle
                raise CircularDependencyError(list(remaining))

            levels.append(current_level)

            # Remove current level from remaining
            for step in current_level:
                remaining.remove(step)
                # Reduce in-degree for dependents
                for dependent in self.reverse_graph.get(step, []):
                    if dependent in remaining:
                        in_degree[dependent] -= 1

        return levels

    def get_ready_steps(self, completed_steps: set[str]) -> list[str]:
        """Get steps that are ready to execute.

        A step is ready if all its dependencies are completed.

        Args:
            completed_steps: Set of step names that have been completed

        Returns:
            List of step names that are ready to execute
        """
        ready = []
        for step_name, deps in self.graph.items():
            if step_name not in completed_steps:
                if all(dep in completed_steps for dep in deps):
                    ready.append(step_name)
        return ready

    def get_dependencies(self, step_name: str) -> list[str]:
        """Get direct dependencies for a step.

        Args:
            step_name: Name of the step

        Returns:
            List of step names that this step depends on
        """
        return self.graph.get(step_name, [])

    def get_dependents(self, step_name: str) -> list[str]:
        """Get steps that depend on this step.

        Args:
            step_name: Name of the step

        Returns:
            List of step names that depend on this step
        """
        return self.reverse_graph.get(step_name, [])
