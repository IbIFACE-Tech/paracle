"""Reflexion capability for MetaAgent.

Enables agents to learn from past experiences through reflection and critique:
- Experience storage (success/failure cases)
- Self-critique and improvement
- Pattern recognition
- Performance tracking
- Adaptive behavior

Inspired by the Reflexion framework for autonomous agents.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class ExperienceType(str, Enum):
    """Type of experience."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    CRITIQUE = "critique"


class ReflectionDepth(str, Enum):
    """Depth of reflection analysis."""

    SHALLOW = "shallow"  # Quick analysis
    MEDIUM = "medium"  # Standard analysis
    DEEP = "deep"  # Comprehensive analysis


@dataclass
class Experience:
    """An agent experience record."""

    id: str
    timestamp: datetime
    agent_name: str
    task: str
    action: str
    result: Any
    experience_type: ExperienceType
    success: bool
    reflection: str | None = None
    critique: str | None = None
    learned_patterns: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "task": self.task,
            "action": self.action,
            "result": self.result,
            "experience_type": self.experience_type.value,
            "success": self.success,
            "reflection": self.reflection,
            "critique": self.critique,
            "learned_patterns": self.learned_patterns,
            "improvement_suggestions": self.improvement_suggestions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Experience":
        """Create from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["experience_type"] = ExperienceType(data["experience_type"])
        return cls(**data)


@dataclass
class Pattern:
    """A learned behavioral pattern."""

    id: str
    name: str
    description: str
    conditions: list[str]  # When this pattern applies
    actions: list[str]  # What to do
    success_rate: float
    usage_count: int
    created_at: datetime
    last_used: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "actions": self.actions,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pattern":
        """Create from dictionary."""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("last_used"):
            data["last_used"] = datetime.fromisoformat(data["last_used"])
        return cls(**data)


class ReflexionConfig(CapabilityConfig):
    """Configuration for reflexion capability."""

    storage_path: Path = Field(
        default=Path("data/reflexion"),
        description="Path to store experience data",
    )
    max_experiences: int = Field(
        default=10000,
        description="Maximum experiences to keep in memory",
    )
    max_patterns: int = Field(
        default=1000,
        description="Maximum patterns to maintain",
    )
    auto_reflect: bool = Field(
        default=True,
        description="Automatically reflect on experiences",
    )
    reflection_depth: ReflectionDepth = Field(
        default=ReflectionDepth.MEDIUM,
        description="Default depth for reflections",
    )
    pattern_threshold: float = Field(
        default=0.7,
        description="Minimum success rate to create pattern",
    )
    enable_critique: bool = Field(
        default=True,
        description="Enable self-critique on failures",
    )


class ReflexionCapability(BaseCapability):
    """Reflexion capability for autonomous learning.

    Enables agents to:
    - Store experiences (success/failure cases)
    - Reflect on past actions
    - Critique their own performance
    - Learn behavioral patterns
    - Improve over time

    Example:
        >>> reflexion = ReflexionCapability()
        >>> await reflexion.initialize()

        >>> # Record an experience
        >>> result = await reflexion.record(
        ...     agent_name="coder",
        ...     task="implement feature X",
        ...     action="wrote code with tests",
        ...     result={"status": "success", "tests_passed": 10},
        ...     success=True
        ... )

        >>> # Reflect on the experience
        >>> reflection = await reflexion.reflect(
        ...     experience_id=result.output["experience_id"],
        ...     depth="deep"
        ... )

        >>> # Query similar experiences
        >>> similar = await reflexion.query(
        ...     task="implement feature",
        ...     limit=5
        ... )

        >>> # Get learned patterns
        >>> patterns = await reflexion.get_patterns(
        ...     agent_name="coder"
        ... )
    """

    name = "reflexion"
    description = "Learning from experience through reflection and critique"

    def __init__(self, config: ReflexionConfig | None = None):
        """Initialize reflexion capability."""
        super().__init__(config or ReflexionConfig())
        self.config: ReflexionConfig = self.config
        self._experiences: dict[str, Experience] = {}
        self._patterns: dict[str, Pattern] = {}
        self._agent_stats: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize reflexion storage."""
        self.config.storage_path.mkdir(parents=True, exist_ok=True)

        # Load existing experiences
        exp_file = self.config.storage_path / "experiences.jsonl"
        if exp_file.exists():
            with open(exp_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        exp = Experience.from_dict(json.loads(line))
                        self._experiences[exp.id] = exp

        # Load existing patterns
        pattern_file = self.config.storage_path / "patterns.json"
        if pattern_file.exists():
            with open(pattern_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for p_data in data.get("patterns", []):
                    pattern = Pattern.from_dict(p_data)
                    self._patterns[pattern.id] = pattern

        await super().initialize()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute reflexion operation.

        Args:
            action: Operation (record, reflect, critique, query, patterns, stats)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "record")
        start_time = time.time()

        try:
            if action == "record":
                result = await self._record_experience(**kwargs)
            elif action == "reflect":
                result = await self._reflect(**kwargs)
            elif action == "critique":
                result = await self._critique(**kwargs)
            elif action == "query":
                result = self._query_experiences(**kwargs)
            elif action == "patterns":
                result = self._get_patterns(**kwargs)
            elif action == "stats":
                result = self._get_stats(**kwargs)
            elif action == "save":
                result = await self._save(**kwargs)
            elif action == "clear":
                result = await self._clear(**kwargs)
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

    def _generate_id(self, data: str) -> str:
        """Generate unique ID from data."""
        unique = f"{data}-{time.time()}"
        return hashlib.md5(unique.encode()).hexdigest()[:16]

    async def _record_experience(
        self,
        agent_name: str,
        task: str,
        action_taken: str,
        result: Any,
        success: bool,
        experience_type: str | None = None,
        metadata: dict | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Record a new experience.

        Args:
            agent_name: Name of the agent
            task: Task description
            action_taken: Action taken
            result: Result of the action
            success: Whether action was successful
            experience_type: Type of experience (auto-detected if None)
            metadata: Additional metadata

        Returns:
            Experience info dict
        """
        # Auto-detect experience type
        if experience_type is None:
            if success:
                experience_type = ExperienceType.SUCCESS
            else:
                experience_type = ExperienceType.FAILURE
        else:
            experience_type = ExperienceType(experience_type)

        exp_id = self._generate_id(f"{agent_name}-{task}-{action_taken}")

        experience = Experience(
            id=exp_id,
            timestamp=datetime.utcnow(),
            agent_name=agent_name,
            task=task,
            action=action_taken,
            result=result,
            experience_type=experience_type,
            success=success,
            metadata=metadata or {},
        )

        # Auto-reflect if enabled
        if self.config.auto_reflect:
            reflection = self._generate_reflection(
                experience, self.config.reflection_depth
            )
            experience.reflection = reflection

        # Auto-critique on failure if enabled
        if self.config.enable_critique and not success:
            critique = self._generate_critique(experience)
            experience.critique = critique

        self._experiences[exp_id] = experience

        # Update agent stats
        self._update_stats(agent_name, success)

        # Check for pattern creation
        if success and self._should_create_pattern(agent_name, task):
            await self._create_pattern_from_experience(experience)

        # Auto-save
        await self._append_experience(experience)

        # Enforce limits
        if len(self._experiences) > self.config.max_experiences:
            await self._prune_experiences()

        return {
            "experience_id": exp_id,
            "agent_name": agent_name,
            "task": task,
            "success": success,
            "experience_type": experience_type.value,
            "reflection": experience.reflection,
            "critique": experience.critique,
        }

    def _generate_reflection(
        self, experience: Experience, depth: ReflectionDepth
    ) -> str:
        """Generate reflection on an experience.

        Args:
            experience: The experience to reflect on
            depth: Depth of reflection

        Returns:
            Reflection text
        """
        # Simple rule-based reflection
        # In production, this would use an LLM
        if experience.success:
            reflection = (
                f"Successfully completed '{experience.task}' by {experience.action}."
            )

            if depth in (ReflectionDepth.MEDIUM, ReflectionDepth.DEEP):
                reflection += f" Result: {experience.result}"

            if depth == ReflectionDepth.DEEP:
                # Look for similar past experiences
                similar = self._find_similar_experiences(experience, limit=3)
                if similar:
                    reflection += f" Similar past successes: {len(similar)}"
        else:
            reflection = (
                f"Failed to complete '{experience.task}'. Action: {experience.action}"
            )

            if depth in (ReflectionDepth.MEDIUM, ReflectionDepth.DEEP):
                reflection += f" Error: {experience.result}"

            if depth == ReflectionDepth.DEEP:
                # Suggest improvements
                reflection += (
                    " Consider: review approach, check assumptions, seek assistance."
                )

        return reflection

    def _generate_critique(self, experience: Experience) -> str:
        """Generate self-critique for a failed experience.

        Args:
            experience: Failed experience

        Returns:
            Critique text
        """
        # Simple rule-based critique
        # In production, this would use an LLM
        critique_parts = [
            f"Analysis of failure for task '{experience.task}':",
            f"- Action taken: {experience.action}",
            f"- Result: {experience.result}",
        ]

        # Check for similar past failures
        similar_failures = [
            e
            for e in self._experiences.values()
            if e.agent_name == experience.agent_name
            and not e.success
            and e.task == experience.task
        ]

        if len(similar_failures) > 2:
            critique_parts.append(
                f"- Warning: This is failure #{len(similar_failures)} for similar task"
            )
            critique_parts.append("- Recommendation: Consider different approach")

        return "\n".join(critique_parts)

    def _find_similar_experiences(
        self, experience: Experience, limit: int = 5
    ) -> list[Experience]:
        """Find similar past experiences.

        Args:
            experience: Reference experience
            limit: Maximum results

        Returns:
            List of similar experiences
        """
        # Simple similarity based on task matching
        # In production, use semantic similarity (vector search)
        similar = []
        for exp in self._experiences.values():
            if exp.id == experience.id:
                continue
            if exp.agent_name != experience.agent_name:
                continue

            # Check task similarity (simple string matching)
            if (
                experience.task.lower() in exp.task.lower()
                or exp.task.lower() in experience.task.lower()
            ):
                similar.append(exp)

        # Sort by timestamp (most recent first)
        similar.sort(key=lambda e: e.timestamp, reverse=True)
        return similar[:limit]

    async def _reflect(
        self,
        experience_id: str,
        depth: str = "medium",
        **kwargs,
    ) -> dict[str, Any]:
        """Reflect on a specific experience.

        Args:
            experience_id: Experience ID
            depth: Reflection depth (shallow, medium, deep)

        Returns:
            Reflection result
        """
        if experience_id not in self._experiences:
            raise ValueError(f"Experience not found: {experience_id}")

        experience = self._experiences[experience_id]
        depth_enum = ReflectionDepth(depth)

        reflection = self._generate_reflection(experience, depth_enum)
        experience.reflection = reflection

        # Update stored experience
        await self._append_experience(experience)

        return {
            "experience_id": experience_id,
            "reflection": reflection,
            "depth": depth,
        }

    async def _critique(
        self,
        experience_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate critique for an experience.

        Args:
            experience_id: Experience ID

        Returns:
            Critique result
        """
        if experience_id not in self._experiences:
            raise ValueError(f"Experience not found: {experience_id}")

        experience = self._experiences[experience_id]

        critique = self._generate_critique(experience)
        experience.critique = critique

        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(experience)
        experience.improvement_suggestions = suggestions

        # Update stored experience
        await self._append_experience(experience)

        return {
            "experience_id": experience_id,
            "critique": critique,
            "suggestions": suggestions,
        }

    def _generate_improvement_suggestions(self, experience: Experience) -> list[str]:
        """Generate improvement suggestions based on experience.

        Args:
            experience: Experience to analyze

        Returns:
            List of suggestions
        """
        suggestions = []

        # Check past successes for similar tasks
        successes = [
            e
            for e in self._experiences.values()
            if e.agent_name == experience.agent_name
            and e.success
            and e.task == experience.task
        ]

        if successes:
            suggestions.append(f"Review {len(successes)} past successful approaches")

        # Check if this is a repeated failure
        failures = [
            e
            for e in self._experiences.values()
            if e.agent_name == experience.agent_name
            and not e.success
            and e.task == experience.task
        ]

        if len(failures) > 1:
            suggestions.append(
                "Consider fundamentally different approach (repeated failures detected)"
            )

        # Generic suggestions
        suggestions.append("Break task into smaller steps")
        suggestions.append("Request human feedback or assistance")

        return suggestions

    def _query_experiences(
        self,
        agent_name: str | None = None,
        task: str | None = None,
        success: bool | None = None,
        experience_type: str | None = None,
        limit: int = 10,
        **kwargs,
    ) -> dict[str, Any]:
        """Query past experiences.

        Args:
            agent_name: Filter by agent name
            task: Filter by task (substring match)
            success: Filter by success status
            experience_type: Filter by type
            limit: Maximum results

        Returns:
            Query results
        """
        results = list(self._experiences.values())

        # Apply filters
        if agent_name:
            results = [e for e in results if e.agent_name == agent_name]

        if task:
            task_lower = task.lower()
            results = [e for e in results if task_lower in e.task.lower()]

        if success is not None:
            results = [e for e in results if e.success == success]

        if experience_type:
            exp_type = ExperienceType(experience_type)
            results = [e for e in results if e.experience_type == exp_type]

        # Sort by timestamp (most recent first)
        results.sort(key=lambda e: e.timestamp, reverse=True)

        # Limit
        results = results[:limit]

        return {
            "experiences": [e.to_dict() for e in results],
            "count": len(results),
            "filters": {
                "agent_name": agent_name,
                "task": task,
                "success": success,
                "experience_type": experience_type,
            },
        }

    def _should_create_pattern(self, agent_name: str, task: str) -> bool:
        """Check if a pattern should be created.

        Args:
            agent_name: Agent name
            task: Task description

        Returns:
            True if pattern should be created
        """
        # Get similar successful experiences
        successes = [
            e
            for e in self._experiences.values()
            if e.agent_name == agent_name
            and e.success
            and task.lower() in e.task.lower()
        ]

        # Create pattern if we have enough successes
        return len(successes) >= 3

    async def _create_pattern_from_experience(self, experience: Experience) -> None:
        """Create a behavioral pattern from experience.

        Args:
            experience: Successful experience to learn from
        """
        # Find similar successful experiences
        similar = [
            e
            for e in self._experiences.values()
            if e.agent_name == experience.agent_name
            and e.success
            and experience.task.lower() in e.task.lower()
        ]

        if len(similar) < 3:
            return  # Not enough data

        # Calculate success rate
        total = len(
            [
                e
                for e in self._experiences.values()
                if e.agent_name == experience.agent_name
                and experience.task.lower() in e.task.lower()
            ]
        )
        success_rate = len(similar) / total if total > 0 else 0

        if success_rate < self.config.pattern_threshold:
            return  # Success rate too low

        # Create pattern
        pattern_id = self._generate_id(
            f"pattern-{experience.agent_name}-{experience.task}"
        )

        # Extract common conditions and actions
        conditions = [f"Task: {experience.task}"]
        actions = [experience.action]

        pattern = Pattern(
            id=pattern_id,
            name=f"Pattern for {experience.task}",
            description=f"Learned from {len(similar)} successful experiences",
            conditions=conditions,
            actions=actions,
            success_rate=success_rate,
            usage_count=0,
            created_at=datetime.utcnow(),
        )

        self._patterns[pattern_id] = pattern

        # Save patterns
        await self._save_patterns()

    def _get_patterns(
        self,
        agent_name: str | None = None,
        min_success_rate: float | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Get learned patterns.

        Args:
            agent_name: Filter by agent name
            min_success_rate: Minimum success rate

        Returns:
            Patterns list
        """
        patterns = list(self._patterns.values())

        # Apply filters
        if min_success_rate is not None:
            patterns = [p for p in patterns if p.success_rate >= min_success_rate]

        # Sort by success rate
        patterns.sort(key=lambda p: p.success_rate, reverse=True)

        return {
            "patterns": [p.to_dict() for p in patterns],
            "count": len(patterns),
        }

    def _update_stats(self, agent_name: str, success: bool) -> None:
        """Update agent statistics.

        Args:
            agent_name: Agent name
            success: Whether action was successful
        """
        if agent_name not in self._agent_stats:
            self._agent_stats[agent_name] = {
                "total": 0,
                "successes": 0,
                "failures": 0,
                "success_rate": 0.0,
            }

        stats = self._agent_stats[agent_name]
        stats["total"] += 1
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1

        stats["success_rate"] = stats["successes"] / stats["total"]

    def _get_stats(
        self,
        agent_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Get performance statistics.

        Args:
            agent_name: Filter by agent name

        Returns:
            Statistics
        """
        if agent_name:
            if agent_name not in self._agent_stats:
                return {"agent_name": agent_name, "stats": None}
            return {
                "agent_name": agent_name,
                "stats": self._agent_stats[agent_name],
            }

        return {
            "agents": self._agent_stats,
            "total_experiences": len(self._experiences),
            "total_patterns": len(self._patterns),
        }

    async def _append_experience(self, experience: Experience) -> None:
        """Append experience to storage file.

        Args:
            experience: Experience to save
        """
        exp_file = self.config.storage_path / "experiences.jsonl"
        with open(exp_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(experience.to_dict()) + "\n")

    async def _save_patterns(self) -> None:
        """Save patterns to storage."""
        pattern_file = self.config.storage_path / "patterns.json"
        data = {
            "patterns": [p.to_dict() for p in self._patterns.values()],
        }
        with open(pattern_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    async def _save(self, **kwargs) -> dict[str, Any]:
        """Save all data to disk.

        Returns:
            Save result
        """
        # Experiences are already saved incrementally
        # Just save patterns
        await self._save_patterns()

        return {
            "saved": True,
            "experiences": len(self._experiences),
            "patterns": len(self._patterns),
        }

    async def _prune_experiences(self) -> None:
        """Remove oldest experiences to maintain limit."""
        # Sort by timestamp
        experiences = sorted(self._experiences.values(), key=lambda e: e.timestamp)

        # Remove oldest
        to_remove = len(experiences) - self.config.max_experiences
        for exp in experiences[:to_remove]:
            del self._experiences[exp.id]

    async def _clear(
        self,
        agent_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Clear experiences and patterns.

        Args:
            agent_name: Clear only for specific agent

        Returns:
            Clear result
        """
        if agent_name:
            # Clear only for specific agent
            to_remove = [
                exp_id
                for exp_id, exp in self._experiences.items()
                if exp.agent_name == agent_name
            ]
            for exp_id in to_remove:
                del self._experiences[exp_id]

            if agent_name in self._agent_stats:
                del self._agent_stats[agent_name]

            count = len(to_remove)
        else:
            # Clear all
            count = len(self._experiences)
            self._experiences.clear()
            self._patterns.clear()
            self._agent_stats.clear()

        return {
            "cleared": True,
            "count": count,
            "agent_name": agent_name,
        }

    # Convenience methods
    async def record(
        self,
        agent_name: str,
        task: str,
        action_taken: str,
        result: Any,
        success: bool,
        **kwargs,
    ) -> CapabilityResult:
        """Record an experience."""
        params = {
            "agent_name": agent_name,
            "task": task,
            "action_taken": action_taken,
            "result": result,
            "success": success,
            **kwargs,
        }
        return await self.execute(action="record", **params)

    async def reflect(
        self, experience_id: str, depth: str = "medium"
    ) -> CapabilityResult:
        """Reflect on an experience."""
        return await self.execute(
            action="reflect", experience_id=experience_id, depth=depth
        )

    async def query(self, **kwargs) -> CapabilityResult:
        """Query past experiences."""
        return await self.execute(action="query", **kwargs)

    async def get_patterns(self, **kwargs) -> CapabilityResult:
        """Get learned patterns."""
        return await self.execute(action="patterns", **kwargs)

    async def get_stats(self, agent_name: str | None = None) -> CapabilityResult:
        """Get performance statistics."""
        return await self.execute(action="stats", agent_name=agent_name)
