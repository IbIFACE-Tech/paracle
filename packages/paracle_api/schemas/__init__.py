"""Paracle API Schemas."""

from paracle_api.schemas.agent_crud import (
    AgentCreateRequest,
    AgentDeleteResponse,
    AgentListResponse,
    AgentResponse,
    AgentStatusUpdateRequest,
    AgentUpdateRequest,
    SpecListResponse,
    SpecRegisterRequest,
    SpecResponse,
)
from paracle_api.schemas.health import HealthResponse
from paracle_api.schemas.logs import (
    AgentLogsResponse,
    LogActionRequest,
    LogActionResponse,
    LogDecisionRequest,
    LogDecisionResponse,
    RecentLogsResponse,
)
from paracle_api.schemas.parac import (
    SessionEndRequest,
    SessionEndResponse,
    SessionStartResponse,
    StatusResponse,
    SyncRequest,
    SyncResponse,
    ValidationResponse,
)
from paracle_api.schemas.tool_crud import (
    ToolCreateRequest,
    ToolDeleteResponse,
    ToolEnableRequest,
    ToolEnableResponse,
    ToolListResponse,
    ToolResponse,
    ToolUpdateRequest,
)
from paracle_api.schemas.workflow_crud import (
    WorkflowCreateRequest,
    WorkflowDeleteResponse,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdateRequest,
)

__all__ = [
    # Health
    "HealthResponse",
    # Parac
    "StatusResponse",
    "SyncRequest",
    "SyncResponse",
    "ValidationResponse",
    "SessionStartResponse",
    "SessionEndRequest",
    "SessionEndResponse",
    # Logs
    "LogActionRequest",
    "LogActionResponse",
    "LogDecisionRequest",
    "LogDecisionResponse",
    "RecentLogsResponse",
    "AgentLogsResponse",
    # Agent CRUD
    "AgentCreateRequest",
    "AgentResponse",
    "AgentUpdateRequest",
    "AgentDeleteResponse",
    "AgentListResponse",
    "AgentStatusUpdateRequest",
    "SpecRegisterRequest",
    "SpecResponse",
    "SpecListResponse",
    # Workflow CRUD
    "WorkflowCreateRequest",
    "WorkflowResponse",
    "WorkflowUpdateRequest",
    "WorkflowDeleteResponse",
    "WorkflowListResponse",
    "WorkflowExecuteRequest",
    "WorkflowExecuteResponse",
    # Tool CRUD
    "ToolCreateRequest",
    "ToolResponse",
    "ToolUpdateRequest",
    "ToolDeleteResponse",
    "ToolListResponse",
    "ToolEnableRequest",
    "ToolEnableResponse",
]
