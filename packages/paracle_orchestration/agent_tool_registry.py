"""Agent tool registry - maps agents to their executable tools."""

import logging
from typing import Any

from paracle_tools import (
    # Architect tools
    code_analysis,
    diagram_generation,
    pattern_matching,
    # Coder tools
    code_generation,
    refactoring,
    testing,
    # Git tools (shared by coder and releasemanager)
    git_add,
    git_commit,
    git_push,
    git_status,
    git_tag,
    # Reviewer tools
    static_analysis,
    security_scan,
    code_review,
    # Tester tools
    test_generation,
    test_execution,
    coverage_analysis,
    # PM tools
    task_tracking,
    milestone_management,
    team_coordination,
    # Documenter tools
    markdown_generation,
    api_doc_generation,
    diagram_creation,
    # Release Manager tools
    version_management,
    changelog_generation,
    cicd_integration,
    package_publishing,
)

logger = logging.getLogger("paracle.orchestration.agent_tool_registry")


class AgentToolRegistry:
    """Registry mapping agents to their available tools.
    
    This provides the bridge between agent definitions in manifest.yaml
    and the actual executable tool instances.
    """

    def __init__(self):
        """Initialize the registry with agent-to-tool mappings."""
        self._registry = self._build_registry()

    def _build_registry(self) -> dict[str, dict[str, Any]]:
        """Build the agent-to-tools mapping.
        
        Maps agent IDs to dictionaries of tool names and instances.
        Tool names match those in .parac/agents/manifest.yaml.
        """
        return {
            "architect": {
                "code_analysis": code_analysis,
                "diagram_generation": diagram_generation,
                "pattern_matching": pattern_matching,
            },
            "coder": {
                "code_generation": code_generation,
                "refactoring": refactoring,
                "testing": testing,
                "git_add": git_add,
                "git_commit": git_commit,
                "git_status": git_status,
                "git_push": git_push,
                "git_tag": git_tag,
            },
            "reviewer": {
                "static_analysis": static_analysis,
                "security_scan": security_scan,
                "code_review": code_review,
            },
            "tester": {
                "test_generation": test_generation,
                "test_execution": test_execution,
                "coverage_analysis": coverage_analysis,
            },
            "pm": {
                "task_tracking": task_tracking,
                "milestone_management": milestone_management,
                "team_coordination": team_coordination,
            },
            "documenter": {
                "markdown_generation": markdown_generation,
                "api_doc_generation": api_doc_generation,
                "diagram_creation": diagram_creation,
            },
            "releasemanager": {
                "git_add": git_add,
                "git_commit": git_commit,
                "git_status": git_status,
                "git_push": git_push,
                "git_tag": git_tag,
                "version_management": version_management,
                "changelog_generation": changelog_generation,
                "cicd_integration": cicd_integration,
                "package_publishing": package_publishing,
            },
        }

    def get_tools_for_agent(self, agent_id: str) -> dict[str, Any]:
        """Get all tools available to an agent.
        
        Args:
            agent_id: Agent ID (e.g., 'architect', 'coder', 'releasemanager')
            
        Returns:
            Dictionary of tool_name -> tool_instance
        """
        tools = self._registry.get(agent_id, {})
        
        if not tools:
            logger.warning(f"No tools registered for agent: {agent_id}")
        else:
            logger.info(f"Loaded {len(tools)} tools for agent: {agent_id}")
        
        return tools

    def get_tool(self, agent_id: str, tool_name: str) -> Any | None:
        """Get a specific tool for an agent.
        
        Args:
            agent_id: Agent ID
            tool_name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        agent_tools = self.get_tools_for_agent(agent_id)
        return agent_tools.get(tool_name)

    def list_agents(self) -> list[str]:
        """List all agents with registered tools.
        
        Returns:
            List of agent IDs
        """
        return list(self._registry.keys())

    def list_tools(self, agent_id: str = None) -> dict[str, list[str]]:
        """List all tools, optionally filtered by agent.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            Dictionary of agent_id -> list of tool names
        """
        if agent_id:
            return {agent_id: list(self._registry.get(agent_id, {}).keys())}
        
        return {
            agent: list(tools.keys())
            for agent, tools in self._registry.items()
        }

    def has_tool(self, agent_id: str, tool_name: str) -> bool:
        """Check if an agent has a specific tool.
        
        Args:
            agent_id: Agent ID
            tool_name: Tool name
            
        Returns:
            True if agent has tool, False otherwise
        """
        return tool_name in self._registry.get(agent_id, {})


# Global registry instance
agent_tool_registry = AgentToolRegistry()


__all__ = ["AgentToolRegistry", "agent_tool_registry"]
