"""stdio transport for MCP (existing functionality)."""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class StdioTransport:
    """Standard input/output transport for MCP.

    This is the traditional MCP transport using stdin/stdout,
    suitable for local process communication.

    Example:
        ```python
        transport = StdioTransport()
        await transport.connect()
        response = await transport.send_request({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        })
        ```
    """

    def __init__(self):
        """Initialize stdio transport."""
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        """Connect stdio streams."""
        # For stdio, streams are always available
        self.reader = asyncio.StreamReader()
        self.writer = None  # Will be set when needed

    async def disconnect(self) -> None:
        """Close stdio streams."""
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()

    async def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send MCP request via stdio.

        Args:
            request: JSON-RPC request.

        Returns:
            dict: JSON-RPC response.
        """
        # Write request to stdout
        request_json = json.dumps(request)
        print(request_json, flush=True)

        # Read response from stdin
        if self.reader is None:
            raise RuntimeError("Transport not connected")

        response_line = await self.reader.readline()
        response = json.loads(response_line.decode())

        return response

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()
