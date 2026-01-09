"""AI Compliance Example - VS Code Copilot Integration.

This example demonstrates how the AI Compliance Engine integrates with
VS Code Copilot to prevent .parac/ structure violations in real-time.

Scenario: Copilot tries to create files in wrong locations, and the
compliance engine blocks these violations and suggests correct paths.
"""

from paracle_core.governance import AIAssistantMonitor, get_compliance_engine


def example_1_simple_validation():
    """Example 1: Simple file path validation."""
    print("=== Example 1: Simple Validation ===\n")

    engine = get_compliance_engine()

    # Copilot wants to create a database file
    proposed_path = ".parac/costs.db"
    print(f"Copilot proposes: {proposed_path}")

    result = engine.validate_file_path(proposed_path)

    if not result.is_valid:
        print(f"❌ BLOCKED: {result.error}")
        print(f"✅ Use instead: {result.suggested_path}")
    else:
        print("✅ Path is valid")

    print()


def example_2_batch_validation():
    """Example 2: Validate multiple files at once."""
    print("=== Example 2: Batch Validation ===\n")

    engine = get_compliance_engine()

    # Copilot wants to create multiple files
    proposed_files = [
        ".parac/costs.db",  # Wrong
        ".parac/app.log",  # Wrong
        ".parac/architecture.md",  # Wrong
        ".parac/memory/data/metrics.db",  # Correct
    ]

    print("Copilot proposes creating:")
    for path in proposed_files:
        print(f"  - {path}")
    print()

    violations = engine.get_violations(proposed_files)

    if violations:
        print(f"❌ Found {len(violations)} violations:\n")
        for v in violations:
            print(f"File: {v.path}")
            print(f"Error: {v.error}")
            print(f"Fix: {v.suggested_path}")
            print()
    else:
        print("✅ All paths valid")


def example_3_real_time_blocking():
    """Example 3: Real-time blocking during file creation."""
    print("=== Example 3: Real-Time Blocking (IDE Hook) ===\n")

    monitor = AIAssistantMonitor()

    # Simulate Copilot trying to create a file
    file_path = ".parac/costs.db"
    print(f"Copilot attempts to create: {file_path}\n")

    response = monitor.on_file_create(file_path)

    if not response["allowed"]:
        print("❌ FILE CREATION BLOCKED")
        print(f"Reason: {response['error']}")
        print(f"\n💡 Suggestion: Use {response['suggested_path']}")
        print("\n📖 Documentation:")
        print(response["documentation"])
    else:
        print("✅ File creation allowed")

    print()


def example_4_auto_fix():
    """Example 4: Auto-fix suggestions."""
    print("=== Example 4: Auto-Fix Suggestions ===\n")

    engine = get_compliance_engine()

    wrong_paths = [
        ".parac/costs.db",
        ".parac/debug.log",
        ".parac/architecture.md",
        ".parac/decisions.md",
    ]

    print("Auto-fixing wrong paths:\n")
    for wrong_path in wrong_paths:
        correct_path = engine.auto_fix_path(wrong_path)
        if correct_path:
            print(f"❌ {wrong_path}")
            print(f"✅ {correct_path}")
            print()


def example_5_vscode_integration():
    """Example 5: VS Code pre-save validation."""
    print("=== Example 5: VS Code Pre-Save Hook ===\n")

    engine = get_compliance_engine()

    # Simulate VS Code pre-save event
    file_path = ".parac/costs.db"
    print(f"VS Code: Saving {file_path}...\n")

    validation = engine.generate_pre_save_validation(file_path)

    if not validation["allow_save"]:
        print("❌ SAVE BLOCKED")
        print(f"Error: {validation['error']}")
        print("\n💡 Quick Fix Available:")
        print(f"  Title: {validation['quick_fix']['title']}")
        print(f"  Action: {validation['quick_fix']['action']}")
        print(f"  Target: {validation['quick_fix']['target']}")

        # Simulate accepting quick fix
        print("\n✅ User accepts quick fix")
        correct_path = validation["suggested_path"]
        print(f"File will be saved as: {correct_path}")
    else:
        print("✅ Save allowed")

    print()


def example_6_monitoring_violations():
    """Example 6: Monitor and report violations."""
    print("=== Example 6: Violation Monitoring ===\n")

    monitor = AIAssistantMonitor()

    # Simulate multiple Copilot attempts
    attempts = [
        ".parac/costs.db",
        ".parac/app.log",
        ".parac/memory/data/metrics.db",  # Valid
        ".parac/architecture.md",
    ]

    print("Simulating Copilot attempts:\n")
    for path in attempts:
        response = monitor.on_file_create(path)
        status = "✅ Allowed" if response["allowed"] else "❌ Blocked"
        print(f"{status}: {path}")

    print("\n📊 Violations Report:\n")
    print(monitor.get_violations_report())


def example_7_copilot_workflow():
    """Example 7: Complete Copilot workflow with compliance."""
    print("=== Example 7: Complete Copilot Workflow ===\n")

    engine = get_compliance_engine()

    # Copilot generates code that creates files
    print("Copilot generates code:")
    print("```python")
    print('db_path = ".parac/costs.db"')
    print("# Create database...")
    print("```\n")

    # Validate before executing
    print("Compliance Engine: Validating db_path...\n")
    result = engine.validate_file_path(".parac/costs.db")

    if not result.is_valid:
        print("❌ Validation failed!")
        print(f"Error: {result.error}")
        print("\n✅ Auto-correcting code:")
        print("```python")
        print(f'db_path = "{result.suggested_path}"')
        print("# Create database...")
        print("```\n")

        # Validate corrected path
        corrected_result = engine.validate_file_path(result.suggested_path)
        if corrected_result.is_valid:
            print("✅ Corrected code passes validation")
            print("✅ Execution proceeds with correct path")


def example_8_copilot_learning():
    """Example 8: Teaching Copilot the correct structure."""
    print("=== Example 8: Teaching Copilot ===\n")

    engine = get_compliance_engine()

    # Get documentation for a category
    from paracle_core.governance.ai_compliance import FileCategory

    print("Copilot asks: Where should database files go?\n")
    docs = engine.get_structure_documentation(FileCategory.OPERATIONAL_DATA)
    print("Compliance Engine responds:")
    print(docs)
    print("\n✅ Copilot learns correct structure")


def main():
    """Run all examples."""
    examples = [
        example_1_simple_validation,
        example_2_batch_validation,
        example_3_real_time_blocking,
        example_4_auto_fix,
        example_5_vscode_integration,
        example_6_monitoring_violations,
        example_7_copilot_workflow,
        example_8_copilot_learning,
    ]

    for example in examples:
        example()
        print("-" * 70)
        print()


if __name__ == "__main__":
    print("AI Compliance Engine - VS Code Copilot Integration")
    print("=" * 70)
    print()
    main()
    print("\n✅ All examples completed!")
    print("\nKey Takeaways:")
    print("1. AI Compliance Engine validates ALL file operations")
    print("2. Violations are BLOCKED before they happen")
    print("3. Auto-fix suggestions guide Copilot to correct paths")
    print("4. Real-time integration with VS Code and other IDEs")
    print("5. 100% enforcement of .parac/ structure governance")
