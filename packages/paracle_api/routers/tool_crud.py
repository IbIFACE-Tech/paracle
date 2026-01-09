"""Tool CRUD API router.

Provides REST endpoints for tool lifecycle management:
- POST /api/tools - Register new tool
- GET /api/tools - List tools with filters
- GET /api/tools/{tool_id} - Get tool details
- PUT /api/tools/{tool_id} - Update tool
- DELETE /api/tools/{tool_id} - Delete tool
- PUT /api/tools/{tool_id}/enable - Enable/disable tool
"""

from fastapi import APIRouter, HTTPException, Query
from paracle_domain.models import Tool
from paracle_store.tool_repository import ToolRepository

from paracle_api.schemas.tool_crud import (
    ToolCreateRequest,
    ToolDeleteResponse,
    ToolEnableRequest,
    ToolEnableResponse,
    ToolListResponse,
    ToolResponse,
    ToolUpdateRequest,
)

# Global repository instance (in-memory for now)
# TODO: Replace with dependency injection in Phase 2
_repository = ToolRepository()

router = APIRouter(prefix="/api/tools", tags=["tool_crud"])


# =============================================================================
# Helper Functions
# =============================================================================


def _tool_to_response(tool: Tool) -> ToolResponse:
    """Convert Tool to ToolResponse."""
    return ToolResponse(
        id=tool.id,
        name=tool.spec.name,
        description=tool.spec.description,
        enabled=tool.enabled,
        is_mcp=tool.spec.is_mcp,
        mcp_server=tool.spec.mcp_server,
        created_at=tool.created_at,
    )


# =============================================================================
# Tool CRUD Endpoints
# =============================================================================


@router.post(
    "",
    response_model=ToolResponse,
    status_code=201,
    operation_id="createTool",
    summary="Register a new tool",
)
async def create_tool(request: ToolCreateRequest) -> ToolResponse:
    """Register a new tool.

    Args:
        request: Tool creation request

    Returns:
        Created tool details

    Raises:
        HTTPException: 400 if spec invalid, 409 if tool already exists
    """
    # Check if tool with same name already exists
    existing = _repository.find_by_name(request.spec.name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Tool '{request.spec.name}' already exists",
        )

    try:
        tool = Tool(spec=request.spec, enabled=request.enabled)
        tool = _repository.add(tool)

        return _tool_to_response(tool)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=ToolListResponse,
    operation_id="listTools",
    summary="List tools with filters",
)
async def list_tools(
    enabled: bool | None = Query(None, description="Filter by enabled status"),
    is_mcp: bool | None = Query(None, description="Filter by MCP tools only"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> ToolListResponse:
    """List tools with optional filters.

    Args:
        enabled: Filter by enabled status (optional)
        is_mcp: Filter MCP tools only (optional)
        limit: Maximum results to return
        offset: Offset for pagination

    Returns:
        List of tools matching filters
    """
    # Start with all tools
    tools = _repository.list()

    # Apply filters
    if enabled is not None:
        if enabled:
            tools = _repository.find_enabled()
        else:
            tools = [t for t in tools if not t.enabled]

    if is_mcp is not None:
        if is_mcp:
            tools = _repository.find_mcp_tools()
        else:
            tools = [t for t in tools if not t.spec.is_mcp]

    total = len(tools)

    # Apply pagination
    tools = tools[offset : offset + limit]

    return ToolListResponse(
        tools=[_tool_to_response(t) for t in tools],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{tool_id}",
    response_model=ToolResponse,
    operation_id="getToolById",
    summary="Get tool details by ID",
)
async def get_tool(tool_id: str) -> ToolResponse:
    """Get tool details by ID.

    Args:
        tool_id: Tool identifier

    Returns:
        Tool details

    Raises:
        HTTPException: 404 if tool not found
    """
    tool = _repository.get(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_id}' not found",
        )

    return _tool_to_response(tool)


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(tool_id: str, request: ToolUpdateRequest) -> ToolResponse:
    """Update a tool's configuration.

    Only updates provided fields. Null values are ignored.

    Args:
        tool_id: Tool identifier
        request: Update request with new values

    Returns:
        Updated tool details

    Raises:
        HTTPException: 404 if tool not found
    """
    tool = _repository.get(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_id}' not found",
        )

    # Update spec fields
    spec = tool.spec
    if request.description is not None:
        spec.description = request.description
    if request.parameters is not None:
        spec.parameters = request.parameters
    if request.returns is not None:
        spec.returns = request.returns
    if request.mcp_server is not None:
        spec.mcp_server = request.mcp_server

    # Save changes
    tool = _repository.update(tool)

    return _tool_to_response(tool)


@router.delete("/{tool_id}", response_model=ToolDeleteResponse)
async def delete_tool(tool_id: str) -> ToolDeleteResponse:
    """Delete (unregister) a tool.

    Args:
        tool_id: Tool identifier

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: 404 if tool not found
    """
    tool = _repository.get(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_id}' not found",
        )

    success = _repository.delete(tool_id)

    return ToolDeleteResponse(
        success=success,
        tool_id=tool_id,
        message=f"Tool '{tool.spec.name}' deleted successfully",
    )


@router.put("/{tool_id}/enable", response_model=ToolEnableResponse)
async def enable_disable_tool(
    tool_id: str, request: ToolEnableRequest
) -> ToolEnableResponse:
    """Enable or disable a tool.

    Args:
        tool_id: Tool identifier
        request: Enable/disable request

    Returns:
        Operation result

    Raises:
        HTTPException: 404 if tool not found
    """
    tool = _repository.get(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_id}' not found",
        )

    # Update enabled status
    if request.enabled:
        _repository.enable(tool_id)
        message = f"Tool '{tool.spec.name}' enabled"
    else:
        _repository.disable(tool_id)
        message = f"Tool '{tool.spec.name}' disabled"

    # Get updated tool
    tool = _repository.get(tool_id)

    return ToolEnableResponse(
        success=True,
        tool_id=tool_id,
        enabled=tool.enabled,
        message=message,
    )
