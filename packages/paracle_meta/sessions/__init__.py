"""Interactive session modes for paracle_meta.

This module provides interactive session modes for the meta-agent:
- ChatSession: Multi-turn conversation with tool use
- PlanSession: Structured task decomposition and execution
- EditSession: Structured code editing with diff previews

NEW in v1.5.0: ChatSession now integrates PlanSession and EditSession,
allowing seamless access to planning and editing tools from within chat mode.

Example:
    >>> from paracle_meta.sessions import ChatSession, PlanSession, EditSession
    >>> from paracle_meta.capabilities.providers import AnthropicProvider
    >>> from paracle_meta.registry import CapabilityRegistry
    >>>
    >>> # Start a chat session with planning and editing enabled (default)
    >>> async with ChatSession(provider, registry) as chat:
    ...     response = await chat.send("Hello!")
    ...     print(response.content)
    ...
    ...     # Planning tools are now available in chat
    ...     response = await chat.send("Create a plan to build a REST API")
    ...     print(response.content)  # Shows plan with steps
    ...
    ...     # Editing tools are now available in chat
    ...     response = await chat.send("Edit main.py to add type hints")
    ...     print(response.content)  # Shows diff preview
    >>>
    >>> # You can still use standalone sessions if preferred
    >>> async with PlanSession(provider, registry) as planner:
    ...     plan = await planner.create_plan("Build a REST API")
    ...     await planner.execute_plan(plan)
    >>>
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
from paracle_meta.sessions.plan import (
    Plan,
    PlanConfig,
    PlanSession,
    PlanStep,
    StepStatus,
)

__all__ = [
    # Base
    "Session",
    "SessionConfig",
    "SessionMessage",
    # Chat (now with integrated planning and editing)
    "ChatSession",
    "ChatConfig",
    # Plan
    "PlanSession",
    "PlanConfig",
    "PlanStep",
    "Plan",
    "StepStatus",
    # Edit
    "EditSession",
    "EditConfig",
    "EditOperation",
    "EditBatch",
    "EditType",
    "EditStatus",
]
