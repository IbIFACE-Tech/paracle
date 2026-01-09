"""Example 06: Agent Skills System

This example demonstrates the Agent Skills system in Paracle:
- How skills are organized and structured
- How agents reference skills in their specs
- Progressive disclosure pattern (Discovery → Activation → Execution)
- How to use skills in agent development

For complete details, see:
- .parac/agents/skills/ - All available skills
- .parac/agents/specs/ - Agent specifications with skills
- .parac/agents/SKILL_ASSIGNMENTS.md - Skills mapped to agents
- .parac/agents/manifest.yaml - Agent definitions
"""

from pathlib import Path


def list_available_skills() -> list[str]:
    """List all available skills in the .parac/agents/skills/ directory.

    This is the Discovery phase of progressive disclosure.
    """
    skills_dir = Path(__file__).parent.parent / ".parac" / "agents" / "skills"

    skills = [
        d.name
        for d in skills_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]

    return sorted(skills)


def get_skill_metadata(skill_name: str) -> dict[str, str]:
    """Get skill metadata from SKILL.md frontmatter.

    This retrieves the discovery-level information (~100 tokens).
    """
    skills_dir = Path(__file__).parent.parent / ".parac" / "agents" / "skills"
    skill_file = skills_dir / skill_name / "SKILL.md"

    if not skill_file.exists():
        raise FileNotFoundError(f"Skill not found: {skill_name}")

    content = skill_file.read_text(encoding="utf-8")

    # Extract YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            # Simple YAML parsing (in production, use proper YAML parser)
            metadata = {}
            for line in frontmatter.strip().split("\n"):
                if ": " in line:
                    key, value = line.split(": ", 1)
                    metadata[key.strip()] = value.strip()
            return metadata

    return {}


def get_agent_skills(agent_id: str) -> list[str]:
    """Get skills assigned to a specific agent.

    Reads from agent specification file.
    """
    specs_dir = Path(__file__).parent.parent / ".parac" / "agents" / "specs"
    spec_file = specs_dir / f"{agent_id}.md"

    if not spec_file.exists():
        raise FileNotFoundError(f"Agent spec not found: {agent_id}")

    content = spec_file.read_text(encoding="utf-8")

    # Extract skills from ## Skills section
    skills = []
    in_skills_section = False

    for line in content.split("\n"):
        if "## Skills" in line:
            in_skills_section = True
            continue
        elif line.startswith("## ") and in_skills_section:
            break  # Next section
        elif in_skills_section and line.strip().startswith("-"):
            skill = line.strip()[1:].strip()
            skills.append(skill)

    return skills


def demonstrate_progressive_disclosure(skill_name: str):
    """Demonstrate the progressive disclosure pattern for a skill.

    Phase 1: Discovery - Show metadata (~100 tokens)
    Phase 2: Activation - Load full SKILL.md (~2000-5000 tokens)
    Phase 3: Execution - Use scripts/references/assets as needed
    """
    print(f"\n{'='*60}")
    print(f"Progressive Disclosure: {skill_name}")
    print(f"{'='*60}\n")

    # Phase 1: Discovery
    print("📋 PHASE 1: DISCOVERY (~100 tokens)")
    print("-" * 60)
    metadata = get_skill_metadata(skill_name)
    print(f"Name: {metadata.get('name', 'N/A')}")
    print(f"Description: {metadata.get('description', 'N/A')}")

    # Phase 2: Activation (would load full SKILL.md)
    print("\n📖 PHASE 2: ACTIVATION (~2000-5000 tokens)")
    print("-" * 60)
    skills_dir = Path(__file__).parent.parent / ".parac" / "agents" / "skills"
    skill_file = skills_dir / skill_name / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")
    token_estimate = len(content) / 4  # Rough estimate
    print(f"Full SKILL.md loaded: ~{int(token_estimate)} tokens")
    print("Contains: Instructions, examples, best practices")

    # Phase 3: Execution (check for optional directories)
    print("\n⚡ PHASE 3: EXECUTION (On-demand)")
    print("-" * 60)
    skill_dir = skills_dir / skill_name

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        scripts = list(scripts_dir.glob("*"))
        print(f"✅ scripts/ available: {len(scripts)} executable examples")

    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        refs = list(refs_dir.glob("*.md"))
        print(f"✅ references/ available: {len(refs)} extended docs")

    assets_dir = skill_dir / "assets"
    if assets_dir.exists():
        assets = list(assets_dir.glob("*"))
        print(f"✅ assets/ available: {len(assets)} templates")


def show_agent_capabilities(agent_id: str):
    """Show all skills available to a specific agent."""
    print(f"\n{'='*60}")
    print(f"Agent Capabilities: {agent_id}")
    print(f"{'='*60}\n")

    skills = get_agent_skills(agent_id)
    print(f"This agent has {len(skills)} skills:\n")

    for skill in skills:
        metadata = get_skill_metadata(skill)
        print(f"• {skill}")
        print(f"  {metadata.get('description', 'No description')}\n")


def main():
    """Run agent skills examples."""
    print("\n" + "=" * 60)
    print("PARACLE AGENT SKILLS SYSTEM DEMO")
    print("=" * 60)

    # Example 1: List all available skills
    print("\n1️⃣  DISCOVERING AVAILABLE SKILLS")
    print("-" * 60)
    skills = list_available_skills()
    print(f"Found {len(skills)} skills in the system:\n")
    for skill in skills:
        print(f"  • {skill}")

    # Example 2: Get metadata for a specific skill
    print("\n\n2️⃣  SKILL METADATA (Discovery Phase)")
    print("-" * 60)
    skill_name = "api-development"
    metadata = get_skill_metadata(skill_name)
    print(f"\nSkill: {metadata.get('name')}")
    print(f"Description: {metadata.get('description')}")

    # Example 3: Progressive disclosure demonstration
    demonstrate_progressive_disclosure("api-development")

    # Example 4: Agent capabilities
    show_agent_capabilities("coder")

    # Example 5: Skill distribution matrix
    print(f"\n{'='*60}")
    print("SKILL DISTRIBUTION ACROSS AGENTS")
    print(f"{'='*60}\n")

    agents = ["architect", "coder", "documenter", "pm", "reviewer", "tester"]

    print("Agent Skills Matrix:")
    print("-" * 60)
    for agent_id in agents:
        skills = get_agent_skills(agent_id)
        print(f"{agent_id:12s} → {len(skills)} skills: {', '.join(skills[:3])}...")

    # Example 6: Find agents with a specific skill
    print("\n\n6️⃣  FINDING AGENTS WITH SPECIFIC SKILLS")
    print("-" * 60)

    target_skill = "security-hardening"
    print(f"\nAgents with '{target_skill}' skill:\n")

    for agent_id in agents:
        skills = get_agent_skills(agent_id)
        if target_skill in skills:
            print(f"  ✅ {agent_id}")

    print("\n" + "=" * 60)
    print("✨ Agent Skills System Demo Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("• Read .parac/agents/SKILL_ASSIGNMENTS.md for full mapping")
    print("• Explore .parac/agents/skills/ to see all skill details")
    print("• Check .parac/agents/manifest.yaml for agent definitions")
    print("• Use skills when implementing agents in your workflows")
    print()


if __name__ == "__main__":
    main()
