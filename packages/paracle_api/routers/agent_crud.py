"""Agent CRUD API router.

Provides REST endpoints for full agent lifecycle management:
- POST /api/agents - Create new agent
- GET /api/agents - List agents with filters
- GET /api/agents/{agent_id} - Get agent details
- PUT /api/agents/{agent_id} - Update agent
- DELETE /api/agents/{agent_id} - Delete agent
- PUT /api/agents/{agent_id}/status - Update agent status
- POST /api/specs - Register agent spec
- GET /api/specs - List specs
- GET /api/specs/{name} - Get spec details
- DELETE /api/specs/{name} - Delete spec
"""

from fastapi import APIRouter, HTTPException, Query
from paracle_domain.inheritance import resolve_inheritance
from paracle_domain.models import Agent, AgentSpec
from paracle_store.agent_repository import AgentRepository

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

# Global repository instance (in-memory for now)
# TODO: Replace with dependency injection in Phase 2
_repository = AgentRepository()

router = APIRouter(prefix="/api", tags=["agent_crud"])


# =============================================================================
# Helper Functions
# =============================================================================


def _agent_to_response(agent: Agent) -> AgentResponse:
    """Convert Agent to AgentResponse."""
    spec = agent.get_effective_spec()
    return AgentResponse(
        id=agent.id,
        spec_name=spec.name,
        description=spec.description,
        provider=spec.provider,
        model=spec.model,
        status=agent.status.phase,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


def _spec_to_response(spec: AgentSpec) -> SpecResponse:
    """Convert AgentSpec to SpecResponse."""
    return SpecResponse(
        name=spec.name,
        description=spec.description,
        provider=spec.provider,
        model=spec.model,
        parent=spec.parent,
        tools_count=len(spec.tools),
    )


# =============================================================================
# Agent CRUD Endpoints
# =============================================================================


@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=201,
    operation_id="createAgent",
    summary="Create a new agent",
)
async def create_agent(request: AgentCreateRequest) -> AgentResponse:
    """Create a new agent.

    Can create from an existing spec or from an inline spec.

    Args:
        request: Agent creation request

    Returns:
        Created agent details

    Raises:
        HTTPException: 404 if spec_name not found, 400 if spec invalid
    """
    try:
        if request.spec_name:
            # Create from existing spec
            spec = _repository.get_spec(request.spec_name)
            if spec is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Spec '{request.spec_name}' not found",
                )
        else:
            # Create from inline spec
            spec = request.spec
            # Register the spec for future use
            _repository.register_spec(spec)

        # Resolve inheritance if requested
        resolved_spec = None
        if request.resolve_inheritance and spec.has_parent():
            # Build spec registry for resolution
            spec_registry = {s.name: s for s in _repository.list_specs()}
            try:
                resolved_spec = resolve_inheritance(spec, spec_registry)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Inheritance resolution failed: {str(e)}",
                )

        # Create agent
        agent = Agent(spec=spec, resolved_spec=resolved_spec)
        agent = _repository.add(agent)

        return _agent_to_response(agent)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/agents",
    response_model=AgentListResponse,
    operation_id="listAgentsCrud",
    summary="List agents with filters",
)
async def list_agents(
    status: str | None = Query(None, description="Filter by status"),
    provider: str | None = Query(None, description="Filter by provider"),
    spec_name: str | None = Query(None, description="Filter by spec name"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> AgentListResponse:
    """List agents with optional filters.

    Args:
        status: Filter by status (optional)
        provider: Filter by provider (optional)
        spec_name: Filter by spec name (optional)
        limit: Maximum results to return
        offset: Offset for pagination

    Returns:
        List of agents matching filters
    """
    # Start with all agents
    agents = _repository.list()

    # Apply filters
    if status:
        from paracle_domain.models import EntityStatus

        try:
            status_enum = EntityStatus(status)
            agents = [a for a in agents if a.status.phase == status_enum]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}",
            )

    if provider:
        agents = [a for a in agents if a.get_effective_spec().provider == provider]

    if spec_name:
        agents = [a for a in agents if a.spec.name == spec_name]

    total = len(agents)

    # Apply pagination
    agents = agents[offset : offset + limit]

    return AgentListResponse(
        agents=[_agent_to_response(a) for a in agents],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    operation_id="getAgentDetails",
    summary="Get agent details by ID",
)
async def get_agent(agent_id: str) -> AgentResponse:
    """Get agent details by ID.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent details

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = _repository.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found",
        )

    return _agent_to_response(agent)


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, request: AgentUpdateRequest) -> AgentResponse:
    """Update an agent's configuration.

    Only updates provided fields. Null values are ignored.

    Args:
        agent_id: Agent identifier
        request: Update request with new values

    Returns:
        Updated agent details

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = _repository.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found",
        )

    # Update spec fields
    spec = agent.spec
    if request.description is not None:
        spec.description = request.description
    if request.temperature is not None:
        spec.temperature = request.temperature
    if request.max_tokens is not None:
        spec.max_tokens = request.max_tokens
    if request.system_prompt is not None:
        spec.system_prompt = request.system_prompt
    if request.tools is not None:
        spec.tools = request.tools
    if request.config is not None:
        spec.config = request.config
    if request.metadata is not None:
        spec.metadata = request.metadata

    # Update timestamp
    from paracle_domain.models import utc_now

    agent.updated_at = utc_now()

    # Save changes
    agent = _repository.update(agent)

    return _agent_to_response(agent)


@router.delete("/agents/{agent_id}", response_model=AgentDeleteResponse)
async def delete_agent(agent_id: str) -> AgentDeleteResponse:
    """Delete an agent.

    Args:
        agent_id: Agent identifier

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = _repository.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found",
        )

    success = _repository.delete(agent_id)

    return AgentDeleteResponse(
        success=success,
        agent_id=agent_id,
        message=f"Agent '{agent_id}' deleted successfully",
    )


@router.put("/agents/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: str, request: AgentStatusUpdateRequest
) -> AgentResponse:
    """Update agent status.

    Args:
        agent_id: Agent identifier
        request: Status update request

    Returns:
        Updated agent details

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = _repository.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found",
        )

    # Update status
    agent.update_status(
        phase=request.phase,
        message=request.message,
        error=request.error,
    )

    # Save changes
    agent = _repository.update(agent)

    return _agent_to_response(agent)


# =============================================================================
# Spec Management Endpoints
# =============================================================================


@router.post("/specs", response_model=SpecResponse, status_code=201)
async def register_spec(request: SpecRegisterRequest) -> SpecResponse:
    """Register a new agent spec.

    Args:
        request: Spec registration request

    Returns:
        Registered spec details

    Raises:
        HTTPException: 409 if spec already exists and overwrite=False
    """
    spec = request.spec

    # Check if spec already exists
    existing = _repository.get_spec(spec.name)
    if existing is not None and not request.overwrite:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Spec '{spec.name}' already exists. " "Use overwrite=true to replace."
            ),
        )

    # Register spec
    registered = _repository.register_spec(spec)

    return _spec_to_response(registered)


@router.get("/specs", response_model=SpecListResponse)
async def list_specs() -> SpecListResponse:
    """List all registered agent specs.

    Returns:
        List of all specs
    """
    specs = _repository.list_specs()

    return SpecListResponse(
        specs=[_spec_to_response(s) for s in specs],
        total=len(specs),
    )


@router.get("/specs/{name}", response_model=SpecResponse)
async def get_spec(name: str) -> SpecResponse:
    """Get spec details by name.

    Args:
        name: Spec name

    Returns:
        Spec details

    Raises:
        HTTPException: 404 if spec not found
    """
    spec = _repository.get_spec(name)
    if spec is None:
        raise HTTPException(
            status_code=404,
            detail=f"Spec '{name}' not found",
        )

    return _spec_to_response(spec)


@router.delete("/specs/{name}", response_model=AgentDeleteResponse)
async def delete_spec(name: str) -> AgentDeleteResponse:
    """Delete a spec.

    Args:
        name: Spec name

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: 404 if spec not found
    """
    spec = _repository.get_spec(name)
    if spec is None:
        raise HTTPException(
            status_code=404,
            detail=f"Spec '{name}' not found",
        )

    success = _repository.remove_spec(name)

    return AgentDeleteResponse(
        success=success,
        agent_id=name,
        message=f"Spec '{name}' deleted successfully",
    )
