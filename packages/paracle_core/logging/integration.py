"""Integration module for connecting logging with other Paracle components.

Provides automatic logging integration with:
- EventBus (paracle_events)
- API middleware (paracle_api)
- Agents (paracle_domain)
- Workflows (paracle_orchestration)
"""

import logging
import time
from collections.abc import Callable

from paracle_core.logging.audit import (
    AuditCategory,
    AuditEvent,
    AuditOutcome,
    AuditSeverity,
    get_audit_logger,
)
from paracle_core.logging.context import correlation_id, get_correlation_id
from paracle_core.logging.logger import get_logger

logger = get_logger(__name__)


def setup_eventbus_logging(event_bus=None) -> None:
    """Set up automatic logging for EventBus events.

    Subscribes to all event types and logs them appropriately.

    Args:
        event_bus: EventBus instance (if None, uses global bus)
    """
    # Import here to avoid circular imports
    try:
        from paracle_events import Event, EventType, get_event_bus
    except ImportError:
        logger.warning("paracle_events not available, skipping EventBus integration")
        return

    if event_bus is None:
        event_bus = get_event_bus()

    audit_logger = get_audit_logger()

    def log_event(event: Event) -> None:
        """Log an event from the EventBus."""
        # Map event types to audit categories
        category_map = {
            EventType.AGENT_CREATED: AuditCategory.AGENT_CREATED,
            EventType.AGENT_STARTED: AuditCategory.AGENT_STARTED,
            EventType.AGENT_COMPLETED: AuditCategory.AGENT_COMPLETED,
            EventType.AGENT_FAILED: AuditCategory.AGENT_FAILED,
            EventType.WORKFLOW_STARTED: AuditCategory.WORKFLOW_STARTED,
            EventType.WORKFLOW_COMPLETED: AuditCategory.WORKFLOW_COMPLETED,
            EventType.WORKFLOW_FAILED: AuditCategory.WORKFLOW_FAILED,
            EventType.TOOL_INVOKED: AuditCategory.AI_OUTPUT,
            EventType.TOOL_COMPLETED: AuditCategory.AI_OUTPUT,
        }

        category = category_map.get(event.type, AuditCategory.SYSTEM_STARTUP)

        # Determine outcome
        outcome = AuditOutcome.SUCCESS
        severity = AuditSeverity.INFO
        if "failed" in event.type.value.lower():
            outcome = AuditOutcome.FAILURE
            severity = AuditSeverity.HIGH

        # Create audit event
        audit_event = AuditEvent(
            category=category,
            action=event.type.value,
            actor=event.source or "system",
            actor_type="agent" if "agent" in event.type.value.lower() else "system",
            resource=event.source or "unknown",
            outcome=outcome,
            severity=severity,
            evidence=event.data,
            correlation_id=get_correlation_id(),
        )

        audit_logger.log(audit_event)

        # Also log to standard logger
        log_level = logging.ERROR if outcome == AuditOutcome.FAILURE else logging.INFO
        logger.log(
            log_level,
            f"Event: {event.type.value}",
            extra={
                "event_type": event.type.value,
                "event_source": event.source,
                "event_data": event.data,
            },
        )

    # Subscribe to all event types
    for event_type in EventType:
        event_bus.subscribe(event_type, log_event)

    logger.info("EventBus logging integration enabled")


def create_request_logging_middleware():
    """Create ASGI middleware for request logging.

    Returns:
        ASGI middleware class

    Usage:
        from fastapi import FastAPI
        app = FastAPI()
        app.add_middleware(create_request_logging_middleware())
    """

    class RequestLoggingMiddleware:
        """ASGI middleware for request logging with correlation IDs."""

        def __init__(self, app):
            self.app = app
            self.logger = get_logger("paracle.api.requests")

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                await self.app(scope, receive, send)
                return

            # Extract or generate correlation ID
            headers = dict(scope.get("headers", []))
            cid = headers.get(b"x-correlation-id", b"").decode() or None

            start_time = time.time()
            status_code = 500

            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    # Add correlation ID to response headers
                    if cid:
                        headers_list = list(message.get("headers", []))
                        headers_list.append((b"x-correlation-id", cid.encode()))
                        message["headers"] = headers_list
                await send(message)

            with correlation_id(cid):
                try:
                    await self.app(scope, receive, send_wrapper)
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    method = scope.get("method", "UNKNOWN")
                    path = scope.get("path", "/")

                    self.logger.log_request(
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        client_ip=scope.get("client", ("", 0))[0],
                    )

    return RequestLoggingMiddleware


def log_agent_execution(
    agent_name: str,
    execution_id: str | None = None,
) -> Callable:
    """Decorator for logging agent execution.

    Args:
        agent_name: Name of the agent
        execution_id: Optional execution ID

    Returns:
        Decorator function

    Usage:
        @log_agent_execution("code-reviewer")
        async def execute(self, input_data):
            ...
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()

            # Log start
            audit_logger.log_agent_action(
                agent_name=agent_name,
                action="started",
                outcome=AuditOutcome.PENDING,
                evidence={"execution_id": execution_id},
            )

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)

                # Log completion
                duration_ms = (time.time() - start_time) * 1000
                audit_logger.log_agent_action(
                    agent_name=agent_name,
                    action="completed",
                    outcome=AuditOutcome.SUCCESS,
                    evidence={
                        "execution_id": execution_id,
                        "duration_ms": duration_ms,
                    },
                )

                return result

            except Exception as e:
                # Log failure
                duration_ms = (time.time() - start_time) * 1000
                audit_logger.log_agent_action(
                    agent_name=agent_name,
                    action="failed",
                    outcome=AuditOutcome.FAILURE,
                    severity=AuditSeverity.HIGH,
                    evidence={
                        "execution_id": execution_id,
                        "duration_ms": duration_ms,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                raise

        return wrapper

    return decorator


def log_workflow_execution(workflow_name: str) -> Callable:
    """Decorator for logging workflow execution.

    Args:
        workflow_name: Name of the workflow

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()

            # Generate execution ID
            exec_id = f"wf-{int(time.time() * 1000)}"

            with correlation_id() as cid:
                # Log start
                audit_logger.log(
                    AuditEvent(
                        category=AuditCategory.WORKFLOW_STARTED,
                        action="started",
                        actor="system",
                        actor_type="workflow",
                        resource=f"workflow/{workflow_name}",
                        resource_type="workflow",
                        outcome=AuditOutcome.PENDING,
                        evidence={"execution_id": exec_id},
                        correlation_id=cid,
                    )
                )

                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)

                    # Log completion
                    duration_ms = (time.time() - start_time) * 1000
                    audit_logger.log(
                        AuditEvent(
                            category=AuditCategory.WORKFLOW_COMPLETED,
                            action="completed",
                            actor="system",
                            actor_type="workflow",
                            resource=f"workflow/{workflow_name}",
                            resource_type="workflow",
                            outcome=AuditOutcome.SUCCESS,
                            evidence={
                                "execution_id": exec_id,
                                "duration_ms": duration_ms,
                            },
                            correlation_id=cid,
                        )
                    )

                    return result

                except Exception as e:
                    # Log failure
                    duration_ms = (time.time() - start_time) * 1000
                    audit_logger.log(
                        AuditEvent(
                            category=AuditCategory.WORKFLOW_FAILED,
                            action="failed",
                            actor="system",
                            actor_type="workflow",
                            resource=f"workflow/{workflow_name}",
                            resource_type="workflow",
                            outcome=AuditOutcome.FAILURE,
                            severity=AuditSeverity.HIGH,
                            evidence={
                                "execution_id": exec_id,
                                "duration_ms": duration_ms,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                            correlation_id=cid,
                        )
                    )
                    raise

        return wrapper

    return decorator
