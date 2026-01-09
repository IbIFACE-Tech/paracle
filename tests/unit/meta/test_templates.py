"""Unit tests for paracle_meta.templates module."""

import pytest
from paracle_meta.exceptions import TemplateNotFoundError
from paracle_meta.templates import Template, TemplateEvolution, TemplateLibrary


class TestTemplate:
    """Tests for Template model."""

    def test_create_template(self):
        """Test creating a template."""
        template = Template(
            id="tmpl_agent_security",
            artifact_type="agent",
            pattern="security audit",
            name="SecurityAuditor",
            content="name: SecurityAuditor\nrole: Security auditor",
            quality_score=9.0,
        )
        assert template.id == "tmpl_agent_security"
        assert template.quality_score == 9.0

    def test_customize_template(self):
        """Test customizing template with placeholders."""
        template = Template(
            id="tmpl_test",
            artifact_type="agent",
            pattern="test",
            name="TestTemplate",
            content="name: {{name}}\ndescription: {{description}}",
        )

        customized = template.customize(
            name="MyAgent", description="My custom agent", context={}
        )
        assert "name: MyAgent" in customized
        assert "description: My custom agent" in customized

    def test_customize_template_with_context(self):
        """Test customizing with context variables."""
        template = Template(
            id="tmpl_test",
            artifact_type="workflow",
            pattern="test",
            name="TestTemplate",
            content="name: {{name}}\nenvironment: {{environment}}",
        )

        customized = template.customize(
            name="DeployWorkflow",
            description="Deploy to production",
            context={"environment": "production"},
        )
        assert "environment: production" in customized


class TestTemplateLibrary:
    """Tests for TemplateLibrary."""

    @pytest.fixture
    def library(self, tmp_path):
        """Create library with temp database."""
        return TemplateLibrary(db_path=tmp_path / "templates.db")

    @pytest.fixture
    def sample_template(self):
        """Create sample template."""
        return Template(
            id="tmpl_security_auditor_v1",
            artifact_type="agent",
            pattern="security audit review",
            name="SecurityAuditor",
            content="name: SecurityAuditor\nrole: Security code auditor",
            quality_score=9.0,
            usage_count=10,
            avg_rating=4.5,
        )

    @pytest.mark.asyncio
    async def test_save_and_get_template(self, library, sample_template):
        """Test saving and retrieving a template."""
        template_id = await library.save(sample_template)
        assert template_id == sample_template.id

        retrieved = await library.get(template_id)
        assert retrieved.name == sample_template.name
        assert retrieved.quality_score == sample_template.quality_score

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self, library):
        """Test getting nonexistent template raises error."""
        with pytest.raises(TemplateNotFoundError):
            await library.get("nonexistent_id")

    @pytest.mark.asyncio
    async def test_find_similar(self, library, sample_template):
        """Test finding similar templates."""
        await library.save(sample_template)

        # Search for similar
        found = await library.find_similar(
            artifact_type="agent", description="security audit code review"
        )
        assert found is not None
        assert found.pattern == "security audit review"

    @pytest.mark.asyncio
    async def test_find_similar_no_match(self, library):
        """Test find_similar returns None when no match."""
        found = await library.find_similar(
            artifact_type="workflow", description="completely unrelated thing"
        )
        # Should return None since no templates exist
        assert found is None

    @pytest.mark.asyncio
    async def test_list_templates(self, library, sample_template):
        """Test listing templates."""
        await library.save(sample_template)

        templates = await library.list_templates(artifact_type="agent")
        assert len(templates) >= 1
        assert any(t.id == sample_template.id for t in templates)

    @pytest.mark.asyncio
    async def test_list_templates_with_quality_filter(self, library):
        """Test listing templates with quality filter."""
        low_quality = Template(
            id="tmpl_low",
            artifact_type="agent",
            pattern="test",
            name="LowQuality",
            content="test",
            quality_score=5.0,
        )
        high_quality = Template(
            id="tmpl_high",
            artifact_type="agent",
            pattern="test",
            name="HighQuality",
            content="test",
            quality_score=9.0,
        )

        await library.save(low_quality)
        await library.save(high_quality)

        # Filter by quality
        templates = await library.list_templates(artifact_type="agent", min_quality=8.0)
        assert all(t.quality_score >= 8.0 for t in templates)

    @pytest.mark.asyncio
    async def test_update_usage(self, library, sample_template):
        """Test updating usage count."""
        await library.save(sample_template)
        await library.update_usage(sample_template.id)

        retrieved = await library.get(sample_template.id)
        assert retrieved.usage_count == sample_template.usage_count + 1

    @pytest.mark.asyncio
    async def test_update_rating(self, library, sample_template):
        """Test updating average rating."""
        await library.save(sample_template)
        await library.update_rating(sample_template.id, 5.0)

        retrieved = await library.get(sample_template.id)
        # New average should incorporate the new rating
        assert retrieved.avg_rating != sample_template.avg_rating

    @pytest.mark.asyncio
    async def test_count(self, library, sample_template):
        """Test counting templates."""
        initial_count = await library.count()

        await library.save(sample_template)

        final_count = await library.count()
        assert final_count == initial_count + 1


class TestTemplateEvolution:
    """Tests for TemplateEvolution."""

    @pytest.fixture
    def library(self, tmp_path):
        """Create library with temp database."""
        return TemplateLibrary(db_path=tmp_path / "templates.db")

    @pytest.fixture
    def evolution(self, library):
        """Create evolution manager."""
        return TemplateEvolution(
            library=library,
            min_samples=3,
            min_rating=4.0,
            min_quality=8.0,
        )

    @pytest.mark.asyncio
    async def test_check_for_promotion_insufficient_samples(self, evolution):
        """Test promotion fails with insufficient samples."""
        result = await evolution.check_for_promotion(
            generation_id="gen_123",
            artifact_type="agent",
            name="TestAgent",
            content="test content",
            quality_score=9.0,
            feedback_count=2,  # Below min_samples=3
            avg_rating=5.0,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_check_for_promotion_low_rating(self, evolution):
        """Test promotion fails with low rating."""
        result = await evolution.check_for_promotion(
            generation_id="gen_123",
            artifact_type="agent",
            name="TestAgent",
            content="test content",
            quality_score=9.0,
            feedback_count=5,
            avg_rating=3.5,  # Below min_rating=4.0
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_check_for_promotion_success(self, evolution):
        """Test successful promotion to template."""
        result = await evolution.check_for_promotion(
            generation_id="gen_123",
            artifact_type="agent",
            name="SecurityAuditor",
            content="name: SecurityAuditor\nrole: Security auditor",
            quality_score=9.0,
            feedback_count=5,
            avg_rating=4.5,
        )
        assert result is not None
        assert result.artifact_type == "agent"
        assert result.source == "promotion"

    @pytest.mark.asyncio
    async def test_evolve_template(self, evolution, library):
        """Test evolving a template."""
        # First create a template
        original = Template(
            id="tmpl_test_v1",
            artifact_type="agent",
            pattern="test",
            name="TestAgent",
            content="original content",
            quality_score=8.0,
            version=1,
        )
        await library.save(original)

        # Evolve it
        evolved = await evolution.evolve_template(
            template_id="tmpl_test_v1",
            improved_content="improved content",
            new_quality=9.5,
        )

        assert evolved.version == 2
        assert evolved.quality_score == 9.5
        assert evolved.source == "evolution"
        assert "evolved_from" in evolved.metadata
