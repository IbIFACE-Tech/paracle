"""Integration tests for Security Agent.

Tests the security agent's ability to perform security audits,
vulnerability detection, and compliance checking using inheritance.
"""

import pytest
from paracle_domain.factory import AgentFactory
from paracle_domain.models import AgentSpec
from paracle_store import AgentRepository


@pytest.fixture
def security_agent_spec():
    """Base security agent specification."""
    return AgentSpec(
        name="security",
        description="Security auditing and vulnerability detection",
        provider="openai",
        model="gpt-4",
        temperature=0.2,
        tools=[
            "bandit",
            "safety",
            "semgrep",
            "detect_secrets",
            "pip_audit",
            "trivy",
            "static_analysis",
            "security_scan",
            "vulnerability_detector",
            "secret_scanner",
            "dependency_auditor",
            "compliance_checker",
        ],
        skills=[
            "security-hardening",
            "testing-qa",
            "paracle-development",
            "performance-optimization",
        ],
        metadata={
            "role": "security_audit",
            "standards": ["OWASP Top 10", "CWE Top 25"],
            "compliance": ["GDPR", "SOC2"],
        },
    )


@pytest.fixture
def python_security_spec():
    """Python-specific security agent."""
    return AgentSpec(
        name="python-security-specialist",
        parent="security",
        description="Python security specialist",
        provider="openai",
        model="gpt-4",
        temperature=0.15,
        tools=["pylint_secure_coding"],
        skills=["python-security"],
        metadata={
            "language": "python",
            "focus": ["pickle", "eval", "subprocess", "path_traversal"],
        },
    )


@pytest.fixture
def api_security_spec():
    """API-specific security agent."""
    return AgentSpec(
        name="api-security-specialist",
        parent="security",
        description="API security specialist",
        provider="openai",
        model="gpt-4",
        temperature=0.2,
        tools=["owasp_zap", "burp_suite", "api_fuzzer"],
        skills=["api-security"],
        metadata={
            "protocols": ["REST", "GraphQL", "gRPC"],
            "focus": ["auth", "authorization", "rate_limit", "injection"],
        },
    )


@pytest.fixture
def agent_factory(security_agent_spec):
    """Agent factory with security agent registered."""
    repo = AgentRepository()
    repo.register_spec(security_agent_spec)
    return AgentFactory(spec_provider=repo.get_spec)


class TestSecurityAgentBasics:
    """Test basic security agent functionality."""

    def test_security_agent_creation(self, security_agent_spec, agent_factory):
        """Test creating base security agent."""
        agent = agent_factory.create(security_agent_spec)
        effective = agent.get_effective_spec()

        assert effective.name == "security"
        assert effective.description == "Security auditing and vulnerability detection"
        assert effective.temperature == 0.2
        assert len(effective.tools) == 12
        assert len(effective.skills) == 4

    def test_security_agent_has_all_tools(self, security_agent_spec, agent_factory):
        """Test security agent has all required security tools."""
        agent = agent_factory.create(security_agent_spec)
        effective = agent.get_effective_spec()

        # Core security tools
        assert "bandit" in effective.tools
        assert "safety" in effective.tools
        assert "semgrep" in effective.tools
        assert "detect_secrets" in effective.tools
        assert "pip_audit" in effective.tools
        assert "trivy" in effective.tools

        # Analysis tools
        assert "static_analysis" in effective.tools
        assert "security_scan" in effective.tools
        assert "vulnerability_detector" in effective.tools
        assert "secret_scanner" in effective.tools
        assert "dependency_auditor" in effective.tools
        assert "compliance_checker" in effective.tools

    def test_security_agent_has_all_skills(self, security_agent_spec, agent_factory):
        """Test security agent has all required skills."""
        agent = agent_factory.create(security_agent_spec)
        effective = agent.get_effective_spec()

        assert "security-hardening" in effective.skills
        assert "testing-qa" in effective.skills
        assert "paracle-development" in effective.skills
        assert "performance-optimization" in effective.skills

    def test_security_agent_metadata(self, security_agent_spec, agent_factory):
        """Test security agent has proper metadata."""
        agent = agent_factory.create(security_agent_spec)
        effective = agent.get_effective_spec()

        assert effective.metadata["role"] == "security_audit"
        assert "OWASP Top 10" in effective.metadata["standards"]
        assert "CWE Top 25" in effective.metadata["standards"]
        assert "GDPR" in effective.metadata["compliance"]
        assert "SOC2" in effective.metadata["compliance"]


class TestPythonSecuritySpecialist:
    """Test Python security specialist via inheritance."""

    def test_python_security_inherits_from_security(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test Python security specialist inherits from base security agent."""
        # Register both specs
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        agent = agent_factory.create(python_security_spec)
        effective = agent.get_effective_spec()

        # Check inheritance
        assert effective.name == "python-security-specialist"
        assert effective.parent == "security"

    def test_python_security_inherits_tools(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test Python security agent inherits all base tools."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        agent = agent_factory.create(python_security_spec)
        effective = agent.get_effective_spec()

        # Should have base tools (12) + python-specific (1) = 13
        assert len(effective.tools) == 13

        # Base tools
        assert "bandit" in effective.tools
        assert "safety" in effective.tools
        assert "semgrep" in effective.tools
        assert "detect_secrets" in effective.tools

        # Python-specific tool
        assert "pylint_secure_coding" in effective.tools

    def test_python_security_inherits_skills(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test Python security agent inherits skills."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        agent = agent_factory.create(python_security_spec)
        effective = agent.get_effective_spec()

        # Should have base skills (4) + python-specific (1) = 5
        assert len(effective.skills) == 5

        # Base skills
        assert "security-hardening" in effective.skills
        assert "testing-qa" in effective.skills
        assert "paracle-development" in effective.skills

        # Python-specific skill
        assert "python-security" in effective.skills

    def test_python_security_overrides_temperature(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test Python security agent can override temperature."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        agent = agent_factory.create(python_security_spec)
        effective = agent.get_effective_spec()

        # Should override to stricter temperature
        assert effective.temperature == 0.15
        assert effective.temperature < security_agent_spec.temperature

    def test_python_security_merges_metadata(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test Python security agent merges metadata."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        agent = agent_factory.create(python_security_spec)
        effective = agent.get_effective_spec()

        # Should have base metadata
        assert "role" in effective.metadata
        assert "standards" in effective.metadata
        assert "compliance" in effective.metadata

        # Should have Python-specific metadata
        assert effective.metadata["language"] == "python"
        assert "pickle" in effective.metadata["focus"]
        assert "eval" in effective.metadata["focus"]
        assert "subprocess" in effective.metadata["focus"]
        assert "path_traversal" in effective.metadata["focus"]


class TestAPISecuritySpecialist:
    """Test API security specialist via inheritance."""

    def test_api_security_inherits_from_security(
        self, security_agent_spec, api_security_spec, agent_factory
    ):
        """Test API security specialist inherits from base security agent."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(api_security_spec)

        agent = agent_factory.create(api_security_spec)
        effective = agent.get_effective_spec()

        assert effective.name == "api-security-specialist"
        assert effective.parent == "security"

    def test_api_security_inherits_tools(
        self, security_agent_spec, api_security_spec, agent_factory
    ):
        """Test API security agent inherits all base tools."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(api_security_spec)

        agent = agent_factory.create(api_security_spec)
        effective = agent.get_effective_spec()

        # Should have base tools (12) + API-specific (3) = 15
        assert len(effective.tools) == 15

        # Base tools
        assert "bandit" in effective.tools
        assert "safety" in effective.tools
        assert "trivy" in effective.tools

        # API-specific tools
        assert "owasp_zap" in effective.tools
        assert "burp_suite" in effective.tools
        assert "api_fuzzer" in effective.tools

    def test_api_security_inherits_skills(
        self, security_agent_spec, api_security_spec, agent_factory
    ):
        """Test API security agent inherits skills."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(api_security_spec)

        agent = agent_factory.create(api_security_spec)
        effective = agent.get_effective_spec()

        # Should have base skills (4) + API-specific (1) = 5
        assert len(effective.skills) == 5

        # Base skills
        assert "security-hardening" in effective.skills
        assert "testing-qa" in effective.skills

        # API-specific skill
        assert "api-security" in effective.skills

    def test_api_security_metadata(
        self, security_agent_spec, api_security_spec, agent_factory
    ):
        """Test API security agent has proper metadata."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(api_security_spec)

        agent = agent_factory.create(api_security_spec)
        effective = agent.get_effective_spec()

        # API-specific metadata
        assert "REST" in effective.metadata["protocols"]
        assert "GraphQL" in effective.metadata["protocols"]
        assert "gRPC" in effective.metadata["protocols"]

        assert "auth" in effective.metadata["focus"]
        assert "authorization" in effective.metadata["focus"]
        assert "rate_limit" in effective.metadata["focus"]
        assert "injection" in effective.metadata["focus"]


class TestSecurityAgentInheritanceChain:
    """Test multi-level inheritance for security agents."""

    def test_specialized_python_api_security(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test creating Python API security agent (3-level inheritance)."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        # Create Python API security specialist
        python_api_security = AgentSpec(
            name="python-api-security-specialist",
            parent="python-security-specialist",
            description="Python API security specialist",
            provider="openai",
            model="gpt-4-turbo",
            temperature=0.1,
            tools=["fastapi_security_scanner"],
            skills=["fastapi-security"],
            metadata={
                "framework": "fastapi",
                "focus": ["pydantic_injection", "async_race_conditions"],
            },
        )

        repo.register_spec(python_api_security)
        agent = agent_factory.create(python_api_security)
        effective = agent.get_effective_spec()

        # Check 3-level inheritance
        assert effective.name == "python-api-security-specialist"
        assert effective.parent == "python-security-specialist"

        # Should have tools from all 3 levels:
        # - security (12)
        # - python-security-specialist (1)
        # - python-api-security-specialist (1)
        # Total: 14 tools
        assert len(effective.tools) == 14

        # Base security tools
        assert "bandit" in effective.tools
        assert "safety" in effective.tools

        # Python security tools
        assert "pylint_secure_coding" in effective.tools

        # Python API security tools
        assert "fastapi_security_scanner" in effective.tools

    def test_no_duplicate_tools(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test that inherited tools don't duplicate."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        agent = agent_factory.create(python_security_spec)
        effective = agent.get_effective_spec()

        # Check no duplicates
        assert len(effective.tools) == len(set(effective.tools))

    def test_no_duplicate_skills(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test that inherited skills don't duplicate."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        agent = agent_factory.create(python_security_spec)
        effective = agent.get_effective_spec()

        # Check no duplicates
        assert len(effective.skills) == len(set(effective.skills))


class TestSecurityAgentWorkflows:
    """Test security agent in workflow scenarios."""

    def test_security_workflow_with_multiple_agents(
        self,
        security_agent_spec,
        python_security_spec,
        api_security_spec,
        agent_factory,
    ):
        """Test security workflow using multiple specialized agents."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)
        repo.register_spec(api_security_spec)

        # Create all three agents
        security = agent_factory.create(security_agent_spec)
        python_security = agent_factory.create(python_security_spec)
        api_security = agent_factory.create(api_security_spec)

        # Get effective specs
        sec_eff = security.get_effective_spec()
        py_sec_eff = python_security.get_effective_spec()
        api_sec_eff = api_security.get_effective_spec()

        # Verify all agents are distinct
        assert sec_eff.name == "security"
        assert py_sec_eff.name == "python-security-specialist"
        assert api_sec_eff.name == "api-security-specialist"

        # Verify tool counts are different
        assert len(sec_eff.tools) == 12
        assert len(py_sec_eff.tools) == 13
        assert len(api_sec_eff.tools) == 15

    def test_security_audit_workflow(
        self, security_agent_spec, python_security_spec, agent_factory
    ):
        """Test complete security audit workflow."""
        repo = agent_factory._spec_provider.__self__
        repo.register_spec(python_security_spec)

        # Workflow steps
        workflow_steps = [
            {
                "agent": "security",
                "task": "dependency_scan",
                "tools": ["pip_audit", "safety", "trivy"],
            },
            {
                "agent": "security",
                "task": "secret_scan",
                "tools": ["detect_secrets"],
            },
            {
                "agent": "python-security-specialist",
                "task": "python_code_review",
                "tools": ["bandit", "pylint_secure_coding"],
            },
            {
                "agent": "security",
                "task": "compliance_check",
                "tools": ["compliance_checker"],
            },
        ]

        # Verify agents can be created for each step
        for step in workflow_steps:
            if step["agent"] == "security":
                agent = agent_factory.create(security_agent_spec)
                effective = agent.get_effective_spec()
            else:
                agent = agent_factory.create(python_security_spec)
                effective = agent.get_effective_spec()

            # Verify agent has required tools
            for tool in step["tools"]:
                assert tool in effective.tools


class TestSecurityAgentValidation:
    """Test security agent validation and error handling."""

    def test_security_agent_requires_security_tools(self, agent_factory):
        """Test that security agent requires security tools."""
        # Security agent without security tools should be invalid
        invalid_spec = AgentSpec(
            name="invalid-security",
            description="Invalid security agent",
            provider="openai",
            model="gpt-4",
            tools=[],  # No tools!
            skills=["security-hardening"],
        )

        # Should still create (validation is separate concern)
        agent = agent_factory.create(invalid_spec)
        effective = agent.get_effective_spec()
        assert len(effective.tools) == 0

    def test_security_agent_requires_provider(self):
        """Test that security agent requires LLM provider."""
        with pytest.raises(Exception):  # Pydantic validation error
            AgentSpec(
                name="security",
                description="Security agent",
                # Missing provider!
                model="gpt-4",
                tools=["bandit"],
                skills=["security-hardening"],
            )

    def test_security_agent_temperature_bounds(self, agent_factory):
        """Test security agent temperature within valid bounds."""
        spec = AgentSpec(
            name="security",
            description="Security agent",
            provider="openai",
            model="gpt-4",
            temperature=0.2,  # Valid for security work
            tools=["bandit"],
            skills=["security-hardening"],
        )

        agent = agent_factory.create(spec)
        effective = agent.get_effective_spec()
        assert 0.0 <= effective.temperature <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
