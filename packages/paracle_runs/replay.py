"""Run replay functionality."""

from typing import Any

from paracle_runs.models import AgentRunMetadata, WorkflowRunMetadata
from paracle_runs.storage import get_run_storage


def replay_agent_run(
    run_id: str,
) -> tuple[AgentRunMetadata, dict[str, Any]]:
    """Replay an agent run with the same inputs.

    Args:
        run_id: Run ID to replay

    Returns:
        Tuple of (metadata, run_data) containing all run information

    Raises:
        FileNotFoundError: If run not found

    Note:
        Full replay (re-executing the agent) requires integration
        with agent execution system. This function currently just
        loads and returns the original run data.
    """
    storage = get_run_storage()
    metadata, run_data = storage.load_agent_run(run_id)

    # TODO: Execute agent with run_data["input"]
    # This would require integrating with agent execution system
    # For now, return the original run data

    return metadata, run_data


def replay_workflow_run(
    run_id: str,
) -> tuple[WorkflowRunMetadata, dict[str, Any]]:
    """Replay a workflow run with the same inputs.

    Args:
        run_id: Run ID to replay

    Returns:
        Tuple of (metadata, run_data) containing all run information

    Raises:
        FileNotFoundError: If run not found

    Note:
        Full replay (re-executing the workflow) requires integration
        with workflow execution system. This function currently just
        loads and returns the original run data.
    """
    storage = get_run_storage()
    metadata, run_data = storage.load_workflow_run(run_id)

    # TODO: Execute workflow with run_data["inputs"]
    # This would require integrating with workflow execution system
    # For now, return the original run data

    return metadata, run_data
