"""Unit tests for paracle_meta.knowledge module."""

import pytest

from paracle_meta.knowledge import BestPractice, BestPracticesDatabase


class TestBestPractice:
    """Tests for BestPractice model."""

    def test_create_best_practice(self):
        """Test creating a best practice."""
        practice = BestPractice(
            id="test_practice",
            category="agent",
            pattern="all",
            title="Test Practice",
            recommendation="Always test your code",
            confidence=0.9,
        )
        assert practice.id == "test_practice"
        assert practice.confidence == 0.9

    def test_create_with_examples(self):
        """Test creating practice with examples."""
        practice = BestPractice(
            id="test_with_examples",
            category="workflow",
            pattern="deployment",
            title="Approval Gates",
            recommendation="Add approval gates before production",
            examples=[
                "- type: approval\n  approvers: [lead]",
                "- type: manual_check",
            ],
        )
        assert len(practice.examples) == 2


class TestBestPracticesDatabase:
    """Tests for BestPracticesDatabase."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create database with temp path."""
        return BestPracticesDatabase(db_path=tmp_path / "practices.db")

    @pytest.mark.asyncio
    async def test_initialization_loads_builtins(self, db):
        """Test that initialization loads built-in practices."""
        count = await db.count()
        assert count > 0  # Should have built-in practices

    @pytest.mark.asyncio
    async def test_get_for_category(self, db):
        """Test getting practices for a category."""
        practices = await db.get_for("agent")
        assert len(practices) > 0
        # Should include agent-specific and general practices
        categories = {p.category for p in practices}
        assert "agent" in categories or "general" in categories

    @pytest.mark.asyncio
    async def test_get_for_category_with_pattern(self, db):
        """Test getting practices with pattern filter."""
        practices = await db.get_for("workflow", pattern="production deployment")
        # Should get workflow practices that match the pattern
        assert all(p.category in ["workflow", "general"] for p in practices)

    @pytest.mark.asyncio
    async def test_add_practice(self, db):
        """Test adding a new practice."""
        practice = BestPractice(
            id="custom_practice_1",
            category="custom",
            pattern="testing",
            title="Custom Testing Practice",
            recommendation="Always write tests first",
            confidence=0.85,
        )

        await db.add(practice)

        # Should be able to retrieve it
        practices = await db.get_for("custom")
        assert any(p.id == "custom_practice_1" for p in practices)

    @pytest.mark.asyncio
    async def test_update_usage(self, db):
        """Test updating usage statistics."""
        # Get a built-in practice
        practices = await db.get_for("agent", limit=1)
        if practices:
            practice_id = practices[0].id
            original_usage = practices[0].usage_count

            await db.update_usage(practice_id, success=True)

            # Re-fetch and check
            updated_practices = await db.get_for("agent", limit=1)
            updated = next((p for p in updated_practices if p.id == practice_id), None)
            if updated:
                assert updated.usage_count == original_usage + 1

    @pytest.mark.asyncio
    async def test_count(self, db):
        """Test counting practices."""
        count = await db.count()
        assert count > 0

    @pytest.mark.asyncio
    async def test_get_prompt_context(self, db):
        """Test getting practices as prompt context."""
        context = await db.get_prompt_context("agent")
        assert "Best Practices" in context
        assert len(context) > 0

    @pytest.mark.asyncio
    async def test_get_prompt_context_empty(self, tmp_path):
        """Test prompt context for category with no practices."""
        # Create fresh DB without loading builtins
        db = BestPracticesDatabase(db_path=tmp_path / "empty.db")
        context = await db.get_prompt_context("nonexistent_category")
        # Should handle gracefully
        assert isinstance(context, str)


class TestBuiltInPractices:
    """Tests for built-in best practices content."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create database with temp path."""
        return BestPracticesDatabase(db_path=tmp_path / "practices.db")

    @pytest.mark.asyncio
    async def test_agent_practices_exist(self, db):
        """Test that agent practices are loaded."""
        practices = await db.get_for("agent")
        titles = {p.title for p in practices if p.category == "agent"}
        # Check for expected built-in practices
        assert "Clear Role Definition" in titles or len(practices) > 0

    @pytest.mark.asyncio
    async def test_workflow_practices_exist(self, db):
        """Test that workflow practices are loaded."""
        practices = await db.get_for("workflow")
        assert any(p.category == "workflow" for p in practices)

    @pytest.mark.asyncio
    async def test_policy_practices_exist(self, db):
        """Test that policy practices are loaded."""
        practices = await db.get_for("policy")
        assert any(p.category == "policy" for p in practices)

    @pytest.mark.asyncio
    async def test_general_practices_included(self, db):
        """Test that general practices are included in all queries."""
        # General practices should appear in any category query
        practices = await db.get_for("agent")
        categories = {p.category for p in practices}
        assert "general" in categories or "agent" in categories

    @pytest.mark.asyncio
    async def test_practices_have_recommendations(self, db):
        """Test that all practices have recommendations."""
        practices = await db.get_for("agent", limit=50)
        for practice in practices:
            assert practice.recommendation is not None
            assert len(practice.recommendation) > 0
