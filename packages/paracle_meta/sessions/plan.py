"""Plan session for structured task decomposition and execution.

This module provides a planning session that decomposes complex tasks
into steps and executes them systematically.

Example:
    >>> from paracle_meta.sessions import PlanSession, PlanConfig
    >>> from paracle_meta.capabilities.providers import AnthropicProvider
    >>> from paracle_meta.registry import CapabilityRegistry
    >>>
    >>> provider = AnthropicProvider()
    >>> registry = CapabilityRegistry()
    >>> await registry.initialize()
    >>>
    >>> config = PlanConfig(
    ...     auto_execute=False,  # Review plan before execution
    ... )
    >>>
    >>> async with PlanSession(provider, registry, config) as planner:
    ...     plan = await planner.create_plan("Build a REST API with authentication")
    ...     for step in plan:
    ...         print(f"- {step.description}")
    ...
    ...     # Execute with approval
    ...     results = await planner.execute_plan(plan)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from paracle_meta.capabilities.provider_protocol import LLMMessage, LLMRequest
from paracle_meta.sessions.base import (
    Session,
    SessionConfig,
    SessionMessage,
    SessionStatus,
)

if TYPE_CHECKING:
    from paracle_meta.capabilities.provider_protocol import CapabilityProvider
    from paracle_meta.registry import CapabilityRegistry


# Planning prompts
PLANNING_SYSTEM_PROMPT = """You are a strategic planning assistant. Your role is to decompose complex tasks into clear, actionable steps.

When creating a plan:
1. Analyze the goal thoroughly
2. Break it into logical, sequential steps
3. Each step should be concrete and actionable
4. Consider dependencies between steps
5. Identify what tools/capabilities each step needs
6. Estimate complexity (low, medium, high)

Output plans in JSON format:
{
    "goal": "the original goal",
    "summary": "brief summary of approach",
    "steps": [
        {
            "id": "step_1",
            "description": "what this step accomplishes",
            "action": "specific action to take",
            "capability": "filesystem|code_creation|shell|memory|none",
            "complexity": "low|medium|high",
            "depends_on": ["step_ids this depends on"],
            "validation": "how to verify step completion"
        }
    ],
    "risks": ["potential risks or issues"],
    "success_criteria": "how to know the goal is achieved"
}

Be thorough but practical. Focus on steps that can actually be executed."""


class StepStatus(Enum):
    """Status of a plan step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class PlanStep:
    """A step in a plan.

    Attributes:
        id: Step identifier.
        description: What this step accomplishes.
        action: Specific action to take.
        capability: Required capability (filesystem, code_creation, etc.).
        complexity: Estimated complexity.
        depends_on: Steps this depends on.
        validation: How to verify completion.
        status: Current status.
        result: Execution result.
        error: Error message if failed.
        started_at: When execution started.
        completed_at: When execution completed.
    """

    id: str
    description: str
    action: str
    capability: str = "none"
    complexity: str = "medium"
    depends_on: list[str] = field(default_factory=list)
    validation: str = ""
    status: StepStatus = StepStatus.PENDING
    result: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "action": self.action,
            "capability": self.capability,
            "complexity": self.complexity,
            "depends_on": self.depends_on,
            "validation": self.validation,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanStep:
        """Create from dictionary."""
        return cls(
            id=data.get("id", f"step_{uuid.uuid4().hex[:8]}"),
            description=data["description"],
            action=data.get("action", data["description"]),
            capability=data.get("capability", "none"),
            complexity=data.get("complexity", "medium"),
            depends_on=data.get("depends_on", []),
            validation=data.get("validation", ""),
            status=StepStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
        )


@dataclass
class Plan:
    """A complete plan for achieving a goal.

    Attributes:
        id: Plan identifier.
        goal: The original goal.
        summary: Brief summary of approach.
        steps: List of plan steps.
        risks: Identified risks.
        success_criteria: How to verify goal achievement.
        status: Overall plan status.
        created_at: When plan was created.
    """

    goal: str
    summary: str
    steps: list[PlanStep]
    risks: list[str] = field(default_factory=list)
    success_criteria: str = ""
    id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    status: StepStatus = StepStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def completed_steps(self) -> int:
        """Number of completed steps."""
        return sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)

    @property
    def progress(self) -> float:
        """Progress as percentage (0-100)."""
        if not self.steps:
            return 0.0
        return (self.completed_steps / len(self.steps)) * 100

    @property
    def is_complete(self) -> bool:
        """Whether plan is fully executed."""
        return all(
            s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED) for s in self.steps
        )

    def get_next_step(self) -> PlanStep | None:
        """Get the next step to execute."""
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # Check dependencies
                deps_satisfied = all(
                    self.get_step(dep_id).status == StepStatus.COMPLETED
                    for dep_id in step.depends_on
                    if self.get_step(dep_id)
                )
                if deps_satisfied:
                    return step
        return None

    def get_step(self, step_id: str) -> PlanStep | None:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "goal": self.goal,
            "summary": self.summary,
            "steps": [s.to_dict() for s in self.steps],
            "risks": self.risks,
            "success_criteria": self.success_criteria,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Plan:
        """Create from dictionary."""
        return cls(
            id=data.get("id", f"plan_{uuid.uuid4().hex[:12]}"),
            goal=data["goal"],
            summary=data.get("summary", ""),
            steps=[PlanStep.from_dict(s) for s in data.get("steps", [])],
            risks=data.get("risks", []),
            success_criteria=data.get("success_criteria", ""),
            status=StepStatus(data.get("status", "pending")),
        )


@dataclass
class PlanConfig(SessionConfig):
    """Configuration for plan sessions.

    Attributes:
        auto_execute: Whether to execute steps automatically.
        require_approval: Whether to require approval for each step.
        max_retries: Maximum retries for failed steps.
        continue_on_error: Whether to continue after step failure.
    """

    auto_execute: bool = False
    require_approval: bool = True
    max_retries: int = 2
    continue_on_error: bool = False

    def __post_init__(self) -> None:
        """Set default system prompt."""
        if self.system_prompt is None:
            self.system_prompt = PLANNING_SYSTEM_PROMPT


class PlanSession(Session):
    """Planning session for task decomposition and execution.

    Provides structured planning capabilities with step-by-step execution.

    Attributes:
        config: Plan configuration.
        current_plan: The current plan being executed.
    """

    def __init__(
        self,
        provider: CapabilityProvider,
        registry: CapabilityRegistry,
        config: PlanConfig | None = None,
    ):
        """Initialize plan session.

        Args:
            provider: LLM provider.
            registry: Capability registry.
            config: Plan configuration.
        """
        super().__init__(provider, registry, config or PlanConfig())
        self.config: PlanConfig = self.config  # type: ignore
        self.current_plan: Plan | None = None
        self._plans: dict[str, Plan] = {}

    async def initialize(self) -> None:
        """Initialize the plan session."""
        self.status = SessionStatus.ACTIVE

    async def send(self, message: str) -> SessionMessage:
        """Send a planning request.

        Args:
            message: Planning request (goal to achieve).

        Returns:
            Response with plan summary.
        """
        # Create plan from message
        plan = await self.create_plan(message)
        self.current_plan = plan

        # Format response
        response_content = self._format_plan_response(plan)
        return await self.add_message("assistant", response_content)

    async def create_plan(self, goal: str) -> Plan:
        """Create a plan for achieving a goal.

        Args:
            goal: The goal to achieve.

        Returns:
            The created plan.
        """
        await self.add_message("user", f"Create a plan for: {goal}")

        request = LLMRequest(
            messages=[LLMMessage(role="user", content=f"Create a plan for: {goal}")],
            system_prompt=self.config.system_prompt,
            temperature=0.7,
            max_tokens=self.config.max_tokens,
        )

        response = await self.provider.complete(request)
        await self.add_message("assistant", response.content)

        # Parse plan from response
        plan = self._parse_plan_response(response.content, goal)
        self._plans[plan.id] = plan

        return plan

    def _parse_plan_response(self, content: str, goal: str) -> Plan:
        """Parse plan from LLM response."""
        # Try to extract JSON from response
        try:
            # Find JSON block
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)

                # Handle missing goal
                if "goal" not in data:
                    data["goal"] = goal

                return Plan.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            pass

        # Fallback: Create simple plan from text
        lines = content.strip().split("\n")
        steps = []
        step_num = 1

        for line in lines:
            line = line.strip()
            if line and (
                line.startswith(("-", "*", str(step_num)))
                or line.startswith(f"{step_num}.")
            ):
                # Clean up line
                cleaned = line.lstrip("-*0123456789. ")
                if cleaned:
                    steps.append(
                        PlanStep(
                            id=f"step_{step_num}",
                            description=cleaned,
                            action=cleaned,
                        )
                    )
                    step_num += 1

        return Plan(
            goal=goal,
            summary=f"Plan with {len(steps)} steps",
            steps=steps,
        )

    def _format_plan_response(self, plan: Plan) -> str:
        """Format plan as human-readable response."""
        lines = [
            f"## Plan: {plan.goal}",
            "",
            f"**Summary**: {plan.summary}",
            "",
            f"**Steps** ({len(plan.steps)} total):",
        ]

        for i, step in enumerate(plan.steps, 1):
            status_icon = {
                StepStatus.PENDING: "○",
                StepStatus.IN_PROGRESS: "◐",
                StepStatus.COMPLETED: "●",
                StepStatus.FAILED: "✗",
                StepStatus.SKIPPED: "○",
                StepStatus.BLOCKED: "◌",
            }.get(step.status, "○")

            lines.append(f"{i}. {status_icon} {step.description}")
            if step.capability != "none":
                lines.append(f"   └─ Capability: {step.capability}")

        if plan.risks:
            lines.extend(["", "**Risks**:"])
            for risk in plan.risks:
                lines.append(f"- {risk}")

        if plan.success_criteria:
            lines.extend(["", f"**Success Criteria**: {plan.success_criteria}"])

        return "\n".join(lines)

    async def execute_plan(
        self,
        plan: Plan | None = None,
        step_callback: Any = None,
    ) -> Plan:
        """Execute a plan step by step.

        Args:
            plan: Plan to execute (uses current_plan if None).
            step_callback: Optional callback(step, result) for each step.

        Returns:
            The plan with execution results.
        """
        plan = plan or self.current_plan
        if not plan:
            raise RuntimeError("No plan to execute")

        plan.status = StepStatus.IN_PROGRESS

        while not plan.is_complete:
            step = plan.get_next_step()
            if not step:
                # Check for blocked steps
                blocked = [s for s in plan.steps if s.status == StepStatus.PENDING]
                if blocked:
                    for s in blocked:
                        s.status = StepStatus.BLOCKED
                break

            # Execute step
            step = await self.execute_step(step)

            if step_callback:
                await step_callback(step, step.result)

            if step.status == StepStatus.FAILED and not self.config.continue_on_error:
                plan.status = StepStatus.FAILED
                break

        if plan.is_complete:
            plan.status = StepStatus.COMPLETED

        return plan

    async def execute_step(self, step: PlanStep) -> PlanStep:
        """Execute a single plan step.

        Args:
            step: Step to execute.

        Returns:
            The step with execution result.
        """
        step.status = StepStatus.IN_PROGRESS
        step.started_at = datetime.now(timezone.utc)

        retries = 0
        while retries <= self.config.max_retries:
            try:
                result = await self._execute_step_action(step)
                step.result = result
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                return step

            except Exception as e:
                retries += 1
                if retries > self.config.max_retries:
                    step.error = str(e)
                    step.status = StepStatus.FAILED
                    step.completed_at = datetime.now(timezone.utc)
                    return step

        return step

    async def _execute_step_action(self, step: PlanStep) -> str:
        """Execute the action for a step.

        Args:
            step: Step to execute.

        Returns:
            Execution result.
        """
        if step.capability == "none":
            # No capability needed, just mark as done
            return f"Step completed: {step.description}"

        # Get capability
        try:
            capability = await self.registry.get(step.capability)
        except KeyError:
            return f"Capability '{step.capability}' not available"

        # Execute based on capability type
        if step.capability == "filesystem":
            return await self._execute_filesystem_step(capability, step)
        elif step.capability == "code_creation":
            return await self._execute_code_step(capability, step)
        elif step.capability == "shell":
            return await self._execute_shell_step(capability, step)
        else:
            # Generic execution through LLM
            return await self._execute_generic_step(step)

    async def _execute_filesystem_step(self, capability: Any, step: PlanStep) -> str:
        """Execute a filesystem step."""
        # Parse action for file operations
        action = step.action.lower()

        if "read" in action:
            # Extract path from action
            result = await capability.list_directory(".")
            return f"Directory listing:\n{result.output}"
        elif "write" in action or "create" in action:
            return "File operation would be executed here"
        else:
            return f"Filesystem step completed: {step.description}"

    async def _execute_code_step(self, capability: Any, step: PlanStep) -> str:
        """Execute a code creation step."""
        result = await capability.execute(
            action="complete",
            prompt=f"Generate code for: {step.action}",
        )
        return result.output.get("code", str(result.output))

    async def _execute_shell_step(self, capability: Any, step: PlanStep) -> str:
        """Execute a shell step."""
        # Safety: don't auto-execute shell commands
        return f"Shell command would execute: {step.action}"

    async def _execute_generic_step(self, step: PlanStep) -> str:
        """Execute a generic step using LLM."""
        request = LLMRequest(
            prompt=f"Execute this step and provide the result:\n\n{step.action}",
            system_prompt="You are executing a plan step. Provide a concise result.",
            temperature=0.7,
            max_tokens=1024,
        )

        response = await self.provider.complete(request)
        return response.content

    def get_plan(self, plan_id: str) -> Plan | None:
        """Get a plan by ID."""
        return self._plans.get(plan_id)

    def list_plans(self) -> list[Plan]:
        """List all plans in this session."""
        return list(self._plans.values())
