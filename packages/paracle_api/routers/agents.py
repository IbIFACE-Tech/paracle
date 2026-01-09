"""Agent discovery API router.

Provides REST endpoints for agent introspection and manifest generation:
- GET /agents - List all discovered agents
- GET /agents/{agent_id} - Get agent metadata
- GET /agents/{agent_id}/spec - Get agent specification content
- GET /manifest - Get manifest as JSON
- POST /manifest - Generate and write manifest.yaml
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from paracle_core.parac.agent_discovery import AgentDiscovery
from paracle_core.parac.manifest_generator import ManifestGenerator
from paracle_core.parac.state import find_parac_root

from paracle_api.schemas.agents import (
    AgentListResponse,
    AgentMetadataResponse,
    AgentSpecResponse,
    ManifestAgentEntry,
    ManifestResponse,
    ManifestWriteResponse,
)

router = APIRouter(prefix="/agents", tags=["agents"])


def get_parac_root_or_raise() -> Path:
    """Get .parac/ root or raise HTTP 404.

    Returns:
        Path to .parac/ directory.

    Raises:
        HTTPException: If .parac/ not found.
    """
    parac_root = find_parac_root()
    if parac_root is None:
        raise HTTPException(
            status_code=404,
            detail="No .parac/ directory found. Initialize with 'paracle init'.",
        )
    return parac_root


@router.get(
    "",
    response_model=AgentListResponse,
    operation_id="listAgents",
    summary="List all discovered agents",
    description="Discover and list all agents from .parac/agents/specs/",
)
async def list_agents() -> AgentListResponse:
    """List all discovered agents.

    Returns:
        List of agent metadata for all discovered agents.

    Raises:
        HTTPException: 404 if .parac/ not found.
    """
    parac_root = get_parac_root_or_raise()
    discovery = AgentDiscovery(parac_root)

    agents = discovery.discover_agents()

    return AgentListResponse(
        agents=[
            AgentMetadataResponse(
                id=agent.id,
                name=agent.name,
                role=agent.role,
                spec_file=str(agent.spec_file),
                capabilities=agent.capabilities,
                description=agent.description,
            )
            for agent in agents
        ],
        count=len(agents),
        parac_root=str(parac_root),
    )


@router.get(
    "/{agent_id}",
    response_model=AgentMetadataResponse,
    operation_id="getAgentById",
    summary="Get agent metadata by ID",
    description="Retrieve detailed metadata for a specific agent",
)
async def get_agent(agent_id: str) -> AgentMetadataResponse:
    """Get agent metadata by ID.

    Args:
        agent_id: Agent identifier (filename without extension).

    Returns:
        Agent metadata.

    Raises:
        HTTPException: 404 if agent not found or .parac/ not found.
    """
    parac_root = get_parac_root_or_raise()
    discovery = AgentDiscovery(parac_root)

    agent = discovery.get_agent(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found.",
        )

    return AgentMetadataResponse(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        spec_file=str(agent.spec_file),
        capabilities=agent.capabilities,
        description=agent.description,
    )


@router.get(
    "/{agent_id}/spec",
    response_model=AgentSpecResponse,
    operation_id="getAgentSpec",
    summary="Get agent specification",
)
async def get_agent_spec(agent_id: str) -> AgentSpecResponse:
    """Get agent specification content.

    Args:
        agent_id: Agent identifier (filename without extension).

    Returns:
        Full agent specification with metadata.

    Raises:
        HTTPException: 404 if agent not found or .parac/ not found.
    """
    parac_root = get_parac_root_or_raise()
    discovery = AgentDiscovery(parac_root)

    agent = discovery.get_agent(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found.",
        )

    content = discovery.get_agent_spec_content(agent_id)
    if content is None:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read specification for agent '{agent_id}'.",
        )

    return AgentSpecResponse(
        agent_id=agent.id,
        spec_file=str(agent.spec_file),
        content=content,
        metadata=AgentMetadataResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role,
            spec_file=str(agent.spec_file),
            capabilities=agent.capabilities,
            description=agent.description,
        ),
    )


@router.get(
    "/manifest",
    response_model=ManifestResponse,
    tags=["manifest"],
    operation_id="getManifest",
    summary="Get agent manifest",
)
async def get_manifest() -> ManifestResponse:
    """Get manifest as JSON.

    Generates manifest in memory without writing to disk.

    Returns:
        Manifest with all discovered agents.

    Raises:
        HTTPException: 404 if .parac/ not found.
    """
    parac_root = get_parac_root_or_raise()
    generator = ManifestGenerator(parac_root)

    manifest_data = generator.generate_manifest()

    return ManifestResponse(
        schema_version=manifest_data["schema_version"],
        generated_at=manifest_data["generated_at"],
        workspace_root=manifest_data["workspace"]["root"],
        parac_root=manifest_data["workspace"]["parac_root"],
        agents=[ManifestAgentEntry(**agent) for agent in manifest_data["agents"]],
        count=len(manifest_data["agents"]),
    )


@router.post(
    "/manifest",
    response_model=ManifestWriteResponse,
    tags=["manifest"],
    operation_id="writeManifest",
    summary="Write agent manifest to file",
)
async def write_manifest(
    force: bool = Query(
        default=False,
        description="Force overwrite even if manifest exists",
    )
) -> ManifestWriteResponse:
    """Generate and write manifest.yaml.

    Creates .parac/manifest.yaml with all discovered agents.

    Args:
        force: Force overwrite even if manifest exists.

    Returns:
        Write operation result with manifest path and agent count.

    Raises:
        HTTPException: 404 if .parac/ not found.
    """
    parac_root = get_parac_root_or_raise()
    generator = ManifestGenerator(parac_root)

    manifest_path = parac_root / "manifest.yaml"

    # Check if manifest exists
    if manifest_path.exists() and not force:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Manifest already exists at {manifest_path}. "
                "Use ?force=true to overwrite."
            ),
        )

    generator.write_manifest()

    # Get count from manifest
    manifest_data = generator.generate_manifest()

    return ManifestWriteResponse(
        success=True,
        manifest_path=str(manifest_path),
        agents_count=len(manifest_data["agents"]),
    )
