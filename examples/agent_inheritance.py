"""Example: Agent Inheritance."""

from paracle_domain.models import AgentSpec


def main() -> None:
    """Demonstrate agent inheritance - Paracle's unique feature."""
    print("🧬 Paracle Example: Agent Inheritance\n")

    # Base agent
    print("1️⃣ Creating base agent...")
    base_agent = AgentSpec(
        name="base-coder",
        description="Base coding agent",
        provider="openai",
        model="gpt-4",
        temperature=0.7,
        system_prompt="You are a software developer."
    )
    print(f"   ✅ Base agent: {base_agent.name}")
    print(f"      Temperature: {base_agent.temperature}")
    print(f"      Model: {base_agent.model}\n")

    # Python specialist (inherits from base)
    print("2️⃣ Creating Python specialist (inherits from base)...")
    python_expert = AgentSpec(
        name="python-expert",
        description="Python specialist",
        parent="base-coder",  # 🔥 Inheritance!
        provider="openai",
        model="gpt-4",
        temperature=0.5,  # Override
        system_prompt="You are an expert Python developer specializing in best practices."
    )
    print(f"   ✅ Specialist: {python_expert.name}")
    print(f"      Inherits from: {python_expert.parent}")
    print(f"      Temperature: {python_expert.temperature} (overridden)")
    print(f"      Model: {python_expert.model} (inherited)\n")

    # Security specialist (inherits from Python expert)
    print("3️⃣ Creating security specialist (inherits from Python expert)...")
    security_expert = AgentSpec(
        name="security-expert",
        description="Security specialist",
        parent="python-expert",  # 🔥 Multi-level inheritance!
        provider="openai",
        model="gpt-4",
        temperature=0.3,  # Override again
        system_prompt="You are a security expert focusing on secure Python code."
    )
    print(f"   ✅ Security expert: {security_expert.name}")
    print(f"      Inherits from: {security_expert.parent}")
    print(f"      Temperature: {security_expert.temperature} (overridden)")
    print(f"\n📊 Inheritance Chain:")
    print(f"   base-coder (temp: 0.7)")
    print(f"      ↓")
    print(f"   python-expert (temp: 0.5)")
    print(f"      ↓")
    print(f"   security-expert (temp: 0.3)")
    print(f"\n💡 Each level specializes and overrides as needed!")
    print(f"📝 Note: Inheritance resolution implemented in Phase 1")


if __name__ == "__main__":
    main()
