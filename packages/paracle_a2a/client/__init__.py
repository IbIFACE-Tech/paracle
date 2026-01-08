"""A2A Client Components.

Client for calling external A2A-compatible agents.
"""

from paracle_a2a.client.a2a_client import ParacleA2AClient
from paracle_a2a.client.discovery import AgentDiscovery
from paracle_a2a.client.streaming import StreamingHandler

__all__ = [
    "AgentDiscovery",
    "ParacleA2AClient",
    "StreamingHandler",
]
