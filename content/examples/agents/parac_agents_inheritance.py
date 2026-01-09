"""Example: Using agent inheritance with .parac/agents/ declarations.

This example demonstrates how to:
1. Load agent specs from .parac/agents/specs/
2. Create inheritance hierarchies
3. Test with real agent definitions (Paracle's own agents)
4. Use inherited agents in workflows

Scenario: Creating specialized reviewers from the base reviewer agent
- Base: reviewer (general code review)
- Child 1: security-reviewer (inherits from reviewer, focuses on security)
- Child 2: performance-reviewer (inherits from reviewer, focuses on performance)
"""

from pathlib import Path

from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_store import AgentRepository


def load_agent_spec_from_file(spec_path: Path) -> dict:
    """Load agent spec from .parac/agents/specs/ markdown file.

    This is a simplified loader - in production, you'd use the full
    agent spec parser that handles the markdown format.

    Args:
        spec_path: Path to the agent spec file

    Returns:
        Dict with agent spec data
    """
    # For this example, we'll extract key info from the markdown
    with open(spec_path, encoding="utf-8") as f:
        content = f.read()

    # Extract title (first # heading)
    lines = content.split("\n")
    name = None
    role = None
    skills = []

    for i, line in enumerate(lines):
        if line.startswith("# ") and not name:
            name = line[2:].strip().replace(" Agent", "").lower().replace(" ", "-")
        elif line.strip() == "## Role" and i + 2 < len(lines):
            role = lines[i + 2].strip()
        elif line.strip() == "## Skills":
            # Read skills (markdown list items)
            j = i + 2
            while j < len(lines) and lines[j].startswith("- "):
                skill = lines[j][2:].strip()
                if skill:
                    skills.append(skill)
                j += 1

    return {
        "name": name,
        "role": role,
        "skills": skills,
    }


def main() -> None:
    """Run the .parac/agents/ inheritance example."""
    print("\n🏗️  AGENT INHERITANCE WITH .parac/agents/")
    print("=" * 70)
    print("Using Paracle's own agent definitions from .parac/agents/specs/")
    print("=" * 70)

    # Setup
    repo = AgentRepository()
    factory = AgentFactory(spec_provider=repo.get_spec)

    # Path to .parac/agents/specs/
    parac_root = Path(__file__).parent.parent / ".parac"
    specs_dir = parac_root / "agents" / "specs"

    print(f"\n📂 Loading specs from: {specs_dir}")

    # =============================================================================
    # Step 1: Load base reviewer agent from .parac/
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 1: Load Base Reviewer Agent")
    print("=" * 70)

    reviewer_file = specs_dir / "reviewer.md"
    if not reviewer_file.exists():
        print(f"❌ File not found: {reviewer_file}")
        return

    reviewer_info = load_agent_spec_from_file(reviewer_file)
    print(f"\n✅ Loaded: {reviewer_info['name']}")
    print(f"   Role: {reviewer_info['role']}")
    print(f"   Skills: {', '.join(reviewer_info['skills'])}")

    # Create base reviewer spec
    base_reviewer = AgentSpec(
        name="reviewer",
        description=reviewer_info["role"],
        provider="openai",
        model="gpt-4",
        temperature=0.3,
        system_prompt=(
            "You are a code reviewer ensuring quality and best practices. "
            "Review code for correctness, security, performance, and maintainability."
        ),
        tools=["static_analysis", "security_scan", "code_review"],
        skills=reviewer_info["skills"],
        metadata={
            "role": "code_review",
            "source": ".parac/agents/specs/reviewer.md",
        },
    )

    repo.register_spec(base_reviewer)
    base_agent = factory.create(base_reviewer)

    print("\n📊 Base Reviewer Agent Created:")
    print(f"   Name: {base_reviewer.name}")
    print(f"   Temperature: {base_reviewer.temperature}")
    print(f"   Tools: {len(base_reviewer.tools)} tools")
    print(f"   Skills: {len(base_reviewer.skills)} skills")

    # =============================================================================
    # Step 2: Create Security-Focused Reviewer (Inherits from reviewer)
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 2: Create Security-Focused Reviewer (Child)")
    print("=" * 70)

    security_reviewer = AgentSpec(
        name="security-reviewer",
        description="Security-focused code reviewer specializing in vulnerability detection",
        parent="reviewer",  # 🔥 INHERITS FROM BASE REVIEWER!
        provider="openai",
        model="gpt-4",
        temperature=0.2,  # Stricter for security
        system_prompt=(
            "You are a security expert reviewing code for vulnerabilities. "
            "Focus on OWASP Top 10, SQL injection, XSS, CSRF, authentication flaws, "
            "secret management, input validation, and secure coding practices."
        ),
        tools=[
            "vulnerability_scanner",
            "dependency_checker",
            "secret_detector",
        ],  # Additional security tools
        skills=[
            "owasp-top-10",
            "penetration-testing",
            "threat-modeling",
        ],  # Additional security skills
        metadata={
            "focus": "security",
            "owasp_version": "2023",
            "severity_threshold": "medium",
        },
    )

    repo.register_spec(security_reviewer)
    security_agent = factory.create(security_reviewer)
    security_effective = security_agent.get_effective_spec()

    print("\n✅ Security Reviewer Created")
    print(f"   Parent: {security_reviewer.parent}")
    print(f"   Temperature: {security_reviewer.temperature} (overridden - stricter)")
    print("\n📊 Inherited + Added:")
    print(f"   Tools: {len(security_effective.tools)} total")
    print(f"     - From base: {base_reviewer.tools}")
    print(f"     - Added: {security_reviewer.tools}")
    print(f"   Skills: {len(security_effective.skills)} total")
    print(f"     - From base: {len(base_reviewer.skills)} skills")
    print(f"     - Added: {len(security_reviewer.skills)} skills")

    # =============================================================================
    # Step 3: Create Performance-Focused Reviewer (Inherits from reviewer)
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 3: Create Performance-Focused Reviewer (Child)")
    print("=" * 70)

    performance_reviewer = AgentSpec(
        name="performance-reviewer",
        description="Performance-focused code reviewer specializing in optimization",
        parent="reviewer",  # 🔥 INHERITS FROM BASE REVIEWER!
        provider="openai",
        model="gpt-4-turbo",  # Upgraded model
        temperature=0.25,
        system_prompt=(
            "You are a performance expert reviewing code for efficiency. "
            "Focus on algorithmic complexity, database query optimization, "
            "caching strategies, memory usage, and scalability issues."
        ),
        tools=[
            "profiler",
            "complexity_analyzer",
            "memory_tracker",
        ],  # Additional performance tools
        skills=[
            "algorithmic-optimization",
            "database-tuning",
            "caching-strategies",
        ],  # Additional performance skills
        metadata={
            "focus": "performance",
            "complexity_threshold": "O(n log n)",
            "memory_limit_mb": 512,
        },
    )

    repo.register_spec(performance_reviewer)
    performance_agent = factory.create(performance_reviewer)
    performance_effective = performance_agent.get_effective_spec()

    print("\n✅ Performance Reviewer Created")
    print(f"   Parent: {performance_reviewer.parent}")
    print(f"   Model: {performance_reviewer.model} (upgraded)")
    print("\n📊 Inherited + Added:")
    print(f"   Tools: {len(performance_effective.tools)} total")
    print(f"   Skills: {len(performance_effective.skills)} total")

    # =============================================================================
    # Step 4: Create Python-Specific Security Reviewer (2-level inheritance)
    # =============================================================================
    print("\n" + "=" * 70)
    print("STEP 4: Create Python-Specific Security Reviewer (Grandchild)")
    print("=" * 70)

    python_security_reviewer = AgentSpec(
        name="python-security-reviewer",
        description="Python-specific security reviewer",
        parent="security-reviewer",  # 🔥 INHERITS FROM SECURITY REVIEWER!
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.15,  # Even stricter
        system_prompt=(
            "You are a Python security expert. "
            "Focus on Python-specific vulnerabilities: pickle deserialization, "
            "eval/exec abuse, path traversal, subprocess injection, "
            "regex DoS, and Python-specific OWASP issues."
        ),
        tools=[
            "bandit",  # Python security linter
            "safety",  # Python dependency checker
        ],
        skills=[
            "python-security",
            "pickle-safety",
        ],
        metadata={
            "language": "python",
            "python_version": "3.10+",
        },
    )

    repo.register_spec(python_security_reviewer)
    python_security_agent = factory.create(python_security_reviewer)
    python_security_effective = python_security_agent.get_effective_spec()

    print("\n✅ Python Security Reviewer Created")
    print(f"   Parent: {python_security_reviewer.parent}")
    print(
        "   Inheritance Chain: reviewer → security-reviewer → python-security-reviewer"
    )
    print("\n📊 Accumulated Through 2-Level Inheritance:")
    print(f"   Tools: {len(python_security_effective.tools)} total")
    print(f"     - From base (reviewer): {len(base_reviewer.tools)}")
    print(f"     - From parent (security): {len(security_reviewer.tools)}")
    print(f"     - Own: {len(python_security_reviewer.tools)}")
    print(f"   Skills: {len(python_security_effective.skills)} total")

    # =============================================================================
    # Step 5: Demonstration Summary
    # =============================================================================
    print("\n" + "=" * 70)
    print("📊 INHERITANCE HIERARCHY SUMMARY")
    print("=" * 70)

    print("\n🌳 Agent Tree:")
    print(
        """
    reviewer (base from .parac/agents/specs/reviewer.md)
    ├── security-reviewer
    │   └── python-security-reviewer (2-level inheritance)
    └── performance-reviewer
    """
    )

    print("\n📈 Tool Accumulation:")
    print(f"   reviewer:                  {len(base_reviewer.tools)} tools")
    print(
        f"   security-reviewer:         {len(security_effective.tools)} tools (inherited + added)"
    )
    print(
        f"   python-security-reviewer:  {len(python_security_effective.tools)} tools (inherited + added)"
    )
    print(
        f"   performance-reviewer:      {len(performance_effective.tools)} tools (inherited + added)"
    )

    print("\n🎓 Skill Accumulation:")
    print(f"   reviewer:                  {len(base_reviewer.skills)} skills")
    print(f"   security-reviewer:         {len(security_effective.skills)} skills")
    print(
        f"   python-security-reviewer:  {len(python_security_effective.skills)} skills"
    )
    print(f"   performance-reviewer:      {len(performance_effective.skills)} skills")

    print("\n🌡️  Temperature Specialization:")
    print(f"   reviewer:                  {base_reviewer.temperature} (balanced)")
    print(f"   security-reviewer:         {security_reviewer.temperature} (stricter)")
    print(
        f"   python-security-reviewer:  {python_security_reviewer.temperature} (strictest)"
    )
    print(
        f"   performance-reviewer:      {performance_reviewer.temperature} (moderate)"
    )

    # =============================================================================
    # Step 6: Verification
    # =============================================================================
    print("\n" + "=" * 70)
    print("🧪 VERIFICATION")
    print("=" * 70)

    # Verify inheritance
    assert (
        "static_analysis" in python_security_effective.tools
    ), "Base tool should be inherited"
    assert (
        "vulnerability_scanner" in python_security_effective.tools
    ), "Parent tool should be inherited"
    assert "bandit" in python_security_effective.tools, "Own tool should be present"
    print("✅ Tool inheritance through 2 levels: VERIFIED")

    assert (
        "security-hardening" in python_security_effective.skills
    ), "Base skill should be inherited"
    assert (
        "owasp-top-10" in python_security_effective.skills
    ), "Parent skill should be inherited"
    assert (
        "python-security" in python_security_effective.skills
    ), "Own skill should be present"
    print("✅ Skill inheritance through 2 levels: VERIFIED")

    assert (
        python_security_effective.temperature == 0.15
    ), "Temperature should be overridden"
    print("✅ Property override: VERIFIED")

    assert (
        "role" in python_security_effective.metadata
    ), "Base metadata should be inherited"
    assert (
        "focus" in python_security_effective.metadata
    ), "Parent metadata should be inherited"
    assert (
        "language" in python_security_effective.metadata
    ), "Own metadata should be present"
    print("✅ Metadata merging: VERIFIED")

    # =============================================================================
    # Step 7: Practical Usage
    # =============================================================================
    print("\n" + "=" * 70)
    print("💼 PRACTICAL USAGE")
    print("=" * 70)

    print("\n✅ Use Cases:")
    print("   1. General review:     Use 'reviewer' agent")
    print("   2. Security audit:     Use 'security-reviewer' agent")
    print("   3. Python security:    Use 'python-security-reviewer' agent")
    print("   4. Performance check:  Use 'performance-reviewer' agent")

    print("\n🎯 Benefits:")
    print("   - Base reviewer defined once in .parac/agents/specs/")
    print("   - Specialized reviewers inherit and extend")
    print("   - Easy to add new specializations")
    print("   - Update base affects all children")
    print("   - Type-safe with Pydantic validation")

    print("\n🚀 Integration with Workflows:")
    print("   - Load agent specs from .parac/agents/specs/")
    print("   - Create inheritance hierarchies dynamically")
    print("   - Use in workflows for specialized tasks")
    print("   - Mix base agents and specialized agents")

    print("\n" + "=" * 70)
    print("✅ ALL VERIFICATIONS PASSED!")
    print("=" * 70)
    print("\n💡 This demonstrates Paracle's unique agent inheritance")
    print("   working with real agent definitions from .parac/agents/!")


if __name__ == "__main__":
    main()
