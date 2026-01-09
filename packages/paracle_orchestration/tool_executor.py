"""Tool-enabled agent executor for agents that need system tools."""

import logging
from typing import Any

from paracle_orchestration.agent_executor import AgentExecutor
from paracle_orchestration.agent_tool_registry import agent_tool_registry

logger = logging.getLogger("paracle.orchestration.tool_executor")


class ToolEnabledAgentExecutor(AgentExecutor):
    """Agent executor with tool support.

    Extends AgentExecutor to allow agents to use their assigned tools
    based on the agent_tool_registry.
    """

    def __init__(self, agent_id: str = None, *args, **kwargs):
        """Initialize with optional agent ID.

        Args:
            agent_id: Agent ID to load tools for (e.g., 'releasemanager', 'coder')
        """
        super().__init__(*args, **kwargs)
        self.agent_id = agent_id
        self.tools = self._register_tools()

    def _register_tools(self) -> dict[str, Any]:
        """Register available tools for the agent.

        If agent_id is provided, loads agent-specific tools.
        Otherwise, loads git tools for backward compatibility.
        """
        if self.agent_id:
            tools = agent_tool_registry.get_tools_for_agent(self.agent_id)
            logger.info(f"Loaded {len(tools)} tools for agent '{self.agent_id}'")
            return tools

        # Fallback: load git tools for backward compatibility
        from paracle_tools import git_add, git_commit, git_push, git_status, git_tag

        logger.warning("No agent_id provided, loading git tools only")
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
