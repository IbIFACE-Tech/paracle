"""Unit tests for ReflexionCapability."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from paracle_meta.capabilities.reflexion import (
    ReflexionCapability,
    ReflexionConfig,
    ExperienceType,
    ReflectionDepth,
)


@pytest.fixture
def temp_db():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def reflexion(temp_db):
    """Create ReflexionCapability instance."""
    config = ReflexionConfig(
        db_path=temp_db,
        auto_reflect=True,
        auto_critique=True,
    )
    return ReflexionCapability(config)


@pytest.mark.asyncio
async def test_reflexion_initialization(reflexion):
    """Test ReflexionCapability initialization."""
    assert reflexion.name == "reflexion"
    assert reflexion.config.auto_reflect is True
    assert reflexion.config.auto_critique is True


@pytest.mark.asyncio
async def test_record_success_experience(reflexion):
    """Test recording a successful experience."""
    result = await reflexion.record(
        agent_name="test-agent",
        task="Generate code",
        action_taken="Used template pattern",
        result={"code": "class Foo: pass"},
        success=True,
    )

    assert result.success is True
    assert "experience_id" in result.output
    assert result.output["experience_type"] == ExperienceType.SUCCESS


@pytest.mark.asyncio
async def test_record_failure_experience(reflexion):
    """Test recording a failed experience."""
    result = await reflexion.record(
        agent_name="test-agent",
        task="Parse JSON",
        action_taken="Used json.loads",
        result={"error": "Invalid JSON"},
        success=False,
    )

    assert result.success is True
    assert result.output["experience_type"] == ExperienceType.FAILURE


@pytest.mark.asyncio
async def test_auto_reflection(reflexion):
    """Test automatic reflection on experiences."""
    # Record experience (should auto-reflect)
    result = await reflexion.record(
        agent_name="test-agent",
        task="Implement feature",
        action_taken="TDD approach",
        result={"tests": 10, "coverage": 95},
        success=True,
    )

    exp_id = result.output["experience_id"]

    # Check if reflection was created
    query_result = await reflexion.query(experience_id=exp_id)
    assert query_result.success is True
    assert len(query_result.output["experiences"]) == 1

    experience = query_result.output["experiences"][0]
    assert "reflection" in experience
    assert experience["reflection"] is not None


@pytest.mark.asyncio
async def test_manual_reflection(reflexion):
    """Test manual reflection with different depths."""
    # Record without auto-reflect
    reflexion.config.auto_reflect = False

    result = await reflexion.record(
        agent_name="test-agent",
        task="Debug issue",
        action_taken="Added logging",
        result={"found": True},
        success=True,
    )

    exp_id = result.output["experience_id"]

    # Manual reflection - shallow
    shallow_result = await reflexion.reflect(experience_id=exp_id, depth="shallow")
    assert shallow_result.success is True

    # Manual reflection - deep
    deep_result = await reflexion.reflect(experience_id=exp_id, depth="deep")
    assert deep_result.success is True


@pytest.mark.asyncio
async def test_critique_experience(reflexion):
    """Test critiquing an experience."""
    # Record experience
    result = await reflexion.record(
        agent_name="test-agent",
        task="Write tests",
        action_taken="Wrote 50 tests",
        result={"coverage": 60},
        success=True,
    )

    exp_id = result.output["experience_id"]

    # Critique
    critique_result = await reflexion.critique(experience_id=exp_id)
    assert critique_result.success is True
    assert "strengths" in critique_result.output
    assert "weaknesses" in critique_result.output
    assert "improvements" in critique_result.output


@pytest.mark.asyncio
async def test_query_by_agent(reflexion):
    """Test querying experiences by agent name."""
    # Record multiple experiences
    await reflexion.record(
        agent_name="agent1",
        task="Task 1",
        action_taken="Action 1",
        result={},
        success=True,
    )

    await reflexion.record(
        agent_name="agent2",
        task="Task 2",
        action_taken="Action 2",
        result={},
        success=True,
    )

    # Query agent1 experiences
    result = await reflexion.query(agent_name="agent1")
    assert result.success is True
    assert len(result.output["experiences"]) == 1
    assert result.output["experiences"][0]["agent_name"] == "agent1"


@pytest.mark.asyncio
async def test_query_by_success(reflexion):
    """Test querying by success status."""
    # Record successes and failures
    await reflexion.record(
        agent_name="test-agent",
        task="Task 1",
        action_taken="Action 1",
        result={},
        success=True,
    )

    await reflexion.record(
        agent_name="test-agent",
        task="Task 2",
        action_taken="Action 2",
        result={},
        success=False,
    )

    # Query only failures
    result = await reflexion.query(success=False)
    assert result.success is True
    for exp in result.output["experiences"]:
        assert exp["success"] is False


@pytest.mark.asyncio
async def test_query_by_experience_type(reflexion):
    """Test querying by experience type."""
    # Record different types
    await reflexion.record(
        agent_name="test-agent",
        task="Task 1",
        action_taken="Action 1",
        result={},
        success=True,
        experience_type=ExperienceType.SUCCESS,
    )

    await reflexion.record(
        agent_name="test-agent",
        task="Task 2",
        action_taken="Action 2",
        result={},
        success=False,
        experience_type=ExperienceType.FAILURE,
    )

    # Query failures
    result = await reflexion.query(experience_type=ExperienceType.FAILURE)
    assert result.success is True
    for exp in result.output["experiences"]:
        assert exp["experience_type"] == ExperienceType.FAILURE


@pytest.mark.asyncio
async def test_get_patterns(reflexion):
    """Test pattern extraction from experiences."""
    # Record similar successful experiences
    for i in range(5):
        await reflexion.record(
            agent_name="test-agent",
            task=f"Implement feature {i}",
            action_taken="Used TDD",
            result={"coverage": 90 + i},
            success=True,
        )

    # Get patterns
    result = await reflexion.get_patterns(agent_name="test-agent")
    assert result.success is True
    assert "success_patterns" in result.output


@pytest.mark.asyncio
async def test_get_insights(reflexion):
    """Test getting insights from experiences."""
    # Record experiences
    for i in range(10):
        await reflexion.record(
            agent_name="test-agent",
            task=f"Task {i}",
            action_taken=f"Action {i}",
            result={},
            success=i % 2 == 0,  # Alternate success/failure
        )

    # Get insights
    result = await reflexion.get_insights(agent_name="test-agent")
    assert result.success is True
    assert "success_rate" in result.output
    assert "total_experiences" in result.output
    assert result.output["total_experiences"] == 10


@pytest.mark.asyncio
async def test_experience_with_metadata(reflexion):
    """Test recording experience with custom metadata."""
    result = await reflexion.record(
        agent_name="test-agent",
        task="Deploy service",
        action_taken="Blue-green deployment",
        result={"uptime": "99.9%"},
        success=True,
        metadata={
            "environment": "production",
            "duration_seconds": 120,
            "rollback_available": True,
        },
    )

    assert result.success is True

    # Query and check metadata
    query_result = await reflexion.query(experience_id=result.output["experience_id"])
    exp = query_result.output["experiences"][0]
    assert exp["metadata"]["environment"] == "production"
    assert exp["metadata"]["duration_seconds"] == 120


@pytest.mark.asyncio
async def test_persistence(temp_db):
    """Test experience persistence across instances."""
    # First instance - record experience
    config1 = ReflexionConfig(db_path=temp_db, auto_reflect=False)
    cap1 = ReflexionCapability(config1)

    result = await cap1.record(
        agent_name="test-agent",
        task="Test task",
        action_taken="Test action",
        result={},
        success=True,
    )
    exp_id = result.output["experience_id"]

    # Second instance - should load existing experiences
    config2 = ReflexionConfig(db_path=temp_db, auto_reflect=False)
    cap2 = ReflexionCapability(config2)

    query_result = await cap2.query(experience_id=exp_id)
    assert query_result.success is True
    assert len(query_result.output["experiences"]) == 1


@pytest.mark.asyncio
async def test_limit_and_offset(reflexion):
    """Test pagination with limit and offset."""
    # Record 10 experiences
    for i in range(10):
        await reflexion.record(
            agent_name="test-agent",
            task=f"Task {i}",
            action_taken=f"Action {i}",
            result={},
            success=True,
        )

    # Query with limit
    result = await reflexion.query(limit=5)
    assert result.success is True
    assert len(result.output["experiences"]) == 5

    # Query with offset
    result = await reflexion.query(offset=5, limit=5)
    assert result.success is True
    assert len(result.output["experiences"]) == 5
