"""Paracle Transport Layer - Remote development and SSH support.

This package provides transport mechanisms for remote Paracle execution,
including SSH tunneling, WebSocket connections, and tunnel management.

Phase 8.1: Basic SSH Transport (v1.3.0)
"""

from paracle_transport.base import Transport, TransportError
from paracle_transport.remote_config import RemoteConfig, RemotesConfig, TunnelConfig
from paracle_transport.ssh import SSHTransport, SSHTunnelError
from paracle_transport.tunnel_manager import TunnelManager

__all__ = [
    "Transport",
    "TransportError",
    "SSHTransport",
    "SSHTunnelError",
    "RemoteConfig",
    "RemotesConfig",
    "TunnelConfig",
    "TunnelManager",
]

__version__ = "1.3.0"
