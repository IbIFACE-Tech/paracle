"""Example: Using skills with agent execution.

This example shows how to use the skill loading and injection system.
"""

import asyncio

from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_orchestration.coordinator import AgentCoordinator
from paracle_orchestration.skill_loader import SkillLoader


async def main() -> None:
    """Demonstrate skill loading and injection."""

    print("=" * 60)
    print("Paracle Skill System Demo")
    print("=" * 60)

    # 1. Discover available skills
    print("\n1. Discovering skills...")
    skill_loader = SkillLoader()
    available_skills = skill_loader.discover_skills()
    print(f"   Found {len(available_skills)} skills:")
    for skill_id in available_skills[:5]:  # Show first 5
        print(f"   - {skill_id}")
    if len(available_skills) > 5:
        print(f"   ... and {len(available_skills) - 5} more")

    # 2. Load skills for a specific agent
    print("\n2. Loading skills for 'coder' agent...")
    coder_skills = skill_loader.load_agent_skills("coder")
    print(f"   Loaded {len(coder_skills)} skills for coder:")
    for skill in coder_skills:
        print(f"   - {skill.name} ({skill.skill_id})")

    # 3. Create agent with skills
    print("\n3. Creating agent with skills enabled...")
    agent_spec = AgentSpec(
        name="coder",
        role="Code implementation specialist",
        system_prompt="You are a skilled programmer.",
        provider="openai",
        model="gpt-4",
        skills=[
            "paracle-development",
            "api-development",
            "testing-qa",
        ],
    )

    factory = AgentFactory()
    agent = factory.create(agent_spec)

    # 4. Initialize coordinator with skills enabled
    print("\n4. Initializing coordinator with skills...")
    coordinator = AgentCoordinator(
        agent_factory=factory,
        enable_skills=True,
        skill_injection_mode="full",  # Can be: full, summary, references, minimal
    )

    # 5. Execute agent (skills will be auto-loaded)
    print("\n5. Executing agent with skills...")
    try:
        result = await coordinator.execute_agent(
            agent=agent,
            inputs={"task": "Implement a simple REST API endpoint"},
            load_skills=True,  # Enable skill loading for this execution
        )

        print(f"\n   ✅ Execution completed in {result['execution_time']:.2f}s")
        print(f"   Skills loaded: {result['metadata']['skills_loaded']}")
        print(f"   Skill IDs: {result['metadata']['skill_ids']}")

        # Show loaded skills
        if result["skills"]:
            print("\n   Loaded skills:")
            for skill in result["skills"]:
                print(f"   - {skill['name']} ({skill['skill_id']})")

    except Exception as e:
        print(f"\n   ❌ Execution failed: {e}")

    # 6. Demonstrate different injection modes
    print("\n6. Testing different skill injection modes...")

    modes = ["full", "summary", "references", "minimal"]
    for mode in modes:
        coordinator_mode = AgentCoordinator(
            agent_factory=factory,
            enable_skills=True,
            skill_injection_mode=mode,
        )

        result = await coordinator_mode.execute_agent(
            agent=agent,
            inputs={"task": "Test mode"},
            load_skills=True,
        )

        print(
            f"   - {mode.upper()}: {result['metadata']['skills_loaded']} skills")

    # 7. Disable skills
    print("\n7. Executing without skills...")
    coordinator_no_skills = AgentCoordinator(
        agent_factory=factory,
        enable_skills=False,
    )

    result = await coordinator_no_skills.execute_agent(
        agent=agent,
        inputs={"task": "No skills mode"},
    )

    print(
        f"   Skills loaded: {result['metadata']['skills_loaded']} (disabled)")

    print("\n" + "=" * 60)
    print("✅ Skill system demo completed!")
    print("=" * 60)

    # Additional information
    print("\n📚 Skill Injection Modes:")
    print("   - full: Complete skill content in system prompt")
    print("   - summary: Only descriptions")
    print("   - references: Reference documentation only")
    print("   - minimal: Just skill names")

    print("\n📁 Skill Location:")
    print(f"   {skill_loader.skills_dir}")

    print("\n🔧 Usage in Code:")
    print("   coordinator = AgentCoordinator(")
    print("       agent_factory=factory,")
    print("       enable_skills=True,")
    print("       skill_injection_mode='full',")
    print("   )")


if __name__ == "__main__":
    asyncio.run(main())
