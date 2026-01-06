"""
Model Context Protocol (MCP) implementation.

This module provides a complete implementation of the Model Context Protocol,
enabling Paracle to discover and use MCP-compatible tools from external servers.

MCP Specification: https://modelcontextprotocol.io/
"""

from paracle_mcp.client import MCPClient
from paracle_mcp.registry import MCPToolRegistry

__all__ = [
    "MCPClient",
    "MCPToolRegistry",
]
