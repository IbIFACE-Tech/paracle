"""
Tool management and Model Context Protocol (MCP) integration.

This package provides:
- MCP client for discovering and calling MCP-compatible tools
- Tool registry for managing available tools
- Tool integration with Paracle agents
"""

__version__ = "0.0.1"

from paracle_tools.mcp import MCPClient, MCPToolRegistry

__all__ = [
    "MCPClient",
    "MCPToolRegistry",
]
