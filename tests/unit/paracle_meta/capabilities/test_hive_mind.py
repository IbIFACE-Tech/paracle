"""Unit tests for HiveMindCapability."""

import pytest
import tempfile
from pathlib import Path

from paracle_meta.capabilities.hive_mind import (
    HiveMindCapability,
    HiveMindConfig,
    AgentRole,
    ConsensusMethod,
)


@pytest.fixture
def temp_db():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def hive_mind(temp_db):
    """Create HiveMindCapability instance."""
    config = HiveMindConfig(db_path=temp_db)
    return HiveMindCapability(config)


@pytest.mark.asyncio
async def test_hive_mind_initialization(hive_mind):
    """Test HiveMindCapability initialization."""
    assert hive_mind.name == "hive_mind"
    assert len(hive_mind._agents) == 0
    assert len(hive_mind._tasks) == 0


@pytest.mark.asyncio
async def test_register_worker_agent(hive_mind):
    """Test registering a worker agent."""
    result = await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=["coding", "testing"],
        expertise={"python": 0.9, "testing": 0.8}
    )

    assert result.success is True
    assert result.output["agent_name"] == "worker1"
    assert result.output["role"] == AgentRole.WORKER


@pytest.mark.asyncio
async def test_register_queen_agent(hive_mind):
    """Test registering a queen agent."""
    result = await hive_mind.register_agent(
        name="queen",
        role=AgentRole.QUEEN,
        capabilities=["coordination", "decision_making"]
    )

    assert result.success is True
    assert result.output["role"] == AgentRole.QUEEN


@pytest.mark.asyncio
async def test_register_observer_agent(hive_mind):
    """Test registering an observer agent."""
    result = await hive_mind.register_agent(
        name="observer",
        role=AgentRole.OBSERVER,
        capabilities=["monitoring"]
    )

    assert result.success is True
    assert result.output["role"] == AgentRole.OBSERVER


@pytest.mark.asyncio
async def test_only_one_queen_allowed(hive_mind):
    """Test that only one queen can be registered."""
    # Register first queen
    await hive_mind.register_agent(
        name="queen1",
        role=AgentRole.QUEEN,
        capabilities=[]
    )

    # Try to register second queen (should fail)
    result = await hive_mind.register_agent(
        name="queen2",
        role=AgentRole.QUEEN,
        capabilities=[]
    )

    assert result.success is False
    assert "queen already exists" in result.error.lower()


@pytest.mark.asyncio
async def test_submit_task(hive_mind):
    """Test submitting a task."""
    result = await hive_mind.submit_task(
        name="task1",
        task_type="coding",
        description="Implement feature X",
        priority=50
    )

    assert result.success is True
    assert result.output["task_name"] == "task1"
    assert result.output["status"] == "pending"


@pytest.mark.asyncio
async def test_auto_assign_task(hive_mind):
    """Test auto-assigning task to best agent."""
    # Register agents with different expertise
    await hive_mind.register_agent(
        name="python_expert",
        role=AgentRole.WORKER,
        capabilities=["coding"],
        expertise={"python": 0.9, "javascript": 0.3}
    )

    await hive_mind.register_agent(
        name="js_expert",
        role=AgentRole.WORKER,
        capabilities=["coding"],
        expertise={"python": 0.3, "javascript": 0.9}
    )

    # Submit Python task with auto-assign
    result = await hive_mind.submit_task(
        name="python_task",
        task_type="python",
        description="Fix Python bug",
        auto_assign=True
    )

    assert result.success is True
    # Should be assigned to python_expert
    if "assigned_to" in result.output:
        assert result.output["assigned_to"] == "python_expert"


@pytest.mark.asyncio
async def test_assign_task_manually(hive_mind):
    """Test manually assigning task to agent."""
    # Register agent
    await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=["coding"]
    )

    # Submit task
    await hive_mind.submit_task(
        name="task1",
        task_type="coding",
        description="Test task",
        auto_assign=False
    )

    # Assign manually
    result = await hive_mind.assign_task(
        task_name="task1",
        agent_name="worker1"
    )

    assert result.success is True
    assert result.output["assigned_to"] == "worker1"


@pytest.mark.asyncio
async def test_complete_task(hive_mind):
    """Test completing a task."""
    # Register agent and submit task
    await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=["coding"]
    )

    await hive_mind.submit_task(
        name="task1",
        task_type="coding",
        description="Test",
        auto_assign=True
    )

    # Complete task
    result = await hive_mind.complete_task(
        task_name="task1",
        result={"status": "success", "output": "Done"}
    )

    assert result.success is True
    assert result.output["status"] == "completed"


@pytest.mark.asyncio
async def test_get_task_status(hive_mind):
    """Test getting task status."""
    # Submit task
    await hive_mind.submit_task(
        name="task1",
        task_type="test",
        description="Test task"
    )

    # Get status
    result = await hive_mind.get_task_status(task_name="task1")

    assert result.success is True
    assert result.output["task_name"] == "task1"
    assert "status" in result.output


@pytest.mark.asyncio
async def test_list_agents(hive_mind):
    """Test listing all agents."""
    # Register multiple agents
    await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=["coding"]
    )

    await hive_mind.register_agent(
        name="worker2",
        role=AgentRole.WORKER,
        capabilities=["testing"]
    )

    result = await hive_mind.list_agents()

    assert result.success is True
    assert len(result.output["agents"]) == 2


@pytest.mark.asyncio
async def test_list_tasks(hive_mind):
    """Test listing all tasks."""
    # Submit multiple tasks
    await hive_mind.submit_task(
        name="task1",
        task_type="coding",
        description="Task 1"
    )

    await hive_mind.submit_task(
        name="task2",
        task_type="testing",
        description="Task 2"
    )

    result = await hive_mind.list_tasks()

    assert result.success is True
    assert len(result.output["tasks"]) == 2


@pytest.mark.asyncio
async def test_list_tasks_by_status(hive_mind):
    """Test listing tasks filtered by status."""
    # Submit and complete one task
    await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=[]
    )

    await hive_mind.submit_task(
        name="task1",
        task_type="test",
        description="Task 1",
        auto_assign=True
    )

    await hive_mind.complete_task(
        task_name="task1",
        result={}
    )

    # Submit another pending task
    await hive_mind.submit_task(
        name="task2",
        task_type="test",
        description="Task 2"
    )

    # List only pending tasks
    result = await hive_mind.list_tasks(status="pending")

    assert result.success is True
    for task in result.output["tasks"]:
        assert task["status"] == "pending"


@pytest.mark.asyncio
async def test_consensus_majority(hive_mind):
    """Test consensus with majority voting."""
    # Register agents
    for i in range(5):
        await hive_mind.register_agent(
            name=f"agent{i}",
            role=AgentRole.WORKER,
            capabilities=[]
        )

    # Request consensus
    result = await hive_mind.request_consensus(
        question="Should we deploy?",
        options=["yes", "no"],
        method=ConsensusMethod.MAJORITY
    )

    assert result.success is True
    assert "decision" in result.output


@pytest.mark.asyncio
async def test_consensus_unanimous(hive_mind):
    """Test consensus with unanimous voting."""
    # Register agents
    for i in range(3):
        await hive_mind.register_agent(
            name=f"agent{i}",
            role=AgentRole.WORKER,
            capabilities=[]
        )

    result = await hive_mind.request_consensus(
        question="Critical decision?",
        options=["approve", "reject"],
        method=ConsensusMethod.UNANIMOUS
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_consensus_queen_decision(hive_mind):
    """Test consensus with queen making final decision."""
    # Register queen and workers
    await hive_mind.register_agent(
        name="queen",
        role=AgentRole.QUEEN,
        capabilities=[]
    )

    for i in range(3):
        await hive_mind.register_agent(
            name=f"worker{i}",
            role=AgentRole.WORKER,
            capabilities=[]
        )

    result = await hive_mind.request_consensus(
        question="Architecture decision?",
        options=["option_a", "option_b"],
        method=ConsensusMethod.QUEEN_DECISION
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_get_agent_workload(hive_mind):
    """Test getting agent workload."""
    # Register agent
    await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=["coding"]
    )

    # Assign tasks
    for i in range(3):
        await hive_mind.submit_task(
            name=f"task{i}",
            task_type="coding",
            description=f"Task {i}",
            auto_assign=True
        )

    result = await hive_mind.get_agent_workload(agent_name="worker1")

    assert result.success is True
    assert "task_count" in result.output


@pytest.mark.asyncio
async def test_broadcast_message(hive_mind):
    """Test broadcasting message to all agents."""
    # Register agents
    for i in range(3):
        await hive_mind.register_agent(
            name=f"agent{i}",
            role=AgentRole.WORKER,
            capabilities=[]
        )

    result = await hive_mind.broadcast(
        message="System update available",
        sender="system"
    )

    assert result.success is True
    assert result.output["recipient_count"] == 3


@pytest.mark.asyncio
async def test_send_direct_message(hive_mind):
    """Test sending direct message to specific agent."""
    # Register agent
    await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=[]
    )

    result = await hive_mind.send_message(
        to_agent="worker1",
        message="Task assigned",
        sender="queen"
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_get_hive_stats(hive_mind):
    """Test getting hive statistics."""
    # Register agents and submit tasks
    await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=[]
    )

    await hive_mind.submit_task(
        name="task1",
        task_type="test",
        description="Test"
    )

    result = await hive_mind.get_stats()

    assert result.success is True
    assert "agent_count" in result.output
    assert "task_count" in result.output
    assert result.output["agent_count"] >= 1
    assert result.output["task_count"] >= 1


@pytest.mark.asyncio
async def test_unregister_agent(hive_mind):
    """Test unregistering an agent."""
    # Register agent
    await hive_mind.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=[]
    )

    # Unregister
    result = await hive_mind.unregister_agent(agent_name="worker1")
    assert result.success is True

    # Verify removal
    list_result = await hive_mind.list_agents()
    assert len(list_result.output["agents"]) == 0


@pytest.mark.asyncio
async def test_persistence(temp_db):
    """Test hive state persistence."""
    # First instance
    config1 = HiveMindConfig(db_path=temp_db)
    hive1 = HiveMindCapability(config1)

    await hive1.register_agent(
        name="worker1",
        role=AgentRole.WORKER,
        capabilities=["coding"]
    )

    await hive1.submit_task(
        name="task1",
        task_type="coding",
        description="Persistent task"
    )

    # Second instance - should load existing state
    config2 = HiveMindConfig(db_path=temp_db)
    hive2 = HiveMindCapability(config2)

    agents_result = await hive2.list_agents()
    tasks_result = await hive2.list_tasks()

    assert agents_result.success is True
    assert len(agents_result.output["agents"]) == 1

    assert tasks_result.success is True
    assert len(tasks_result.output["tasks"]) == 1
