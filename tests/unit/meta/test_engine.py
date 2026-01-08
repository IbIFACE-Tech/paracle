"""Unit tests for paracle_meta.engine module."""

import pytest

from paracle_meta.engine import MetaAgent
from paracle_meta.generators.base import GenerationRequest, GenerationResult


class TestMetaAgent:
    """Tests for MetaAgent main class."""

    @pytest.fixture
    def meta(self, tmp_path):
        """Create MetaAgent with temp directories."""
        # Create temp config path
        config_path = tmp_path / "meta_agent.yaml"
        return MetaAgent(
            config_path=config_path,
            learning_enabled=True,
            cost_optimization=True,
        )

    @pytest.fixture
    def meta_disabled(self, tmp_path):
        """Create MetaAgent with features disabled."""
        config_path = tmp_path / "meta_agent.yaml"
        return MetaAgent(
            config_path=config_path,
            learning_enabled=False,
            cost_optimization=False,
        )

    def test_initialization(self, meta):
        """Test MetaAgent initialization."""
        assert meta.orchestrator is not None
        assert meta.learning_engine is not None
        assert meta.cost_optimizer is not None
        assert meta.quality_scorer is not None

    def test_initialization_with_providers(self, tmp_path):
        """Test initialization with specific providers."""
        meta = MetaAgent(
            config_path=tmp_path / "config.yaml",
            providers=["anthropic", "openai"],
        )
        assert "anthropic" in meta.orchestrator.available_providers
        assert "openai" in meta.orchestrator.available_providers

    @pytest.mark.asyncio
    async def test_generate_agent(self, meta):
        """Test generating an agent."""
        result = await meta.generate_agent(
            name="SecurityAuditor",
            description="Reviews Python code for security vulnerabilities",
        )

        assert isinstance(result, GenerationResult)
        assert result.artifact_type == "agent"
        assert result.name == "SecurityAuditor"
        assert result.content is not None
        assert result.quality_score >= 0

    @pytest.mark.asyncio
    async def test_generate_workflow(self, meta):
        """Test generating a workflow."""
        result = await meta.generate_workflow(
            name="deployment",
            goal="Deploy to production with tests and rollback on failure",
        )

        assert isinstance(result, GenerationResult)
        assert result.artifact_type == "workflow"
        assert result.name == "deployment"

    @pytest.mark.asyncio
    async def test_generate_skill(self, meta):
        """Test generating a skill."""
        result = await meta.generate_skill(
            name="api-testing",
            description="Test REST APIs with automated validation",
        )

        assert isinstance(result, GenerationResult)
        assert result.artifact_type == "skill"

    @pytest.mark.asyncio
    async def test_generate_policy(self, meta):
        """Test generating a policy."""
        result = await meta.generate_policy(
            name="security-policy",
            requirements="Enforce OWASP Top 10 compliance",
            policy_type="security",
        )

        assert isinstance(result, GenerationResult)
        assert result.artifact_type == "policy"

    @pytest.mark.asyncio
    async def test_generate_with_context(self, meta):
        """Test generating with additional context."""
        result = await meta.generate_agent(
            name="CustomAgent",
            description="An agent with custom requirements",
            context={
                "team": "platform",
                "language": "python",
                "existing_tools": ["read_file", "write_file"],
            },
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_record_feedback(self, meta):
        """Test recording feedback."""
        # First generate something
        result = await meta.generate_agent(
            name="FeedbackTestAgent",
            description="Agent for testing feedback",
        )

        # Record feedback - should not raise
        await meta.record_feedback(
            generation_id=result.id,
            rating=5,
            comment="Excellent quality!",
            usage_count=3,
        )

    @pytest.mark.asyncio
    async def test_get_statistics(self, meta):
        """Test getting statistics."""
        # Generate something first
        await meta.generate_agent(
            name="StatsTestAgent",
            description="Agent for testing stats",
        )

        stats = await meta.get_statistics()

        assert isinstance(stats, dict)
        assert "provider_performance" in stats
        assert "templates_learned" in stats
        assert "best_practices_count" in stats

    def test_estimate_complexity_short(self, meta):
        """Test complexity estimation for short description."""
        request = GenerationRequest(
            artifact_type="agent",
            name="Simple",
            description="A simple agent",
        )
        complexity = meta._estimate_complexity(request)
        assert 0 <= complexity <= 1
        assert complexity < 0.3  # Short description = low complexity

    def test_estimate_complexity_long(self, meta):
        """Test complexity estimation for long description."""
        long_desc = "A very detailed agent that " + "does many things " * 50
        request = GenerationRequest(
            artifact_type="agent",
            name="Complex",
            description=long_desc,
        )
        complexity = meta._estimate_complexity(request)
        assert 0 <= complexity <= 1
        assert complexity > 0.3  # Long description = higher complexity

    def test_estimate_complexity_with_context(self, meta):
        """Test complexity estimation with context."""
        request = GenerationRequest(
            artifact_type="agent",
            name="ContextAgent",
            description="Agent with context",
            context={"key": "value"},  # Has context
        )
        complexity = meta._estimate_complexity(request)
        assert complexity > 0  # Context adds complexity

    def test_get_generator_agent(self, meta):
        """Test getting agent generator."""
        generator = meta._get_generator("agent")
        assert generator is meta.agent_generator

    def test_get_generator_workflow(self, meta):
        """Test getting workflow generator."""
        generator = meta._get_generator("workflow")
        assert generator is meta.workflow_generator

    def test_get_generator_skill(self, meta):
        """Test getting skill generator."""
        generator = meta._get_generator("skill")
        assert generator is meta.skill_generator

    def test_get_generator_policy(self, meta):
        """Test getting policy generator."""
        generator = meta._get_generator("policy")
        assert generator is meta.policy_generator


class TestMetaAgentDisabled:
    """Tests for MetaAgent with features disabled."""

    @pytest.fixture
    def meta(self, tmp_path):
        """Create MetaAgent with features disabled."""
        return MetaAgent(
            config_path=tmp_path / "config.yaml",
            learning_enabled=False,
            cost_optimization=False,
        )

    @pytest.mark.asyncio
    async def test_generate_without_learning(self, meta):
        """Test generating without learning engine."""
        result = await meta.generate_agent(
            name="NoLearnAgent",
            description="Agent without learning",
        )
        # Should still work
        assert result is not None

    @pytest.mark.asyncio
    async def test_statistics_disabled(self, meta):
        """Test statistics with features disabled."""
        stats = await meta.get_statistics()
        # Learning stats should show disabled
        assert "enabled" in stats or "total_generations" in stats


class TestEngineGenerationRequest:
    """Tests for GenerationRequest in engine module."""

    def test_create_minimal(self):
        """Test creating minimal request."""
        request = GenerationRequest(
            artifact_type="agent",
            name="Test",
            description="Test description",
        )
        assert request.artifact_type == "agent"
        assert request.context == {}
        assert request.auto_apply is False


class TestEngineGenerationResult:
    """Tests for GenerationResult in engine module."""

    def test_create_with_all_fields(self):
        """Test creating result with all fields."""
        result = GenerationResult(
            id="test_123",
            artifact_type="agent",
            name="TestAgent",
            content="test content",
            provider="anthropic",
            model="claude-sonnet-4",
            quality_score=9.0,
            cost_usd=0.01,
            tokens_input=100,
            tokens_output=200,
            reasoning="Test reasoning",
        )
        assert result.id == "test_123"
        assert result.quality_score == 9.0
