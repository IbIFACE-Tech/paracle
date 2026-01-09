"""Remote configuration models."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TunnelConfig(BaseModel):
    """SSH tunnel configuration.

    Attributes:
        local: Local port number.
        remote: Remote port number.
        description: Human-readable tunnel description.
    """

    local: int = Field(..., ge=1, le=65535, description="Local port")
    remote: int = Field(..., ge=1, le=65535, description="Remote port")
    description: str = Field(default="", description="Tunnel description")

    @field_validator("local", "remote")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number range."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class RemoteConfig(BaseModel):
    """Configuration for a remote Paracle instance.

    Attributes:
        name: Remote profile name (e.g., "production", "staging").
        type: Transport type (currently only "ssh").
        host: SSH connection string (user@hostname).
        workspace: Path to .parac/ workspace on remote host.
        port: SSH port number (default: 22).
        identity_file: Path to SSH private key.
        tunnels: List of port tunnels to create.
    """

    name: str = Field(..., description="Remote profile name")
    type: Literal["ssh"] = Field(default="ssh", description="Transport type")
    host: str = Field(..., description="SSH connection string (user@host)")
    workspace: str = Field(..., description="Remote workspace path")
    port: int = Field(default=22, ge=1, le=65535, description="SSH port")
    identity_file: str | None = Field(
        default=None, description="Path to SSH private key"
    )
    tunnels: list[TunnelConfig] = Field(
        default_factory=list, description="Port tunnels"
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host format (user@hostname)."""
        if "@" not in v:
            raise ValueError("Host must be in format 'user@hostname'")
        return v

    @field_validator("identity_file")
    @classmethod
    def validate_identity_file(cls, v: str | None) -> str | None:
        """Validate identity file exists if provided."""
        if v is not None:
            path = Path(v).expanduser()
            if not path.exists():
                raise ValueError(f"Identity file not found: {v}")
        return v

    @property
    def username(self) -> str:
        """Extract username from host string."""
        return self.host.split("@")[0]

    @property
    def hostname(self) -> str:
        """Extract hostname from host string."""
        return self.host.split("@")[1]


class RemotesConfig(BaseModel):
    """Configuration for all remote instances.

    This is the root model for .parac/config/remotes.yaml.

    Attributes:
        remotes: Dictionary of remote profiles by name.
        default: Default remote profile name.
    """

    remotes: dict[str, RemoteConfig] = Field(
        default_factory=dict, description="Remote profiles"
    )
    default: str | None = Field(default=None, description="Default remote name")

    def get_remote(self, name: str) -> RemoteConfig:
        """Get remote configuration by name.

        Args:
            name: Remote profile name.

        Returns:
            RemoteConfig: Remote configuration.

        Raises:
            KeyError: If remote not found.
        """
        if name not in self.remotes:
            raise KeyError(f"Remote '{name}' not found in configuration")
        return self.remotes[name]

    def get_default(self) -> RemoteConfig | None:
        """Get default remote configuration.

        Returns:
            RemoteConfig | None: Default remote config or None.
        """
        if self.default is None:
            return None
        return self.get_remote(self.default)
