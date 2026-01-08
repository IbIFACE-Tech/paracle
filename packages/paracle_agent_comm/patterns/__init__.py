"""Communication Pattern Implementations.

Provides specialized implementations for different communication patterns:
- Peer-to-peer: Direct agent-to-agent messaging
- Broadcast: All messages sent to all agents
- Coordinator: Hub-spoke pattern with designated coordinator
"""

from paracle_agent_comm.patterns.broadcast import BroadcastPattern
from paracle_agent_comm.patterns.coordinator import CoordinatorPattern
from paracle_agent_comm.patterns.peer_to_peer import PeerToPeerPattern

__all__ = [
    "PeerToPeerPattern",
    "BroadcastPattern",
    "CoordinatorPattern",
]
