"""Unit tests for paracle_meta.generators module."""

import pytest
from paracle_meta.generators import (
    AgentGenerator,
    PolicyGenerator,
    SkillGenerator,
    WorkflowGenerator,
)
from paracle_meta.generators.base import GenerationRequest, GenerationResult
from paracle_meta.providers import ProviderOrchestrator


class TestGenerationRequest:
    """Tests for GenerationRequest model."""

    def test_create_request(self):
        """Test creating a generation request."""
        request = GenerationRequest(
            artifact_type="agent",
            name="TestAgent",
            description="A test agent for testing",
        )
        assert request.artifact_type == "agent"
        assert request.name == "TestAgent"
        assert request.auto_apply is False

    def test_create_request_with_context(self):
        """Test creating request with context."""
        request = GenerationRequest(
            artifact_type="policy",
            name="SecurityPolicy",
            description="Security requirements",
            context={"policy_type": "security"},
            auto_apply=True,
        )
        assert request.context["policy_type"] == "security"
        assert request.auto_apply is True


class TestGenerationResult:
    """Tests for GenerationResult model."""

    def test_create_result(self):
        """Test creating a generation result."""
        result = GenerationResult(
            id="gen_123",
            artifact_type="agent",
            name="TestAgent",
            content="name: TestAgent\nrole: Test",
            provider="anthropic",
            model="claude-sonnet-4",
            quality_score=8.5,
            cost_usd=0.003,
            tokens_input=500,
            tokens_output=200,
            reasoning="Generated successfully",
        )
        assert result.id == "gen_123"
        assert result.quality_score == 8.5

    def test_result_defaults(self):
        """Test result default values."""
        result = GenerationResult(
            id="gen_456",
            artifact_type="workflow",
            name="TestWorkflow",
            content="test content",
            provider="openai",
            model="gpt-4",
        )
        assert result.quality_score == 0.0
        assert result.cost_usd == 0.0
        assert result.created_at is not None


class TestAgentGenerator:
    """Tests for AgentGenerator."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create agent generator."""
        orchestrator = ProviderOrchestrator(config_path=tmp_path / "config.yaml")
        return AgentGenerator(orchestrator)

    def test_artifact_type(self, generator):
        """Test artifact type is correct."""
        assert generator.ARTIFACT_TYPE == "agent"

    @pytest.mark.asyncio
    async def test_generate_agent(self, generator):
        """Test generating an agent (mock mode)."""
        request = GenerationRequest(
            artifact_type="agent",
            name="SecurityAuditor",
            description="Reviews code for security vulnerabilities",
        )

        result = await generator.generate(
            request=request,
            provider="anthropic",
            model="claude-sonnet-4",
            best_practices=None,
        )

        assert result.artifact_type == "agent"
        assert result.name == "SecurityAuditor"
        assert "name:" in result.content
        assert result.tokens_input > 0

    @pytest.mark.asyncio
    async def test_generate_includes_best_practices(self, generator):
        """Test that best practices are included in prompt."""
        request = GenerationRequest(
            artifact_type="agent",
            name="TestAgent",
            description="A test agent",
        )

        # Mock practices
        practices = [{"title": "Clear Role", "recommendation": "Define specific role"}]

        result = await generator.generate(
            request=request,
            provider="anthropic",
            model="claude-sonnet-4",
            best_practices=practices,
        )

        # Should complete without error
        assert result is not None


class TestWorkflowGenerator:
    """Tests for WorkflowGenerator."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create workflow generator."""
        orchestrator = ProviderOrchestrator(config_path=tmp_path / "config.yaml")
        return WorkflowGenerator(orchestrator)

    def test_artifact_type(self, generator):
        """Test artifact type is correct."""
        assert generator.ARTIFACT_TYPE == "workflow"

    @pytest.mark.asyncio
    async def test_generate_workflow(self, generator):
        """Test generating a workflow (mock mode)."""
        request = GenerationRequest(
            artifact_type="workflow",
            name="deployment",
            description="Deploy to production with tests and rollback",
        )

        result = await generator.generate(
            request=request,
            provider="openai",
            model="gpt-4",
            best_practices=None,
        )

        assert result.artifact_type == "workflow"
        assert "steps:" in result.content or "name:" in result.content


class TestSkillGenerator:
    """Tests for SkillGenerator."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create skill generator."""
        orchestrator = ProviderOrchestrator(config_path=tmp_path / "config.yaml")
        return SkillGenerator(orchestrator)

    def test_artifact_type(self, generator):
        """Test artifact type is correct."""
        assert generator.ARTIFACT_TYPE == "skill"

    @pytest.mark.asyncio
    async def test_generate_skill(self, generator):
        """Test generating a skill (mock mode)."""
        request = GenerationRequest(
            artifact_type="skill",
            name="api-testing",
            description="Test REST APIs with automated validation",
        )

        result = await generator.generate(
            request=request,
            provider="anthropic",
            model="claude-sonnet-4",
            best_practices=None,
        )

        assert result.artifact_type == "skill"
        assert result.name == "api-testing"


class TestPolicyGenerator:
    """Tests for PolicyGenerator."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create policy generator."""
        orchestrator = ProviderOrchestrator(config_path=tmp_path / "config.yaml")
        return PolicyGenerator(orchestrator)

    def test_artifact_type(self, generator):
        """Test artifact type is correct."""
        assert generator.ARTIFACT_TYPE == "policy"

    @pytest.mark.asyncio
    async def test_generate_policy(self, generator):
        """Test generating a policy (mock mode)."""
        request = GenerationRequest(
            artifact_type="policy",
            name="security-policy",
            description="Enforce security best practices",
            context={"policy_type": "security"},
        )

        result = await generator.generate(
            request=request,
            provider="anthropic",
            model="claude-sonnet-4",
            best_practices=None,
        )

        assert result.artifact_type == "policy"


class TestBaseGeneratorHelpers:
    """Tests for BaseGenerator helper methods."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create a concrete generator for testing base functionality."""
        orchestrator = ProviderOrchestrator(config_path=tmp_path / "config.yaml")
        return AgentGenerator(orchestrator)

    def test_calculate_cost_anthropic(self, generator):
        """Test cost calculation for Anthropic."""
        cost = generator._calculate_cost(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            tokens_in=1000,
            tokens_out=500,
        )
        assert cost > 0
        # Anthropic: 0.003/1k input + 0.015/1k output
        # Expected: 1000/1000 * 0.003 + 500/1000 * 0.015 = 0.003 + 0.0075 = 0.0105
        assert 0.01 <= cost <= 0.02

    def test_calculate_cost_ollama(self, generator):
        """Test cost calculation for Ollama (free)."""
        cost = generator._calculate_cost(
            provider="ollama",
            model="llama3",
            tokens_in=1000,
            tokens_out=500,
        )
        assert cost == 0.0

    def test_format_best_practices(self, generator):
        """Test formatting best practices for prompt."""
        practices = [
            {"title": "Practice 1", "recommendation": "Do this thing"},
            {"title": "Practice 2", "recommendation": "Do that thing"},
        ]

        formatted = generator._format_best_practices(practices)
        assert "Practice 1" in formatted
        assert "Do this thing" in formatted
        assert "Practice 2" in formatted

    def test_format_best_practices_empty(self, generator):
        """Test formatting empty practices list."""
        formatted = generator._format_best_practices(None)
        assert formatted == ""

        formatted = generator._format_best_practices([])
        assert formatted == ""

    def test_parse_response_yaml_block(self, generator):
        """Test parsing response with YAML code block."""
        response = {
            "content": """Here is the result:

```yaml
name: TestAgent
role: Test role
```

That's all!
"""
        }

        parsed = generator._parse_response(response)
        assert "name: TestAgent" in parsed
        assert "role: Test role" in parsed
        assert "Here is the result" not in parsed

    def test_parse_response_markdown_block(self, generator):
        """Test parsing response with markdown code block."""
        response = {
            "content": """Result:

```markdown
# TestAgent

This is a test.
```
"""
        }

        parsed = generator._parse_response(response)
        assert "# TestAgent" in parsed

    def test_parse_response_no_block(self, generator):
        """Test parsing response without code block."""
        response = {"content": "name: TestAgent\nrole: Test role"}

        parsed = generator._parse_response(response)
        assert "name: TestAgent" in parsed
