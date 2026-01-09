"""Example: Hello World Agent."""

from paracle_domain.models import AgentSpec, Agent


def main() -> None:
    """Create a simple hello world agent."""
    print("🎉 Paracle Example: Hello World Agent\n")

    # Define agent specification
    agent_spec = AgentSpec(
        name="hello-world-agent",
        description="A friendly greeting agent",
        provider="openai",  # Will be implemented in Phase 2
        model="gpt-4",
        temperature=0.7,
        system_prompt="You are a friendly assistant that greets users."
    )

    # Create agent instance
    agent = Agent(spec=agent_spec)

    print(f"✅ Agent created successfully!")
    print(f"   ID: {agent.id}")
    print(f"   Name: {agent.spec.name}")
    print(f"   Provider: {agent.spec.provider}")
    print(f"   Model: {agent.spec.model}")
    print(f"   Status: {agent.status.phase}")
    print(f"\n📝 Note: Full execution coming in Phase 2-3!")


if __name__ == "__main__":
    main()
