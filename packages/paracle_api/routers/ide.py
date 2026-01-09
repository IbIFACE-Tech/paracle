"""IDE integration API router.

Provides REST endpoints for IDE configuration management:
- GET /ide/list - List supported IDEs
- GET /ide/status - Get IDE integration status
- POST /ide/init - Initialize IDE configurations
- POST /ide/sync - Synchronize IDE configurations
- POST /ide/generate - Generate single IDE configuration
"""

from fastapi import APIRouter, HTTPException
from paracle_core.parac.state import find_parac_root

from paracle_api.schemas.ide import (
    IDEGenerateRequest,
    IDEGenerateResponse,
    IDEInfo,
    IDEInitRequest,
    IDEInitResponse,
    IDEInitResultItem,
    IDEListResponse,
    IDEStatusItem,
    IDEStatusResponse,
    IDESyncRequest,
    IDESyncResponse,
)

router = APIRouter(prefix="/ide", tags=["ide"])


def get_parac_root_or_raise() -> tuple:
    """Get .parac/ root or raise HTTP 404.

    Returns:
        Tuple of (parac_root, project_root).

    Raises:
        HTTPException: If .parac/ not found.
    """
    parac_root = find_parac_root()
    if parac_root is None:
        raise HTTPException(
            status_code=404,
            detail="No .parac/ directory found. Initialize with 'paracle init'.",
        )
    return parac_root, parac_root.parent


def get_generator():
    """Get IDE config generator or raise HTTP 500.

    Returns:
        IDEConfigGenerator instance.

    Raises:
        HTTPException: If jinja2 not installed.
    """
    parac_root, _ = get_parac_root_or_raise()

    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"IDE generator not available: {e}. Install jinja2.",
        )

    return IDEConfigGenerator(parac_root)


@router.get("/list", response_model=IDEListResponse, operation_id="listIDEs")
async def list_ides() -> IDEListResponse:
    """List all supported IDEs.

    Returns information about each supported IDE including
    file names and destination paths.
    """
    try:
        from paracle_core.parac.ide_generator import IDEConfigGenerator
    except ImportError:
        # Fallback if jinja2 not installed
        return IDEListResponse(
            ides=[
                IDEInfo(
                    name="cursor",
                    display_name="Cursor",
                    file_name=".cursorrules",
                    destination="./.cursorrules",
                    max_context_size=100000,
                ),
                IDEInfo(
                    name="claude",
                    display_name="Claude Code",
                    file_name="CLAUDE.md",
                    destination=".claude/CLAUDE.md",
                    max_context_size=50000,
                ),
                IDEInfo(
                    name="cline",
                    display_name="Cline",
                    file_name=".clinerules",
                    destination="./.clinerules",
                    max_context_size=50000,
                ),
                IDEInfo(
                    name="copilot",
                    display_name="GitHub Copilot",
                    file_name="copilot-instructions.md",
                    destination=".github/copilot-instructions.md",
                    max_context_size=30000,
                ),
                IDEInfo(
                    name="windsurf",
                    display_name="Windsurf",
                    file_name=".windsurfrules",
                    destination="./.windsurfrules",
                    max_context_size=50000,
                ),
            ]
        )

    # Use actual generator for accurate info
    from pathlib import Path

    generator = IDEConfigGenerator(Path(".parac"))

    ides = []
    for name, config in generator.SUPPORTED_IDES.items():
        ides.append(
            IDEInfo(
                name=name,
                display_name=config.display_name,
                file_name=config.file_name,
                destination=f"{config.destination_dir}/{config.file_name}",
                max_context_size=config.max_context_size,
            )
        )

    return IDEListResponse(ides=ides)


@router.get("/status", response_model=IDEStatusResponse, operation_id="getIDEStatus")
async def get_status() -> IDEStatusResponse:
    """Get IDE integration status.

    Returns which configurations are generated and copied.
    """
    generator = get_generator()
    status = generator.get_status()

    items = []
    for ide_name, ide_status in status["ides"].items():
        items.append(
            IDEStatusItem(
                name=ide_name,
                generated=ide_status["generated"],
                copied=ide_status["copied"],
                generated_path=ide_status["generated_path"],
                project_path=ide_status["project_path"],
            )
        )

    generated_count = sum(1 for item in items if item.generated)
    copied_count = sum(1 for item in items if item.copied)

    return IDEStatusResponse(
        parac_root=status["parac_root"],
        project_root=status["project_root"],
        ide_output_dir=status["ide_output_dir"],
        ides=items,
        generated_count=generated_count,
        copied_count=copied_count,
    )


@router.post("/init", response_model=IDEInitResponse, operation_id="initIDEConfigs")
async def init_ides(request: IDEInitRequest | None = None) -> IDEInitResponse:
    """Initialize IDE configuration files.

    Generates IDE-specific configuration files from .parac/ context
    and optionally copies them to the project root.
    """
    if request is None:
        request = IDEInitRequest()

    generator = get_generator()
    supported = generator.get_supported_ides()

    # Determine which IDEs to initialize
    if not request.ides or "all" in request.ides:
        ides_to_init = supported
    else:
        ides_to_init = [ide.lower() for ide in request.ides if ide.lower() in supported]

    if not ides_to_init:
        raise HTTPException(
            status_code=400,
            detail=f"No valid IDEs specified. Supported: {', '.join(supported)}",
        )

    # Check for existing files if not forcing
    if not request.force:
        existing = []
        for ide_name in ides_to_init:
            config = generator.get_ide_config(ide_name)
            if config:
                generated_file = generator.ide_output_dir / config.file_name
                if generated_file.exists():
                    existing.append(ide_name)

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Files exist for: {', '.join(existing)}. Use force=true.",
            )

    # Generate configs
    results = []
    manifest_path = None

    for ide_name in ides_to_init:
        result = IDEInitResultItem(ide=ide_name, generated=False, copied=False)

        try:
            # Generate to .parac/integrations/ide/
            path = generator.generate_to_file(ide_name)
            result.generated = True
            result.generated_path = str(path)

            # Copy to project root if requested
            if request.copy_to_root:
                dest = generator.copy_to_project(ide_name)
                result.copied = True
                result.project_path = str(dest)

        except Exception as e:
            result.error = str(e)

        results.append(result)

    # Generate manifest
    try:
        manifest_path = str(generator.generate_manifest())
    except Exception:
        pass

    generated_count = sum(1 for r in results if r.generated)
    copied_count = sum(1 for r in results if r.copied)
    failed_count = sum(1 for r in results if r.error is not None)

    return IDEInitResponse(
        success=failed_count == 0,
        results=results,
        generated_count=generated_count,
        copied_count=copied_count,
        failed_count=failed_count,
        manifest_path=manifest_path,
    )


@router.post("/sync", response_model=IDESyncResponse, operation_id="syncIDEConfigs")
async def sync_ides(request: IDESyncRequest | None = None) -> IDESyncResponse:
    """Synchronize IDE configs with .parac/ state.

    Regenerates all IDE configuration files from current .parac/ context.
    """
    if request is None:
        request = IDESyncRequest()

    generator = get_generator()
    errors = []

    # Generate all configs
    try:
        generated = generator.generate_all()
        synced = list(generated.keys())
    except Exception as e:
        errors.append(f"Generation failed: {e}")
        synced = []

    # Copy to project root if requested
    copied = []
    if request.copy_to_root and synced:
        try:
            copied_paths = generator.copy_all_to_project()
            copied = list(copied_paths.keys())
        except Exception as e:
            errors.append(f"Copy failed: {e}")

    # Update manifest
    try:
        generator.generate_manifest()
    except Exception:
        pass

    return IDESyncResponse(
        success=len(errors) == 0,
        synced=synced,
        copied=copied,
        errors=errors,
    )


@router.post(
    "/generate",
    response_model=IDEGenerateResponse,
    operation_id="generateIDEConfig",
)
async def generate_ide(request: IDEGenerateRequest) -> IDEGenerateResponse:
    """Generate configuration for a single IDE.

    Returns the generated content without writing to files.
    Useful for previewing or custom integrations.
    """
    generator = get_generator()

    config = generator.get_ide_config(request.ide)
    if not config:
        supported = generator.get_supported_ides()
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported IDE: {request.ide}. Supported: {', '.join(supported)}",
        )

    try:
        content = generator.generate(request.ide)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {e}",
        )

    return IDEGenerateResponse(
        ide=request.ide,
        content=content,
        size=len(content),
    )
