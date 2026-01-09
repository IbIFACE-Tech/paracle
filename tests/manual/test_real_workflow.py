#!/usr/bin/env python3
"""
Real Workflow Execution Test

Test a real workflow execution with GitHub agents.
Uses the hello_world workflow as a simple starting point.
"""

import asyncio
import os
import sys
from pathlib import Path


async def test_real_workflow_execution():
    """Test real workflow execution."""

    print("\n" + "=" * 70)
    print("🚀 REAL WORKFLOW EXECUTION TEST")
    print("=" * 70 + "\n")

    # Set API key check
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY=sk-...")
        print("   Continuing with mock execution...\n")
    else:
        print(f"✅ OpenAI API key found: {api_key[:10]}...{api_key[-4:]}\n")

    # Load workflow
    workflow_path = Path(".parac/workflows/templates/hello_world.yaml")

    if not workflow_path.exists():
        print(f"❌ Workflow not found: {workflow_path}")
        return False

    import yaml

    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)

    print(f"📋 Workflow: {workflow['name']}")
    print(f"   Description: {workflow.get('description', 'N/A')}")
    print(f"   Steps: {len(workflow.get('steps', []))}")
    print()

    # Try to execute via Paracle CLI
    print("🔄 Attempting real execution via Paracle CLI...")
    print()

    try:
        from click.testing import CliRunner
        from paracle_cli.main import cli

        runner = CliRunner()

        # Run workflow
        result = runner.invoke(
            cli, ["workflow", "run", "hello_world", "--dry-run"]  # Dry run first
        )

        print("📤 CLI Output:")
        print(result.output)

        if result.exit_code == 0:
            print("\n✅ Dry run successful!")
            print("\n💡 Next: Remove --dry-run to execute for real")
        else:
            print(f"\n⚠️  Exit code: {result.exit_code}")
            if result.exception:
                print(f"   Exception: {result.exception}")

        return result.exit_code == 0

    except ImportError as e:
        print(f"⚠️  CLI not available: {e}")
        print("   This is expected if paracle CLI is not installed")
        return test_manual_orchestration()


async def test_manual_orchestration():
    """Test manual orchestration without CLI."""

    print("\n📋 Testing manual orchestration...\n")

    try:
        from paracle_domain.models import WorkflowSpec
        from paracle_orchestration.orchestrator import Orchestrator

        # Load workflow
        workflow_path = Path(".parac/workflows/templates/hello_world.yaml")
        import yaml

        with open(workflow_path) as f:
            workflow_data = yaml.safe_load(f)

        print(f"✅ Loaded workflow: {workflow_data['name']}")

        # Create workflow spec
        workflow_spec = WorkflowSpec(**workflow_data)
        print("✅ Created WorkflowSpec")
        print(f"   Steps: {len(workflow_spec.steps)}")

        # Create orchestrator
        orchestrator = Orchestrator()
        print("✅ Created Orchestrator")

        # Execute (dry run)
        print("\n🔄 Executing workflow (dry-run)...\n")

        result = await orchestrator.execute(workflow_spec, inputs={}, dry_run=True)

        print("✅ Execution completed!")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Steps executed: {len(result.get('steps', []))}")

        return True

    except Exception as e:
        print(f"❌ Manual orchestration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def show_available_workflows():
    """Show all available workflows."""

    print("\n" + "=" * 70)
    print("📚 AVAILABLE WORKFLOWS")
    print("=" * 70 + "\n")

    catalog_path = Path(".parac/workflows/catalog.yaml")

    if not catalog_path.exists():
        print("❌ Catalog not found")
        return

    import yaml

    with open(catalog_path) as f:
        catalog = yaml.safe_load(f)

    workflows = catalog.get("workflows", [])
    active = [w for w in workflows if w.get("status") == "active"]

    print(f"Total workflows: {len(workflows)}")
    print(f"Active workflows: {len(active)}\n")

    print("🎯 Recommended for testing:\n")

    test_workflows = [
        ("hello_world", "Simplest workflow (1 step)"),
        ("code_review", "Real-world quality workflow (6 steps)"),
        ("bugfix", "Complete dev workflow (5 steps)"),
    ]

    for name, desc in test_workflows:
        wf = next((w for w in workflows if w["name"] == name), None)
        if wf:
            status_emoji = "✅" if wf.get("status") == "active" else "⚠️"
            print(f"   {status_emoji} {name}")
            print(f"      {desc}")
            print(f"      File: {wf.get('file', 'N/A')}")
            print()


async def main():
    """Run tests."""

    print("\n🧪 Paracle Real Workflow Execution Tests\n")

    # Show available workflows
    await show_available_workflows()

    # Test execution
    success = await test_real_workflow_execution()

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    if success:
        print("\n✅ Workflow execution test PASSED")
        print("\n💡 Next steps:")
        print("   1. Run without --dry-run for real execution")
        print("   2. Set OPENAI_API_KEY for live LLM calls")
        print("   3. Test with code_review workflow")
    else:
        print("\n⚠️  Workflow execution test had issues")
        print("\n💡 Troubleshooting:")
        print("   1. Check .parac/workflows/ exists")
        print("   2. Verify agents in .github/agents/")
        print("   3. Install dependencies: uv sync")

    print("\n" + "=" * 70 + "\n")

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
