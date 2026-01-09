"""Agent discovery API schemas.

Pydantic models for agent-related API responses.
"""

from pydantic import BaseModel, Field


class AgentMetadataResponse(BaseModel):
    """Agent metadata response model."""

    id: str = Field(
        description="Agent unique identifier (filename)",
        examples=["coder", "architect", "tester"],
    )
    name: str = Field(
        description="Agent display name", examples=["Coder Agent", "Architect Agent"]
    )
    role: str = Field(
        description="Agent primary role",
        examples=["Implementation", "Design", "Testing"],
    )
    spec_file: str = Field(
        description="Path to agent specification file",
        examples=[".parac/agents/specs/coder.md"],
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of agent capabilities",
        examples=[["code_implementation", "testing", "debugging"]],
    )
    description: str | None = Field(
        default=None,
        description="Agent description",
        examples=["Implements features following architecture"],
    )


class AgentListResponse(BaseModel):
    """Response for listing all agents."""

    agents: list[AgentMetadataResponse] = Field(description="List of discovered agents")
    count: int = Field(description="Total number of agents")
    parac_root: str = Field(description="Path to .parac/ directory")


class AgentSpecResponse(BaseModel):
    """Response for agent specification content."""

    agent_id: str = Field(description="Agent identifier")
    spec_file: str = Field(description="Path to specification file")
    content: str = Field(description="Full markdown specification content")
    metadata: AgentMetadataResponse = Field(description="Agent metadata")


class ManifestAgentEntry(BaseModel):
    """Agent entry in manifest."""

    id: str
    name: str
    role: str
    spec_file: str
    capabilities: list[str] = Field(default_factory=list)
    description: str | None = None


class ManifestResponse(BaseModel):
    """Response for manifest generation."""

    schema_version: str = Field(description="Manifest schema version")
    generated_at: str = Field(description="Generation timestamp (ISO 8601)")
    workspace_root: str = Field(description="Workspace root path")
    parac_root: str = Field(description="Path to .parac/ directory")
    agents: list[ManifestAgentEntry] = Field(description="List of discovered agents")
    count: int = Field(description="Total number of agents")


class ManifestWriteResponse(BaseModel):
    """Response for manifest write operation."""

    success: bool = Field(description="Operation success status")
    manifest_path: str = Field(description="Path to written manifest file")
    agents_count: int = Field(description="Number of agents in manifest")
