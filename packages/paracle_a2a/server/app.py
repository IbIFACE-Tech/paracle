"""A2A Server Application.

FastAPI application implementing A2A protocol endpoints.
"""

import json
from pathlib import Path
from typing import Any

from paracle_a2a.config import A2AServerConfig
from paracle_a2a.exceptions import (
    A2AError,
    AgentNotFoundError,
    InvalidParamsError,
    InvalidRequestError,
    MethodNotFoundError,
    TaskNotFoundError,
)
from paracle_a2a.models import (
    Message,
    Task,
    TaskIdParams,
    TaskQueryParams,
    TaskSendParams,
    agent_card_to_well_known,
    create_message,
    event_to_sse,
)
from paracle_a2a.server.agent_card_generator import AgentCardGenerator
from paracle_a2a.server.agent_executor import ParacleA2AExecutor
from paracle_a2a.server.event_queue import TaskEventQueue
from paracle_a2a.server.task_manager import TaskManager


def create_a2a_app(
    parac_root: Path | str = ".parac",
    config: A2AServerConfig | None = None,
) -> Any:
    """Create A2A FastAPI application.

    Args:
        parac_root: Path to .parac directory
        config: Server configuration

    Returns:
        FastAPI application
    """
    try:
        from fastapi import FastAPI, Request, Response
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import StreamingResponse
    except ImportError as e:
        raise ImportError(
            "FastAPI is required for A2A server. "
            "Install with: pip install paracle[api]"
        ) from e

    parac_root = Path(parac_root)
    config = config or A2AServerConfig()

    # Initialize components
    event_queue = TaskEventQueue() if config.enable_streaming else None

    task_manager = TaskManager(
        config=config,
        on_status_update=event_queue.publish_status_update if event_queue else None,
        on_artifact_update=event_queue.publish_artifact_update if event_queue else None,
    )

    executor = ParacleA2AExecutor(
        parac_root=parac_root,
        task_manager=task_manager,
        event_queue=event_queue,
    )

    card_generator = AgentCardGenerator(
        parac_root=parac_root,
        config=config,
    )

    # Create FastAPI app
    app = FastAPI(
        title="Paracle A2A Server",
        description="A2A protocol server for Paracle agents",
        version="0.1.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store references
    app.state.config = config
    app.state.task_manager = task_manager
    app.state.executor = executor
    app.state.card_generator = card_generator
    app.state.event_queue = event_queue

    # Helper functions

    def get_base_url(request: Request) -> str:
        """Get base URL from request."""
        return str(request.base_url).rstrip("/")

    def make_jsonrpc_response(
        result: Any,
        request_id: Any,
    ) -> dict[str, Any]:
        """Create JSON-RPC 2.0 response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    def make_jsonrpc_error(
        error: A2AError,
        request_id: Any,
    ) -> dict[str, Any]:
        """Create JSON-RPC 2.0 error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error.to_jsonrpc_error(),
        }

    # Agent Card endpoints

    @app.get("/.well-known/agent.json")
    async def get_root_agent_card(request: Request) -> dict[str, Any]:
        """Get root-level Agent Card."""
        base_url = get_base_url(request)
        card = card_generator.generate_root_card(base_url)
        return agent_card_to_well_known(card)

    @app.get(f"{config.base_path}/agents/{{agent_id}}/.well-known/agent.json")
    async def get_agent_card(
        agent_id: str,
        request: Request,
    ) -> dict[str, Any]:
        """Get Agent Card for specific agent."""
        base_url = get_base_url(request)
        card = card_generator.generate_card(agent_id, base_url)
        if not card:
            raise AgentNotFoundError(agent_id)
        return agent_card_to_well_known(card)

    @app.get(f"{config.base_path}/agents")
    async def list_agents(request: Request) -> dict[str, Any]:
        """List available agents."""
        base_url = get_base_url(request)
        cards = card_generator.generate_all_cards(base_url)
        return {
            "agents": [
                {"id": agent_id, "name": card.name, "description": card.description}
                for agent_id, card in cards.items()
            ]
        }

    # JSON-RPC endpoint for specific agent

    @app.post(f"{config.base_path}/agents/{{agent_id}}")
    async def jsonrpc_endpoint(
        agent_id: str,
        request: Request,
    ) -> Response:
        """JSON-RPC 2.0 endpoint for agent operations."""
        # Verify agent exists
        available = card_generator.get_available_agents()
        if agent_id not in available:
            return Response(
                content=json.dumps(
                    make_jsonrpc_error(
                        AgentNotFoundError(agent_id),
                        None,
                    )
                ),
                media_type="application/json",
                status_code=404,
            )

        # Parse request
        try:
            body = await request.json()
        except Exception:
            return Response(
                content=json.dumps(
                    make_jsonrpc_error(
                        InvalidRequestError("Invalid JSON"),
                        None,
                    )
                ),
                media_type="application/json",
                status_code=400,
            )

        # Validate JSON-RPC format
        if body.get("jsonrpc") != "2.0":
            return Response(
                content=json.dumps(
                    make_jsonrpc_error(
                        InvalidRequestError("Invalid JSON-RPC version"),
                        body.get("id"),
                    )
                ),
                media_type="application/json",
                status_code=400,
            )

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        try:
            result = await handle_method(
                agent_id=agent_id,
                method=method,
                params=params,
                request=request,
            )
            return Response(
                content=json.dumps(make_jsonrpc_response(result, request_id)),
                media_type="application/json",
            )
        except A2AError as e:
            return Response(
                content=json.dumps(make_jsonrpc_error(e, request_id)),
                media_type="application/json",
                status_code=400 if e.code > -32600 else 500,
            )

    async def handle_method(
        agent_id: str,
        method: str,
        params: dict[str, Any],
        request: Request,
    ) -> Any:
        """Handle JSON-RPC method call."""
        if method == "tasks/send":
            return await handle_tasks_send(agent_id, params)
        elif method == "tasks/get":
            return await handle_tasks_get(params)
        elif method == "tasks/list":
            return await handle_tasks_list(params)
        elif method == "tasks/cancel":
            return await handle_tasks_cancel(params)
        elif method == "tasks/sendSubscribe":
            # Would return SSE stream - handled separately
            raise MethodNotFoundError("Use GET /stream/{task_id} for streaming")
        else:
            raise MethodNotFoundError(f"Unknown method: {method}")

    async def handle_tasks_send(
        agent_id: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle tasks/send method."""
        try:
            send_params = TaskSendParams(**params)
        except Exception as e:
            raise InvalidParamsError(str(e)) from e

        # Convert message to our format
        msg_data = send_params.message
        if isinstance(msg_data, dict):
            message = Message(**msg_data)
        elif isinstance(msg_data, str):
            message = create_message(msg_data, role="user")
        else:
            message = create_message(str(msg_data), role="user")

        # Create or get task
        task = await task_manager.create_task(
            message=message,
            context_id=send_params.context_id,
            session_id=send_params.session_id,
            task_id=send_params.id,
            metadata=send_params.metadata,
        )

        # Execute task in background
        messages = await task_manager.get_task_messages(task.id)
        # Fire and forget execution
        import asyncio

        asyncio.create_task(executor.execute_task(agent_id, task, messages))

        return task_to_response(task)

    async def handle_tasks_get(params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/get method."""
        try:
            id_params = TaskIdParams(**params)
        except Exception as e:
            raise InvalidParamsError(str(e)) from e

        task = await task_manager.get_task(id_params.id)
        artifacts = await task_manager.get_task_artifacts(task.id)
        messages = await task_manager.get_task_messages(task.id)

        response = task_to_response(task)
        response["artifacts"] = [
            a.model_dump(by_alias=True, exclude_none=True) for a in artifacts
        ]
        response["messages"] = [
            m.model_dump(by_alias=True, exclude_none=True) for m in messages
        ]
        return response

    async def handle_tasks_list(params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/list method."""
        try:
            query_params = TaskQueryParams(**params)
        except Exception as e:
            raise InvalidParamsError(str(e)) from e

        tasks = await task_manager.list_tasks(
            context_id=query_params.context_id,
            session_id=query_params.session_id,
            states=query_params.states,
            limit=query_params.limit,
            offset=query_params.offset,
        )

        return {
            "tasks": [task_to_response(t) for t in tasks],
            "total": len(tasks),
        }

    async def handle_tasks_cancel(params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/cancel method."""
        try:
            id_params = TaskIdParams(**params)
        except Exception as e:
            raise InvalidParamsError(str(e)) from e

        task = await task_manager.cancel_task(id_params.id)
        return task_to_response(task)

    def task_to_response(task: Task) -> dict[str, Any]:
        """Convert Task to response dict."""
        return task.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude=(
                {"history"} if not config.enable_state_transition_history else set()
            ),
        )

    # SSE Streaming endpoint

    @app.get(f"{config.base_path}/agents/{{agent_id}}/stream/{{task_id}}")
    async def stream_task(
        agent_id: str,
        task_id: str,
        request: Request,
    ) -> StreamingResponse:
        """SSE stream for task updates."""
        if not config.enable_streaming or not event_queue:
            return Response(
                content="Streaming not enabled",
                status_code=501,
            )

        # Verify task exists
        try:
            await task_manager.get_task(task_id)
        except TaskNotFoundError:
            return Response(
                content=json.dumps({"error": "Task not found"}),
                status_code=404,
                media_type="application/json",
            )

        import uuid

        subscriber_id = str(uuid.uuid4())

        async def event_generator() -> Any:
            async for event in event_queue.subscribe(task_id, subscriber_id):
                yield event_to_sse(event)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Health check

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "protocol": "a2a", "version": "0.2.5"}

    return app


def run_a2a_server(
    parac_root: Path | str = ".parac",
    config: A2AServerConfig | None = None,
) -> None:
    """Run A2A server.

    Args:
        parac_root: Path to .parac directory
        config: Server configuration
    """
    try:
        import uvicorn
    except ImportError as e:
        raise ImportError(
            "uvicorn is required for A2A server. "
            "Install with: pip install paracle[api]"
        ) from e

    config = config or A2AServerConfig()
    app = create_a2a_app(parac_root, config)

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
    )
