"""HiveMind capability for MetaAgent.

Multi-agent coordination with Queen-led architecture:
- Queen agent coordinates worker agents
- Task distribution and load balancing
- Result aggregation
- Consensus mechanisms
- Shared knowledge base
- Agent communication protocols

Inspired by claude-flow's multi-agent orchestration.
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class AgentRole(str, Enum):
    """Agent role in the hive."""

    QUEEN = "queen"  # Coordinator
    WORKER = "worker"  # Task executor
    OBSERVER = "observer"  # Monitor only


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConsensusMethod(str, Enum):
    """Consensus algorithm."""

    MAJORITY = "majority"  # Simple majority vote
    UNANIMOUS = "unanimous"  # All agents must agree
    WEIGHTED = "weighted"  # Weighted by agent expertise
    QUEEN_DECISION = "queen_decision"  # Queen has final say


@dataclass
class HiveAgent:
    """An agent in the hive."""

    id: str
    name: str
    role: AgentRole
    capabilities: list[str]
    status: str = "idle"  # idle, busy, offline
    expertise: dict[str, float] = field(default_factory=dict)  # Task type -> score
    current_task: str | None = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_duration_ms: float = 0.0
    last_active: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "status": self.status,
            "expertise": self.expertise,
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_duration_ms": (
                self.total_duration_ms / self.completed_tasks
                if self.completed_tasks > 0
                else 0
            ),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class HiveTask:
    """A task in the hive."""

    id: str
    name: str
    task_type: str
    description: str
    priority: int = 50  # 0=highest, 100=lowest
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "description": self.description,
            "priority": self.priority,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class ConsensusRequest:
    """A request for agent consensus."""

    id: str
    question: str
    options: list[str]
    method: ConsensusMethod
    votes: dict[str, str] = field(default_factory=dict)  # agent_id -> option
    weights: dict[str, float] = field(default_factory=dict)  # agent_id -> weight
    decision: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "question": self.question,
            "options": self.options,
            "method": self.method.value,
            "votes": self.votes,
            "weights": self.weights,
            "decision": self.decision,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class HiveMindConfig(CapabilityConfig):
    """Configuration for HiveMind capability."""

    max_agents: int = Field(
        default=100,
        description="Maximum agents in hive",
    )
    max_tasks: int = Field(
        default=1000,
        description="Maximum pending tasks",
    )
    task_timeout: float = Field(
        default=300.0,
        description="Default task timeout in seconds",
    )
    enable_load_balancing: bool = Field(
        default=True,
        description="Enable automatic load balancing",
    )
    enable_shared_knowledge: bool = Field(
        default=True,
        description="Enable shared knowledge base",
    )
    queen_required: bool = Field(
        default=True,
        description="Require a Queen agent for coordination",
    )


class HiveMindCapability(BaseCapability):
    """Multi-agent coordination with Queen-led architecture.

    Coordinates multiple agents working together:
    - Queen agent orchestrates workers
    - Automatic task distribution
    - Load balancing across agents
    - Consensus mechanisms for decisions
    - Shared knowledge base
    - Performance tracking

    Example:
        >>> hive = HiveMindCapability()
        >>> await hive.initialize()

        >>> # Register Queen
        >>> await hive.register_agent(
        ...     name="queen",
        ...     role="queen",
        ...     capabilities=["coordination", "decision_making"]
        ... )

        >>> # Register workers
        >>> await hive.register_agent(
        ...     name="worker1",
        ...     role="worker",
        ...     capabilities=["coding", "testing"],
        ...     expertise={"coding": 0.9, "testing": 0.7}
        ... )

        >>> # Submit task
        >>> result = await hive.submit_task(
        ...     name="implement_feature",
        ...     task_type="coding",
        ...     description="Add user authentication",
        ...     priority=10
        ... )

        >>> # Get consensus
        >>> consensus = await hive.request_consensus(
        ...     question="Which framework to use?",
        ...     options=["FastAPI", "Flask", "Django"],
        ...     method="weighted"
        ... )
    """

    name = "hive_mind"
    description = "Multi-agent coordination with Queen-led architecture"

    def __init__(self, config: HiveMindConfig | None = None):
        """Initialize HiveMind capability."""
        super().__init__(config or HiveMindConfig())
        self.config: HiveMindConfig = self.config
        self._agents: dict[str, HiveAgent] = {}
        self._tasks: dict[str, HiveTask] = {}
        self._consensus_requests: dict[str, ConsensusRequest] = {}
        self._shared_knowledge: dict[str, Any] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: dict[str, asyncio.Task] = {}
        self._queen_id: str | None = None

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute HiveMind operation.

        Args:
            action: Operation (register, submit_task, assign, complete, consensus, etc.)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "list_agents")
        start_time = time.time()

        try:
            if action == "register":
                result = await self._register_agent(**kwargs)
            elif action == "unregister":
                result = self._unregister_agent(**kwargs)
            elif action == "submit_task":
                result = await self._submit_task(**kwargs)
            elif action == "assign_task":
                result = await self._assign_task(**kwargs)
            elif action == "complete_task":
                result = await self._complete_task(**kwargs)
            elif action == "cancel_task":
                result = self._cancel_task(**kwargs)
            elif action == "request_consensus":
                result = await self._request_consensus(**kwargs)
            elif action == "vote":
                result = await self._vote(**kwargs)
            elif action == "resolve_consensus":
                result = self._resolve_consensus(**kwargs)
            elif action == "share_knowledge":
                result = self._share_knowledge(**kwargs)
            elif action == "get_knowledge":
                result = self._get_knowledge(**kwargs)
            elif action == "list_agents":
                result = self._list_agents(**kwargs)
            elif action == "list_tasks":
                result = self._list_tasks(**kwargs)
            elif action == "stats":
                result = self._get_stats(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        unique = f"{prefix}-{time.time()}"
        return hashlib.md5(unique.encode()).hexdigest()[:16]

    async def _register_agent(
        self,
        name: str,
        role: str,
        capabilities: list[str],
        expertise: dict[str, float] | None = None,
        metadata: dict | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Register an agent in the hive.

        Args:
            name: Agent name
            role: Agent role (queen, worker, observer)
            capabilities: List of capabilities
            expertise: Expertise scores by task type
            metadata: Additional metadata

        Returns:
            Agent registration info
        """
        if len(self._agents) >= self.config.max_agents:
            raise ValueError(f"Maximum agents limit reached: {self.config.max_agents}")

        role_enum = AgentRole(role)

        # Check Queen constraint
        if role_enum == AgentRole.QUEEN:
            if self._queen_id and self._queen_id in self._agents:
                raise ValueError("A Queen agent is already registered")

        agent_id = self._generate_id("agent")

        agent = HiveAgent(
            id=agent_id,
            name=name,
            role=role_enum,
            capabilities=capabilities,
            expertise=expertise or {},
            metadata=metadata or {},
        )

        self._agents[agent_id] = agent

        if role_enum == AgentRole.QUEEN:
            self._queen_id = agent_id

        return {
            "agent_id": agent_id,
            "name": name,
            "role": role,
            "capabilities": capabilities,
        }

    def _unregister_agent(self, agent_id: str, **kwargs) -> dict[str, Any]:
        """Unregister an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Unregistration result
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        agent = self._agents.pop(agent_id)

        # If Queen is being removed, clear Queen ID
        if agent.role == AgentRole.QUEEN:
            self._queen_id = None

        # Cancel any assigned tasks
        for task in self._tasks.values():
            if task.assigned_to == agent_id and task.status in (TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS):
                task.status = TaskStatus.PENDING
                task.assigned_to = None

        return {
            "agent_id": agent_id,
            "name": agent.name,
            "removed": True,
        }

    async def _submit_task(
        self,
        name: str,
        task_type: str,
        description: str,
        priority: int = 50,
        metadata: dict | None = None,
        auto_assign: bool = True,
        **extra,
    ) -> dict[str, Any]:
        """Submit a task to the hive.

        Args:
            name: Task name
            task_type: Type of task
            description: Task description
            priority: Priority (0=highest, 100=lowest)
            metadata: Additional metadata
            auto_assign: Automatically assign to best agent

        Returns:
            Task info
        """
        if len(self._tasks) >= self.config.max_tasks:
            raise ValueError(f"Maximum tasks limit reached: {self.config.max_tasks}")

        task_id = self._generate_id("task")

        task = HiveTask(
            id=task_id,
            name=name,
            task_type=task_type,
            description=description,
            priority=priority,
            metadata=metadata or {},
        )

        self._tasks[task_id] = task

        # Auto-assign if enabled
        if auto_assign:
            await self._auto_assign_task(task_id)

        return {
            "task_id": task_id,
            "name": name,
            "task_type": task_type,
            "priority": priority,
            "status": task.status.value,
            "assigned_to": task.assigned_to,
        }

    async def _auto_assign_task(self, task_id: str) -> None:
        """Automatically assign task to best available agent.

        Args:
            task_id: Task ID
        """
        task = self._tasks[task_id]

        # Find best agent for this task
        best_agent = None
        best_score = -1.0

        for agent in self._agents.values():
            # Skip non-workers
            if agent.role != AgentRole.WORKER:
                continue

            # Skip busy agents
            if agent.status == "busy":
                continue

            # Check if agent has required capability
            if task.task_type not in agent.capabilities:
                continue

            # Calculate score
            expertise_score = agent.expertise.get(task.task_type, 0.5)

            # Penalize by current load (completed tasks)
            load_penalty = agent.completed_tasks / (agent.completed_tasks + agent.failed_tasks + 1)
            score = expertise_score * (1 - 0.3 * load_penalty)

            if score > best_score:
                best_score = score
                best_agent = agent

        if best_agent:
            await self._assign_task(task_id=task_id, agent_id=best_agent.id)

    async def _assign_task(
        self,
        task_id: str,
        agent_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Assign a task to a specific agent.

        Args:
            task_id: Task ID
            agent_id: Agent ID

        Returns:
            Assignment result
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        task = self._tasks[task_id]
        agent = self._agents[agent_id]

        # Check if already assigned
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Task already {task.status.value}")

        # Assign
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = agent_id
        task.assigned_at = datetime.utcnow()

        agent.status = "busy"
        agent.current_task = task_id

        return {
            "task_id": task_id,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "assigned": True,
        }

    async def _complete_task(
        self,
        task_id: str,
        result: Any,
        success: bool = True,
        error: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Mark a task as completed.

        Args:
            task_id: Task ID
            result: Task result
            success: Whether task succeeded
            error: Error message if failed

        Returns:
            Completion result
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self._tasks[task_id]

        if not task.assigned_to or task.assigned_to not in self._agents:
            raise ValueError("Task not assigned to any agent")

        agent = self._agents[task.assigned_to]

        # Update task
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.utcnow()
        task.result = result
        task.error = error

        # Update agent
        agent.status = "idle"
        agent.current_task = None
        agent.last_active = datetime.utcnow()

        if success:
            agent.completed_tasks += 1
        else:
            agent.failed_tasks += 1

        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds() * 1000
            agent.total_duration_ms += duration

        return {
            "task_id": task_id,
            "status": task.status.value,
            "success": success,
            "agent_id": agent.id,
        }

    def _cancel_task(self, task_id: str, **kwargs) -> dict[str, Any]:
        """Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            Cancellation result
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self._tasks[task_id]

        # Free agent if assigned
        if task.assigned_to and task.assigned_to in self._agents:
            agent = self._agents[task.assigned_to]
            agent.status = "idle"
            agent.current_task = None

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()

        return {
            "task_id": task_id,
            "cancelled": True,
        }

    async def _request_consensus(
        self,
        question: str,
        options: list[str],
        method: str = "majority",
        **kwargs,
    ) -> dict[str, Any]:
        """Request consensus from agents.

        Args:
            question: Question to decide
            options: Available options
            method: Consensus method

        Returns:
            Consensus request info
        """
        if len(options) < 2:
            raise ValueError("At least 2 options required")

        method_enum = ConsensusMethod(method)

        request_id = self._generate_id("consensus")

        request = ConsensusRequest(
            id=request_id,
            question=question,
            options=options,
            method=method_enum,
        )

        self._consensus_requests[request_id] = request

        return {
            "consensus_id": request_id,
            "question": question,
            "options": options,
            "method": method,
        }

    async def _vote(
        self,
        consensus_id: str,
        agent_id: str,
        vote: str,
        weight: float | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Cast a vote for consensus.

        Args:
            consensus_id: Consensus request ID
            agent_id: Agent ID
            vote: Chosen option
            weight: Vote weight (for weighted consensus)

        Returns:
            Vote result
        """
        if consensus_id not in self._consensus_requests:
            raise ValueError(f"Consensus request not found: {consensus_id}")

        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        request = self._consensus_requests[consensus_id]

        if vote not in request.options:
            raise ValueError(f"Invalid option: {vote}. Must be one of {request.options}")

        # Record vote
        request.votes[agent_id] = vote

        # Record weight if provided
        if weight is not None:
            request.weights[agent_id] = weight

        return {
            "consensus_id": consensus_id,
            "agent_id": agent_id,
            "vote": vote,
            "total_votes": len(request.votes),
        }

    def _resolve_consensus(self, consensus_id: str, **kwargs) -> dict[str, Any]:
        """Resolve a consensus request.

        Args:
            consensus_id: Consensus request ID

        Returns:
            Consensus decision
        """
        if consensus_id not in self._consensus_requests:
            raise ValueError(f"Consensus request not found: {consensus_id}")

        request = self._consensus_requests[consensus_id]

        if request.decision:
            return {
                "consensus_id": consensus_id,
                "decision": request.decision,
                "already_resolved": True,
            }

        decision = None

        if request.method == ConsensusMethod.MAJORITY:
            # Simple majority
            vote_counts = {}
            for vote in request.votes.values():
                vote_counts[vote] = vote_counts.get(vote, 0) + 1

            if vote_counts:
                decision = max(vote_counts, key=vote_counts.get)

        elif request.method == ConsensusMethod.UNANIMOUS:
            # All votes must match
            if request.votes:
                votes_set = set(request.votes.values())
                if len(votes_set) == 1:
                    decision = votes_set.pop()

        elif request.method == ConsensusMethod.WEIGHTED:
            # Weighted vote
            weighted_scores = {}
            for agent_id, vote in request.votes.items():
                weight = request.weights.get(agent_id, 1.0)
                weighted_scores[vote] = weighted_scores.get(vote, 0.0) + weight

            if weighted_scores:
                decision = max(weighted_scores, key=weighted_scores.get)

        elif request.method == ConsensusMethod.QUEEN_DECISION:
            # Queen decides
            if self._queen_id and self._queen_id in request.votes:
                decision = request.votes[self._queen_id]

        request.decision = decision
        request.resolved_at = datetime.utcnow()

        return {
            "consensus_id": consensus_id,
            "decision": decision,
            "method": request.method.value,
            "total_votes": len(request.votes),
        }

    def _share_knowledge(
        self,
        key: str,
        value: Any,
        **kwargs,
    ) -> dict[str, Any]:
        """Share knowledge with the hive.

        Args:
            key: Knowledge key
            value: Knowledge value

        Returns:
            Share result
        """
        if not self.config.enable_shared_knowledge:
            raise ValueError("Shared knowledge is disabled")

        self._shared_knowledge[key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return {
            "key": key,
            "shared": True,
        }

    def _get_knowledge(self, key: str, **kwargs) -> dict[str, Any]:
        """Get knowledge from the hive.

        Args:
            key: Knowledge key

        Returns:
            Knowledge value
        """
        if not self.config.enable_shared_knowledge:
            raise ValueError("Shared knowledge is disabled")

        if key not in self._shared_knowledge:
            raise ValueError(f"Knowledge not found: {key}")

        return self._shared_knowledge[key]

    def _list_agents(
        self,
        role: str | None = None,
        status: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """List agents in the hive.

        Args:
            role: Filter by role
            status: Filter by status

        Returns:
            Agents list
        """
        agents = list(self._agents.values())

        # Apply filters
        if role:
            role_enum = AgentRole(role)
            agents = [a for a in agents if a.role == role_enum]

        if status:
            agents = [a for a in agents if a.status == status]

        return {
            "agents": [a.to_dict() for a in agents],
            "count": len(agents),
        }

    def _list_tasks(
        self,
        status: str | None = None,
        agent_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """List tasks in the hive.

        Args:
            status: Filter by status
            agent_id: Filter by assigned agent

        Returns:
            Tasks list
        """
        tasks = list(self._tasks.values())

        # Apply filters
        if status:
            status_enum = TaskStatus(status)
            tasks = [t for t in tasks if t.status == status_enum]

        if agent_id:
            tasks = [t for t in tasks if t.assigned_to == agent_id]

        # Sort by priority
        tasks.sort(key=lambda t: t.priority)

        return {
            "tasks": [t.to_dict() for t in tasks],
            "count": len(tasks),
        }

    def _get_stats(self, **kwargs) -> dict[str, Any]:
        """Get hive statistics.

        Returns:
            Statistics
        """
        total_agents = len(self._agents)
        by_role = {}
        for agent in self._agents.values():
            role = agent.role.value
            by_role[role] = by_role.get(role, 0) + 1

        total_tasks = len(self._tasks)
        by_status = {}
        for task in self._tasks.values():
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1

        completed = sum(a.completed_tasks for a in self._agents.values())
        failed = sum(a.failed_tasks for a in self._agents.values())

        return {
            "total_agents": total_agents,
            "agents_by_role": by_role,
            "queen_id": self._queen_id,
            "total_tasks": total_tasks,
            "tasks_by_status": by_status,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "success_rate": (
                completed / (completed + failed) if (completed + failed) > 0 else 0.0
            ),
            "shared_knowledge_items": len(self._shared_knowledge),
        }

    # Convenience methods
    async def register_agent(
        self,
        name: str,
        role: str,
        capabilities: list[str],
        **kwargs,
    ) -> CapabilityResult:
        """Register an agent."""
        return await self.execute(
            action="register",
            name=name,
            role=role,
            capabilities=capabilities,
            **kwargs,
        )

    async def submit_task(
        self,
        name: str,
        task_type: str,
        description: str,
        **kwargs,
    ) -> CapabilityResult:
        """Submit a task."""
        return await self.execute(
            action="submit_task",
            name=name,
            task_type=task_type,
            description=description,
            **kwargs,
        )

    async def request_consensus(
        self,
        question: str,
        options: list[str],
        method: str = "majority",
    ) -> CapabilityResult:
        """Request consensus."""
        return await self.execute(
            action="request_consensus",
            question=question,
            options=options,
            method=method,
        )

    async def list_agents(self, **kwargs) -> CapabilityResult:
        """List agents."""
        return await self.execute(action="list_agents", **kwargs)

    async def get_stats(self) -> CapabilityResult:
        """Get statistics."""
        return await self.execute(action="stats")
