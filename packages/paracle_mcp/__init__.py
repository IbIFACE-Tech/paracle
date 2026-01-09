"""
Model Context Protocol (MCP) implementation.

This module provides a complete implementation of the Model Context Protocol,
enabling Paracle to discover and use MCP-compatible tools from external servers,
and exposing Paracle tools to IDEs via an MCP server.

MCP Specification: https://modelcontextprotocol.io/
"""

from paracle_mcp.api_bridge import MCPAPIBridge
from paracle_mcp.client import MCPClient
from paracle_mcp.registry import MCPToolRegistry
from paracle_mcp.server import ParacleMCPServer

__all__ = [
    "MCPAPIBridge",
    "MCPClient",
    "MCPToolRegistry",
    "ParacleMCPServer",
]
