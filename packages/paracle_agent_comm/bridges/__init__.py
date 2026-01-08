"""Protocol Bridges.

Bridges for integrating with external agent communication protocols:
- A2A Bridge: Connect to external A2A-compatible agents
- ACP Bridge: Connect to ACP agents (future, when A2A+ACP merger stabilizes)
"""

from paracle_agent_comm.bridges.a2a_bridge import A2ABridge

__all__ = [
    "A2ABridge",
]
