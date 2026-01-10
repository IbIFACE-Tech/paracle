"""MCP Server exposing Paracle tools.

This module provides a Model Context Protocol (MCP) server that exposes
all Paracle tools to IDEs and AI assistants. Supports both stdio and HTTP transports.

Tool sources:
- Built-in agent tools from agent_tool_registry
- Custom Python tools from .parac/tools/custom/
- External MCP servers from .parac/tools/mcp/mcp.yaml or mcp.json
- Context, workflow, and memory tools

MCP Specification: https://modelcontextprotocol.io/
"""

import asyncio
import importlib.util
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from paracle_mcp.api_bridge import TOOL_API_MAPPINGS, MCPAPIBridge

# Import IDE tools
try:
    from paracle_tools.ide_tools import (
        IDE_TOOLS,
        IDECommandError,
        IDENotFoundError,
    )
    IDE_TOOLS_AVAILABLE = True
except ImportError:
    IDE_TOOLS = []
    IDE_TOOLS_AVAILABLE = False

logger = logging.getLogger("paracle.mcp.server")


@dataclass
class ExternalMCPServer:
    """Configuration for an external MCP server."""

    id: str
    name: str
    description: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    tools_prefix: str = ""
    enabled: bool = True
    _process: subprocess.Popen | None = field(default=None, repr=False)
    _tools: list[dict] = field(default_factory=list, repr=False)


@dataclass
class CustomTool:
    """Configuration for a custom Python tool."""

    name: str
    description: str
    file: str
    parameters: dict = field(default_factory=dict)
    _module: Any = field(default=None, repr=False)


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

    def __init__(self, parac_root: Path | None = None, api_base_url: str = "http://localhost:8000"):
        """Initialize the MCP server.

        Args:
            parac_root: Path to .parac/ directory (auto-detected if not provided)
            api_base_url: Base URL for REST API (for API bridge)
        """
        self.parac_root = parac_root or self._find_parac_root()
        self.tools = self._load_all_tools()
        self.custom_tools: list[CustomTool] = []
        self.external_mcp_servers: list[ExternalMCPServer] = []
        self.active_agent: str | None = None

        # Initialize API bridge (ADR-022: MCP Full Coverage)
        self.api_bridge = MCPAPIBridge(
            api_base_url=api_base_url,
            timeout=30.0,
            enable_fallback=True
        )
        self.api_tools: list[dict] = []  # Tools from OpenAPI

        # Load user-defined tools from .parac/tools/
        if self.parac_root:
            self._load_custom_tools()
            self._load_external_mcp_servers()

        # Load API tools from OpenAPI if API available
        self._load_api_tools()

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
            logger.info(
                f"Loaded {len(all_tools)} tools from agent_tool_registry")
        except ImportError as e:
            logger.warning(f"Could not import agent_tool_registry: {e}")

        return all_tools

    def _load_custom_tools(self) -> None:
        """Load custom Python tools from .parac/tools/custom/.

        Custom tools are Python files with an execute() function and metadata.
        """
        if not self.parac_root:
            return

        custom_dir = self.parac_root / "tools" / "custom"
        if not custom_dir.exists():
            return

        # Also check registry.yaml for custom tool definitions
        registry_path = self.parac_root / "tools" / "registry.yaml"
        custom_defs = {}
        if registry_path.exists():
            with open(registry_path, encoding="utf-8") as f:
                registry = yaml.safe_load(f) or {}
                for tool_def in registry.get("custom", []):
                    if tool_def.get("name"):
                        custom_defs[tool_def["name"]] = tool_def

        # Load Python tools from custom directory
        for py_file in custom_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            tool_name = py_file.stem
            try:
                # Load module dynamically
                spec = importlib.util.spec_from_file_location(
                    tool_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Get metadata from module or registry
                    description = getattr(
                        module,
                        "DESCRIPTION",
                        custom_defs.get(tool_name, {}).get(
                            "description", f"Custom tool: {tool_name}"
                        ),
                    )
                    parameters = getattr(
                        module,
                        "PARAMETERS",
                        custom_defs.get(tool_name, {}).get("parameters", {}),
                    )

                    custom_tool = CustomTool(
                        name=tool_name,
                        description=description,
                        file=str(py_file),
                        parameters=parameters,
                        _module=module,
                    )
                    self.custom_tools.append(custom_tool)
                    logger.info(f"Loaded custom tool: {tool_name}")

            except Exception as e:
                logger.warning(f"Failed to load custom tool {tool_name}: {e}")

    def _load_external_mcp_servers(self) -> None:
        """Load external MCP server configurations from .parac/tools/mcp/.

        Supports both mcp.yaml and mcp.json formats, as well as servers.yaml.
        """
        if not self.parac_root:
            return

        mcp_dir = self.parac_root / "tools" / "mcp"
        if not mcp_dir.exists():
            return

        # Try loading from mcp.yaml, mcp.json, or servers.yaml
        config_files = [
            mcp_dir / "mcp.yaml",
            mcp_dir / "mcp.json",
            mcp_dir / "servers.yaml",
        ]

        servers_config = []
        for config_file in config_files:
            if config_file.exists():
                with open(config_file, encoding="utf-8") as f:
                    if config_file.suffix == ".json":
                        config = json.load(f)
                    else:
                        config = yaml.safe_load(f) or {}

                    # Handle different config formats
                    if "servers" in config:
                        servers_config = config["servers"]
                    elif "mcpServers" in config:
                        # VS Code format: convert to list
                        for name, srv_config in config["mcpServers"].items():
                            srv_config["id"] = name
                            srv_config["name"] = name
                            servers_config.append(srv_config)
                    break

        # Create ExternalMCPServer instances
        for srv in servers_config:
            if not srv.get("enabled", True):
                continue

            # Expand environment variables in args
            args = []
            for arg in srv.get("args", []):
                if isinstance(arg, str) and arg.startswith("${") and arg.endswith("}"):
                    env_var = arg[2:-1]
                    args.append(os.environ.get(env_var, arg))
                else:
                    args.append(arg)

            # Expand environment variables in env dict
            env = {}
            for key, val in srv.get("env", {}).items():
                if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
                    env_var = val[2:-1]
                    env[key] = os.environ.get(env_var, "")
                else:
                    env[key] = val

            server = ExternalMCPServer(
                id=srv.get("id", srv.get("name", "")),
                name=srv.get("name", srv.get("id", "")),
                description=srv.get("description", ""),
                command=srv.get("command", ""),
                args=args,
                env=env,
                tools_prefix=srv.get("tools_prefix", srv.get("id", "")),
                enabled=srv.get("enabled", True),
            )
            self.external_mcp_servers.append(server)
            logger.info(f"Loaded external MCP server: {server.id}")

    def _load_api_tools(self) -> None:
        """Load tools from REST API OpenAPI specification.

        Implements ADR-022 Phase 2: Auto-generate MCP tools from OpenAPI spec.
        This enables instant coverage of all API endpoints without manual duplication.
        """
        if not self.api_bridge.is_api_available():
            logger.warning(
                "REST API not available, skipping OpenAPI tool generation")
            return

        try:
            # Fetch OpenAPI spec from API
            response = self.api_bridge.client.get(
                f"{self.api_bridge.api_base_url}/openapi.json")
            response.raise_for_status()
            openapi_spec = response.json()

            # Generate MCP tools from OpenAPI paths
            for path, path_item in openapi_spec.get("paths", {}).items():
                for method, operation in path_item.items():
                    if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        continue

                    # Generate tool name from operationId or path
                    operation_id = operation.get("operationId")
                    if not operation_id:
                        # Generate from path and method
                        tool_name = f"paracle_api_{method}_{path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"
                    else:
                        tool_name = f"paracle_{operation_id}"

                    # Build parameter schema from OpenAPI
                    parameters = operation.get("parameters", [])
                    request_body = operation.get("requestBody", {})

                    properties = {}
                    required = []

                    # Add path/query parameters
                    for param in parameters:
                        param_name = param.get("name")
                        param_schema = param.get("schema", {})
                        properties[param_name] = {
                            "type": param_schema.get("type", "string"),
                            "description": param.get("description", "")
                        }
                        if param.get("required", False):
                            required.append(param_name)

                    # Add request body schema
                    if request_body:
                        content = request_body.get("content", {})
                        json_schema = content.get(
                            "application/json", {}).get("schema", {})
                        if json_schema.get("properties"):
                            properties.update(json_schema["properties"])
                            if json_schema.get("required"):
                                required.extend(json_schema["required"])

                    tool_schema = {
                        "name": tool_name,
                        "description": operation.get("summary", operation.get("description", f"API: {method.upper()} {path}")),
                        "inputSchema": {
                            "type": "object",
                            "properties": properties,
                            "required": required if required else None
                        }
                    }

                    self.api_tools.append(tool_schema)

            logger.info(
                f"Loaded {len(self.api_tools)} tools from OpenAPI specification")

        except Exception as e:
            logger.error(f"Failed to load API tools from OpenAPI: {e}")

    def _get_context_tools(self) -> list[dict]:
        """Get context tool schemas.

        Returns:
            List of context tool schemas
        """
        return [
            {
                "name": "context_current_state",
                "description": "Get current project state from .parac/memory/context/current_state.yaml",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "context_roadmap",
                "description": "Get project roadmap from .parac/roadmap/roadmap.yaml",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "context_decisions",
                "description": "Get architectural decisions from .parac/roadmap/decisions.md",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "context_policies",
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
                "name": "workflow_run",
                "description": "Execute a Paracle workflow",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "enum": (
                                workflows
                                if workflows
                                else [
                                    "feature_development",
                                    "bugfix",
                                    "code_review",
                                    "release",
                                ]
                            ),
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
                "name": "workflow_list",
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
                "name": "memory_log_action",
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

    def _get_ide_tools(self) -> list[dict]:
        """Get IDE tool schemas.

        Returns:
            List of IDE tool schemas for VS Code, Cursor, Windsurf, Codium integration
        """
        if not IDE_TOOLS_AVAILABLE:
            return []

        schemas = []
        for tool in IDE_TOOLS:
            # Convert parameters to JSON Schema format
            properties = {}
            required = []

            for param_name, param_def in tool.get("parameters", {}).items():
                prop = {
                    "type": param_def.get("type", "string"),
                    "description": param_def.get("description", ""),
                }
                properties[param_name] = prop

                if param_def.get("required", False):
                    required.append(param_name)

            input_schema = {
                "type": "object",
                "properties": properties,
            }
            if required:
                input_schema["required"] = required

            schemas.append({
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": input_schema,
            })

        return schemas

    def _convert_to_json_schema(self, params: dict) -> dict:
        """Convert tool parameters to JSON Schema format for MCP.

        Args:
            params: Tool parameters in Paracle format

        Returns:
            Parameters in JSON Schema format
        """
        # If already in JSON Schema format, return as-is
        if "type" in params and params.get("type") == "object":
            return params

        # If empty, return empty schema
        if not params:
            return {"type": "object", "properties": {}}

        # Convert from Paracle format to JSON Schema
        properties = {}
        required = []

        for param_name, param_def in params.items():
            if isinstance(param_def, dict):
                prop = {
                    "type": param_def.get("type", "string"),
                    "description": param_def.get("description", ""),
                }
                if "default" in param_def:
                    prop["default"] = param_def["default"]
                if "enum" in param_def:
                    prop["enum"] = param_def["enum"]
                properties[param_name] = prop

                if param_def.get("required", False):
                    required.append(param_name)

        schema = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required

        return schema

    def get_tool_schemas(self) -> list[dict]:
        """Generate MCP tool schemas for all tools.

        Returns:
            List of tool schemas in MCP format
        """
        schemas = []

        # Agent tools
        for name, tool in self.tools.items():
            description = getattr(tool, "description", f"Paracle {name} tool")
            raw_params = getattr(
                tool, "parameters", {"type": "object", "properties": {}}
            )
            input_schema = self._convert_to_json_schema(raw_params)
            schemas.append(
                {
                    "name": name,
                    "description": description,
                    "inputSchema": input_schema,
                }
            )

        # Context tools
        schemas.extend(self._get_context_tools())

        # Workflow tools
        schemas.extend(self._get_workflow_tools())

        # Memory tools
        schemas.extend(self._get_memory_tools())

        # IDE tools (VS Code, Cursor, Windsurf, Codium)
        schemas.extend(self._get_ide_tools())

        # API tools from OpenAPI (ADR-022 Phase 2)
        schemas.extend(self.api_tools)

        # Custom tools from .parac/tools/custom/
        for custom_tool in self.custom_tools:
            input_schema = self._convert_to_json_schema(custom_tool.parameters)
            schemas.append(
                {
                    "name": f"custom_{custom_tool.name}",
                    "description": custom_tool.description,
                    "inputSchema": input_schema,
                }
            )

        # External MCP server tools (placeholder schemas)
        for server in self.external_mcp_servers:
            schemas.append(
                {
                    "name": f"{server.tools_prefix}_info",
                    "description": f"{server.description} - List available tools from {server.name}",
                    "inputSchema": {"type": "object", "properties": {}},
                }
            )

        # Agent router tool
        try:
            from paracle_orchestration.agent_tool_registry import agent_tool_registry

            agent_list = agent_tool_registry.list_agents()
        except ImportError:
            agent_list = [
                "architect",
                "coder",
                "reviewer",
                "tester",
                "pm",
                "documenter",
                "releasemanager",
            ]

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
        """Handle context_* tool calls.

        Args:
            name: Tool name (context_current_state, etc.)
            _arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self.parac_root:
            return {"error": "No .parac/ directory found"}

        tool_name = name.replace("context_", "")

        if tool_name == "current_state":
            path = self.parac_root / "memory" / "context" / "current_state.yaml"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": yaml.dump(content, default_flow_style=False),
                        }
                    ]
                }
            return {"error": "current_state.yaml not found"}

        elif tool_name == "roadmap":
            path = self.parac_root / "roadmap" / "roadmap.yaml"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": yaml.dump(content, default_flow_style=False),
                        }
                    ]
                }
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
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Available policies: {', '.join(policies)}",
                            }
                        ]
                    }
                return {"error": "Policies directory not found"}

        return {"error": f"Unknown context tool: {name}"}

    async def _handle_workflow_tool(self, name: str, arguments: dict) -> dict:
        """Handle workflow_* tool calls.

        Args:
            name: Tool name (workflow_run, workflow_list)
            arguments: Tool arguments

        Returns:
            Tool result
        """
        tool_name = name.replace("workflow_", "")

        if tool_name == "list":
            if self.parac_root:
                catalog_path = self.parac_root / "workflows" / "catalog.yaml"
                if catalog_path.exists():
                    with open(catalog_path, encoding="utf-8") as f:
                        catalog = yaml.safe_load(f)
                    workflows = []
                    for wf in catalog.get("workflows", []):
                        if wf.get("status") == "active":
                            workflows.append(
                                f"- {wf['name']}: {wf.get('description', '')[:100]}"
                            )
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Available workflows:\n" + "\n".join(workflows),
                            }
                        ]
                    }
            return {"content": [{"type": "text", "text": "No workflows catalog found"}]}

        elif tool_name == "run":
            workflow_id = arguments.get("workflow_id")
            inputs = arguments.get("inputs", {})

            # Execute workflow via CLI
            try:
                cmd = [
                    sys.executable,
                    "-m",
                    "paracle_cli.main",
                    "workflow",
                    "run",
                    workflow_id,
                ]

                # Add inputs as --input key=value pairs
                for key, value in inputs.items():
                    cmd.extend(["--input", f"{key}={value}"])

                cwd = str(self.parac_root.parent) if self.parac_root else None
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    cwd=cwd,
                )

                if result.returncode == 0:
                    msg = (
                        f"✅ Workflow '{workflow_id}' completed "
                        f"successfully\n\nOutput:\n{result.stdout}"
                    )
                    return {"content": [{"type": "text", "text": msg}]}
                else:
                    msg = (
                        f"❌ Workflow '{workflow_id}' failed\n\n"
                        f"Error:\n{result.stderr}"
                    )
                    return {"content": [{"type": "text", "text": msg}], "isError": True}
            except subprocess.TimeoutExpired:
                msg = f"⏱️ Workflow '{workflow_id}' timed out " f"after 5 minutes"
                return {"content": [{"type": "text", "text": msg}], "isError": True}
            except Exception as e:
                msg = f"❌ Error executing workflow '{workflow_id}': " f"{str(e)}"
                return {"content": [{"type": "text", "text": msg}], "isError": True}

        return {"error": f"Unknown workflow tool: {name}"}

    async def _handle_memory_tool(self, name: str, arguments: dict) -> dict:
        """Handle memory_* tool calls.

        Args:
            name: Tool name (memory_log_action)
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if name == "memory_log_action":
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

            return {
                "content": [
                    {"type": "text", "text": f"Action logged: {log_entry.strip()}"}
                ]
            }

        return {"error": f"Unknown memory tool: {name}"}

    async def _handle_custom_tool(self, name: str, arguments: dict) -> dict:
        """Handle custom_* tool calls.

        Args:
            name: Tool name (custom_<tool_name>)
            arguments: Tool arguments

        Returns:
            Tool result
        """
        tool_name = name.replace("custom_", "")

        # Find the custom tool
        custom_tool = None
        for ct in self.custom_tools:
            if ct.name == tool_name:
                custom_tool = ct
                break

        if not custom_tool:
            return {"error": f"Custom tool not found: {tool_name}"}

        if not custom_tool._module:
            return {"error": f"Custom tool module not loaded: {tool_name}"}

        # Execute the tool
        try:
            execute_fn = getattr(custom_tool._module, "execute", None)
            if not execute_fn:
                return {"error": f"Custom tool {tool_name} has no execute() function"}

            if asyncio.iscoroutinefunction(execute_fn):
                result = await execute_fn(**arguments)
            else:
                result = execute_fn(**arguments)

            return {"content": [{"type": "text", "text": str(result)}]}

        except Exception as e:
            logger.exception(f"Error executing custom tool {tool_name}")
            return {"error": str(e)}

    async def _handle_ide_tool(self, name: str, arguments: dict) -> dict:
        """Handle ide_* tool calls.

        Args:
            name: Tool name (ide_open_file, ide_diff, etc.)
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not IDE_TOOLS_AVAILABLE:
            return {
                "content": [{"type": "text", "text": "IDE tools not available. Install paracle_tools package."}],
                "isError": True
            }

        # Find the tool function
        tool_func = None
        for tool in IDE_TOOLS:
            if tool["name"] == name:
                tool_func = tool["function"]
                break

        if not tool_func:
            return {"error": f"Unknown IDE tool: {name}"}

        try:
            result = tool_func(**arguments)

            if result.get("success"):
                # Format successful result
                text_parts = [f"IDE: {result.get('ide', 'unknown')}"]

                if "file" in result:
                    text_parts.append(f"File: {result['file']}")
                if "line" in result and result["line"]:
                    text_parts.append(f"Line: {result['line']}")
                if "folder" in result:
                    text_parts.append(f"Folder: {result['folder']}")
                if "extensions" in result:
                    text_parts.append(f"Extensions ({result.get('count', 0)}):")
                    for ext in result["extensions"][:20]:  # Limit to first 20
                        text_parts.append(f"  - {ext}")
                if "version_info" in result:
                    text_parts.append("Version info:")
                    for line in result["version_info"]:
                        text_parts.append(f"  {line}")

                return {"content": [{"type": "text", "text": "\n".join(text_parts)}]}
            else:
                # Format error result
                error = result.get("error", "Unknown error")
                return {"content": [{"type": "text", "text": f"Error: {error}"}], "isError": True}

        except IDENotFoundError as e:
            return {
                "content": [{"type": "text", "text": f"No IDE found: {e}"}],
                "isError": True
            }
        except IDECommandError as e:
            return {
                "content": [{"type": "text", "text": f"IDE command failed: {e}"}],
                "isError": True
            }
        except Exception as e:
            logger.exception(f"Error executing IDE tool {name}")
            return {"error": str(e)}

    async def _handle_external_mcp_tool(
        self, server: ExternalMCPServer, name: str, arguments: dict
    ) -> dict:
        """Handle external MCP server tool calls.

        Args:
            server: External MCP server configuration
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result (proxied from external server)
        """
        # Handle info tool - list available tools from this server
        if name == f"{server.tools_prefix}_info":
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"External MCP Server: {server.name}\n"
                        f"Description: {server.description}\n"
                        f"Command: {server.command} {' '.join(server.args)}\n"
                        f"Tools prefix: {server.tools_prefix}_*\n\n"
                        f"Note: To use this server, start it separately and configure your IDE.\n"
                        f"Example: {server.command} {' '.join(server.args)}",
                    }
                ]
            }

        # For other tools, we'd need to proxy to the external server
        # This is a placeholder - full proxy implementation would require
        # starting the external process and communicating via stdio
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Tool {name} is provided by external MCP server '{server.name}'.\n"
                    f"To use it, configure your IDE to connect to this server directly:\n"
                    f"  Command: {server.command}\n"
                    f"  Args: {server.args}",
                }
            ]
        }

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
                    {
                        "type": "text",
                        "text": f"Active agent set to: {self.active_agent}",
                    }
                ]
            }

        # Context tools
        if name.startswith("context_"):
            return await self._handle_context_tool(name, arguments)

        # Workflow tools
        if name.startswith("workflow_"):
            return await self._handle_workflow_tool(name, arguments)

        # Memory tools
        if name.startswith("memory_"):
            return await self._handle_memory_tool(name, arguments)

        # IDE tools (VS Code, Cursor, Windsurf, Codium)
        if name.startswith("ide_"):
            return await self._handle_ide_tool(name, arguments)

        # API bridge tools (ADR-022: Route through REST API)
        if name in TOOL_API_MAPPINGS or name.startswith("paracle_api_") or name.startswith("paracle_"):
            # Check if this tool should use API bridge
            if name in TOOL_API_MAPPINGS or any(t["name"] == name for t in self.api_tools):
                try:
                    result = await self.api_bridge.call_api_tool(name, arguments)
                    # Format result for MCP
                    if "error" in result:
                        return {"content": [{"type": "text", "text": f"Error: {result['error']}"}], "isError": True}
                    else:
                        # Convert JSON result to text
                        import json
                        text = json.dumps(result, indent=2)
                        return {"content": [{"type": "text", "text": text}]}
                except Exception as e:
                    logger.error(f"API bridge call failed for {name}: {e}")
                    # Fall through to agent tools as last resort

        # Custom tools
        if name.startswith("custom_"):
            return await self._handle_custom_tool(name, arguments)

        # External MCP server tools
        for server in self.external_mcp_servers:
            if name.startswith(f"{server.tools_prefix}_"):
                return await self._handle_external_mcp_tool(server, name, arguments)

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
                        "serverInfo": {
                            "name": "paracle-mcp",
                            "version": "1.0.1",
                            "icon": "https://raw.githubusercontent.com/IbIFACE-Tech/paracle-lite/main/assets/paracle_icon.png",
                        },
                    }
                else:
                    response = {"error": f"Unknown method: {method}"}

                result = {"jsonrpc": "2.0",
                          "id": request_id, "result": response}
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
            logger.error(
                "aiohttp not installed. Install with: pip install aiohttp")
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
                    "serverInfo": {
                        "name": "paracle-mcp",
                        "version": "1.0.1",
                        "icon": "https://raw.githubusercontent.com/IbIFACE-Tech/paracle-lite/main/assets/paracle_icon.png",
                    },
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
