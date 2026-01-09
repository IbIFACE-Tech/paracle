"""A2A Server Components.

Exposes Paracle agents as A2A-compatible endpoints.
"""

from paracle_a2a.server.agent_card_generator import AgentCardGenerator
from paracle_a2a.server.agent_executor import ParacleA2AExecutor
from paracle_a2a.server.event_queue import EventQueue, TaskEventQueue
from paracle_a2a.server.task_manager import TaskManager

__all__ = [
    "AgentCardGenerator",
    "EventQueue",
    "ParacleA2AExecutor",
    "TaskEventQueue",
    "TaskManager",
]
