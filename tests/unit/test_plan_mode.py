"""
Unit tests for Plan Mode (WorkflowPlanner).

Tests workflow execution planning including:
- Topological sorting and cycle detection
- Parallel group identification
- Cost and time estimation
- Approval gate detection
- Optimization suggestions
"""

import pytest
from paracle_domain.models import WorkflowSpec, WorkflowStep
from paracle_orchestration import ExecutionGroup, ExecutionPlan, WorkflowPlanner
from paracle_orchestration.exceptions import InvalidWorkflowError


@pytest.fixture
def simple_workflow() -> WorkflowSpec:
    """Simple linear workflow (A → B → C)."""
    return WorkflowSpec(
        name="simple-workflow",
        description="Linear workflow",
        steps=[
            WorkflowStep(
                id="step_a",
                name="Step A",
                agent="agent-1",
                prompt="Do A",
            ),
            WorkflowStep(
                id="step_b",
                name="Step B",
                agent="agent-1",
                prompt="Do B",
                depends_on=["step_a"],
            ),
            WorkflowStep(
                id="step_c",
                name="Step C",
                agent="agent-1",
                prompt="Do C",
                depends_on=["step_b"],
            ),
        ],
    )


@pytest.fixture
def parallel_workflow() -> WorkflowSpec:
    """Workflow with parallel opportunities (A → [B, C, D] → E)."""
    return WorkflowSpec(
        name="parallel-workflow",
        description="Workflow with parallel steps",
        steps=[
            WorkflowStep(
                id="step_a",
                name="Step A",
                agent="agent-1",
                prompt="Do A",
            ),
            WorkflowStep(
                id="step_b",
                name="Step B",
                agent="agent-1",
                prompt="Do B",
                depends_on=["step_a"],
            ),
            WorkflowStep(
                id="step_c",
                name="Step C",
                agent="agent-1",
                prompt="Do C",
                depends_on=["step_a"],
            ),
            WorkflowStep(
                id="step_d",
                name="Step D",
                agent="agent-1",
                prompt="Do D",
                depends_on=["step_a"],
            ),
            WorkflowStep(
                id="step_e",
                name="Step E",
                agent="agent-1",
                prompt="Do E",
                depends_on=["step_b", "step_c", "step_d"],
            ),
        ],
    )


@pytest.fixture
def approval_workflow() -> WorkflowSpec:
    """Workflow with approval gates."""
    return WorkflowSpec(
        name="approval-workflow",
        description="Workflow with human approval",
        steps=[
            WorkflowStep(
                id="step_a",
                name="Step A",
                agent="agent-1",
                prompt="Do A",
            ),
            WorkflowStep(
                id="step_b",
                name="Step B",
                agent="agent-1",
                prompt="Do B",
                depends_on=["step_a"],
                requires_approval=True,
            ),
            WorkflowStep(
                id="step_c",
                name="Step C",
                agent="agent-1",
                prompt="Do C",
                depends_on=["step_b"],
            ),
        ],
    )


@pytest.fixture
def cyclic_workflow() -> WorkflowSpec:
    """Workflow with circular dependency (A → B → C → A)."""
    return WorkflowSpec(
        name="cyclic-workflow",
        description="Invalid workflow with cycle",
        steps=[
            WorkflowStep(
                id="step_a",
                name="Step A",
                agent="agent-1",
                prompt="Do A",
                depends_on=["step_c"],  # Cycle!
            ),
            WorkflowStep(
                id="step_b",
                name="Step B",
                agent="agent-1",
                prompt="Do B",
                depends_on=["step_a"],
            ),
            WorkflowStep(
                id="step_c",
                name="Step C",
                agent="agent-1",
                prompt="Do C",
                depends_on=["step_b"],
            ),
        ],
    )


# ============================================================================
# Planner Initialization Tests
# ============================================================================


def test_planner_default_config():
    """Test planner with default configuration."""
    planner = WorkflowPlanner()

    assert planner.token_cost_per_1k is not None
    assert "default" in planner.token_cost_per_1k
    assert planner.avg_tokens_per_step == 500
    assert planner.avg_step_duration_seconds == 5


def test_planner_custom_config():
    """Test planner with custom configuration."""
    custom_costs = {"gpt-4": 0.05, "default": 0.02}
    planner = WorkflowPlanner(
        token_cost_per_1k=custom_costs,
        avg_tokens_per_step=1000,
        avg_step_duration_seconds=10,
    )

    assert planner.token_cost_per_1k == custom_costs
    assert planner.avg_tokens_per_step == 1000
    assert planner.avg_step_duration_seconds == 10


# ============================================================================
# Plan Generation Tests
# ============================================================================


def test_plan_simple_workflow(simple_workflow):
    """Test planning a simple linear workflow."""
    planner = WorkflowPlanner()
    plan = planner.plan(simple_workflow)

    assert isinstance(plan, ExecutionPlan)
    assert plan.workflow_name == "simple-workflow"
    assert plan.total_steps == 3
    assert plan.execution_order == ["step_a", "step_b", "step_c"]
    assert len(plan.parallel_groups) == 3  # All sequential
    assert plan.estimated_tokens > 0
    assert plan.estimated_cost_usd > 0
    assert plan.estimated_time_seconds > 0


def test_plan_parallel_workflow(parallel_workflow):
    """Test planning workflow with parallel opportunities."""
    planner = WorkflowPlanner()
    plan = planner.plan(parallel_workflow)

    assert plan.workflow_name == "parallel-workflow"
    assert plan.total_steps == 5

    # Check execution order starts with step_a
    assert plan.execution_order[0] == "step_a"

    # Check parallel groups - should have 3 groups (A, [B,C,D], E)
    assert len(plan.parallel_groups) == 3

    # Group 1 should have 3 parallel steps (B, C, D)
    parallel_group = next(g for g in plan.parallel_groups if len(g.steps) == 3)
    assert parallel_group.can_parallelize
    assert len(parallel_group.steps) == 3
    assert set(parallel_group.steps) == {"step_b", "step_c", "step_d"}


def test_plan_approval_workflow(approval_workflow):
    """Test planning workflow with approval gates."""
    planner = WorkflowPlanner()
    plan = planner.plan(approval_workflow)

    assert plan.workflow_name == "approval-workflow"
    assert plan.total_steps == 3

    # Check approval gates
    assert len(plan.approval_gates) == 1
    assert "step_b" in plan.approval_gates


def test_plan_empty_workflow():
    """Test planning workflow with no steps."""
    empty_workflow = WorkflowSpec(
        name="empty",
        description="No steps",
        steps=[],
    )

    planner = WorkflowPlanner()

    with pytest.raises(InvalidWorkflowError, match="no steps"):
        planner.plan(empty_workflow)


# ============================================================================
# Validation Tests
# ============================================================================


def test_plan_cyclic_workflow_raises_error(cyclic_workflow):
    """Test that cyclic workflows raise InvalidWorkflowError."""
    planner = WorkflowPlanner()

    with pytest.raises(InvalidWorkflowError, match="Cycle detected"):
        planner.plan(cyclic_workflow)


def test_plan_missing_dependency():
    """Test workflow with missing dependency."""
    workflow = WorkflowSpec(
        name="invalid",
        description="Missing dependency",
        steps=[
            WorkflowStep(
                id="step_a",
                name="Step A",
                agent="agent-1",
                prompt="Do A",
                depends_on=["nonexistent"],  # Missing!
            ),
        ],
    )

    planner = WorkflowPlanner()

    with pytest.raises(InvalidWorkflowError, match="non-existent"):
        planner.plan(workflow)


def test_plan_duplicate_step_ids():
    """Test workflow with duplicate step IDs."""
    workflow = WorkflowSpec(
        name="invalid",
        description="Duplicate IDs",
        steps=[
            WorkflowStep(
                id="step_a",
                name="Step A",
                agent="agent-1",
                prompt="Do A",
            ),
            WorkflowStep(
                id="step_a",  # Duplicate!
                name="Step A Again",
                agent="agent-1",
                prompt="Do A again",
            ),
        ],
    )

    planner = WorkflowPlanner()

    with pytest.raises(InvalidWorkflowError, match="duplicate"):
        planner.plan(workflow)


# ============================================================================
# Cost Estimation Tests
# ============================================================================


def test_cost_estimation_simple(simple_workflow):
    """Test cost estimation for simple workflow."""
    planner = WorkflowPlanner(
        token_cost_per_1k={"default": 0.01},
        avg_tokens_per_step=500,
    )

    plan = planner.plan(simple_workflow)

    # 3 steps × 500 tokens = 1500 tokens
    assert plan.estimated_tokens == 1500

    # Cost: 1500 tokens × $0.01/1K = $0.015
    assert abs(plan.estimated_cost_usd - 0.015) < 0.001


def test_cost_estimation_custom_tokens():
    """Test cost estimation with custom token count."""
    planner = WorkflowPlanner(avg_tokens_per_step=1000)

    workflow = WorkflowSpec(
        name="test",
        description="Test",
        steps=[
            WorkflowStep(
                id="step_a",
                name="Step A",
                agent="agent-1",
                prompt="Do A",
            ),
        ],
    )

    plan = planner.plan(workflow)

    assert plan.estimated_tokens == 1000


# ============================================================================
# Time Estimation Tests
# ============================================================================


def test_time_estimation_sequential(simple_workflow):
    """Test time estimation for sequential workflow."""
    planner = WorkflowPlanner(avg_step_duration_seconds=5)

    plan = planner.plan(simple_workflow)

    # 3 sequential steps × 5s = 15s
    assert plan.estimated_time_seconds == 15


def test_time_estimation_parallel(parallel_workflow):
    """Test time estimation accounts for parallelism."""
    planner = WorkflowPlanner(avg_step_duration_seconds=5)

    plan = planner.plan(parallel_workflow)

    # Group 1: step_a (5s)
    # Group 2: max(step_b, step_c, step_d) = 5s (parallel)
    # Group 3: step_e (5s)
    # Total: 15s (not 25s!)
    assert plan.estimated_time_seconds == 15


# ============================================================================
# Optimization Suggestions Tests
# ============================================================================


def test_optimization_suggestions_parallel(parallel_workflow):
    """Test optimization suggestions for parallel workflow."""
    planner = WorkflowPlanner()
    plan = planner.plan(parallel_workflow)

    # Should suggest parallelization
    suggestions = plan.optimization_suggestions
    assert len(suggestions) > 0
    assert any("parallel" in s.lower() for s in suggestions)


def test_optimization_suggestions_approval(approval_workflow):
    """Test optimization suggestions for workflow with approvals."""
    planner = WorkflowPlanner()
    plan = planner.plan(approval_workflow)

    # Should warn about approval gates
    suggestions = plan.optimization_suggestions
    assert any("approval" in s.lower() for s in suggestions)


def test_optimization_suggestions_long_chain():
    """Test optimization suggestions for long dependency chain."""
    # Create workflow with long chain (10 sequential steps)
    steps = []
    for i in range(10):
        step = WorkflowStep(
            id=f"step_{i}",
            name=f"Step {i}",
            agent="agent-1",
            prompt=f"Do {i}",
        )
        if i > 0:
            step.depends_on = [f"step_{i-1}"]
        steps.append(step)

    workflow = WorkflowSpec(
        name="long-chain",
        description="Long dependency chain",
        steps=steps,
    )

    planner = WorkflowPlanner()
    plan = planner.plan(workflow)

    # Should warn about long chain
    suggestions = plan.optimization_suggestions
    assert any("chain" in s.lower() or "depth" in s.lower() for s in suggestions)


# ============================================================================
# ExecutionPlan Model Tests
# ============================================================================


def test_execution_plan_serialization(simple_workflow):
    """Test ExecutionPlan can be serialized to dict."""
    planner = WorkflowPlanner()
    plan = planner.plan(simple_workflow)

    plan_dict = plan.model_dump()

    assert isinstance(plan_dict, dict)
    assert "workflow_name" in plan_dict
    assert "total_steps" in plan_dict
    assert "execution_order" in plan_dict
    assert "parallel_groups" in plan_dict
    assert "estimated_cost_usd" in plan_dict


def test_execution_group_model():
    """Test ExecutionGroup model."""
    group = ExecutionGroup(
        group_number=1,
        steps=["step_a", "step_b"],
        can_parallelize=True,
        estimated_duration_seconds=5.0,
    )

    assert group.group_number == 1
    assert group.steps == ["step_a", "step_b"]
    assert group.can_parallelize is True
    assert group.estimated_duration_seconds == 5.0

    # Test serialization
    group_dict = group.model_dump()
    assert isinstance(group_dict, dict)
    assert group_dict["group_number"] == 1


# ============================================================================
# Edge Cases
# ============================================================================


def test_plan_single_step_workflow():
    """Test planning workflow with single step."""
    workflow = WorkflowSpec(
        name="single",
        description="Single step",
        steps=[
            WorkflowStep(
                id="step_a",
                name="Step A",
                agent="agent-1",
                prompt="Do A",
            ),
        ],
    )

    planner = WorkflowPlanner()
    plan = planner.plan(workflow)

    assert plan.total_steps == 1
    assert plan.execution_order == ["step_a"]
    assert len(plan.parallel_groups) == 1
    assert not plan.parallel_groups[0].can_parallelize


def test_plan_complex_dag():
    """Test planning complex DAG with multiple paths."""
    workflow = WorkflowSpec(
        name="complex",
        description="Complex DAG",
        steps=[
            WorkflowStep(id="a", name="A", agent="agent-1", prompt="Do A"),
            WorkflowStep(
                id="b",
                name="B",
                agent="agent-1",
                prompt="Do B",
                depends_on=["a"],
            ),
            WorkflowStep(
                id="c",
                name="C",
                agent="agent-1",
                prompt="Do C",
                depends_on=["a"],
            ),
            WorkflowStep(
                id="d",
                name="D",
                agent="agent-1",
                prompt="Do D",
                depends_on=["b"],
            ),
            WorkflowStep(
                id="e",
                name="E",
                agent="agent-1",
                prompt="Do E",
                depends_on=["c"],
            ),
            WorkflowStep(
                id="f",
                name="F",
                agent="agent-1",
                prompt="Do F",
                depends_on=["d", "e"],
            ),
        ],
    )

    planner = WorkflowPlanner()
    plan = planner.plan(workflow)

    assert plan.total_steps == 6
    assert plan.execution_order[0] == "a"  # Must start with a
    assert plan.execution_order[-1] == "f"  # Must end with f

    # Check parallelization opportunities
    parallel_groups = [g for g in plan.parallel_groups if g.can_parallelize]
    assert len(parallel_groups) >= 2  # At least b,c and d,e can parallelize
