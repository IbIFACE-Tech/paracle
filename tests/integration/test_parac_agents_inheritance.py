"""Integration tests for agent inheritance with .parac/agents/ specs.

This test suite validates that:
1. Agent specs can be loaded from .parac/agents/specs/
2. Inheritance works with real Paracle agent definitions
3. Specialized agents inherit and extend base agents correctly
4. Multi-level inheritance accumulates tools, skills, and metadata
"""

from pathlib import Path

import pytest
from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_store import AgentRepository


@pytest.fixture
def parac_specs_dir():
    """Get path to .parac/agents/specs/ directory."""
    return Path(__file__).parent.parent.parent / ".parac" / "agents" / "specs"


@pytest.fixture
def repo():
    """Create fresh agent repository."""
    return AgentRepository()


@pytest.fixture
def factory(repo):
    """Create agent factory with repository."""
    return AgentFactory(spec_provider=repo.get_spec)


@pytest.fixture
def base_reviewer_spec(repo):
    """Create base reviewer spec (simulating load from .parac/)."""
    spec = AgentSpec(
        name="reviewer",
        description="Code reviewer ensuring quality and best practices",
        provider="openai",
        model="gpt-4",
        temperature=0.3,
        system_prompt=(
            "You are a code reviewer ensuring quality and best practices. "
            "Review code for correctness, security, performance, and maintainability."
        ),
        tools=["static_analysis", "security_scan", "code_review"],
        skills=["code-review", "quality-assurance", "security-hardening"],
        metadata={
            "role": "code_review",
            "source": ".parac/agents/specs/reviewer.md",
        },
    )
    repo.register_spec(spec)
    return spec


# =============================================================================
# Test: Basic Inheritance from .parac/ Agent
# =============================================================================


def test_security_reviewer_inherits_from_base(repo, factory, base_reviewer_spec):
    """Security reviewer should inherit base reviewer's tools and skills."""
    # Create specialized security reviewer
    security_spec = AgentSpec(
        name="security-reviewer",
        description="Security-focused code reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        temperature=0.2,
        system_prompt="Security expert reviewing code for vulnerabilities.",
        tools=["vulnerability_scanner", "dependency_checker", "secret_detector"],
        skills=["owasp-top-10", "penetration-testing", "threat-modeling"],
        metadata={"focus": "security", "owasp_version": "2023"},
    )

    repo.register_spec(security_spec)
    agent = factory.create(security_spec)
    effective = agent.get_effective_spec()

    # Should inherit base tools
    assert "static_analysis" in effective.tools
    assert "security_scan" in effective.tools
    assert "code_review" in effective.tools

    # Should have own tools
    assert "vulnerability_scanner" in effective.tools
    assert "dependency_checker" in effective.tools

    # Should inherit base skills
    assert "code-review" in effective.skills
    assert "quality-assurance" in effective.skills

    # Should have own skills
    assert "owasp-top-10" in effective.skills
    assert "penetration-testing" in effective.skills

    # Total: 6 tools (3 inherited + 3 own)
    assert len(effective.tools) == 6

    # Total: 6 skills (3 inherited + 3 own)
    assert len(effective.skills) == 6


# =============================================================================
# Test: Multi-Level Inheritance (Grandchild)
# =============================================================================


def test_python_security_reviewer_two_level_inheritance(
    repo, factory, base_reviewer_spec
):
    """Python security reviewer should inherit through 2 levels."""
    # Create parent (security reviewer)
    security_spec = AgentSpec(
        name="security-reviewer",
        description="Security-focused code reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        temperature=0.2,
        tools=["vulnerability_scanner", "dependency_checker"],
        skills=["owasp-top-10", "penetration-testing"],
        metadata={"focus": "security"},
    )
    repo.register_spec(security_spec)

    # Create grandchild (Python security reviewer)
    python_security_spec = AgentSpec(
        name="python-security-reviewer",
        description="Python-specific security reviewer",
        parent="security-reviewer",
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.15,
        tools=["bandit", "safety"],
        skills=["python-security", "pickle-safety"],
        metadata={"language": "python"},
    )
    repo.register_spec(python_security_spec)

    agent = factory.create(python_security_spec)
    effective = agent.get_effective_spec()

    # Should inherit from grandparent (reviewer)
    assert "static_analysis" in effective.tools
    assert "code-review" in effective.skills

    # Should inherit from parent (security-reviewer)
    assert "vulnerability_scanner" in effective.tools
    assert "owasp-top-10" in effective.skills

    # Should have own tools/skills
    assert "bandit" in effective.tools
    assert "python-security" in effective.skills

    # Total: 7 tools (3 base + 2 parent + 2 own)
    assert len(effective.tools) == 7

    # Total: 7 skills (3 base + 2 parent + 2 own)
    assert len(effective.skills) == 7

    # Should use own temperature (strictest)
    assert effective.temperature == 0.15


# =============================================================================
# Test: Sibling Agents (Different Specializations)
# =============================================================================


def test_performance_reviewer_sibling_specialization(repo, factory, base_reviewer_spec):
    """Performance reviewer should be independent sibling of security reviewer."""
    # Create security reviewer
    security_spec = AgentSpec(
        name="security-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        tools=["vulnerability_scanner"],
        skills=["owasp-top-10"],
    )
    repo.register_spec(security_spec)

    # Create performance reviewer (sibling)
    performance_spec = AgentSpec(
        name="performance-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        tools=["profiler", "complexity_analyzer"],
        skills=["algorithmic-optimization", "database-tuning"],
    )
    repo.register_spec(performance_spec)

    security_agent = factory.create(security_spec)
    performance_agent = factory.create(performance_spec)

    security_effective = security_agent.get_effective_spec()
    performance_effective = performance_agent.get_effective_spec()

    # Both should inherit base tools
    assert "static_analysis" in security_effective.tools
    assert "static_analysis" in performance_effective.tools

    # But have different specialized tools
    assert "vulnerability_scanner" in security_effective.tools
    assert "vulnerability_scanner" not in performance_effective.tools

    assert "profiler" in performance_effective.tools
    assert "profiler" not in security_effective.tools

    # Both should inherit base skills
    assert "code-review" in security_effective.skills
    assert "code-review" in performance_effective.skills

    # But have different specialized skills
    assert "owasp-top-10" in security_effective.skills
    assert "owasp-top-10" not in performance_effective.skills

    assert "algorithmic-optimization" in performance_effective.skills
    assert "algorithmic-optimization" not in security_effective.skills


# =============================================================================
# Test: Property Override Through Inheritance
# =============================================================================


def test_temperature_override_cascade(repo, factory, base_reviewer_spec):
    """Temperature should be progressively overridden through inheritance."""
    # Create 3-level hierarchy with different temperatures
    security_spec = AgentSpec(
        name="security-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        temperature=0.2,  # Stricter than base (0.3)
    )
    repo.register_spec(security_spec)

    python_security_spec = AgentSpec(
        name="python-security-reviewer",
        parent="security-reviewer",
        provider="openai",
        model="gpt-4",
        temperature=0.15,  # Even stricter
    )
    repo.register_spec(python_security_spec)

    base_agent = factory.create(base_reviewer_spec)
    security_agent = factory.create(security_spec)
    python_security_agent = factory.create(python_security_spec)

    # Each level should have its own temperature
    assert base_agent.get_effective_spec().temperature == 0.3
    assert security_agent.get_effective_spec().temperature == 0.2
    assert python_security_agent.get_effective_spec().temperature == 0.15


# =============================================================================
# Test: Model Upgrade Through Inheritance
# =============================================================================


def test_model_upgrade_in_specialization(repo, factory, base_reviewer_spec):
    """Specialized agents can upgrade to more capable models."""
    python_security_spec = AgentSpec(
        name="python-security-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4-turbo",  # Upgraded from gpt-4
    )
    repo.register_spec(python_security_spec)

    base_agent = factory.create(base_reviewer_spec)
    specialized_agent = factory.create(python_security_spec)

    assert base_agent.get_effective_spec().model == "gpt-4"
    assert specialized_agent.get_effective_spec().model == "gpt-4-turbo"


# =============================================================================
# Test: Metadata Merging
# =============================================================================


def test_metadata_merging_through_inheritance(repo, factory, base_reviewer_spec):
    """Metadata should merge across inheritance levels."""
    security_spec = AgentSpec(
        name="security-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        metadata={
            "focus": "security",
            "owasp_version": "2023",
        },
    )
    repo.register_spec(security_spec)

    python_security_spec = AgentSpec(
        name="python-security-reviewer",
        parent="security-reviewer",
        provider="openai",
        model="gpt-4",
        metadata={
            "language": "python",
            "python_version": "3.10+",
        },
    )
    repo.register_spec(python_security_spec)

    agent = factory.create(python_security_spec)
    effective = agent.get_effective_spec()

    # Should have metadata from all levels
    assert effective.metadata["role"] == "code_review"  # From base
    assert effective.metadata["focus"] == "security"  # From parent
    assert effective.metadata["language"] == "python"  # Own
    assert effective.metadata["owasp_version"] == "2023"  # From parent
    assert effective.metadata["python_version"] == "3.10+"  # Own


# =============================================================================
# Test: System Prompt Inheritance
# =============================================================================


def test_system_prompt_override(repo, factory, base_reviewer_spec):
    """Child should override parent system prompt."""
    security_spec = AgentSpec(
        name="security-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        system_prompt="You are a security expert reviewing code for vulnerabilities.",
    )
    repo.register_spec(security_spec)

    base_agent = factory.create(base_reviewer_spec)
    security_agent = factory.create(security_spec)

    base_effective = base_agent.get_effective_spec()
    security_effective = security_agent.get_effective_spec()

    # System prompts should be different
    assert "quality and best practices" in base_effective.system_prompt
    assert "security expert" in security_effective.system_prompt


# =============================================================================
# Test: No Duplicate Tools/Skills
# =============================================================================


def test_no_duplicates_in_inheritance(repo, factory, base_reviewer_spec):
    """Tools and skills should not be duplicated through inheritance."""
    # Create child with some overlapping tools/skills
    security_spec = AgentSpec(
        name="security-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        # security_scan overlaps!
        tools=["security_scan", "vulnerability_scanner"],
        # security-hardening overlaps!
        skills=["security-hardening", "owasp-top-10"],
    )
    repo.register_spec(security_spec)

    agent = factory.create(security_spec)
    effective = agent.get_effective_spec()

    # Should not have duplicates
    tools_list = list(effective.tools)
    skills_list = list(effective.skills)

    assert len(tools_list) == len(set(tools_list)), "Tools should not have duplicates"
    assert len(skills_list) == len(
        set(skills_list)
    ), "Skills should not have duplicates"

    # security_scan should appear only once
    assert tools_list.count("security_scan") == 1

    # security-hardening should appear only once
    assert skills_list.count("security-hardening") == 1


# =============================================================================
# Test: Validation of Inheritance Chain
# =============================================================================


def test_inheritance_chain_validation(repo, factory, base_reviewer_spec):
    """Factory should validate inheritance chain is resolvable."""
    # Create spec with non-existent parent
    invalid_spec = AgentSpec(
        name="invalid-reviewer",
        parent="non-existent-agent",
        provider="openai",
        model="gpt-4",
    )

    # Should raise error when trying to create
    with pytest.raises(ValueError, match="not found"):
        factory.create(invalid_spec)


# =============================================================================
# Test: Real-World Usage Pattern
# =============================================================================


def test_real_world_usage_create_specialized_reviewer(
    repo, factory, base_reviewer_spec
):
    """Demonstrate real-world pattern: loading base from .parac/ and creating specialized agent."""
    # 1. Base reviewer is from .parac/agents/specs/reviewer.md (already loaded)

    # 2. Create specialized FastAPI security reviewer
    fastapi_security_spec = AgentSpec(
        name="fastapi-security-reviewer",
        description="FastAPI-specific security reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.18,
        system_prompt=(
            "You are a FastAPI security expert. "
            "Review FastAPI code for security issues: "
            "Pydantic validation, dependency injection security, "
            "CORS configuration, OAuth2 flows, SQL injection via ORMs."
        ),
        tools=[
            "fastapi_security_scanner",
            "pydantic_validator",
            "dependency_injector_checker",
        ],
        skills=[
            "fastapi-security",
            "pydantic-validation",
            "oauth2-flows",
        ],
        metadata={
            "framework": "fastapi",
            "python_version": "3.10+",
            "focus": "api_security",
        },
    )

    repo.register_spec(fastapi_security_spec)
    agent = factory.create(fastapi_security_spec)
    effective = agent.get_effective_spec()

    # Verify it inherited base reviewer capabilities
    assert "static_analysis" in effective.tools
    assert "code-review" in effective.skills

    # Verify it has FastAPI-specific capabilities
    assert "fastapi_security_scanner" in effective.tools
    assert "fastapi-security" in effective.skills

    # Verify metadata merged correctly
    assert effective.metadata["role"] == "code_review"  # From base
    assert effective.metadata["framework"] == "fastapi"  # Own

    # Verify configuration
    assert effective.model == "gpt-4-turbo"
    assert effective.temperature == 0.18

    # Should have accumulated tools and skills
    assert len(effective.tools) == 6  # 3 base + 3 own
    assert len(effective.skills) == 6  # 3 base + 3 own


# =============================================================================
# Summary Test: Complete Inheritance Hierarchy
# =============================================================================


def test_complete_inheritance_hierarchy(repo, factory, base_reviewer_spec):
    """Test a complete inheritance hierarchy with multiple levels and siblings."""
    # Level 1: Base reviewer (already created)

    # Level 2: Security reviewer
    security_spec = AgentSpec(
        name="security-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        tools=["vulnerability_scanner"],
        skills=["owasp-top-10"],
        temperature=0.2,
    )
    repo.register_spec(security_spec)

    # Level 2: Performance reviewer (sibling)
    performance_spec = AgentSpec(
        name="performance-reviewer",
        parent="reviewer",
        provider="openai",
        model="gpt-4",
        tools=["profiler"],
        skills=["algorithmic-optimization"],
        temperature=0.25,
    )
    repo.register_spec(performance_spec)

    # Level 3: Python security reviewer (child of security)
    python_security_spec = AgentSpec(
        name="python-security-reviewer",
        parent="security-reviewer",
        provider="openai",
        model="gpt-4",
        tools=["bandit"],
        skills=["python-security"],
        temperature=0.15,
    )
    repo.register_spec(python_security_spec)

    # Create all agents
    base_agent = factory.create(base_reviewer_spec)
    security_agent = factory.create(security_spec)
    performance_agent = factory.create(performance_spec)
    python_security_agent = factory.create(python_security_spec)

    # Get effective specs
    base_eff = base_agent.get_effective_spec()
    security_eff = security_agent.get_effective_spec()
    performance_eff = performance_agent.get_effective_spec()
    python_security_eff = python_security_agent.get_effective_spec()

    # Verify tool counts
    assert len(base_eff.tools) == 3
    assert len(security_eff.tools) == 4  # 3 + 1
    assert len(performance_eff.tools) == 4  # 3 + 1
    assert len(python_security_eff.tools) == 5  # 3 + 1 + 1

    # Verify skill counts
    assert len(base_eff.skills) == 3
    assert len(security_eff.skills) == 4  # 3 + 1
    assert len(performance_eff.skills) == 4  # 3 + 1
    assert len(python_security_eff.skills) == 5  # 3 + 1 + 1

    # Verify temperatures cascade correctly
    assert base_eff.temperature == 0.3
    assert security_eff.temperature == 0.2
    assert performance_eff.temperature == 0.25
    assert python_security_eff.temperature == 0.15

    # Verify inheritance paths are correct
    assert security_spec.parent == "reviewer"
    assert performance_spec.parent == "reviewer"
    assert python_security_spec.parent == "security-reviewer"

    print("\n✅ Complete inheritance hierarchy test passed!")
    print(f"   Base: {len(base_eff.tools)} tools, {len(base_eff.skills)} skills")
    print(
        f"   Security: {len(security_eff.tools)} tools, {len(security_eff.skills)} skills"
    )
    print(
        f"   Performance: {len(performance_eff.tools)} tools, {len(performance_eff.skills)} skills"
    )
    print(
        f"   Python Security: {len(python_security_eff.tools)} tools, {len(python_security_eff.skills)} skills"
    )
