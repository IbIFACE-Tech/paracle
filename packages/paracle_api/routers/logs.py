"""Paracle API Router for Logging.

API-first logging endpoints for agent and system actions.
"""

from fastapi import APIRouter, HTTPException
from paracle_core.parac.logger import ActionType, AgentLogger, AgentType
from paracle_core.parac.state import find_parac_root

from paracle_api.schemas.logs import (
    AgentLogsResponse,
    LogActionRequest,
    LogActionResponse,
    LogDecisionRequest,
    LogDecisionResponse,
    RecentLogsResponse,
)

router = APIRouter(prefix="/logs", tags=["logs"])


def get_logger_or_404() -> AgentLogger:
    """Get AgentLogger or raise 404 if no .parac/ found."""
    parac_root = find_parac_root()
    if parac_root is None:
        raise HTTPException(
            status_code=404,
            detail="No .parac/ workspace found. Run 'paracle init' first.",
        )
    return AgentLogger(parac_root)


@router.post("/action", response_model=LogActionResponse, operation_id="logAction")
def log_action(request: LogActionRequest) -> LogActionResponse:
    """Log an action.

    Records an action in .parac/memory/logs/agent_actions.log.
    """
    logger = get_logger_or_404()

    # Convert string types to enums
    agent_type = AgentType(request.agent)
    action_type = ActionType(request.action)

    entry = logger.log(
        agent=agent_type,
        action=action_type,
        description=request.description,
        details=request.details,
    )

    return LogActionResponse(
        success=True,
        timestamp=entry.timestamp,
        agent=request.agent,
        action=request.action,
        description=request.description,
    )


@router.post(
    "/decision",
    response_model=LogDecisionResponse,
    operation_id="logDecision",
)
def log_decision(request: LogDecisionRequest) -> LogDecisionResponse:
    """Log a decision.

    Records a decision in both .parac/memory/logs/decisions.log
    and .parac/memory/logs/agent_actions.log.
    """
    logger = get_logger_or_404()

    # Convert string type to enum
    agent_type = AgentType(request.agent)

    entry = logger.log_decision(
        agent=agent_type,
        decision=request.decision,
        rationale=request.rationale,
        impact=request.impact,
    )

    return LogDecisionResponse(
        success=True,
        timestamp=entry.timestamp,
        agent=request.agent,
        decision=request.decision,
    )


@router.get("/recent", response_model=RecentLogsResponse, operation_id="getRecentLogs")
def get_recent_logs(count: int = 10) -> RecentLogsResponse:
    """Get the N most recent log entries.

    Args:
        count: Number of entries to retrieve (default: 10)
    """
    logger = get_logger_or_404()

    logs = logger.get_recent_actions(count=count)

    return RecentLogsResponse(
        logs=logs,
        count=len(logs),
    )


@router.get("/today", response_model=RecentLogsResponse, operation_id="getTodayLogs")
def get_today_logs() -> RecentLogsResponse:
    """Get all log entries from today."""
    logger = get_logger_or_404()

    logs = logger.get_today_actions()

    return RecentLogsResponse(
        logs=logs,
        count=len(logs),
    )


@router.get(
    "/agent/{agent}",
    response_model=AgentLogsResponse,
    operation_id="getAgentLogs",
)
def get_agent_logs(agent: str) -> AgentLogsResponse:
    """Get all log entries for a specific agent.

    Args:
        agent: Agent name (e.g., "SystemAgent", "CoderAgent")
    """
    logger = get_logger_or_404()

    # Validate agent type
    try:
        agent_type = AgentType(agent)
    except ValueError:
        valid_agents = [a.value for a in AgentType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent: {agent}. Valid agents: {valid_agents}",
        )

    logs = logger.get_agent_actions(agent_type)

    return AgentLogsResponse(
        agent=agent,
        logs=logs,
        count=len(logs),
    )
