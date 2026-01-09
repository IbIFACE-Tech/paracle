"""IDE integration API schemas.

Pydantic models for IDE configuration generation and management endpoints.
"""

from pydantic import BaseModel, Field


class IDEInfo(BaseModel):
    """Information about a supported IDE."""

    name: str = Field(description="IDE identifier (lowercase)")
    display_name: str = Field(description="Human-readable IDE name")
    file_name: str = Field(description="Configuration file name")
    destination: str = Field(description="Destination path relative to project root")
    max_context_size: int = Field(description="Maximum context size in characters")


class IDEListResponse(BaseModel):
    """Response with list of supported IDEs."""

    ides: list[IDEInfo] = Field(description="List of supported IDEs")


class IDEStatusItem(BaseModel):
    """Status of a single IDE integration."""

    name: str = Field(description="IDE name")
    generated: bool = Field(description="Whether config is in .parac/integrations/ide/")
    copied: bool = Field(description="Whether config is copied to project root")
    generated_path: str | None = Field(
        default=None, description="Path to generated file"
    )
    project_path: str | None = Field(default=None, description="Path to project file")


class IDEStatusResponse(BaseModel):
    """IDE integration status response."""

    parac_root: str = Field(description="Path to .parac/ directory")
    project_root: str = Field(description="Path to project root")
    ide_output_dir: str = Field(
        description="Path to .parac/integrations/ide/ directory"
    )
    ides: list[IDEStatusItem] = Field(description="Status for each IDE")
    generated_count: int = Field(description="Number of generated configs")
    copied_count: int = Field(description="Number of copied configs")


class IDEInitRequest(BaseModel):
    """Request to initialize IDE configurations."""

    ides: list[str] = Field(
        default_factory=list,
        description="IDEs to initialize (empty = all)",
    )
    force: bool = Field(
        default=False,
        description="Overwrite existing files",
    )
    copy_to_root: bool = Field(
        default=True,
        description="Copy to project root after generation",
    )


class IDEInitResultItem(BaseModel):
    """Result for a single IDE initialization."""

    ide: str = Field(description="IDE name")
    generated: bool = Field(description="Whether generation succeeded")
    copied: bool = Field(description="Whether copy succeeded")
    generated_path: str | None = Field(
        default=None, description="Path to generated file"
    )
    project_path: str | None = Field(default=None, description="Path to project file")
    error: str | None = Field(default=None, description="Error message if failed")


class IDEInitResponse(BaseModel):
    """Response from IDE initialization."""

    success: bool = Field(description="Whether all operations succeeded")
    results: list[IDEInitResultItem] = Field(description="Results for each IDE")
    generated_count: int = Field(description="Number successfully generated")
    copied_count: int = Field(description="Number successfully copied")
    failed_count: int = Field(description="Number of failures")
    manifest_path: str | None = Field(default=None, description="Path to manifest file")


class IDESyncRequest(BaseModel):
    """Request to synchronize IDE configurations."""

    copy_to_root: bool = Field(
        default=True,
        description="Copy to project root after generation",
    )


class IDESyncResponse(BaseModel):
    """Response from IDE sync operation."""

    success: bool = Field(description="Whether sync succeeded")
    synced: list[str] = Field(description="IDEs that were synced")
    copied: list[str] = Field(description="IDEs that were copied")
    errors: list[str] = Field(default_factory=list, description="Error messages")


class IDEGenerateRequest(BaseModel):
    """Request to generate a single IDE configuration."""

    ide: str = Field(description="IDE to generate config for")


class IDEGenerateResponse(BaseModel):
    """Response with generated IDE configuration content."""

    ide: str = Field(description="IDE name")
    content: str = Field(description="Generated configuration content")
    size: int = Field(description="Content size in characters")
