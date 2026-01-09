"""WebSocket transport for MCP (remote connections)."""

import asyncio
import json
import logging
from typing import Any

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class WebSocketTransport:
    """WebSocket transport for remote MCP connections.

    This transport enables MCP communication over WebSocket,
    which works better for remote connections than stdio.

    Supports JWT authentication for secure connections.

    Example:
        ```python
        transport = WebSocketTransport(
            url="ws://remote-server.com:8001/mcp",
            auth_token="jwt-token-here"
        )

        async with transport:
            response = await transport.send_request({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            })
        ```
    """

    def __init__(self, url: str, auth_token: str | None = None):
        """Initialize WebSocket transport.

        Args:
            url: WebSocket URL (ws:// or wss://).
            auth_token: Optional JWT authentication token.
        """
        self.url = url
        self.auth_token = auth_token
        self.ws: WebSocketClientProtocol | None = None
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._receive_task: asyncio.Task | None = None

    async def connect(self) -> None:
        """Connect to remote MCP server via WebSocket.

        Raises:
            ConnectionError: If connection fails.
        """
        try:
            # Build headers
            headers: dict[str, str] = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            # Connect
            logger.info(f"Connecting to MCP WebSocket: {self.url}")
            self.ws = await websockets.connect(self.url, extra_headers=headers)
            logger.info("WebSocket connection established")

            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self.url}: {e}") from e

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._receive_task is not None:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self.ws is not None:
            await self.ws.close()
            logger.info("WebSocket connection closed")
            self.ws = None

    async def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send MCP request and await response.

        Args:
            request: JSON-RPC request.

        Returns:
            dict: JSON-RPC response.

        Raises:
            RuntimeError: If not connected.
            TimeoutError: If request times out.
        """
        if self.ws is None:
            raise RuntimeError("WebSocket not connected")

        # Assign request ID if not present
        if "id" not in request:
            self._request_id += 1
            request["id"] = self._request_id

        request_id = request["id"]

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            # Send request
            await self.ws.send(json.dumps(request))
            logger.debug(f"Sent request {request_id}: {request.get('method')}")

            # Wait for response (with timeout)
            response = await asyncio.wait_for(future, timeout=30.0)
            return response

        except asyncio.TimeoutError:
            logger.error(f"Request {request_id} timed out")
            raise TimeoutError(f"Request {request_id} timed out after 30s")
        finally:
            # Clean up pending request
            self._pending_requests.pop(request_id, None)

    async def _receive_loop(self) -> None:
        """Receive messages from WebSocket and dispatch to pending requests."""
        try:
            async for message in self.ws:
                try:
                    response = json.loads(message)
                    request_id = response.get("id")

                    if request_id in self._pending_requests:
                        future = self._pending_requests[request_id]
                        if not future.done():
                            future.set_result(response)
                    else:
                        logger.warning(
                            f"Received response for unknown request: {request_id}"
                        )

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket receive loop error: {e}")

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()
