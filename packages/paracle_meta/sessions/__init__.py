"""Interactive session modes for paracle_meta.

This module provides interactive session modes for the meta-agent:
- ChatSession: Multi-turn conversation with tool use
- PlanSession: Structured task decomposition and execution
- EditSession: Structured code editing with diff previews

Example:
    >>> from paracle_meta.sessions import ChatSession, PlanSession, EditSession
    >>> from paracle_meta.capabilities.providers import AnthropicProvider
    >>> from paracle_meta.registry import CapabilityRegistry
    >>>
    >>> # Start a chat session
    >>> async with ChatSession(provider, registry) as chat:
    ...     response = await chat.send("Hello!")
    ...     print(response.content)
    >>>
    >>> # Start a planning session
    >>> async with PlanSession(provider, registry) as planner:
    ...     plan = await planner.create_plan("Build a REST API")
    ...     await planner.execute_plan(plan)
    >>>
    >>> # Start an edit session
    >>> async with EditSession(provider, registry) as editor:
    ...     edit = await editor.edit_file("main.py", "Add type hints")
    ...     print(edit.diff)  # Preview
    ...     await editor.apply(edit)  # Apply changes
"""

from paracle_meta.sessions.base import Session, SessionConfig, SessionMessage
from paracle_meta.sessions.chat import ChatConfig, ChatSession
from paracle_meta.sessions.edit import (
    EditBatch,
    EditConfig,
    EditOperation,
    EditSession,
    EditStatus,
    EditType,
)
from paracle_meta.sessions.plan import Plan, PlanConfig, PlanSession, PlanStep

__all__ = [
    # Base
    "Session",
    "SessionConfig",
    "SessionMessage",
    # Chat
    "ChatSession",
    "ChatConfig",
    # Plan
    "PlanSession",
    "PlanConfig",
    "PlanStep",
    "Plan",
    # Edit
    "EditSession",
    "EditConfig",
    "EditOperation",
    "EditBatch",
    "EditType",
    "EditStatus",
]
