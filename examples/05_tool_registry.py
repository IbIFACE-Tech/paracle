"""Example: Advanced BuiltinToolRegistry usage.

This example demonstrates advanced features of BuiltinToolRegistry:
- Custom configuration per tool category
- Dynamic tool selection
- Permission management
- Tool metadata and introspection
- Error handling patterns

Run: uv run python examples/05_tool_registry.py
"""

import asyncio
from pathlib import Path

from paracle_tools import BuiltinToolRegistry


async def basic_registry_usage():
    """Demonstrate basic registry operations."""
    print("=" * 70)
    print("1. BASIC REGISTRY USAGE")
    print("=" * 70)

    # Create registry with default configuration
    registry = BuiltinToolRegistry()

    # List all available tools
    print("\n📦 Available tools:")
    tool_names = registry.list_tool_names()
    print(f"   Total: {len(tool_names)} tools")
    for name in tool_names:
        print(f"   - {name}")

    # Get tool details
    print("\n🔍 Tool details:")
    for name in ["read_file", "http_get", "run_command"]:
        tool = registry.get_tool(name)
        if tool:
            print(f"\n   {tool.name}:")
            print(f"   Description: {tool.description}")
            print(f"   Parameters: {list(tool.parameters.keys())}")

    # Check tool availability
    print("\n✅ Tool availability checks:")
    print(f"   Has read_file: {registry.has_tool('read_file')}")
    print(f"   Has write_file: {registry.has_tool('write_file')}")
    print(f"   Has nonexistent_tool: {registry.has_tool('nonexistent_tool')}")


async def categorized_tools():
    """Demonstrate tool categorization."""
    print("\n" + "=" * 70)
    print("2. CATEGORIZED TOOLS")
    print("=" * 70)

    registry = BuiltinToolRegistry()

    # Get tools by category
    categories = registry.get_tools_by_category()

    print("\n📂 Tools by category:")
    for category, tool_names in categories.items():
        print(f"\n   {category.upper()} ({len(tool_names)} tools):")
        for name in tool_names:
            tool = registry.get_tool(name)
            print(f"      - {name}: {tool.description}")


async def security_configuration():
    """Demonstrate security and permission configuration."""
    print("\n" + "=" * 70)
    print("3. SECURITY CONFIGURATION")
    print("=" * 70)

    # Create registry with strict security settings
    registry = BuiltinToolRegistry(
        # Restrict filesystem access
        filesystem_paths=["./examples", "./tests"],

        # Whitelist only safe commands
        allowed_commands=["echo", "git", "ls", "dir", "python"],

        # Set conservative timeouts
        http_timeout=10.0,
        command_timeout=5.0
    )

    print("\n🔒 Security settings applied:")
    print("   Filesystem paths: ./examples, ./tests")
    print("   Allowed commands: echo, git, ls, dir, python")
    print("   HTTP timeout: 10.0s")
    print("   Command timeout: 5.0s")

    # Check tool permissions
    print("\n🛡️ Tool permissions:")
    for tool_name in ["read_file", "http_get", "run_command"]:
        permissions = registry.get_tool_permissions(tool_name)
        print(f"   {tool_name}: {permissions}")

    # Test restricted filesystem access
    print("\n🧪 Testing restrictions:")

    # Allowed path
    result = await registry.execute_tool(
        "read_file",
        path="examples/01_filesystem_tools.py"
    )
    print(f"   Read allowed path: {result.success}")

    # Restricted path (should fail)
    result = await registry.execute_tool(
        "read_file",
        path="/etc/passwd"
    )
    print(f"   Read restricted path: {result.success}")
    if not result.success:
        print(f"   ✓ Correctly blocked: {result.error[:60]}...")

    # Allowed command
    result = await registry.execute_tool(
        "run_command",
        command="echo test"
    )
    print(f"   Run allowed command: {result.success}")

    # Blocked command
    result = await registry.execute_tool(
        "run_command",
        command="rm -rf /"
    )
    print(f"   Run dangerous command: {result.success}")
    if not result.success:
        print(f"   ✓ Correctly blocked: {result.error[:60]}...")


async def dynamic_tool_selection():
    """Demonstrate dynamic tool selection based on task."""
    print("\n" + "=" * 70)
    print("4. DYNAMIC TOOL SELECTION")
    print("=" * 70)

    registry = BuiltinToolRegistry()

    # Define task requirements
    tasks = [
        {"type": "file_read", "tool": "read_file", "path": "README.md"},
        {"type": "api_call", "tool": "http_get", "url": "https://api.github.com"},
        {"type": "command", "tool": "run_command", "command": "git status --short"},
    ]

    print("\n🎯 Executing tasks dynamically:")

    for task in tasks:
        tool_name = task["tool"]

        # Check if tool exists
        if not registry.has_tool(tool_name):
            print(f"   ❌ Tool '{tool_name}' not available")
            continue

        # Get tool
        tool = registry.get_tool(tool_name)
        print(f"\n   📍 Task: {task['type']}")
        print(f"      Tool: {tool.name}")

        # Prepare parameters (exclude 'type' and 'tool')
        params = {k: v for k, v in task.items() if k not in ['type', 'tool']}

        # Execute
        result = await registry.execute_tool(tool_name, **params)

        if result.success:
            print(f"      ✅ Success")
        else:
            print(f"      ❌ Failed: {result.error[:50]}...")


async def error_handling_patterns():
    """Demonstrate error handling patterns."""
    print("\n" + "=" * 70)
    print("5. ERROR HANDLING PATTERNS")
    print("=" * 70)

    registry = BuiltinToolRegistry()

    print("\n🔧 Testing error scenarios:")

    # Non-existent tool
    print("\n   1. Non-existent tool:")
    result = await registry.execute_tool("nonexistent_tool")
    print(f"      Success: {result.success}")
    print(f"      Error: {result.error}")

    # Invalid parameters
    print("\n   2. Missing required parameter:")
    result = await registry.execute_tool("read_file")  # Missing 'path'
    print(f"      Success: {result.success}")
    print(f"      Error: {result.error[:100]}...")

    # File not found
    print("\n   3. File not found:")
    result = await registry.execute_tool(
        "read_file",
        path="nonexistent_file_12345.txt"
    )
    print(f"      Success: {result.success}")
    print(f"      Error: {result.error}")

    # Network error (invalid URL)
    print("\n   4. Network error:")
    result = await registry.execute_tool(
        "http_get",
        url="https://invalid-domain-xyz-12345.com"
    )
    print(f"      Success: {result.success}")
    print(f"      Error: {result.error[:100]}...")


async def batch_operations():
    """Demonstrate batch tool execution."""
    print("\n" + "=" * 70)
    print("6. BATCH OPERATIONS")
    print("=" * 70)

    registry = BuiltinToolRegistry()

    print("\n⚡ Executing multiple operations in parallel:")

    # Define multiple operations
    operations = [
        ("read_file", {"path": "pyproject.toml"}),
        ("list_directory", {"path": "examples"}),
        ("run_command", {"command": "git log -1 --oneline"}),
    ]

    # Execute all in parallel
    tasks = [
        registry.execute_tool(tool_name, **params)
        for tool_name, params in operations
    ]

    results = await asyncio.gather(*tasks)

    # Process results
    for (tool_name, params), result in zip(operations, results):
        print(f"\n   {tool_name}:")
        if result.success:
            print(f"      ✅ Success")
            # Show snippet of output
            if 'content' in result.output:
                lines = result.output['content'].split('\n')[:2]
                print(f"      Preview: {lines[0][:60]}...")
            elif 'stdout' in result.output:
                print(f"      Output: {result.output['stdout'].strip()[:60]}...")
            elif 'count' in result.output:
                print(f"      Found: {result.output['count']} items")
        else:
            print(f"      ❌ Failed: {result.error[:50]}...")


async def runtime_reconfiguration():
    """Demonstrate runtime reconfiguration."""
    print("\n" + "=" * 70)
    print("7. RUNTIME RECONFIGURATION")
    print("=" * 70)

    registry = BuiltinToolRegistry()

    print("\n🔄 Initial configuration:")
    print("   Filesystem paths: (unrestricted)")
    print("   Allowed commands: (default whitelist)")

    # Test access
    result = await registry.execute_tool("read_file", path="/etc/hosts")
    print(f"   Can read /etc/hosts: {result.success}")

    # Reconfigure filesystem paths
    print("\n🔄 Reconfiguring filesystem paths...")
    registry.configure_filesystem_paths(["./examples", "./tests"])
    print("   Filesystem paths: ./examples, ./tests")

    # Test access again
    result = await registry.execute_tool("read_file", path="/etc/hosts")
    print(f"   Can read /etc/hosts: {result.success}")
    if not result.success:
        print(f"   ✓ Access denied: {result.error[:50]}...")

    # Reconfigure allowed commands
    print("\n🔄 Reconfiguring allowed commands...")
    registry.configure_allowed_commands(["echo", "ls"])
    print("   Allowed commands: echo, ls")

    result = await registry.execute_tool("run_command", command="python --version")
    print(f"   Can run python: {result.success}")
    if not result.success:
        print(f"   ✓ Command blocked: {result.error[:50]}...")


async def tool_introspection():
    """Demonstrate tool introspection and metadata."""
    print("\n" + "=" * 70)
    print("8. TOOL INTROSPECTION")
    print("=" * 70)

    registry = BuiltinToolRegistry()

    # Get all tools
    all_tools = registry.list_tools()

    print(f"\n📊 Tool metadata summary:")
    print(f"   Total tools: {len(all_tools)}")

    # Categorize by permission
    perms_count = {}
    for tool_info in all_tools:
        tool_name = tool_info['name']
        permissions = registry.get_tool_permissions(tool_name)
        for perm in permissions:
            perms_count[perm] = perms_count.get(perm, 0) + 1

    print(f"\n   Tools by permission:")
    for perm, count in sorted(perms_count.items()):
        print(f"      {perm}: {count} tools")

    # Show detailed info for one tool
    print(f"\n📖 Detailed tool info (read_file):")
    tool = registry.get_tool("read_file")
    print(f"   Name: {tool.name}")
    print(f"   Description: {tool.description}")
    print(f"   Parameters:")
    for param_name, param_info in tool.parameters.items():
        required = param_info.get('required', False)
        param_type = param_info.get('type', 'any')
        req_marker = "required" if required else "optional"
        print(f"      - {param_name} ({param_type}, {req_marker})")
        if 'description' in param_info:
            print(f"        {param_info['description']}")


async def main():
    """Run all examples."""
    await basic_registry_usage()
    await categorized_tools()
    await security_configuration()
    await dynamic_tool_selection()
    await error_handling_patterns()
    await batch_operations()
    await runtime_reconfiguration()
    await tool_introspection()

    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nKey takeaways:")
    print("- BuiltinToolRegistry provides centralized tool management")
    print("- Security can be configured at registry level")
    print("- Tools can be inspected and selected dynamically")
    print("- Configuration can be changed at runtime")
    print("- Batch operations enable parallel execution")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
