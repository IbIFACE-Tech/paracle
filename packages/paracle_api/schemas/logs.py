"""Paracle API Schemas for Logging."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ActionTypeEnum = Literal[
    "IMPLEMENTATION",
    "TEST",
    "REVIEW",
    "DOCUMENTATION",
    "DECISION",
    "PLANNING",
    "REFACTORING",
    "BUGFIX",
    "UPDATE",
    "SESSION",
    "SYNC",
    "VALIDATION",
    "INIT",
]

AgentTypeEnum = Literal[
    "PMAgent",
    "ArchitectAgent",
    "CoderAgent",
    "TesterAgent",
    "ReviewerAgent",
    "DocumenterAgent",
    "SystemAgent",
]


class LogActionRequest(BaseModel):
    """Request to log an action."""

    action: ActionTypeEnum = Field(..., description="Type of action")
    description: str = Field(..., description="Description of the action")
    agent: AgentTypeEnum = Field(
        default="SystemAgent", description="Agent performing the action"
    )
    details: dict | None = Field(default=None, description="Optional details")


class LogActionResponse(BaseModel):
    """Response after logging an action."""

    success: bool = Field(..., description="Whether logging succeeded")
    timestamp: datetime = Field(..., description="Timestamp of the log entry")
    agent: AgentTypeEnum = Field(..., description="Agent that performed the action")
    action: ActionTypeEnum = Field(..., description="Type of action logged")
    description: str = Field(..., description="Description that was logged")


class LogDecisionRequest(BaseModel):
    """Request to log a decision."""

    agent: AgentTypeEnum = Field(..., description="Agent making the decision")
    decision: str = Field(..., description="What was decided")
    rationale: str = Field(..., description="Why this decision was made")
    impact: str = Field(..., description="Expected impact of the decision")


class LogDecisionResponse(BaseModel):
    """Response after logging a decision."""

    success: bool = Field(..., description="Whether logging succeeded")
    timestamp: datetime = Field(..., description="Timestamp of the log entry")
    agent: AgentTypeEnum = Field(..., description="Agent that made the decision")
    decision: str = Field(..., description="Decision that was logged")


class RecentLogsResponse(BaseModel):
    """Response with recent log entries."""

    logs: list[str] = Field(..., description="List of log lines")
    count: int = Field(..., description="Number of logs returned")


class AgentLogsResponse(BaseModel):
    """Response with logs filtered by agent."""

    agent: AgentTypeEnum = Field(..., description="Agent that was filtered")
    logs: list[str] = Field(..., description="List of log lines for this agent")
    count: int = Field(..., description="Number of logs returned")
