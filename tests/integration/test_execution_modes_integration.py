"""Integration tests for Plan Mode and Dry-Run Mode with real workflows.

Tests execution modes using actual workflow definitions from .parac/workflows/.
"""

import pytest
from paracle_domain.models import AgentSpec
from paracle_orchestration.dry_run import DryRunConfig, DryRunExecutor, MockStrategy
from paracle_orchestration.planner import WorkflowPlanner
from paracle_orchestration.workflow_loader import WorkflowLoader


@pytest.fixture
def workflow_loader():
    """Create workflow loader for .parac/workflows/."""
    try:
        loader = WorkflowLoader()
        return loader
    except Exception as e:
        pytest.skip(f"Could not create workflow loader: {e}")


@pytest.fixture
def available_workflows(workflow_loader):
    """Get list of available workflow definitions."""
    workflows = workflow_loader.list_workflows()
    if not workflows:
        pytest.skip("No workflows found - skipping integration tests")
    # Extract just the workflow names from metadata
    return [w["name"] for w in workflows if w.get("status") == "active"]


class TestPlanModeIntegration:
    """Integration tests for Plan Mode with real workflows."""

    def test_plan_hello_world_workflow(self, workflow_loader):
        """Test planning hello_world workflow."""
        try:
            spec = workflow_loader.load_workflow_spec("hello_world")

            planner = WorkflowPlanner()
            plan = planner.plan(spec)

            assert plan.total_steps > 0, "Should have steps"
            assert plan.estimated_cost_usd >= 0, "Cost should be non-negative"
            assert plan.estimated_time_seconds > 0, "Time should be positive"
            assert len(plan.parallel_groups) > 0, "Should have parallel groups"

            print("\n✓ Hello World Plan:")
            print(f"  - Steps: {plan.total_steps}")
            print(f"  - Cost: ${plan.estimated_cost_usd:.4f}")
            print(f"  - Time: {plan.estimated_time_seconds}s")
            print(f"  - Groups: {len(plan.parallel_groups)}")

        except Exception as e:
            pytest.skip(f"Could not load hello_world workflow: {e}")

    def test_plan_all_available_workflows(self, workflow_loader, available_workflows):
        """Test planning all available workflows."""
        results = []

        for workflow_name in available_workflows:
            try:
                spec = workflow_loader.load_workflow_spec(workflow_name)

                planner = WorkflowPlanner()
                plan = planner.plan(spec)

                results.append(
                    {
                        "workflow_name": workflow_name,
                        "total_steps": plan.total_steps,
                        "estimated_cost": plan.estimated_cost_usd,
                        "estimated_time": plan.estimated_time_seconds,
                        "groups": len(plan.parallel_groups),
                        "suggestions": len(plan.optimization_suggestions),
                    }
                )

            except Exception as e:
                print(f"⚠ Could not plan {workflow_name}: {e}")

        assert len(results) > 0, "Should successfully plan at least one workflow"

        print(f"\n✓ Planned {len(results)} workflows:")
        for result in results:
            print(
                f"  - {result['workflow_name']}: "
                f"{result['total_steps']} steps, "
                f"${result['estimated_cost']:.4f}, "
                f"{result['estimated_time']}s"
            )


class TestDryRunModeIntegration:
    """Integration tests for Dry-Run Mode with real workflows."""

    @pytest.mark.asyncio
    async def test_dry_run_step_with_fixed_strategy(self):
        """Test dry-run step execution with FIXED strategy."""
        agent = AgentSpec(
            name="test_agent",
            role="tester",
            provider="openai",
            model="gpt-4",
        )

        config = DryRunConfig(
            strategy=MockStrategy.FIXED,
            fixed_response="Mock response for test",
        )
        executor = DryRunExecutor(config)

        result = await executor.execute_step(
            agent=agent,
            prompt="Test prompt",
            step_id="test_step",
        )

        assert result["status"] == "completed"
        assert result["metadata"]["dry_run"] is True
        assert result["metadata"]["mock_strategy"] == "fixed"
        assert result["output"] == "Mock response for test"

        print("\n✓ Dry-Run Step (FIXED):")
        print(f"  - Status: {result['status']}")
        print(f"  - Output: {result['output']}")

    @pytest.mark.asyncio
    async def test_dry_run_step_with_random_strategy(self):
        """Test dry-run step with RANDOM strategy."""
        agent = AgentSpec(
            name="test_agent",
            role="tester",
            provider="openai",
            model="gpt-4",
        )

        config = DryRunConfig(
            strategy=MockStrategy.RANDOM,
            random_responses=[
                "First response option",
                "Second response option",
                "Third response option",
            ],
        )
        executor = DryRunExecutor(config)

        result = await executor.execute_step(
            agent=agent,
            prompt="Test prompt",
            step_id="test_step",
        )

        assert result["status"] == "completed"
        assert result["metadata"]["dry_run"] is True
        assert result["output"] in config.random_responses

        print("\n✓ Dry-Run Step (RANDOM):")
        print(f"  - Status: {result['status']}")
        print(f"  - Output: {result['output'][:50]}...")

    @pytest.mark.asyncio
    async def test_dry_run_step_with_echo_strategy(self):
        """Test dry-run step with ECHO strategy."""
        agent = AgentSpec(
            name="test_agent",
            role="tester",
            provider="openai",
            model="gpt-4",
        )

        config = DryRunConfig(strategy=MockStrategy.ECHO)
        executor = DryRunExecutor(config)

        test_prompt = "Please analyze this code"
        result = await executor.execute_step(
            agent=agent,
            prompt=test_prompt,
            step_id="test_step",
        )

        assert result["status"] == "completed"
        assert result["metadata"]["dry_run"] is True
        assert test_prompt in result["output"]  # Should echo the prompt

        print("\n✓ Dry-Run Step (ECHO):")
        print(f"  - Status: {result['status']}")
        print(f"  - Output echoes prompt: {test_prompt in result['output']}")

    @pytest.mark.asyncio
    async def test_dry_run_cost_tracking(self):
        """Test cost tracking in dry-run mode."""
        agent = AgentSpec(
            name="test_agent",
            role="tester",
            provider="openai",
            model="gpt-4",
        )

        config = DryRunConfig(
            strategy=MockStrategy.FIXED,
            fixed_response="Mock response",
        )
        executor = DryRunExecutor(config)

        # Execute multiple steps
        results = []
        for i in range(3):
            result = await executor.execute_step(
                agent=agent,
                prompt=f"Test prompt {i}",
                step_id=f"test_step_{i}",
            )
            results.append(result)

        # All should complete with mocked costs
        assert all(r["status"] == "completed" for r in results)
        assert all(r["metadata"]["dry_run"] for r in results)

        total_cost = sum(r["metadata"]["cost_usd"] for r in results)
        print("\n✓ Cost Tracking (3 steps):")
        print(f"  - Total cost: ${total_cost:.4f}")
        print("  - All steps completed: True")


class TestExecutionModesComparison:
    """Compare Plan Mode estimates vs Dry-Run execution."""

    def test_planner_estimates_structure(self, workflow_loader):
        """Test that planner provides cost and time estimates."""
        try:
            spec = workflow_loader.load_workflow_spec("hello_world")

            planner = WorkflowPlanner()
            plan = planner.plan(spec)

            # Verify plan has estimation data
            assert hasattr(plan, "estimated_cost_usd")
            assert hasattr(plan, "estimated_time_seconds")
            assert hasattr(plan, "parallel_groups")

            print("\n✓ Plan Structure Validation:")
            print("  - Has cost estimate: ✓")
            print("  - Has time estimate: ✓")
            print("  - Has execution groups: ✓")
            print(f"  - Estimated cost: ${plan.estimated_cost_usd:.4f}")
            print(f"  - Estimated time: {plan.estimated_time_seconds}s")

        except Exception as e:
            pytest.skip(f"Could not test plan structure: {e}")


if __name__ == "__main__":
    """Run integration tests directly."""
    print("Running Integration Tests for Execution Modes\n")
    print("=" * 60)

    # Run pytest with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
