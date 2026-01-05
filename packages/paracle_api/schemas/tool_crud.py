"""Schemas for Tool CRUD operations.

Request and response models for creating, updating, and deleting tools.
"""

from datetime import datetime

from paracle_domain.models import ToolSpec
from pydantic import BaseModel, Field

# =============================================================================
# Tool Creation
# =============================================================================


class ToolCreateRequest(BaseModel):
    """Request to create (register) a new tool."""

    spec: ToolSpec = Field(..., description="Tool specification")
    enabled: bool = Field(default=True, description="Whether tool is enabled")


class ToolResponse(BaseModel):
    """Response containing tool details."""

    id: str = Field(..., description="Tool ID")
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    enabled: bool = Field(..., description="Whether tool is enabled")
    is_mcp: bool = Field(..., description="Is MCP tool")
    mcp_server: str | None = Field(None, description="MCP server URI")
    created_at: datetime = Field(..., description="Creation timestamp")


# =============================================================================
# Tool Update
# =============================================================================


class ToolUpdateRequest(BaseModel):
    """Request to update a tool."""

    description: str | None = Field(None, description="New description")
    parameters: dict | None = Field(None, description="Updated parameters schema")
    returns: dict | None = Field(None, description="Updated return type schema")
    mcp_server: str | None = Field(None, description="Updated MCP server URI")


# =============================================================================
# Tool Deletion
# =============================================================================


class ToolDeleteResponse(BaseModel):
    """Response for tool deletion."""

    success: bool = Field(..., description="Whether deletion succeeded")
    tool_id: str = Field(..., description="ID of deleted tool")
    message: str = Field(..., description="Deletion message")


# =============================================================================
# Tool Listing
# =============================================================================


class ToolListRequest(BaseModel):
    """Request to list tools with filters."""

    enabled: bool | None = Field(None, description="Filter by enabled status")
    is_mcp: bool | None = Field(None, description="Filter by MCP tools only")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class ToolListResponse(BaseModel):
    """Response containing list of tools."""

    tools: list[ToolResponse] = Field(..., description="List of tools")
    total: int = Field(..., description="Total count (before pagination)")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


# =============================================================================
# Tool Enable/Disable
# =============================================================================


class ToolEnableRequest(BaseModel):
    """Request to enable or disable a tool."""

    enabled: bool = Field(..., description="Whether to enable or disable")


class ToolEnableResponse(BaseModel):
    """Response for enable/disable operation."""

    success: bool = Field(..., description="Whether operation succeeded")
    tool_id: str = Field(..., description="Tool ID")
    enabled: bool = Field(..., description="New enabled status")
    message: str = Field(..., description="Operation message")
