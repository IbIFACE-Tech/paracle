"""Network isolation configuration."""

from typing import Literal

from pydantic import BaseModel, Field

NetworkDriver = Literal["bridge", "overlay", "macvlan", "none"]


class NetworkPolicy(BaseModel):
    """Network access policy.

    Defines what network access is allowed from the sandbox.

    Attributes:
        allow_internet: Allow internet access
        allow_intra_network: Allow communication within sandbox network
        allowed_ports: Ports that can be accessed
        blocked_ips: IP addresses/ranges to block
        allowed_ips: IP addresses/ranges to allow (allowlist mode)
    """

    allow_internet: bool = Field(default=False, description="Allow internet access")

    allow_intra_network: bool = Field(
        default=True, description="Allow communication within network"
    )

    allowed_ports: list[int] = Field(
        default_factory=list, description="Allowed ports for outbound connections"
    )

    blocked_ips: list[str] = Field(
        default_factory=list, description="Blocked IP addresses/CIDR ranges"
    )

    allowed_ips: list[str] = Field(
        default_factory=list,
        description="Allowed IP addresses/CIDR (if set, only these allowed)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "allow_internet": False,
                    "allow_intra_network": True,
                    "allowed_ports": [80, 443],
                    "blocked_ips": ["10.0.0.0/8", "172.16.0.0/12"],
                }
            ]
        }
    }


class NetworkConfig(BaseModel):
    """Network configuration for sandbox.

    Attributes:
        driver: Docker network driver
        subnet: Network subnet (CIDR)
        gateway: Network gateway IP
        enable_ipv6: Enable IPv6
        internal: Make network internal (no external access)
        attachable: Allow manual container attachment
        labels: Network labels
        options: Driver-specific options
    """

    driver: NetworkDriver = Field(default="bridge", description="Network driver type")

    subnet: str | None = Field(
        default=None, description="Network subnet (CIDR notation)"
    )

    gateway: str | None = Field(default=None, description="Network gateway IP")

    enable_ipv6: bool = Field(default=False, description="Enable IPv6")

    internal: bool = Field(
        default=True, description="Internal network (no external routing)"
    )

    attachable: bool = Field(
        default=True, description="Allow manual container attachment"
    )

    labels: dict[str, str] = Field(
        default_factory=lambda: {"paracle.managed": "true"},
        description="Network labels",
    )

    options: dict[str, str] = Field(
        default_factory=dict, description="Driver-specific options"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "driver": "bridge",
                    "subnet": "172.28.0.0/16",
                    "gateway": "172.28.0.1",
                    "internal": True,
                    "attachable": True,
                }
            ]
        }
    }
