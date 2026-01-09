"""Tool repository implementation.

Specialized repository for Tool entities.
"""

from __future__ import annotations

from paracle_domain.models import Tool, ToolSpec

from paracle_store.repository import InMemoryRepository


class ToolRepository(InMemoryRepository[Tool]):
    """Repository for Tool entities."""

    def __init__(self) -> None:
        """Initialize tool repository."""
        super().__init__(
            entity_type="Tool",
            id_getter=lambda t: t.id,
        )

    def register(self, spec: ToolSpec) -> Tool:
        """Register a tool from a spec.

        Args:
            spec: Tool specification

        Returns:
            Registered tool
        """
        tool = Tool(spec=spec)
        return self.add(tool)

    def find_by_name(self, name: str) -> Tool | None:
        """Find a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool if found, None otherwise
        """
        return self.find_one_by(lambda t: t.spec.name == name)

    def find_enabled(self) -> list[Tool]:
        """Find all enabled tools.

        Returns:
            List of enabled tools
        """
        return self.find_by(lambda t: t.enabled)

    def find_mcp_tools(self) -> list[Tool]:
        """Find all MCP tools.

        Returns:
            List of MCP tools
        """
        return self.find_by(lambda t: t.spec.is_mcp)

    def find_internal_tools(self) -> list[Tool]:
        """Find all internal (non-MCP) tools.

        Returns:
            List of internal tools
        """
        return self.find_by(lambda t: not t.spec.is_mcp)

    def find_by_mcp_server(self, server: str) -> list[Tool]:
        """Find tools by MCP server URI.

        Args:
            server: MCP server URI

        Returns:
            List of matching tools
        """
        return self.find_by(lambda t: t.spec.mcp_server == server)

    def enable(self, id: str) -> bool:
        """Enable a tool.

        Args:
            id: Tool ID

        Returns:
            True if enabled, False if not found
        """
        tool = self.get(id)
        if tool is None:
            return False
        tool.enabled = True
        self.update(tool)
        return True

    def disable(self, id: str) -> bool:
        """Disable a tool.

        Args:
            id: Tool ID

        Returns:
            True if disabled, False if not found
        """
        tool = self.get(id)
        if tool is None:
            return False
        tool.enabled = False
        self.update(tool)
        return True
