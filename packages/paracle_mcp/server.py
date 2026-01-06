"""MCP Server exposing Paracle tools.

This module provides a Model Context Protocol (MCP) server that exposes
all Paracle tools to IDEs and AI assistants. Supports both stdio and HTTP transports.

MCP Specification: https://modelcontextprotocol.io/
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("paracle.mcp.server")


class ParacleMCPServer:
    """MCP server exposing all Paracle tools.

    Supports both stdio and HTTP transports for IDE integration.

    The server exposes:
    - Agent-specific tools from agent_tool_registry
    - Context tools (current_state, roadmap, policies, decisions)
    - Workflow tools (run, list)
    - Memory tools (log_action)
    - External MCP tools from .parac/tools/mcp/
    - Custom tools from .parac/tools/custom/
    """

    def __init__(self, parac_root: Path | None = None):
        """Initialize the MCP server.

        Args:
            parac_root: Path to .parac/ directory (auto-detected if not provided)
        """
        self.parac_root = parac_root or self._find_parac_root()
        self.tools = self._load_all_tools()
        self.active_agent: str | None = None

    def _find_parac_root(self) -> Path | None:
        """Find the .parac/ directory by walking up from cwd.

        Returns:
            Path to .parac/ or None if not found
        """
        current = Path.cwd()
        while current != current.parent:
            parac = current / ".parac"
            if parac.is_dir():
                return parac
            current = current.parent
        return None

    def _load_all_tools(self) -> dict[str, Any]:
        """Load all tools from agent_tool_registry and MCP sources.

        Returns:
            Dict mapping tool name to tool object/handler
        """
        all_tools = {}

        # Load from agent_tool_registry
        try:
            from paracle_orchestration.agent_tool_registry import agent_tool_registry

            for agent_id in agent_tool_registry.list_agents():
                agent_tools = agent_tool_registry.get_tools_for_agent(agent_id)
                all_tools.update(agent_tools)
            logger.info(f"Loaded {len(all_tools)} tools from agent_tool_registry")
        except ImportError as e:
            logger.warning(f"Could not import agent_tool_registry: {e}")

        return all_tools

    def _get_context_tools(self) -> list[dict]:
        """Get context tool schemas.

        Returns:
            List of context tool schemas
        """
        return [
            {
                "name": "context.current_state",
                "description": "Get current project state from .parac/memory/context/current_state.yaml",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "context.roadmap",
                "description": "Get project roadmap from .parac/roadmap/roadmap.yaml",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "context.decisions",
                "description": "Get architectural decisions from .parac/roadmap/decisions.md",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "context.policies",
                "description": "Get active policies from .parac/policies/",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy": {
                            "type": "string",
                            "description": "Specific policy name (CODE_STYLE, TESTING, SECURITY)",
                        }
                    },
                },
            },
        ]

    def _get_workflow_tools(self) -> list[dict]:
        """Get workflow tool schemas.

        Returns:
            List of workflow tool schemas
        """
        # Load available workflows
        workflows = []
        if self.parac_root:
            catalog_path = self.parac_root / "workflows" / "catalog.yaml"
            if catalog_path.exists():
                with open(catalog_path, encoding="utf-8") as f:
                    catalog = yaml.safe_load(f)
                    for wf in catalog.get("workflows", []):
                        if wf.get("status") == "active":
                            workflows.append(wf["name"])

        return [
            {
                "name": "workflow.run",
                "description": "Execute a Paracle workflow",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "enum": workflows if workflows else ["feature_development", "bugfix", "code_review", "release"],
                            "description": "Workflow ID to execute",
                        },
                        "inputs": {
                            "type": "object",
                            "description": "Workflow inputs",
                        },
                    },
                    "required": ["workflow_id"],
                },
            },
            {
                "name": "workflow.list",
                "description": "List available Paracle workflows",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def _get_memory_tools(self) -> list[dict]:
        """Get memory tool schemas.

        Returns:
            List of memory tool schemas
        """
        return [
            {
                "name": "memory.log_action",
                "description": "Log agent action to .parac/memory/logs/agent_actions.log",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent": {
                            "type": "string",
                            "description": "Agent ID (e.g., coder, architect)",
                        },
                        "action": {
                            "type": "string",
                            "description": "Action type (IMPLEMENTATION, TEST, REVIEW, etc.)",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the action",
                        },
                    },
                    "required": ["agent", "action", "description"],
                },
            },
        ]

    def get_tool_schemas(self) -> list[dict]:
        """Generate MCP tool schemas for all tools.

        Returns:
            List of tool schemas in MCP format
        """
        schemas = []

        # Agent tools
        for name, tool in self.tools.items():
            description = getattr(tool, "description", f"Paracle {name} tool")
            parameters = getattr(
                tool, "parameters", {"type": "object", "properties": {}}
            )
            schemas.append(
                {
                    "name": name,
                    "description": description,
                    "inputSchema": parameters,
                }
            )

        # Context tools
        schemas.extend(self._get_context_tools())

        # Workflow tools
        schemas.extend(self._get_workflow_tools())

        # Memory tools
        schemas.extend(self._get_memory_tools())

        # Agent router tool
        try:
            from paracle_orchestration.agent_tool_registry import agent_tool_registry
            agent_list = agent_tool_registry.list_agents()
        except ImportError:
            agent_list = ["architect", "coder", "reviewer", "tester", "pm", "documenter", "releasemanager"]

        schemas.append(
            {
                "name": "set_active_agent",
                "description": "Set the active Paracle agent for context-aware operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "enum": agent_list,
                            "description": "Agent ID to activate",
                        }
                    },
                    "required": ["agent_id"],
                },
            }
        )

        return schemas

    async def _handle_context_tool(self, name: str, _arguments: dict) -> dict:
        """Handle context.* tool calls.

        Args:
            name: Tool name (context.current_state, etc.)
            _arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self.parac_root:
            return {"error": "No .parac/ directory found"}

        tool_name = name.replace("context.", "")

        if tool_name == "current_state":
            path = self.parac_root / "memory" / "context" / "current_state.yaml"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                return {"content": [{"type": "text", "text": yaml.dump(content, default_flow_style=False)}]}
            return {"error": "current_state.yaml not found"}

        elif tool_name == "roadmap":
            path = self.parac_root / "roadmap" / "roadmap.yaml"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                return {"content": [{"type": "text", "text": yaml.dump(content, default_flow_style=False)}]}
            return {"error": "roadmap.yaml not found"}

        elif tool_name == "decisions":
            path = self.parac_root / "roadmap" / "decisions.md"
            if path.exists():
                content = path.read_text(encoding="utf-8")
                return {"content": [{"type": "text", "text": content}]}
            return {"error": "decisions.md not found"}

        elif tool_name == "policies":
            policy = _arguments.get("policy")
            if policy:
                path = self.parac_root / "policies" / f"{policy}.md"
                if path.exists():
                    content = path.read_text(encoding="utf-8")
                    return {"content": [{"type": "text", "text": content}]}
                return {"error": f"Policy {policy}.md not found"}
            else:
                # List all policies
                policies_dir = self.parac_root / "policies"
                if policies_dir.exists():
                    policies = [f.stem for f in policies_dir.glob("*.md")]
                    return {"content": [{"type": "text", "text": f"Available policies: {', '.join(policies)}"}]}
                return {"error": "Policies directory not found"}

        return {"error": f"Unknown context tool: {name}"}

    async def _handle_workflow_tool(self, name: str, arguments: dict) -> dict:
        """Handle workflow.* tool calls.

        Args:
            name: Tool name (workflow.run, workflow.list)
            arguments: Tool arguments

        Returns:
            Tool result
        """
        tool_name = name.replace("workflow.", "")

        if tool_name == "list":
            if self.parac_root:
                catalog_path = self.parac_root / "workflows" / "catalog.yaml"
                if catalog_path.exists():
                    with open(catalog_path, encoding="utf-8") as f:
                        catalog = yaml.safe_load(f)
                    workflows = []
                    for wf in catalog.get("workflows", []):
                        if wf.get("status") == "active":
                            workflows.append(f"- {wf['name']}: {wf.get('description', '')[:100]}")
                    return {"content": [{"type": "text", "text": "Available workflows:\n" + "\n".join(workflows)}]}
            return {"content": [{"type": "text", "text": "No workflows catalog found"}]}

        elif tool_name == "run":
            workflow_id = arguments.get("workflow_id")
            inputs = arguments.get("inputs", {})
            # TODO: Implement actual workflow execution
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Workflow '{workflow_id}' execution requested with inputs: {json.dumps(inputs)}\n"
                               f"Note: Full workflow execution not yet implemented. Use CLI: paracle workflow run {workflow_id}",
                    }
                ]
            }

        return {"error": f"Unknown workflow tool: {name}"}

    async def _handle_memory_tool(self, name: str, arguments: dict) -> dict:
        """Handle memory.* tool calls.

        Args:
            name: Tool name (memory.log_action)
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if name == "memory.log_action":
            if not self.parac_root:
                return {"error": "No .parac/ directory found"}

            agent = arguments.get("agent", "unknown")
            action = arguments.get("action", "UNKNOWN")
            description = arguments.get("description", "")

            log_path = self.parac_root / "memory" / "logs" / "agent_actions.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{agent.upper()}] [{action}] {description}\n"

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)

            return {"content": [{"type": "text", "text": f"Action logged: {log_entry.strip()}"}]}

        return {"error": f"Unknown memory tool: {name}"}

    async def handle_list_tools(self) -> dict:
        """MCP list_tools handler.

        Returns:
            Dict with tools list
        """
        return {"tools": self.get_tool_schemas()}

    async def handle_call_tool(self, name: str, arguments: dict) -> dict:
        """MCP call_tool handler.

        Args:
            name: Tool name to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        # Special router tool
        if name == "set_active_agent":
            self.active_agent = arguments.get("agent_id")
            return {
                "content": [
                    {"type": "text", "text": f"Active agent set to: {self.active_agent}"}
                ]
            }

        # Context tools
        if name.startswith("context."):
            return await self._handle_context_tool(name, arguments)

        # Workflow tools
        if name.startswith("workflow."):
            return await self._handle_workflow_tool(name, arguments)

        # Memory tools
        if name.startswith("memory."):
            return await self._handle_memory_tool(name, arguments)

        # Agent tools
        tool = self.tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}

        try:
            if asyncio.iscoroutinefunction(getattr(tool, "_execute", None)):
                result = await tool._execute(**arguments)
            elif hasattr(tool, "_execute"):
                result = tool._execute(**arguments)
            elif callable(tool):
                result = tool(**arguments)
            else:
                return {"error": f"Tool {name} is not callable"}

            return {"content": [{"type": "text", "text": str(result)}]}
        except Exception as e:
            logger.exception(f"Error executing tool {name}")
            return {"error": str(e)}

    async def _stdio_loop(self):
        """Main stdio communication loop for IDE integration."""
        logger.info("Starting MCP server (stdio transport)")

        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                request = json.loads(line)
                method = request.get("method")
                request_id = request.get("id")

                if method == "tools/list":
                    response = await self.handle_list_tools()
                elif method == "tools/call":
                    params = request.get("params", {})
                    response = await self.handle_call_tool(
                        params.get("name"), params.get("arguments", {})
                    )
                elif method == "initialize":
                    response = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "paracle-mcp", "version": "0.0.1"},
                    }
                else:
                    response = {"error": f"Unknown method: {method}"}

                result = {"jsonrpc": "2.0", "id": request_id, "result": response}
                print(json.dumps(result), flush=True)

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {e}"},
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                logger.exception("Error in stdio loop")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {e}"},
                }
                print(json.dumps(error_response), flush=True)

    def serve_stdio(self):
        """Start stdio transport for IDE integration."""
        asyncio.run(self._stdio_loop())

    def serve_http(self, port: int = 3000):
        """Start HTTP transport for debug/flexibility.

        Args:
            port: HTTP port to listen on
        """
        try:
            from aiohttp import web
        except ImportError:
            logger.error("aiohttp not installed. Install with: pip install aiohttp")
            raise

        async def handle_mcp(request):
            data = await request.json()
            method = data.get("method")

            if method == "tools/list":
                result = await self.handle_list_tools()
            elif method == "tools/call":
                params = data.get("params", {})
                result = await self.handle_call_tool(
                    params.get("name"), params.get("arguments", {})
                )
            elif method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "paracle-mcp", "version": "0.0.1"},
                }
            else:
                result = {"error": f"Unknown method: {method}"}

            return web.json_response(
                {"jsonrpc": "2.0", "id": data.get("id"), "result": result}
            )

        async def handle_health(_request):
            return web.json_response({"status": "ok", "server": "paracle-mcp"})

        app = web.Application()
        app.router.add_post("/mcp", handle_mcp)
        app.router.add_get("/health", handle_health)

        logger.info(f"Starting MCP server on http://localhost:{port}")
        web.run_app(app, port=port, print=lambda _: None)


__all__ = ["ParacleMCPServer"]
