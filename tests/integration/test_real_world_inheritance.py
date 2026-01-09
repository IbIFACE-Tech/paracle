"""Integration test for real-world agent inheritance example.

Tests that the inheritance hierarchy works correctly with:
- Multi-level inheritance (4 levels)
- Tool accumulation
- Skill accumulation
- Property overrides
- Metadata merging
"""

import pytest
from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_store import AgentRepository


class TestRealWorldInheritance:
    """Test real-world agent inheritance scenario."""

    @pytest.fixture
    def factory(self) -> AgentFactory:
        """Create agent factory with in-memory repository."""
        repo = AgentRepository()
        return AgentFactory(spec_provider=repo.get_spec), repo

    @pytest.fixture
    def agent_hierarchy(self, factory: tuple) -> dict[str, object]:
        """Create the full agent hierarchy.

        Returns a dict with all agents for testing.
        """
        factory_obj, repo = factory

        # Level 1: Base Code Reviewer
        base_spec = AgentSpec(
            name="base-code-reviewer",
            description="General code reviewer for any language",
            provider="openai",
            model="gpt-4",
            temperature=0.3,
            system_prompt="You are an experienced code reviewer.",
            tools=["read_file", "grep_search"],
            skills=["code-review"],
            metadata={
                "role": "reviewer",
                "experience_level": "senior",
            }
        )
        repo.register_spec(base_spec)
        base_agent = factory_obj.create(base_spec)

        # Level 2: Python Specialist
        python_spec = AgentSpec(
            name="python-code-reviewer",
            description="Python code reviewer",
            parent="base-code-reviewer",
            provider="openai",
            model="gpt-4",
            temperature=0.2,
            system_prompt="You are a Python expert code reviewer.",
            tools=["run_python_linter", "check_type_hints"],
            skills=["python-best-practices", "typing"],
            metadata={
                "language": "python",
                "pep8_strict": True,
            }
        )
        repo.register_spec(python_spec)
        python_agent = factory_obj.create(python_spec)

        # Level 3: FastAPI Specialist
        fastapi_spec = AgentSpec(
            name="fastapi-code-reviewer",
            description="FastAPI/REST API code reviewer",
            parent="python-code-reviewer",
            provider="openai",
            model="gpt-4-turbo",
            temperature=0.25,
            system_prompt="You are a FastAPI and REST API expert.",
            tools=["validate_openapi", "check_api_security"],
            skills=["api-design", "fastapi", "rest-patterns"],
            metadata={
                "framework": "fastapi",
                "api_version": "v1",
            }
        )
        repo.register_spec(fastapi_spec)
        fastapi_agent = factory_obj.create(fastapi_spec)

        # Level 4: Security Specialist
        security_spec = AgentSpec(
            name="security-code-reviewer",
            description="Security-focused code reviewer",
            parent="fastapi-code-reviewer",
            provider="openai",
            model="gpt-4-turbo",
            temperature=0.1,
            system_prompt="You are a security expert.",
            tools=["scan_vulnerabilities", "check_dependencies", "audit_auth"],
            skills=["security-audit", "owasp", "penetration-testing"],
            metadata={
                "security_level": "high",
                "owasp_version": "2023",
            }
        )
        repo.register_spec(security_spec)
        security_agent = factory_obj.create(security_spec)

        return {
            "base": base_agent,
            "python": python_agent,
            "fastapi": fastapi_agent,
            "security": security_agent,
        }

    def test_base_agent_no_inheritance(self, agent_hierarchy: dict) -> None:
        """Test that base agent has no parent."""
        base = agent_hierarchy["base"]
        spec = base.get_effective_spec()

        assert spec.parent is None
        assert len(spec.tools) == 2
        assert len(spec.skills) == 1
        assert spec.temperature == 0.3

    def test_python_inherits_from_base(self, agent_hierarchy: dict) -> None:
        """Test that Python agent inherits from base correctly."""
        python = agent_hierarchy["python"]
        spec = python.get_effective_spec()

        # Check inheritance
        assert python.spec.parent == "base-code-reviewer"

        # Check tool accumulation (2 from base + 2 new)
        assert len(spec.tools) == 4
        assert "read_file" in spec.tools  # From base
        assert "grep_search" in spec.tools  # From base
        assert "run_python_linter" in spec.tools  # New
        assert "check_type_hints" in spec.tools  # New

        # Check skill accumulation (1 from base + 2 new)
        assert len(spec.skills) == 3
        assert "code-review" in spec.skills  # From base
        assert "python-best-practices" in spec.skills  # New
        assert "typing" in spec.skills  # New

        # Check override
        assert spec.temperature == 0.2  # Overridden

        # Check metadata merging
        assert "role" in spec.metadata  # From base
        assert "experience_level" in spec.metadata  # From base
        assert "language" in spec.metadata  # New
        assert "pep8_strict" in spec.metadata  # New

    def test_fastapi_multi_level_inheritance(self, agent_hierarchy: dict) -> None:
        """Test that FastAPI agent inherits through 2 levels."""
        fastapi = agent_hierarchy["fastapi"]
        spec = fastapi.get_effective_spec()

        # Check inheritance chain
        assert fastapi.spec.parent == "python-code-reviewer"

        # Check tool accumulation (2 + 2 + 2 = 6)
        assert len(spec.tools) == 6
        assert "read_file" in spec.tools  # From base
        assert "grep_search" in spec.tools  # From base
        assert "run_python_linter" in spec.tools  # From python
        assert "check_type_hints" in spec.tools  # From python
        assert "validate_openapi" in spec.tools  # New
        assert "check_api_security" in spec.tools  # New

        # Check skill accumulation (1 + 2 + 3 = 6)
        assert len(spec.skills) == 6
        assert "code-review" in spec.skills  # From base
        assert "python-best-practices" in spec.skills  # From python
        assert "typing" in spec.skills  # From python
        assert "api-design" in spec.skills  # New
        assert "fastapi" in spec.skills  # New
        assert "rest-patterns" in spec.skills  # New

        # Check model override
        assert spec.model == "gpt-4-turbo"  # Upgraded

        # Check metadata from all levels
        assert "role" in spec.metadata  # From base
        assert "language" in spec.metadata  # From python
        assert "framework" in spec.metadata  # New
        assert "api_version" in spec.metadata  # New

    def test_security_three_level_inheritance(self, agent_hierarchy: dict) -> None:
        """Test that Security agent inherits through 3 levels."""
        security = agent_hierarchy["security"]
        spec = security.get_effective_spec()

        # Check inheritance chain
        assert security.spec.parent == "fastapi-code-reviewer"

        # Check tool accumulation (2 + 2 + 2 + 3 = 9)
        assert len(spec.tools) == 9
        # From base
        assert "read_file" in spec.tools
        assert "grep_search" in spec.tools
        # From python
        assert "run_python_linter" in spec.tools
        assert "check_type_hints" in spec.tools
        # From fastapi
        assert "validate_openapi" in spec.tools
        assert "check_api_security" in spec.tools
        # From security
        assert "scan_vulnerabilities" in spec.tools
        assert "check_dependencies" in spec.tools
        assert "audit_auth" in spec.tools

        # Check skill accumulation (1 + 2 + 3 + 3 = 9)
        assert len(spec.skills) == 9
        # From base
        assert "code-review" in spec.skills
        # From python
        assert "python-best-practices" in spec.skills
        assert "typing" in spec.skills
        # From fastapi
        assert "api-design" in spec.skills
        assert "fastapi" in spec.skills
        assert "rest-patterns" in spec.skills
        # From security
        assert "security-audit" in spec.skills
        assert "owasp" in spec.skills
        assert "penetration-testing" in spec.skills

        # Check strictest temperature
        assert spec.temperature == 0.1

        # Check metadata from all levels
        assert "role" in spec.metadata  # From base
        assert "experience_level" in spec.metadata  # From base
        assert "language" in spec.metadata  # From python
        assert "pep8_strict" in spec.metadata  # From python
        assert "framework" in spec.metadata  # From fastapi
        assert "api_version" in spec.metadata  # From fastapi
        assert "security_level" in spec.metadata  # From security
        assert "owasp_version" in spec.metadata  # From security

    def test_temperature_overrides_cascade(self, agent_hierarchy: dict) -> None:
        """Test that temperature becomes stricter at each level."""
        base = agent_hierarchy["base"].get_effective_spec()
        python = agent_hierarchy["python"].get_effective_spec()
        fastapi = agent_hierarchy["fastapi"].get_effective_spec()
        security = agent_hierarchy["security"].get_effective_spec()

        assert base.temperature == 0.3
        assert python.temperature == 0.2  # Stricter
        assert fastapi.temperature == 0.25  # Slightly relaxed for API flexibility
        assert security.temperature == 0.1  # Strictest for security

    def test_model_upgrades_cascade(self, agent_hierarchy: dict) -> None:
        """Test that model can be upgraded in child agents."""
        base = agent_hierarchy["base"].get_effective_spec()
        python = agent_hierarchy["python"].get_effective_spec()
        fastapi = agent_hierarchy["fastapi"].get_effective_spec()
        security = agent_hierarchy["security"].get_effective_spec()

        assert base.model == "gpt-4"
        assert python.model == "gpt-4"  # Inherited
        assert fastapi.model == "gpt-4-turbo"  # Upgraded
        assert security.model == "gpt-4-turbo"  # Inherited upgrade

    def test_system_prompts_specialize(self, agent_hierarchy: dict) -> None:
        """Test that system prompts become more specialized."""
        base = agent_hierarchy["base"].get_effective_spec()
        python = agent_hierarchy["python"].get_effective_spec()
        fastapi = agent_hierarchy["fastapi"].get_effective_spec()
        security = agent_hierarchy["security"].get_effective_spec()

        # Each prompt should be unique and specialized
        assert "experienced code reviewer" in base.system_prompt.lower()
        assert "python expert" in python.system_prompt.lower()
        assert "fastapi" in fastapi.system_prompt.lower(
        ) or "rest api" in fastapi.system_prompt.lower()
        assert "security expert" in security.system_prompt.lower()

    def test_no_duplicate_tools(self, agent_hierarchy: dict) -> None:
        """Test that tools are not duplicated during inheritance."""
        security = agent_hierarchy["security"]
        spec = security.get_effective_spec()

        # Check no duplicates
        assert len(spec.tools) == len(set(spec.tools))

        # Verify specific tools appear only once
        assert spec.tools.count("read_file") == 1
        assert spec.tools.count("grep_search") == 1
        assert spec.tools.count("run_python_linter") == 1

    def test_no_duplicate_skills(self, agent_hierarchy: dict) -> None:
        """Test that skills are not duplicated during inheritance."""
        security = agent_hierarchy["security"]
        spec = security.get_effective_spec()

        # Check no duplicates
        assert len(spec.skills) == len(set(spec.skills))

        # Verify specific skills appear only once
        assert spec.skills.count("code-review") == 1
        assert spec.skills.count("python-best-practices") == 1
        assert spec.skills.count("api-design") == 1

    def test_resolved_spec_attached(self, agent_hierarchy: dict) -> None:
        """Test that resolved spec is attached to agent."""
        security = agent_hierarchy["security"]

        assert security.resolved_spec is not None
        assert security.resolved_spec.name == "security-code-reviewer"
        assert len(security.resolved_spec.tools) == 9
        assert len(security.resolved_spec.skills) == 9

    def test_inheritance_chain_depth(self, agent_hierarchy: dict) -> None:
        """Test that inheritance depth is tracked correctly."""
        # Base has depth 0
        base = agent_hierarchy["base"]
        assert base.spec.parent is None

        # Python has depth 1
        python = agent_hierarchy["python"]
        assert python.spec.parent == "base-code-reviewer"

        # FastAPI has depth 2
        fastapi = agent_hierarchy["fastapi"]
        assert fastapi.spec.parent == "python-code-reviewer"

        # Security has depth 3
        security = agent_hierarchy["security"]
        assert security.spec.parent == "fastapi-code-reviewer"

    def test_metadata_child_overrides_parent(self, agent_hierarchy: dict) -> None:
        """Test that child metadata overrides parent keys."""
        python = agent_hierarchy["python"]
        spec = python.get_effective_spec()

        # Base sets experience_level = "senior"
        # Python keeps it (not overridden)
        assert spec.metadata["experience_level"] == "senior"

        # Python adds language = "python"
        assert spec.metadata["language"] == "python"

    def test_practical_usage_scenario(self, agent_hierarchy: dict) -> None:
        """Test a practical usage scenario.

        Simulate using different specialized reviewers for different tasks.
        """
        # Use Python reviewer for Python code
        python = agent_hierarchy["python"]
        python_spec = python.get_effective_spec()
        assert "python-best-practices" in python_spec.skills
        assert "run_python_linter" in python_spec.tools

        # Use FastAPI reviewer for API code
        fastapi = agent_hierarchy["fastapi"]
        fastapi_spec = fastapi.get_effective_spec()
        assert "api-design" in fastapi_spec.skills
        assert "validate_openapi" in fastapi_spec.tools
        # Also has Python capabilities
        assert "python-best-practices" in fastapi_spec.skills
        assert "run_python_linter" in fastapi_spec.tools

        # Use Security reviewer for security audits
        security = agent_hierarchy["security"]
        security_spec = security.get_effective_spec()
        assert "security-audit" in security_spec.skills
        assert "scan_vulnerabilities" in security_spec.tools
        # Also has all parent capabilities
        assert "code-review" in security_spec.skills  # From base
        assert "python-best-practices" in security_spec.skills  # From python
        assert "api-design" in security_spec.skills  # From fastapi

    def test_dry_principle_benefit(self, agent_hierarchy: dict, factory: AgentFactory) -> None:
        """Test DRY principle benefit.

        If we update the base agent, all children should inherit the change.
        """
        # Create a new child from updated base
        repo = factory.repo

        # Get base agent and update it (simulate modification)
        base_spec = AgentSpec(
            name="base-code-reviewer",
            description="Updated base reviewer",
            provider="openai",
            model="gpt-4",
            temperature=0.3,
            system_prompt="Updated system prompt",
            tools=["read_file", "grep_search",
                   "new_common_tool"],  # Added tool
            skills=["code-review", "new_common_skill"],  # Added skill
            metadata={
                "role": "reviewer",
                "experience_level": "senior",
                "version": "2.0",  # New metadata
            }
        )

        # Save updated base (would update existing in real scenario)
        repo.save(base_spec)

        # Create new Python agent that should inherit new changes
        new_python_spec = AgentSpec(
            name="python-reviewer-v2",
            description="New Python reviewer",
            parent="base-code-reviewer",
            provider="openai",
            model="gpt-4",
            temperature=0.2,
            system_prompt="Python expert",
            tools=["python_tool"],
            skills=["python-skill"],
        )

        new_python = factory.create(new_python_spec)
        new_python_effective = new_python.get_effective_spec()

        # Verify new common tool and skill are inherited
        assert "new_common_tool" in new_python_effective.tools
        assert "new_common_skill" in new_python_effective.skills
        assert "version" in new_python_effective.metadata
        assert new_python_effective.metadata["version"] == "2.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
