"""Domain models for Paracle."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AgentSpec(BaseModel):
    """Specification of an agent."""

    name: str = Field(..., description="Unique name of the agent")
    description: Optional[str] = Field(None, description="Agent description")
    provider: str = Field(...,
                          description="LLM provider (openai, anthropic, etc.)")
    model: str = Field(..., description="Model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    system_prompt: Optional[str] = Field(None, description="System prompt")
    parent: Optional[str] = Field(
        None, description="Parent agent name for inheritance")
    config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "name": "code-assistant",
                "description": "A coding assistant",
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7,
            }
        }


class AgentStatus(BaseModel):
    """Runtime status of an agent."""

    # Pending, Running, Succeeded, Failed
    phase: str = Field(default="Pending")
    message: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class Agent(BaseModel):
    """Agent instance."""

    id: str = Field(
        default_factory=lambda: f"agent_{datetime.utcnow().timestamp()}")
    spec: AgentSpec
    status: AgentStatus = Field(default_factory=AgentStatus)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowStep(BaseModel):
    """A step in a workflow."""

    id: str
    name: str
    agent_id: str
    prompt: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)


class WorkflowSpec(BaseModel):
    """Specification of a workflow."""

    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep]
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStatus(BaseModel):
    """Status of workflow execution."""

    phase: str = "Pending"
    current_step: Optional[str] = None
    progress: float = 0.0
    results: Dict[str, Any] = Field(default_factory=dict)


class Workflow(BaseModel):
    """Workflow instance."""

    id: str = Field(
        default_factory=lambda: f"workflow_{datetime.utcnow().timestamp()}")
    spec: WorkflowSpec
    status: WorkflowStatus = Field(default_factory=WorkflowStatus)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}
