"""Test MCP Paracle tools with real workflow execution.

This script tests the MCP Paracle tools for workflow execution.
"""

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_mcp_workflow")


async def test_mcp_workflow_list():
    """Test listing workflows via MCP."""
    print("\n" + "="*70)
    print("🧪 TEST: MCP workflow_list")
    print("="*70 + "\n")

    try:
        from paracle_mcp.server import ParacleMCPServer

        server = ParacleMCPServer()

        # Get workflow tools
        tools = server._get_workflow_tools()
        workflow_list_tool = next(
            t for t in tools if t["name"] == "workflow_list")

        print("✅ Found workflow_list tool")
        print(f"   Description: {workflow_list_tool['description']}")

        # Try to execute (simulate)
        print("\n📋 Available workflows in catalog:")

        catalog_path = server.parac_root / "workflows" / "catalog.yaml"
        if catalog_path.exists():
            import yaml
            with open(catalog_path) as f:
                catalog = yaml.safe_load(f)

            for idx, wf in enumerate(catalog.get("workflows", []), 1):
                status = wf.get("status", "unknown")
                emoji = "✅" if status == "active" else "⚠️"
                print(f"   {emoji} {idx}. {wf['name']}")
                print(f"      Category: {wf.get('category', 'N/A')}")
                print(f"      Status: {status}")
                print(f"      File: {wf.get('file', 'N/A')}")
                print()

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_context_tools():
    """Test context tools via MCP."""
    print("\n" + "="*70)
    print("🧪 TEST: MCP context tools")
    print("="*70 + "\n")

    try:
        from paracle_mcp.server import ParacleMCPServer

        server = ParacleMCPServer()

        # Get context tools
        tools = server._get_context_tools()

        print(f"✅ Found {len(tools)} context tools:\n")

        for tool in tools:
            print(f"   📦 {tool['name']}")
            print(f"      {tool['description']}")
            print()

        # Test reading current_state
        print("📋 Testing context_current_state:")
        state_path = server.parac_root / "memory" / "context" / "current_state.yaml"

        if state_path.exists():
            import yaml
            with open(state_path) as f:
                state = yaml.safe_load(f)

            print("   ✅ Current state loaded")
            print(f"      Version: {state.get('version', 'N/A')}")
            print(f"      Project: {state['project']['name']}")
            print(f"      Phase: {state['project']['phase']}")
            print(f"      Status: {state['project']['status']}")

            # Show recent update
            if state.get("recent_updates"):
                latest = state["recent_updates"][0]
                print("\n   📰 Latest update:")
                print(f"      Date: {latest['date']}")
                print(f"      {latest['update']}")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_tool_registry():
    """Test agent tool registry."""
    print("\n" + "="*70)
    print("🧪 TEST: Agent Tool Registry")
    print("="*70 + "\n")

    try:
        from paracle_orchestration.agent_tool_registry import agent_tool_registry

        agents = agent_tool_registry.list_agents()

        print(f"✅ Loaded {len(agents)} agents:\n")

        for agent_id in agents:
            tools = agent_tool_registry.get_tools_for_agent(agent_id)
            # Handle both string names and tool objects
            tool_names = [t if isinstance(t, str) else t.name for t in tools]

            print(f"   🤖 {agent_id}")
            print(f"      Tools: {len(tools)}")
            print(f"      {', '.join(tool_names[:5])}")
            if len(tool_names) > 5:
                print(f"      ... and {len(tool_names) - 5} more")
            print()

        # Test getting tools for specific agent
        print("📋 Testing reviewer agent tools:")
        reviewer_tools = agent_tool_registry.get_tools_for_agent("reviewer")

        for tool in reviewer_tools:
            tool_name = tool if isinstance(tool, str) else tool.name
            tool_desc = "Tool function" if isinstance(
                tool, str) else getattr(tool, 'description', 'No description')
            print(f"   ✅ {tool_name}")
            print(f"      {tool_desc}")
            print()

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_real_workflow_parsing():
    """Test parsing a real workflow definition."""
    print("\n" + "="*70)
    print("🧪 TEST: Real Workflow Parsing")
    print("="*70 + "\n")

    try:
        workflow_path = Path(".parac/workflows/definitions/bugfix.yaml")

        if not workflow_path.exists():
            print(f"❌ Workflow not found: {workflow_path}")
            return False

        import yaml
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        print(f"✅ Loaded workflow: {workflow['name']}")
        print(f"   Version: {workflow.get('version', 'N/A')}")
        print(f"   Description: {workflow.get('description', 'N/A')[:100]}...")

        print(f"\n📋 Workflow steps ({len(workflow['steps'])}):\n")

        for idx, step in enumerate(workflow["steps"], 1):
            print(f"   [{idx}] {step['id']}")
            print(f"       Agent: {step['agent']}")
            print(f"       Config: model={step['config'].get('model', 'N/A')}, "
                  f"temp={step['config'].get('temperature', 'N/A')}")

            if step.get("depends_on"):
                print(f"       Depends on: {', '.join(step['depends_on'])}")

            if step.get("tools"):
                tool_names = [t.get("name", "unknown") for t in step["tools"]]
                print(f"       Tools: {', '.join(tool_names)}")

            print()

        # Test inputs
        if workflow.get("inputs"):
            print("📥 Required inputs:")
            for input_name, input_spec in workflow["inputs"].items():
                required = "✅ Required" if input_spec.get(
                    "required") else "⚪ Optional"
                print(
                    f"   {required} {input_name}: {input_spec.get('type', 'any')}")
                if input_spec.get("description"):
                    print(f"      {input_spec['description']}")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_github_agent_integration():
    """Test GitHub agent integration with workflows."""
    print("\n" + "="*70)
    print("🧪 TEST: GitHub Agent → Paracle Workflow")
    print("="*70 + "\n")

    try:
        # Load GitHub agent
        github_agent_path = Path(".github/agents/security.agent.md")

        if not github_agent_path.exists():
            print(f"❌ GitHub agent not found: {github_agent_path}")
            return False

        with open(github_agent_path, encoding="utf-8") as f:
            content = f.read()

        print("✅ Loaded GitHub agent: security.agent.md")

        # Parse frontmatter
        import re
        match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)

        if match:
            import yaml
            frontmatter = yaml.safe_load(match.group(1))

            print(f"   Description: {frontmatter.get('description', 'N/A')}")
            print(f"   Tools: {len(frontmatter.get('tools', []))}")

            if frontmatter.get("handoffs"):
                print(f"\n📤 Handoffs ({len(frontmatter['handoffs'])}):")
                for handoff in frontmatter["handoffs"]:
                    print(f"   → {handoff['label']} to {handoff['agent']}")

        # Check if security agent can work with code_review workflow
        print("\n🔄 Testing compatibility with code_review workflow...")

        workflow_path = Path(".parac/workflows/definitions/code_review.yaml")
        import yaml
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        # Find steps using security agent
        security_steps = [s for s in workflow["steps"]
                          if "security" in s["id"].lower()]

        if security_steps:
            print(
                f"   ✅ Found {len(security_steps)} security steps in workflow:")
            for step in security_steps:
                print(f"      - {step['id']}: {step['name']}")
        else:
            print("   ⚠️  No explicit security steps, but security agent can be added")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all MCP tests."""
    print("\n🚀 Starting MCP Paracle Tools Tests\n")

    tests = [
        ("Workflow List", test_mcp_workflow_list),
        ("Context Tools", test_mcp_context_tools),
        ("Agent Tool Registry", test_agent_tool_registry),
        ("Workflow Parsing", test_real_workflow_parsing),
        ("GitHub Agent Integration", test_github_agent_integration),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*70)
    print("🏁 TEST RESULTS SUMMARY")
    print("="*70)

    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for s in results.values() if s)

    print(f"\n📊 Total: {passed}/{total} tests passed")
    print("="*70 + "\n")

    return all(results.values())


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted")
        exit(130)
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
