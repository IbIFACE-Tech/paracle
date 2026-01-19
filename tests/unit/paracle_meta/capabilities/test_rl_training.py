"""Unit tests for RLTrainingCapability."""

import pytest
import numpy as np

from paracle_meta.capabilities.rl_training import (
    RLTrainingCapability,
    RLTrainingConfig,
    RLAlgorithm,
)


@pytest.fixture
def rl_trainer():
    """Create RLTrainingCapability instance."""
    config = RLTrainingConfig(
        default_algorithm=RLAlgorithm.Q_LEARNING,
        learning_rate=0.1,
        discount_factor=0.9,
    )
    return RLTrainingCapability(config)


@pytest.mark.asyncio
async def test_rl_training_initialization(rl_trainer):
    """Test RLTrainingCapability initialization."""
    assert rl_trainer.name == "rl_training"
    assert rl_trainer.config.default_algorithm == RLAlgorithm.Q_LEARNING
    assert rl_trainer.config.learning_rate == 0.1


@pytest.mark.asyncio
async def test_create_training_session(rl_trainer):
    """Test creating a training session."""
    result = await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=4, action_dim=2
    )

    assert result.success is True
    assert result.output["session_id"] == "test-session"
    assert result.output["algorithm"] == RLAlgorithm.Q_LEARNING


@pytest.mark.asyncio
async def test_record_experience(rl_trainer):
    """Test recording an experience."""
    # Create session first
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=4, action_dim=2
    )

    # Record experience
    result = await rl_trainer.record_experience(
        session_id="test-session",
        state=[1.0, 0.5, 0.0, 0.3],
        action_taken=0,
        reward=1.0,
        next_state=[1.0, 0.6, 0.1, 0.4],
        done=False,
    )

    assert result.success is True
    assert "experience_count" in result.output


@pytest.mark.asyncio
async def test_train_step(rl_trainer):
    """Test performing a training step."""
    # Create session and add experiences
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    # Add multiple experiences
    for i in range(10):
        await rl_trainer.record_experience(
            session_id="test-session",
            state=[0.1 * i, 0.2 * i],
            action_taken=i % 2,
            reward=1.0 if i % 2 == 0 else -1.0,
            next_state=[0.1 * (i + 1), 0.2 * (i + 1)],
            done=False,
        )

    # Train
    result = await rl_trainer.train_step(session_id="test-session")

    assert result.success is True
    assert "loss" in result.output or "q_value" in result.output


@pytest.mark.asyncio
async def test_get_action(rl_trainer):
    """Test getting action from trained model."""
    # Create session
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    # Get action
    result = await rl_trainer.get_action(
        session_id="test-session", state=[0.5, 0.3], explore=True
    )

    assert result.success is True
    assert "action" in result.output
    assert 0 <= result.output["action"] < 2


@pytest.mark.asyncio
async def test_exploration_vs_exploitation(rl_trainer):
    """Test exploration vs exploitation."""
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    # Exploration mode
    explore_result = await rl_trainer.get_action(
        session_id="test-session", state=[0.5, 0.3], explore=True
    )
    assert explore_result.success is True

    # Exploitation mode
    exploit_result = await rl_trainer.get_action(
        session_id="test-session", state=[0.5, 0.3], explore=False
    )
    assert exploit_result.success is True


@pytest.mark.asyncio
async def test_different_algorithms():
    """Test creating sessions with different algorithms."""
    algorithms = [
        RLAlgorithm.Q_LEARNING,
        RLAlgorithm.SARSA,
        RLAlgorithm.DQN,
        RLAlgorithm.POLICY_GRADIENT,
        RLAlgorithm.A2C,
        RLAlgorithm.PPO,
    ]

    for algo in algorithms:
        config = RLTrainingConfig(default_algorithm=algo)
        trainer = RLTrainingCapability(config)

        result = await trainer.create_session(
            name=f"session-{algo}", algorithm=algo, state_dim=4, action_dim=2
        )

        assert result.success is True
        assert result.output["algorithm"] == algo


@pytest.mark.asyncio
async def test_save_and_load_model(rl_trainer):
    """Test saving and loading trained model."""
    # Create session and train
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    for i in range(5):
        await rl_trainer.record_experience(
            session_id="test-session",
            state=[0.1 * i, 0.2 * i],
            action_taken=i % 2,
            reward=1.0,
            next_state=[0.1 * (i + 1), 0.2 * (i + 1)],
            done=False,
        )

    await rl_trainer.train_step(session_id="test-session")

    # Save model
    save_result = await rl_trainer.save_model(
        session_id="test-session", path="/tmp/test_model"
    )
    assert save_result.success is True

    # Load model
    load_result = await rl_trainer.load_model(
        session_id="test-session", path="/tmp/test_model"
    )
    assert load_result.success is True


@pytest.mark.asyncio
async def test_get_training_stats(rl_trainer):
    """Test getting training statistics."""
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    # Add experiences
    for i in range(5):
        await rl_trainer.record_experience(
            session_id="test-session",
            state=[0.1, 0.2],
            action_taken=0,
            reward=1.0,
            next_state=[0.2, 0.3],
            done=False,
        )

    result = await rl_trainer.get_stats(session_id="test-session")

    assert result.success is True
    assert "total_experiences" in result.output
    assert result.output["total_experiences"] == 5


@pytest.mark.asyncio
async def test_episode_tracking(rl_trainer):
    """Test tracking episodes."""
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    # Episode 1
    await rl_trainer.record_experience(
        session_id="test-session",
        state=[0.1, 0.2],
        action_taken=0,
        reward=1.0,
        next_state=[0.2, 0.3],
        done=True,  # Episode ends
    )

    # Episode 2
    await rl_trainer.record_experience(
        session_id="test-session",
        state=[0.0, 0.0],
        action_taken=1,
        reward=0.5,
        next_state=[0.1, 0.1],
        done=False,
    )

    result = await rl_trainer.get_stats(session_id="test-session")
    assert result.success is True


@pytest.mark.asyncio
async def test_reward_tracking(rl_trainer):
    """Test tracking cumulative rewards."""
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    rewards = [1.0, 0.5, -0.5, 2.0, 0.0]

    for i, reward in enumerate(rewards):
        await rl_trainer.record_experience(
            session_id="test-session",
            state=[0.1 * i, 0.2 * i],
            action_taken=0,
            reward=reward,
            next_state=[0.1 * (i + 1), 0.2 * (i + 1)],
            done=False,
        )

    result = await rl_trainer.get_stats(session_id="test-session")
    assert result.success is True
    assert "total_experiences" in result.output


@pytest.mark.asyncio
async def test_update_hyperparameters(rl_trainer):
    """Test updating training hyperparameters."""
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    result = await rl_trainer.update_hyperparameters(
        session_id="test-session", learning_rate=0.01, epsilon=0.1
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_reset_session(rl_trainer):
    """Test resetting a training session."""
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    # Add experiences
    await rl_trainer.record_experience(
        session_id="test-session",
        state=[0.1, 0.2],
        action_taken=0,
        reward=1.0,
        next_state=[0.2, 0.3],
        done=False,
    )

    # Reset
    result = await rl_trainer.reset_session(session_id="test-session")
    assert result.success is True

    # Check stats after reset
    stats = await rl_trainer.get_stats(session_id="test-session")
    assert stats.data["total_experiences"] == 0


@pytest.mark.asyncio
async def test_delete_session(rl_trainer):
    """Test deleting a training session."""
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.Q_LEARNING, state_dim=2, action_dim=2
    )

    result = await rl_trainer.delete_session(session_id="test-session")
    assert result.success is True

    # Trying to get stats should fail
    stats_result = await rl_trainer.get_stats(session_id="test-session")
    assert stats_result.success is False


@pytest.mark.asyncio
async def test_list_sessions(rl_trainer):
    """Test listing all training sessions."""
    # Create multiple sessions
    for i in range(3):
        await rl_trainer.create_session(
            name=f"session-{i}",
            algorithm=RLAlgorithm.Q_LEARNING,
            state_dim=2,
            action_dim=2,
        )

    result = await rl_trainer.list_sessions()

    assert result.success is True
    assert len(result.output["sessions"]) == 3


@pytest.mark.asyncio
async def test_continuous_action_space(rl_trainer):
    """Test with continuous action space."""
    await rl_trainer.create_session(
        name="test-session",
        algorithm=RLAlgorithm.PPO,  # PPO handles continuous actions
        state_dim=4,
        action_dim=2,
        continuous_actions=True,
    )

    result = await rl_trainer.get_action(
        session_id="test-session", state=[0.1, 0.2, 0.3, 0.4], explore=True
    )

    assert result.success is True
    assert "action" in result.output


@pytest.mark.asyncio
async def test_batch_training(rl_trainer):
    """Test batch training."""
    await rl_trainer.create_session(
        name="test-session", algorithm=RLAlgorithm.DQN, state_dim=2, action_dim=2
    )

    # Add batch of experiences
    for i in range(32):  # Typical batch size
        await rl_trainer.record_experience(
            session_id="test-session",
            state=[0.1 * i, 0.2 * i],
            action_taken=i % 2,
            reward=1.0 if i % 2 == 0 else -1.0,
            next_state=[0.1 * (i + 1), 0.2 * (i + 1)],
            done=i % 10 == 0,
        )

    # Batch train
    result = await rl_trainer.train_batch(session_id="test-session", batch_size=16)

    assert result.success is True
