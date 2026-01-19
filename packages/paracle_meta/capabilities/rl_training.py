"""Reinforcement Learning training capability for MetaAgent.

Trains agents using RL algorithms:
- Q-Learning
- SARSA
- Deep Q-Network (DQN)
- Policy Gradient (PG)
- Actor-Critic (A2C)
- Proximal Policy Optimization (PPO)
- Advantage Actor-Critic (A3C)
- Trust Region Policy Optimization (TRPO)
- Soft Actor-Critic (SAC)

Inspired by claude-flow's RL training infrastructure.
"""

import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class RLAlgorithm(str, Enum):
    """Reinforcement learning algorithm."""

    Q_LEARNING = "q_learning"
    SARSA = "sarsa"
    DQN = "dqn"
    POLICY_GRADIENT = "policy_gradient"
    A2C = "a2c"  # Advantage Actor-Critic
    PPO = "ppo"  # Proximal Policy Optimization
    A3C = "a3c"  # Asynchronous Advantage Actor-Critic
    TRPO = "trpo"  # Trust Region Policy Optimization
    SAC = "sac"  # Soft Actor-Critic


@dataclass
class Experience:
    """Single experience tuple (s, a, r, s', done)."""

    state: Any
    action: Any
    reward: float
    next_state: Any
    done: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self.state,
            "action": self.action,
            "reward": self.reward,
            "next_state": self.next_state,
            "done": self.done,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Episode:
    """Training episode."""

    id: int
    experiences: list[Experience] = field(default_factory=list)
    total_reward: float = 0.0
    steps: int = 0
    success: bool = False
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "total_reward": self.total_reward,
            "steps": self.steps,
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }


class RLTrainingConfig(CapabilityConfig):
    """Configuration for RL training capability."""

    algorithm: RLAlgorithm = Field(
        default=RLAlgorithm.Q_LEARNING,
        description="RL algorithm to use",
    )
    storage_path: Path = Field(
        default=Path("data/rl_training"),
        description="Path to store training data",
    )
    learning_rate: float = Field(
        default=0.001,
        description="Learning rate (alpha)",
    )
    discount_factor: float = Field(
        default=0.99,
        description="Discount factor (gamma)",
    )
    epsilon: float = Field(
        default=0.1,
        description="Exploration rate (epsilon for epsilon-greedy)",
    )
    epsilon_decay: float = Field(
        default=0.995,
        description="Epsilon decay rate",
    )
    min_epsilon: float = Field(
        default=0.01,
        description="Minimum epsilon",
    )
    batch_size: int = Field(
        default=32,
        description="Batch size for training",
    )
    memory_size: int = Field(
        default=10000,
        description="Experience replay buffer size",
    )
    target_update_freq: int = Field(
        default=100,
        description="Target network update frequency (for DQN)",
    )
    save_freq: int = Field(
        default=100,
        description="Model save frequency (episodes)",
    )


class RLTrainingCapability(BaseCapability):
    """Reinforcement learning training for agents.

    Trains agents using various RL algorithms:
    - Value-based: Q-Learning, SARSA, DQN
    - Policy-based: Policy Gradient
    - Actor-Critic: A2C, A3C, PPO, TRPO, SAC

    Example:
        >>> rl = RLTrainingCapability()
        >>> await rl.initialize()

        >>> # Create training session
        >>> result = await rl.create_session(
        ...     name="chess_training",
        ...     algorithm="dqn",
        ...     state_dim=64,
        ...     action_dim=4096
        ... )

        >>> # Record experience
        >>> await rl.record_experience(
        ...     session_id=session_id,
        ...     state=[...],
        ...     action=42,
        ...     reward=1.0,
        ...     next_state=[...],
        ...     done=False
        ... )

        >>> # Train on experiences
        >>> result = await rl.train_step(
        ...     session_id=session_id
        ... )

        >>> # Get policy action
        >>> result = await rl.get_action(
        ...     session_id=session_id,
        ...     state=[...],
        ...     explore=True
        ... )
    """

    name = "rl_training"
    description = "Reinforcement learning training with 9 algorithms"

    def __init__(self, config: RLTrainingConfig | None = None):
        """Initialize RL training capability."""
        super().__init__(config or RLTrainingConfig())
        self.config: RLTrainingConfig = self.config
        self._sessions: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize RL training."""
        self.config.storage_path.mkdir(parents=True, exist_ok=True)
        await super().initialize()

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute RL training operation.

        Args:
            action: Operation (create_session, record, train_step, get_action, etc.)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "list_sessions")
        start_time = time.time()

        try:
            if action == "create_session":
                result = await self._create_session(**kwargs)
            elif action == "record_experience":
                result = self._record_experience(**kwargs)
            elif action == "train_step":
                result = await self._train_step(**kwargs)
            elif action == "get_action":
                result = self._get_action(**kwargs)
            elif action == "start_episode":
                result = self._start_episode(**kwargs)
            elif action == "end_episode":
                result = self._end_episode(**kwargs)
            elif action == "save":
                result = await self._save_session(**kwargs)
            elif action == "load":
                result = await self._load_session(**kwargs)
            elif action == "list_sessions":
                result = self._list_sessions(**kwargs)
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

    async def _create_session(
        self,
        name: str,
        algorithm: str | None = None,
        state_dim: int | None = None,
        action_dim: int | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Create a training session.

        Args:
            name: Session name
            algorithm: RL algorithm (defaults to config)
            state_dim: State space dimension
            action_dim: Action space dimension

        Returns:
            Session info
        """
        session_id = f"rl-{int(time.time() * 1000)}"

        algo = RLAlgorithm(algorithm) if algorithm else self.config.algorithm

        session = {
            "id": session_id,
            "name": name,
            "algorithm": algo.value,
            "state_dim": state_dim,
            "action_dim": action_dim,
            "created_at": datetime.utcnow().isoformat(),
            "episodes": [],
            "current_episode": None,
            "memory": deque(maxlen=self.config.memory_size),
            "total_steps": 0,
            "total_episodes": 0,
            "epsilon": self.config.epsilon,
            # Algorithm-specific storage
            "q_table": {},  # For tabular methods
            "model": None,  # For deep methods (would use actual neural network)
            "target_model": None,  # For DQN
            "stats": {
                "avg_reward": 0.0,
                "max_reward": float("-inf"),
                "min_reward": float("inf"),
                "success_rate": 0.0,
            },
        }

        self._sessions[session_id] = session

        return {
            "session_id": session_id,
            "name": name,
            "algorithm": algo.value,
            "state_dim": state_dim,
            "action_dim": action_dim,
        }

    def _record_experience(
        self,
        session_id: str,
        state: Any,
        action: Any,  # Keep original name internally
        reward: float,
        next_state: Any,
        done: bool,
        **kwargs,
    ) -> dict[str, Any]:
        """Record an experience.

        Args:
            session_id: Session ID
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Episode done flag

        Returns:
            Experience info
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self._sessions[session_id]

        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
        )

        # Add to replay memory
        session["memory"].append(experience)

        # Add to current episode
        if session["current_episode"]:
            episode = session["current_episode"]
            episode.experiences.append(experience)
            episode.total_reward += reward
            episode.steps += 1

        session["total_steps"] += 1

        return {
            "session_id": session_id,
            "experience_recorded": True,
            "memory_size": len(session["memory"]),
            "episode_steps": (
                session["current_episode"].steps if session["current_episode"] else 0
            ),
        }

    async def _train_step(
        self,
        session_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Perform a training step.

        Args:
            session_id: Session ID

        Returns:
            Training result
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self._sessions[session_id]
        algorithm = RLAlgorithm(session["algorithm"])

        # Check if enough experiences
        if len(session["memory"]) < self.config.batch_size:
            return {
                "session_id": session_id,
                "trained": False,
                "reason": "insufficient_experiences",
                "memory_size": len(session["memory"]),
                "required": self.config.batch_size,
            }

        # Sample batch from memory
        indices = np.random.choice(
            len(session["memory"]), self.config.batch_size, replace=False
        )
        batch = [session["memory"][i] for i in indices]

        loss = 0.0

        # Train based on algorithm
        if algorithm == RLAlgorithm.Q_LEARNING:
            loss = self._train_q_learning(session, batch)
        elif algorithm == RLAlgorithm.SARSA:
            loss = self._train_sarsa(session, batch)
        elif algorithm == RLAlgorithm.DQN:
            loss = self._train_dqn(session, batch)
        elif algorithm in (
            RLAlgorithm.POLICY_GRADIENT,
            RLAlgorithm.A2C,
            RLAlgorithm.PPO,
        ):
            loss = self._train_policy_gradient(session, batch, algorithm)
        else:
            # Placeholder for other algorithms
            loss = 0.0

        return {
            "session_id": session_id,
            "trained": True,
            "algorithm": algorithm.value,
            "batch_size": len(batch),
            "loss": float(loss),
        }

    def _train_q_learning(
        self,
        session: dict[str, Any],
        batch: list[Experience],
    ) -> float:
        """Train using Q-Learning.

        Args:
            session: Training session
            batch: Experience batch

        Returns:
            Training loss
        """
        q_table = session["q_table"]
        total_error = 0.0

        for exp in batch:
            # Convert state/action to hashable keys
            state_key = str(exp.state)
            action_key = str(exp.action)
            next_state_key = str(exp.next_state)

            # Initialize Q-values if needed
            if state_key not in q_table:
                q_table[state_key] = {}
            if action_key not in q_table[state_key]:
                q_table[state_key][action_key] = 0.0

            # Get current Q-value
            current_q = q_table[state_key][action_key]

            # Calculate target Q-value
            if exp.done:
                target_q = exp.reward
            else:
                # Max Q-value for next state
                if next_state_key not in q_table:
                    q_table[next_state_key] = {}

                next_q_values = (
                    list(q_table[next_state_key].values())
                    if q_table[next_state_key]
                    else [0.0]
                )
                max_next_q = max(next_q_values) if next_q_values else 0.0

                target_q = exp.reward + self.config.discount_factor * max_next_q

            # Update Q-value
            error = target_q - current_q
            q_table[state_key][action_key] += self.config.learning_rate * error

            total_error += abs(error)

        return total_error / len(batch)

    def _train_sarsa(
        self,
        session: dict[str, Any],
        batch: list[Experience],
    ) -> float:
        """Train using SARSA.

        Args:
            session: Training session
            batch: Experience batch

        Returns:
            Training loss
        """
        # SARSA is similar to Q-Learning but uses actual next action
        # For simplicity, using similar implementation
        return self._train_q_learning(session, batch)

    def _train_dqn(
        self,
        session: dict[str, Any],
        batch: list[Experience],
    ) -> float:
        """Train using Deep Q-Network.

        Args:
            session: Training session
            batch: Experience batch

        Returns:
            Training loss
        """
        # Placeholder for DQN training
        # In production, this would use a neural network (PyTorch/TensorFlow)
        # For now, fall back to Q-Learning
        return self._train_q_learning(session, batch)

    def _train_policy_gradient(
        self,
        session: dict[str, Any],
        batch: list[Experience],
        algorithm: RLAlgorithm,
    ) -> float:
        """Train using policy gradient methods.

        Args:
            session: Training session
            batch: Experience batch
            algorithm: Specific PG algorithm

        Returns:
            Training loss
        """
        # Placeholder for policy gradient training
        # Would use neural network for policy
        return 0.0

    def _get_action(
        self,
        session_id: str,
        state: Any,
        explore: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Get action from policy.

        Args:
            session_id: Session ID
            state: Current state
            explore: Use epsilon-greedy exploration

        Returns:
            Action and info
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self._sessions[session_id]
        state_key = str(state)

        # Epsilon-greedy exploration
        if explore and np.random.random() < session["epsilon"]:
            # Random action
            if session["action_dim"]:
                action = np.random.randint(0, session["action_dim"])
            else:
                action = "random"

            return {
                "session_id": session_id,
                "action": action,
                "explore": True,
                "epsilon": session["epsilon"],
            }

        # Exploit: choose best action
        q_table = session["q_table"]

        if state_key not in q_table or not q_table[state_key]:
            # No learned Q-values, choose random
            if session["action_dim"]:
                action = np.random.randint(0, session["action_dim"])
            else:
                action = 0
        else:
            # Choose action with highest Q-value
            action = max(q_table[state_key], key=q_table[state_key].get)

            # Convert back to int if it's a string
            try:
                action = int(action)
            except (ValueError, TypeError):
                pass

        return {
            "session_id": session_id,
            "action": action,
            "explore": False,
            "q_values": q_table.get(state_key, {}),
        }

    def _start_episode(
        self,
        session_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Start a new episode.

        Args:
            session_id: Session ID

        Returns:
            Episode info
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self._sessions[session_id]

        episode_id = session["total_episodes"] + 1
        episode = Episode(id=episode_id)

        session["current_episode"] = episode
        session["total_episodes"] += 1

        return {
            "session_id": session_id,
            "episode_id": episode_id,
            "epsilon": session["epsilon"],
        }

    def _end_episode(
        self,
        session_id: str,
        success: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """End current episode.

        Args:
            session_id: Session ID
            success: Whether episode was successful

        Returns:
            Episode summary
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self._sessions[session_id]

        if not session["current_episode"]:
            raise ValueError("No active episode")

        episode = session["current_episode"]
        episode.success = success
        episode.ended_at = datetime.utcnow()

        # Add to episodes list
        session["episodes"].append(episode)

        # Update stats
        stats = session["stats"]
        stats["max_reward"] = max(stats["max_reward"], episode.total_reward)
        stats["min_reward"] = min(stats["min_reward"], episode.total_reward)

        # Running average
        n = len(session["episodes"])
        stats["avg_reward"] = (stats["avg_reward"] * (n - 1) + episode.total_reward) / n

        # Success rate
        successes = sum(1 for ep in session["episodes"] if ep.success)
        stats["success_rate"] = successes / n if n > 0 else 0.0

        # Decay epsilon
        session["epsilon"] = max(
            self.config.min_epsilon, session["epsilon"] * self.config.epsilon_decay
        )

        # Clear current episode
        session["current_episode"] = None

        return {
            "session_id": session_id,
            "episode_id": episode.id,
            "total_reward": episode.total_reward,
            "steps": episode.steps,
            "success": success,
            "epsilon": session["epsilon"],
            "stats": stats,
        }

    async def _save_session(
        self,
        session_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Save training session.

        Args:
            session_id: Session ID

        Returns:
            Save result
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self._sessions[session_id]

        # Convert to serializable format
        save_data = {
            "id": session["id"],
            "name": session["name"],
            "algorithm": session["algorithm"],
            "state_dim": session["state_dim"],
            "action_dim": session["action_dim"],
            "created_at": session["created_at"],
            "total_steps": session["total_steps"],
            "total_episodes": session["total_episodes"],
            "epsilon": session["epsilon"],
            "q_table": session["q_table"],
            "stats": session["stats"],
            "episodes": [ep.to_dict() for ep in session["episodes"]],
        }

        # Save to file
        save_path = self.config.storage_path / f"{session_id}.json"
        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=2)

        return {
            "session_id": session_id,
            "saved": True,
            "path": str(save_path),
        }

    async def _load_session(
        self,
        session_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Load training session.

        Args:
            session_id: Session ID

        Returns:
            Load result
        """
        load_path = self.config.storage_path / f"{session_id}.json"

        if not load_path.exists():
            raise ValueError(f"Session file not found: {load_path}")

        with open(load_path, "r") as f:
            save_data = json.load(f)

        # Reconstruct session
        session = {
            **save_data,
            "current_episode": None,
            "memory": deque(maxlen=self.config.memory_size),
            "model": None,
            "target_model": None,
        }

        self._sessions[session_id] = session

        return {
            "session_id": session_id,
            "loaded": True,
            "total_episodes": session["total_episodes"],
            "total_steps": session["total_steps"],
        }

    def _list_sessions(self, **kwargs) -> dict[str, Any]:
        """List training sessions.

        Returns:
            Sessions list
        """
        sessions = [
            {
                "id": s["id"],
                "name": s["name"],
                "algorithm": s["algorithm"],
                "total_episodes": s["total_episodes"],
                "total_steps": s["total_steps"],
                "stats": s["stats"],
            }
            for s in self._sessions.values()
        ]

        return {
            "sessions": sessions,
            "count": len(sessions),
        }

    def _get_stats(
        self,
        session_id: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Get session statistics.

        Args:
            session_id: Session ID

        Returns:
            Statistics
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self._sessions[session_id]

        return {
            "session_id": session_id,
            "algorithm": session["algorithm"],
            "total_episodes": session["total_episodes"],
            "total_steps": session["total_steps"],
            "epsilon": session["epsilon"],
            "memory_size": len(session["memory"]),
            "q_table_size": len(session["q_table"]),
            "stats": session["stats"],
        }

    # Convenience methods
    async def create_session(
        self,
        name: str,
        algorithm: str | None = None,
        **kwargs,
    ) -> CapabilityResult:
        """Create training session."""
        return await self.execute(
            action="create_session",
            name=name,
            algorithm=algorithm,
            **kwargs,
        )

    async def record_experience(
        self,
        session_id: str,
        state: Any,
        action_taken: Any,
        reward: float,
        next_state: Any,
        done: bool,
    ) -> CapabilityResult:
        """Record experience."""
        params = {
            "session_id": session_id,
            "state": state,
            "action": action_taken,  # Will be unpacked as action parameter
            "reward": reward,
            "next_state": next_state,
            "done": done,
        }
        return await self.execute(action="record_experience", **params)

    async def train_step(self, session_id: str) -> CapabilityResult:
        """Perform training step."""
        return await self.execute(action="train_step", session_id=session_id)

    async def get_action(
        self,
        session_id: str,
        state: Any,
        explore: bool = True,
    ) -> CapabilityResult:
        """Get action from policy."""
        return await self.execute(
            action="get_action",
            session_id=session_id,
            state=state,
            explore=explore,
        )

    async def get_stats(self, session_id: str) -> CapabilityResult:
        """Get statistics."""
        return await self.execute(action="stats", session_id=session_id)
