#!/usr/bin/env python3
"""Execute a workflow from YAML definition.

Usage:
    python run_workflow.py workflow.yaml
    python run_workflow.py workflow.yaml --context '{"user_id": "123"}'
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import yaml


class WorkflowRunner:
    """Simple workflow runner for testing."""

    def __init__(self, workflow_def: dict[str, Any]):
        self.workflow = workflow_def
        self.results = {}

    async def execute_step(self, step: dict[str, Any]) -> Any:
        """Execute a single workflow step."""
        step_id = step["id"]
        agent_id = step["agent"]

        print(f"  ▶ Executing step: {step_id} (agent: {agent_id})")

        # Simulate step execution
        await asyncio.sleep(0.5)

        result = {"status": "success", "output": f"Result from {step_id}"}
        self.results[step_id] = result

        print(f"    ✓ Step {step_id} completed")
        return result

    async def run(self, context: dict[str, Any] = None):
        """Execute the workflow."""
        name = self.workflow["name"]
        print(f"\n🚀 Starting workflow: {name}")

        if context:
            print(f"   Context: {context}")

        steps = self.workflow["steps"]

        for step in steps:
            try:
                await self.execute_step(step)
            except Exception as e:
                print(f"    ✗ Step {step['id']} failed: {e}")
                if step.get("on_error") != "continue":
                    raise

        print(f"\n✅ Workflow '{name}' completed successfully!")
        return self.results


async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_workflow.py workflow.yaml [--context JSON]")
        sys.exit(1)

    workflow_file = Path(sys.argv[1])

    # Parse context if provided
    context = {}
    if "--context" in sys.argv:
        context_idx = sys.argv.index("--context") + 1
        context = json.loads(sys.argv[context_idx])

    # Load workflow
    with open(workflow_file) as f:
        workflow_def = yaml.safe_load(f)

    # Execute
    runner = WorkflowRunner(workflow_def)
    results = await runner.run(context)

    print("\n📊 Results:")
    for step_id, result in results.items():
        print(f"  {step_id}: {result['status']}")


if __name__ == "__main__":
    asyncio.run(main())
