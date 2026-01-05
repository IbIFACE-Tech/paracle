"""Tests for DAG validation and topological sorting."""

import pytest

from paracle_domain.models import WorkflowStep
from paracle_orchestration.dag import DAG
from paracle_orchestration.exceptions import CircularDependencyError, InvalidWorkflowError


def make_step(name: str, agent: str | None = None, **kwargs) -> WorkflowStep:
    """Helper to create WorkflowStep with id defaulting to name."""
    return WorkflowStep(id=name, name=name, agent=agent or name, **kwargs)


class TestDAGConstruction:
    """Test DAG construction and graph building."""

    def test_dag_builds_graph_from_steps(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
        ]

        # Act
        dag = DAG(steps)

        # Assert
        assert "step1" in dag.graph
        assert "step2" in dag.graph
        assert "step3" in dag.graph
        assert dag.graph["step1"] == []
        assert dag.graph["step2"] == ["step1"]
        assert dag.graph["step3"] == ["step1"]

    def test_dag_builds_reverse_graph(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
        ]

        # Act
        dag = DAG(steps)

        # Assert
        assert dag.reverse_graph["step1"] == ["step2", "step3"]
        assert "step2" not in dag.reverse_graph
        assert "step3" not in dag.reverse_graph


class TestDAGValidation:
    """Test DAG validation for correctness."""

    def test_validate_passes_for_valid_dag(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act & Assert (should not raise)
        dag.validate()

    def test_validate_raises_for_missing_dependency(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["nonexistent"]),
        ]
        dag = DAG(steps)

        # Act & Assert
        with pytest.raises(
            InvalidWorkflowError,
            match="Step 'step2' depends on non-existent step 'nonexistent'",
        ):
            dag.validate()

    def test_validate_detects_simple_cycle(self):
        # Arrange
        steps = [
            make_step("step1", depends_on=["step2"]),
            make_step("step2", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act & Assert
        with pytest.raises(CircularDependencyError):
            dag.validate()

    def test_validate_detects_complex_cycle(self):
        # Arrange
        steps = [
            make_step("step1", depends_on=["step3"]),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step2"]),
        ]
        dag = DAG(steps)

        # Act & Assert
        with pytest.raises(CircularDependencyError):
            dag.validate()

    def test_validate_allows_diamond_dependency(self):
        # Arrange
        # step1 -> step2 -> step4
        #      \-> step3 -/
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
            make_step("step4", depends_on=["step2", "step3"]),
        ]
        dag = DAG(steps)

        # Act & Assert (should not raise)
        dag.validate()


class TestTopologicalSort:
    """Test topological sorting."""

    def test_topological_sort_simple_chain(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step2"]),
        ]
        dag = DAG(steps)

        # Act
        sorted_steps = dag.topological_sort()

        # Assert
        assert sorted_steps == ["step1", "step2", "step3"]

    def test_topological_sort_parallel_branches(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act
        sorted_steps = dag.topological_sort()

        # Assert
        assert sorted_steps[0] == "step1"
        assert set(sorted_steps[1:]) == {"step2", "step3"}

    def test_topological_sort_raises_for_cycle(self):
        # Arrange
        steps = [
            make_step("step1", depends_on=["step2"]),
            make_step("step2", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act & Assert
        with pytest.raises(CircularDependencyError):
            dag.topological_sort()


class TestExecutionLevels:
    """Test execution level grouping for parallel execution."""

    def test_get_execution_levels_linear_workflow(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step2"]),
        ]
        dag = DAG(steps)

        # Act
        levels = dag.get_execution_levels()

        # Assert
        assert len(levels) == 3
        assert levels[0] == ["step1"]
        assert levels[1] == ["step2"]
        assert levels[2] == ["step3"]

    def test_get_execution_levels_parallel_workflow(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act
        levels = dag.get_execution_levels()

        # Assert
        assert len(levels) == 2
        assert levels[0] == ["step1"]
        assert set(levels[1]) == {"step2", "step3"}

    def test_get_execution_levels_diamond_workflow(self):
        # Arrange
        # step1 -> step2 -> step4
        #      \-> step3 -/
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
            make_step("step4", depends_on=["step2", "step3"]),
        ]
        dag = DAG(steps)

        # Act
        levels = dag.get_execution_levels()

        # Assert
        assert len(levels) == 3
        assert levels[0] == ["step1"]
        assert set(levels[1]) == {"step2", "step3"}
        assert levels[2] == ["step4"]

    def test_get_execution_levels_raises_for_cycle(self):
        # Arrange
        steps = [
            make_step("step1", depends_on=["step2"]),
            make_step("step2", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act & Assert
        with pytest.raises(CircularDependencyError):
            dag.get_execution_levels()


class TestReadySteps:
    """Test getting ready-to-execute steps."""

    def test_get_ready_steps_at_start(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act
        ready = dag.get_ready_steps(set())

        # Assert
        assert ready == ["step1"]

    def test_get_ready_steps_after_first_completes(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act
        ready = dag.get_ready_steps({"step1"})

        # Assert
        assert set(ready) == {"step2", "step3"}

    def test_get_ready_steps_with_multiple_dependencies(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2"),
            make_step("step3", depends_on=["step1", "step2"]),
        ]
        dag = DAG(steps)

        # Act
        ready_start = dag.get_ready_steps(set())
        ready_one_done = dag.get_ready_steps({"step1"})
        ready_both_done = dag.get_ready_steps({"step1", "step2"})

        # Assert
        assert set(ready_start) == {"step1", "step2"}
        assert ready_one_done == ["step2"]  # step2 has no dependencies, step3 needs both
        assert ready_both_done == ["step3"]


class TestDependencyQueries:
    """Test dependency and dependent queries."""

    def test_get_dependencies(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act & Assert
        assert dag.get_dependencies("step1") == []
        assert dag.get_dependencies("step2") == ["step1"]

    def test_get_dependents(self):
        # Arrange
        steps = [
            make_step("step1"),
            make_step("step2", depends_on=["step1"]),
            make_step("step3", depends_on=["step1"]),
        ]
        dag = DAG(steps)

        # Act & Assert
        assert dag.get_dependents("step1") == ["step2", "step3"]
        assert dag.get_dependents("step2") == []
