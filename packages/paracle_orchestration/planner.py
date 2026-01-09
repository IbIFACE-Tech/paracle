"""Workflow execution planning and analysis.

This module provides tools to analyze workflows and generate execution plans
without actually running them. Useful for:
- Cost estimation before execution
- Time estimation for scheduling
- Identifying optimization opportunities (parallel execution)
- Understanding approval gate requirements
"""

from collections import defaultdict, deque

from paracle_domain.models import WorkflowSpec, WorkflowStep
from pydantic import BaseModel, Field

from paracle_orchestration.exceptions import InvalidWorkflowError


class ExecutionGroup(BaseModel):
    """Group of steps that can execute in parallel."""

    group_number: int = Field(..., description="Execution group index (0-based)")
    steps: list[str] = Field(..., description="Step IDs in this group")
    can_parallelize: bool = Field(
        default=True, description="Whether steps can run in parallel"
    )
    estimated_duration_seconds: int | None = Field(
        None, description="Estimated duration for this group"
    )


class ExecutionPlan(BaseModel):
    """Complete execution plan for a workflow."""

    workflow_name: str = Field(..., description="Workflow name")
    total_steps: int = Field(..., description="Total number of steps")
    execution_order: list[str] = Field(..., description="Steps in topological order")
    parallel_groups: list[ExecutionGroup] = Field(
        ..., description="Parallel execution groups"
    )
    approval_gates: list[str] = Field(..., description="Steps requiring human approval")
    estimated_tokens: int | None = Field(
        None, description="Estimated total tokens (if models known)"
    )
    estimated_cost_usd: float | None = Field(None, description="Estimated cost in USD")
    estimated_time_seconds: int | None = Field(
        None, description="Estimated total execution time"
    )
    optimization_suggestions: list[str] = Field(
        default_factory=list, description="Suggestions for optimization"
    )


class WorkflowPlanner:
    """Analyzes workflows and generates execution plans."""

    def __init__(
        self,
        token_cost_per_1k: dict[str, float] | None = None,
        avg_tokens_per_step: int = 500,
        avg_step_duration_seconds: int = 5,
    ):
        """Initialize planner with cost/time estimation parameters.

        Args:
            token_cost_per_1k: Cost per 1K tokens by model (e.g., {"gpt-4": 0.03})
            avg_tokens_per_step: Average tokens per step (for unknown models)
            avg_step_duration_seconds: Average step duration in seconds
        """
        self.token_cost_per_1k = token_cost_per_1k or {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
            "default": 0.01,
        }
        self.avg_tokens_per_step = avg_tokens_per_step
        self.avg_step_duration_seconds = avg_step_duration_seconds

    def plan(self, workflow: WorkflowSpec) -> ExecutionPlan:
        """Generate execution plan for workflow.

        Args:
            workflow: Workflow specification

        Returns:
            ExecutionPlan with topological order, parallel groups, cost/time estimates

        Raises:
            InvalidWorkflowError: If workflow has cycles or invalid dependencies
        """
        # 1. Validate workflow structure
        self._validate_workflow(workflow)

        # 2. Topological sort
        execution_order = self._topological_sort(workflow.steps)

        # 3. Identify parallel groups
        parallel_groups = self._find_parallel_groups(workflow.steps, execution_order)

        # 4. Find approval gates
        approval_gates = self._find_approval_gates(workflow.steps)

        # 5. Estimate costs and time
        tokens, cost = self._estimate_costs(workflow.steps)
        time_sec = self._estimate_time(parallel_groups)

        # 6. Generate optimization suggestions
        suggestions = self._generate_suggestions(
            workflow.steps, parallel_groups, approval_gates
        )

        return ExecutionPlan(
            workflow_name=workflow.name,
            total_steps=len(workflow.steps),
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            approval_gates=approval_gates,
            estimated_tokens=tokens,
            estimated_cost_usd=cost,
            estimated_time_seconds=time_sec,
            optimization_suggestions=suggestions,
        )

    def _validate_workflow(self, workflow: WorkflowSpec) -> None:
        """Validate workflow structure.

        Args:
            workflow: Workflow specification

        Raises:
            InvalidWorkflowError: If workflow has cycles or invalid dependencies
        """
        if not workflow.steps:
            raise InvalidWorkflowError("Workflow has no steps")

        # Check for duplicate step IDs
        step_ids = [step.id for step in workflow.steps]
        if len(step_ids) != len(set(step_ids)):
            raise InvalidWorkflowError("Workflow has duplicate step IDs")

        # Check for missing dependencies
        valid_ids = set(step_ids)
        for step in workflow.steps:
            for dep in step.depends_on:
                if dep not in valid_ids:
                    raise InvalidWorkflowError(
                        f"Step '{step.id}' depends on non-existent step '{dep}'"
                    )

        # Check for cycles (will be caught by topological sort)
        try:
            self._topological_sort(workflow.steps)
        except InvalidWorkflowError:
            raise

    def _topological_sort(self, steps: list[WorkflowStep]) -> list[str]:
        """Topologically sort steps by dependencies.

        Args:
            steps: List of workflow steps

        Returns:
            List of step IDs in execution order

        Raises:
            InvalidWorkflowError: If cycle detected
        """
        # Build dependency graph
        in_degree = {step.id: len(step.depends_on) for step in steps}
        adj_list = defaultdict(list)

        for step in steps:
            for dep in step.depends_on:
                adj_list[dep].append(step.id)

        # Kahn's algorithm
        queue = deque([step_id for step_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for neighbor in adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(steps):
            raise InvalidWorkflowError("Cycle detected in workflow dependencies")

        return result

    def _find_parallel_groups(
        self, steps: list[WorkflowStep], execution_order: list[str]
    ) -> list[ExecutionGroup]:
        """Identify groups of steps that can execute in parallel.

        Args:
            steps: List of workflow steps
            execution_order: Topologically sorted step IDs

        Returns:
            List of execution groups with parallel steps
        """
        step_map = {step.id: step for step in steps}
        groups: list[ExecutionGroup] = []
        current_group: list[str] = []
        completed: set[str] = set()

        for step_id in execution_order:
            step = step_map[step_id]

            # Check if can add to current group
            # Can parallelize if no dependencies within current group
            can_add_to_group = all(dep not in current_group for dep in step.depends_on)

            if not can_add_to_group and current_group:
                # Finalize current group and start new one
                groups.append(
                    ExecutionGroup(
                        group_number=len(groups),
                        steps=current_group,
                        can_parallelize=len(current_group) > 1,
                        estimated_duration_seconds=self.avg_step_duration_seconds,
                    )
                )
                completed.update(current_group)
                current_group = []

            current_group.append(step_id)

        # Finalize last group
        if current_group:
            groups.append(
                ExecutionGroup(
                    group_number=len(groups),
                    steps=current_group,
                    can_parallelize=len(current_group) > 1,
                    estimated_duration_seconds=self.avg_step_duration_seconds,
                )
            )

        return groups

    def _find_approval_gates(self, steps: list[WorkflowStep]) -> list[str]:
        """Find steps that require human approval.

        Args:
            steps: List of workflow steps

        Returns:
            List of step IDs requiring approval
        """
        return [step.id for step in steps if step.requires_approval]

    def _estimate_costs(
        self, steps: list[WorkflowStep]
    ) -> tuple[int | None, float | None]:
        """Estimate token usage and cost.

        Args:
            steps: List of workflow steps

        Returns:
            Tuple of (estimated_tokens, estimated_cost_usd)
        """
        # For now, use average tokens per step
        # In future, could analyze prompts and context sizes
        total_tokens = len(steps) * self.avg_tokens_per_step

        # Calculate cost using average model cost
        avg_cost_per_1k = self.token_cost_per_1k.get("default", 0.01)
        total_cost = (total_tokens / 1000) * avg_cost_per_1k

        return total_tokens, total_cost

    def _estimate_time(self, groups: list[ExecutionGroup]) -> int:
        """Estimate total execution time.

        Args:
            groups: Parallel execution groups

        Returns:
            Estimated time in seconds
        """
        # Time = sum of group durations (groups run sequentially)
        # Within groups, steps run in parallel, so use max duration
        total_seconds = sum(
            group.estimated_duration_seconds or self.avg_step_duration_seconds
            for group in groups
        )
        return total_seconds

    def _generate_suggestions(
        self,
        steps: list[WorkflowStep],
        groups: list[ExecutionGroup],
        approval_gates: list[str],
    ) -> list[str]:
        """Generate optimization suggestions.

        Args:
            steps: Workflow steps
            groups: Parallel execution groups
            approval_gates: Steps requiring approval

        Returns:
            List of suggestion strings
        """
        suggestions: list[str] = []

        # Parallelization opportunities
        parallel_groups = [g for g in groups if g.can_parallelize]
        if parallel_groups:
            total_parallel = sum(len(g.steps) for g in parallel_groups)
            suggestions.append(
                f"{total_parallel} steps can run in parallel "
                f"({len(parallel_groups)} groups)"
            )

        # Approval gates
        if approval_gates:
            suggestions.append(
                f"{len(approval_gates)} approval gate(s) require human action"
            )

        # Long dependency chains
        max_chain = self._find_longest_chain(steps)
        if max_chain > 5:
            suggestions.append(
                f"Longest dependency chain: {max_chain} steps "
                f"(consider breaking into sub-workflows)"
            )

        return suggestions

    def _find_longest_chain(self, steps: list[WorkflowStep]) -> int:
        """Find longest dependency chain in workflow.

        Args:
            steps: Workflow steps

        Returns:
            Length of longest dependency chain
        """
        step_map = {step.id: step for step in steps}
        memo: dict[str, int] = {}

        def dfs(step_id: str) -> int:
            if step_id in memo:
                return memo[step_id]

            step = step_map[step_id]
            if not step.depends_on:
                memo[step_id] = 1
                return 1

            max_depth = max(dfs(dep) for dep in step.depends_on)
            memo[step_id] = max_depth + 1
            return max_depth + 1

        return max(dfs(step.id) for step in steps) if steps else 0
