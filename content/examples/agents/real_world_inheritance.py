"""Real-world example: Building specialized agents through inheritance.

This example demonstrates Paracle's unique agent inheritance feature
by building a hierarchy of developer agents for different specializations.

Scenario: Building a team of specialized code reviewers
- Base Reviewer: General code review agent
- Python Reviewer: Specializes in Python best practices
- FastAPI Reviewer: Specializes in FastAPI/API design (inherits from Python)
- Security Reviewer: Specializes in security audits (inherits from FastAPI)
"""

from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_store import AgentRepository


def print_agent_info(agent, title: str) -> None:
    """Pretty print agent information."""
    spec = agent.get_effective_spec()
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Name: {spec.name}")
    print(f"Model: {spec.model}")
    print(f"Temperature: {spec.temperature}")
    print(f"Tools: {', '.join(spec.tools) if spec.tools else 'None'}")
    print(f"Skills: {', '.join(spec.skills) if spec.skills else 'None'}")
    print(f"System Prompt: {spec.system_prompt[:100]}..." if spec.system_prompt and len(
        spec.system_prompt) > 100 else f"System Prompt: {spec.system_prompt}")
    if hasattr(agent, 'resolved_spec') and agent.resolved_spec:
        print(
            f"Inheritance Chain: {' -> '.join(reversed([spec.name for spec in [agent.spec] if spec.parent]))}")


def main() -> None:
    """Run the real-world inheritance example."""
    print("\n🎯 REAL-WORLD EXAMPLE: Building Specialized Code Reviewers")
    print("=" * 60)
    print("Demonstrating Paracle's Agent Inheritance Feature")
    print("=" * 60)

    # Initialize repository and factory
    repo = AgentRepository()
    factory = AgentFactory(spec_provider=repo.get_spec)

    # =============================================================================
    # Level 1: Base Code Reviewer
    # =============================================================================
    print("\n📝 STEP 1: Create Base Code Reviewer")
    base_spec = AgentSpec(
        name="base-code-reviewer",
        description="General code reviewer for any language",
        provider="openai",
        model="gpt-4",
        temperature=0.3,  # Low temperature for consistent reviews
        system_prompt=(
            "You are an experienced code reviewer. "
            "Review code for readability, maintainability, and best practices. "
            "Provide constructive feedback with specific examples."
        ),
        tools=["read_file", "grep_search"],
        skills=["code-review"],
        metadata={
            "role": "reviewer",
            "experience_level": "senior",
        }
    )

    # Register the spec first
    repo.register_spec(base_spec)
    base_agent = factory.create(base_spec)
    print(f"✅ Created: {base_spec.name}")
    print(f"   Tools: {base_spec.tools}")
    print(f"   Skills: {base_spec.skills}")
    print(f"   Temperature: {base_spec.temperature}")

    # =============================================================================
    # Level 2: Python Specialist (Inherits from Base)
    # =============================================================================
    print("\n📝 STEP 2: Create Python Specialist (Inherits from Base)")
    python_spec = AgentSpec(
        name="python-code-reviewer",
        description="Python code reviewer specializing in Python best practices",
        parent="base-code-reviewer",  # 🔥 INHERITANCE!
        provider="openai",
        model="gpt-4",
        temperature=0.2,  # Even stricter for Python
        system_prompt=(
            "You are a Python expert code reviewer. "
            "Focus on PEP 8, type hints, docstrings, and Pythonic patterns. "
            "Check for proper exception handling and async/await usage."
        ),
        tools=["run_python_linter", "check_type_hints"],  # Additional tools
        skills=["python-best-practices", "typing"],  # Additional skills
        metadata={
            "language": "python",
            "pep8_strict": True,
        }
        # Register the spec
        repo.register_spec(python_spec)
    )

    python_agent = factory.create(python_spec)
    print(f"✅ Created: {python_spec.name}")
    print(f"   Parent: {python_spec.parent}")
    print(f"   Temperature: {python_spec.temperature} (overridden)")

    # Check merged tools
    effective_spec = python_agent.get_effective_spec()
    print(f"   Tools (inherited + new): {effective_spec.tools}")
    print(f"   Skills (inherited + new): {effective_spec.skills}")

    # =============================================================================
    # Level 3: FastAPI Specialist (Inherits from Python)
    # =============================================================================
    print("\n📝 STEP 3: Create FastAPI Specialist (Inherits from Python Reviewer)")
    fastapi_spec = AgentSpec(
        name="fastapi-code-reviewer",
        description="FastAPI/REST API code reviewer",
        parent="python-code-reviewer",  # 🔥 MULTI-LEVEL INHERITANCE!
        provider="openai",
        model="gpt-4-turbo",  # Upgraded model
        temperature=0.25,
        system_prompt=(
            "You are a FastAPI and REST API expert. "
            "Review API design, endpoint structure, Pydantic models, "
            "authentication, error handling, and OpenAPI documentation."
        ),
        tools=["validate_openapi", "check_api_security"],
        skills=["api-design", "fastapi", "rest-patterns"],
        metadata={
            "framework": "fastapi",
            # Register the spec
            repo.register_spec(fastapi_spec)
            "api_version": "v1",
        }
    )

    fastapi_agent = factory.create(fastapi_spec)
    print(f"✅ Created: {fastapi_spec.name}")
    print(f"   Parent: {fastapi_spec.parent}")
    print(f"   Model: {fastapi_spec.model} (upgraded)")

    effective_spec = fastapi_agent.get_effective_spec()
    print(f"   Tools (accumulated): {effective_spec.tools}")
    print(f"   Skills (accumulated): {effective_spec.skills}")

    # =============================================================================
    # Level 4: Security Specialist (Inherits from FastAPI)
    # =============================================================================
    print("\n📝 STEP 4: Create Security Specialist (Inherits from FastAPI Reviewer)")
    security_spec = AgentSpec(
        name="security-code-reviewer",
        description="Security-focused code reviewer",
        parent="fastapi-code-reviewer",  # 🔥 3-LEVEL INHERITANCE CHAIN!
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.1,  # Very strict for security
        system_prompt=(
            "You are a security expert specializing in code review. "
            "Focus on SQL injection, XSS, CSRF, authentication flaws, "
            "secret management, input validation, and OWASP Top 10."
        ),
        tools=["scan_vulnerabilities", "check_dependencies", "audit_auth"],
        skills=["security-audit", "owasp", "penetration-testing"],
        metadata={
            "security_level": "high",
            "owasp_version": "2023",
        }
    )

    # Register the spec
    repo.register_spec(security_spec)
    security_agent = factory.create(security_spec)
    print(f"✅ Created: {security_spec.name}")
    print(f"   Parent: {security_spec.parent}")
    print(f"   Temperature: {security_spec.temperature} (strictest)")

    effective_spec = security_agent.get_effective_spec()
    print(f"   Tools (accumulated): {effective_spec.tools}")
    print(f"   Skills (accumulated): {effective_spec.skills}")

    # =============================================================================
    # Demonstrate Inheritance Chain
    # =============================================================================
    print("\n" + "=" * 60)
    print("📊 INHERITANCE HIERARCHY ANALYSIS")
    print("=" * 60)

    print("\n🔗 Inheritance Chain (Security Reviewer):")
    print("   base-code-reviewer (temp: 0.3, 2 tools, 1 skill)")
    print("        ↓ inherits & adds")
    print("   python-code-reviewer (temp: 0.2, 4 tools, 3 skills)")
    print("        ↓ inherits & adds")
    print("   fastapi-code-reviewer (temp: 0.25, 6 tools, 6 skills)")
    print("        ↓ inherits & adds")
    print("   security-code-reviewer (temp: 0.1, 9 tools, 9 skills)")

    print("\n📈 Tool Accumulation:")
    print(f"   Level 1 (Base):     {len(base_spec.tools)} tools")
    python_effective = python_agent.get_effective_spec()
    print(
        f"   Level 2 (Python):   {len(python_effective.tools)} tools (inherited + added)")
    fastapi_effective = fastapi_agent.get_effective_spec()
    print(
        f"   Level 3 (FastAPI):  {len(fastapi_effective.tools)} tools (inherited + added)")
    security_effective = security_agent.get_effective_spec()
    print(
        f"   Level 4 (Security): {len(security_effective.tools)} tools (inherited + added)")

    print("\n🎓 Skill Accumulation:")
    print(f"   Level 1 (Base):     {len(base_spec.skills)} skill")
    print(
        f"   Level 2 (Python):   {len(python_effective.skills)} skills (inherited + added)")
    print(
        f"   Level 3 (FastAPI):  {len(fastapi_effective.skills)} skills (inherited + added)")
    print(
        f"   Level 4 (Security): {len(security_effective.skills)} skills (inherited + added)")

    print("\n🎯 Temperature Evolution (stricter at each level):")
    print(f"   Base:     {base_spec.temperature}")
    print(f"   Python:   {python_spec.temperature}")
    print(f"   FastAPI:  {fastapi_spec.temperature}")
    print(f"   Security: {security_spec.temperature}")

    # =============================================================================
    # Practical Usage Example
    # =============================================================================
    print("\n" + "=" * 60)
    print("💼 PRACTICAL USAGE")
    print("=" * 60)

    print("\n✅ All specialized agents inherit from base reviewer:")
    print("   - All have read_file and grep_search tools (from base)")
    print("   - Each adds specialized tools for their domain")
    print("   - System prompts become more specialized down the chain")
    print("   - Temperature becomes stricter for security-sensitive reviews")

    print("\n🚀 Benefits of Inheritance:")
    print("   1. DRY Principle: Define common behavior once in base")
    print("   2. Progressive Specialization: Each level adds domain expertise")
    print("   3. Easy Updates: Change base affects all children")
    print("   4. Type Safety: Pydantic validation at every level")
    print("   5. Flexible Overrides: Children can override any parent property")

    print("\n✨ This is Paracle's unique advantage!")
    print("   No other framework offers agent inheritance like this.")

    # =============================================================================
    # Verify Inheritance Works
    # =============================================================================
    print("\n" + "=" * 60)
    print("🧪 VERIFICATION")
    print("=" * 60)

    # Verify tools are accumulated
    assert "read_file" in security_effective.tools, "Base tool should be inherited"
    assert "run_python_linter" in security_effective.tools, "Python tool should be inherited"
    assert "validate_openapi" in security_effective.tools, "FastAPI tool should be inherited"
    assert "scan_vulnerabilities" in security_effective.tools, "Security tool should be present"
    print("✅ Tool inheritance: VERIFIED")

    # Verify skills are accumulated
    assert "code-review" in security_effective.skills, "Base skill should be inherited"
    assert "python-best-practices" in security_effective.skills, "Python skill should be inherited"
    assert "api-design" in security_effective.skills, "FastAPI skill should be inherited"
    assert "security-audit" in security_effective.skills, "Security skill should be present"
    print("✅ Skill inheritance: VERIFIED")

    # Verify overrides work
    assert security_effective.temperature == 0.1, "Temperature should be overridden"
    assert security_effective.model == "gpt-4-turbo", "Model should be overridden"
    print("✅ Override mechanism: VERIFIED")

    # Verify metadata merging
    assert "role" in security_effective.metadata, "Base metadata should be inherited"
    assert "language" in security_effective.metadata, "Python metadata should be inherited"
    assert "framework" in security_effective.metadata, "FastAPI metadata should be inherited"
    assert "security_level" in security_effective.metadata, "Security metadata should be present"
    print("✅ Metadata merging: VERIFIED")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED! Agent Inheritance Works Perfectly!")
    print("=" * 60)


if __name__ == "__main__":
    main()
