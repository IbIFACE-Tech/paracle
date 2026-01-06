"""Tool-enabled agent executor for agents that need system tools."""

import logging
from pathlib import Path
from typing import Any

from paracle_orchestration.agent_executor import AgentExecutor
from paracle_tools import (
    git_add,
    git_commit,
    git_push,
    git_status,
    git_tag,
)

logger = logging.getLogger("paracle.orchestration.tool_executor")


class ToolEnabledAgentExecutor(AgentExecutor):
    """Agent executor with tool support.
    
    Extends AgentExecutor to allow agents like releasemanager to use
    git and shell tools for automation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tools = self._register_tools()

    def _register_tools(self) -> dict[str, Any]:
        """Register available tools for agents."""
        return {
            "git_add": git_add,
            "git_commit": git_commit,
            "git_status": git_status,
            "git_push": git_push,
            "git_tag": git_tag,
        }

    async def execute_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
            }

        tool = self.tools[tool_name]
        try:
            result = await tool.execute(**kwargs)
            logger.info(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }


__all__ = ["ToolEnabledAgentExecutor"]
