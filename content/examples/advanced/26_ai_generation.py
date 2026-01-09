"""Example: AI-powered generation (optional feature).

This example demonstrates how to use AI providers for generating
agents, skills, and workflows from natural language descriptions.

Requirements:
    - AI provider installed (paracle_meta or external)
    - API keys configured (for external providers)

Quick setup:
    pip install paracle[meta]
    paracle meta activate
"""

import asyncio

from paracle_cli.ai_helper import (
    AIProviderNotAvailable,
    get_ai_provider,
    is_ai_available,
    list_available_providers,
)


async def example_check_availability():
    """Check if AI features are available."""
    print("=" * 60)
    print("Example 1: Check AI Availability")
    print("=" * 60)

    # Check if any AI provider available
    if is_ai_available():
        ai = get_ai_provider()
        print(f"✓ AI provider available: {ai.name}")
    else:
        print("✗ No AI provider available")
        print("\nTo enable AI features:")
        print("  pip install paracle[meta]")
        print("  paracle meta activate")

    # List all available providers
    available = list_available_providers()
    print(f"\nAvailable providers: {', '.join(available) if available else 'none'}")


async def example_generate_agent():
    """Generate agent from natural language description."""
    print("\n" + "=" * 60)
    print("Example 2: Generate Agent with AI")
    print("=" * 60)

    try:
        # Get AI provider
        ai = get_ai_provider()
        if ai is None:
            print("✗ AI not available - skipping example")
            print("  Install: pip install paracle[meta]")
            return

        print(f"Using AI provider: {ai.name}\n")

        # Generate agent
        description = "Python code reviewer focusing on security and performance"
        print(f"Description: {description}\n")

        result = await ai.generate_agent(description)

        print(f"Generated Agent: {result['name']}")
        print("\nYAML Specification:")
        print("-" * 60)
        print(result["yaml"])
        print("-" * 60)

        # In real usage, save to file
        # Path: .parac/agents/specs/{name}.md

    except AIProviderNotAvailable as e:
        print(f"✗ Error: {e}")


async def example_generate_skill():
    """Generate skill from natural language description."""
    print("\n" + "=" * 60)
    print("Example 3: Generate Skill with AI")
    print("=" * 60)

    try:
        ai = get_ai_provider()
        if ai is None:
            print("✗ AI not available - skipping example")
            return

        print(f"Using AI provider: {ai.name}\n")

        # Generate skill
        description = "Extract structured data from CSV files with validation"
        print(f"Description: {description}\n")

        result = await ai.generate_skill(description)

        print(f"Generated Skill: {result['name']}")
        print("\nYAML Specification:")
        print("-" * 60)
        print(result["yaml"])
        print("-" * 60)

        if "code" in result and result["code"]:
            print("\nPython Implementation:")
            print("-" * 60)
            print(result["code"])
            print("-" * 60)

        # In real usage, save to:
        # .parac/agents/skills/{name}/{name}.yaml
        # .parac/agents/skills/{name}/{name}.py

    except AIProviderNotAvailable as e:
        print(f"✗ Error: {e}")


async def example_generate_workflow():
    """Generate workflow from natural language description."""
    print("\n" + "=" * 60)
    print("Example 4: Generate Workflow with AI")
    print("=" * 60)

    try:
        ai = get_ai_provider()
        if ai is None:
            print("✗ AI not available - skipping example")
            return

        print(f"Using AI provider: {ai.name}\n")

        # Generate workflow
        description = "Code review with automated tests and security scanning"
        print(f"Description: {description}\n")

        result = await ai.generate_workflow(description)

        print(f"Generated Workflow: {result['name']}")
        print("\nYAML Specification:")
        print("-" * 60)
        print(result["yaml"])
        print("-" * 60)

        # In real usage, save to:
        # .parac/workflows/{name}.yaml

    except AIProviderNotAvailable as e:
        print(f"✗ Error: {e}")


async def example_progressive_enhancement():
    """Demonstrate progressive enhancement pattern.

    Core functionality works without AI, enhanced with AI if available.
    """
    print("\n" + "=" * 60)
    print("Example 5: Progressive Enhancement")
    print("=" * 60)

    # Try to get AI provider
    ai = get_ai_provider()

    if ai:
        print("✓ AI available - using AI-powered generation")
        description = "Bug fixing agent"
        result = await ai.generate_agent(description)
        print(f"Generated: {result['name']}")
        agent_spec = result["yaml"]
    else:
        print("✗ AI not available - using manual template")
        # Fall back to manual template
        agent_spec = """
# Bug Fixer Agent

## Role
Identifies and fixes bugs in code.

## Skills
- code_analysis
- debugging
- testing
"""
        print("Using template-based configuration")

    print("\nAgent specification ready (with or without AI):")
    print(agent_spec[:200] + "...")


async def example_specific_provider():
    """Use specific AI provider."""
    print("\n" + "=" * 60)
    print("Example 6: Specific AI Provider")
    print("=" * 60)

    # Try specific providers in order
    for provider_name in ["meta", "openai", "anthropic"]:
        try:
            ai = get_ai_provider(provider_name)
            if ai:
                print(f"✓ Using {provider_name}")
                result = await ai.generate_agent("Simple agent")
                print(f"  Generated: {result['name']}")
                break
        except AIProviderNotAvailable:
            print(f"✗ {provider_name} not available")
            continue
    else:
        print("\n✗ No providers available")


async def example_error_handling():
    """Demonstrate graceful degradation."""
    print("\n" + "=" * 60)
    print("Example 7: Graceful Error Handling")
    print("=" * 60)

    try:
        # Try to use AI
        ai = get_ai_provider()

        if ai is None:
            raise AIProviderNotAvailable("No AI provider configured")

        result = await ai.generate_agent("Test agent")
        print(f"✓ Generated with AI: {result['name']}")

    except AIProviderNotAvailable:
        print("✗ AI not available")
        print("→ Falling back to manual configuration")

        # Continue with manual workflow
        print("✓ Using manual agent specification")
        # ... manual logic here ...

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print("→ Falling back to safe defaults")


async def example_batch_generation():
    """Generate multiple agents in batch."""
    print("\n" + "=" * 60)
    print("Example 8: Batch Generation")
    print("=" * 60)

    ai = get_ai_provider()
    if ai is None:
        print("✗ AI not available - skipping batch generation")
        return

    descriptions = [
        "Code reviewer",
        "Test generator",
        "Documentation writer",
    ]

    print(f"Generating {len(descriptions)} agents...\n")

    for desc in descriptions:
        try:
            result = await ai.generate_agent(desc)
            print(f"✓ Generated: {result['name']}")
        except Exception as e:
            print(f"✗ Failed {desc}: {e}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("AI-Powered Generation Examples")
    print("=" * 60)
    print("\nThese examples demonstrate optional AI features.")
    print("Paracle works fully without AI - these are enhancements.\n")

    # Check availability first
    await example_check_availability()

    # Only run generation examples if AI available
    if is_ai_available():
        await example_generate_agent()
        await example_generate_skill()
        await example_generate_workflow()
        await example_progressive_enhancement()
        await example_specific_provider()
        await example_batch_generation()
    else:
        print("\n" + "=" * 60)
        print("AI features not available")
        print("=" * 60)
        print("\nTo enable AI-powered generation:")
        print("  1. Install: pip install paracle[meta]")
        print("  2. Activate: paracle meta activate")
        print("  3. Run examples again")

    # Always run error handling example
    await example_error_handling()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nNext steps:")
    print(
        "  - Create agent: paracle agents create my-agent --role 'description' --ai-enhance"
    )
    print(
        "  - Create skill: paracle agents skills create my-skill --description 'desc' --ai-enhance"
    )
    print(
        "  - Create workflow: paracle workflow create my-workflow --description 'desc' --ai-enhance"
    )
    print("  - Configure: .parac/config/ai.yaml")
    print("  - Check status: paracle generate status")


if __name__ == "__main__":
    asyncio.run(main())
