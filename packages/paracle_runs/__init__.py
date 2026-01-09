"""Run storage and replay for Paracle.

Stores execution history for agents and workflows, including:
- Run metadata (status, duration, costs, tokens)
- Input/output data
- Generated artifacts
- Execution traces
- Logs

Enables:
- Run history tracking
- Debugging via replay
- Cost analysis
- Compliance audit trails
"""

from paracle_runs.exceptions import (
    InvalidRunMetadataError,
    ReplayError,
    RunCleanupError,
    RunLoadError,
    RunNotFoundError,
    RunQueryError,
    RunSaveError,
    RunStorageError,
)
from paracle_runs.models import AgentRunMetadata, RunStatus, WorkflowRunMetadata
from paracle_runs.replay import replay_agent_run, replay_workflow_run
from paracle_runs.storage import RunStorage, get_run_storage, set_run_storage

__version__ = "1.0.1"

__all__ = [
    # Exceptions
    "RunStorageError",
    "RunNotFoundError",
    "ReplayError",
    "RunSaveError",
    "RunLoadError",
    "RunQueryError",
    "RunCleanupError",
    "InvalidRunMetadataError",
    # Models
    "AgentRunMetadata",
    "WorkflowRunMetadata",
    "RunStatus",
    # Storage
    "RunStorage",
    "get_run_storage",
    "set_run_storage",
    # Replay
    "replay_agent_run",
    "replay_workflow_run",
]
