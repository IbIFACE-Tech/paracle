"""MCP (Model Context Protocol) exporter for skill tools.

Exports skill-bundled tools as MCP server tool definitions.
These can be used to expose Paracle tools via MCP servers.

See: https://modelcontextprotocol.io/specification/2025-06-18/schema
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from paracle_skills.exporters.base import BaseExporter, ExportResult

if TYPE_CHECKING:
    from paracle_skills.models import SkillSpec


class MCPExporter(BaseExporter):
    """Export skill tools as MCP tool definitions.

    Generates JSON files containing tool definitions compatible with
    the Model Context Protocol specification.

    Output format:
        {
            "skill": "skill-name",
            "description": "Skill description",
            "tools": [
                {
                    "name": "tool-name",
                    "description": "Tool description",
                    "inputSchema": { ... },
                    "outputSchema": { ... },
                    "annotations": { ... }
                }
            ]
        }

    Example:
        >>> exporter = MCPExporter()
        >>> result = exporter.export_skill(skill, Path("."))
        >>> print(result.output_path)  # .parac/tools/mcp/skill-name.json
    """

    @property
    def platform_name(self) -> str:
        """Return the platform identifier."""
        return "mcp"

    @property
    def output_directory(self) -> str:
        """Return the default output directory."""
        return ".parac/tools/mcp"

    def export_skill(
        self,
        skill: SkillSpec,
        output_dir: Path,
        overwrite: bool = False,
    ) -> ExportResult:
        """Export skill tools as MCP definitions.

        Creates:
            <output_dir>/.parac/tools/mcp/<skill-name>.json

        Args:
            skill: Skill specification to export
            output_dir: Root directory (typically project root)
            overwrite: Whether to overwrite existing file

        Returns:
            ExportResult with status and created files
        """
        files_created = []
        errors = []

        # Only export if skill has tools
        if not skill.tools:
            return ExportResult(
                success=True,
                platform="mcp",
                skill_name=skill.name,
                output_path=None,
                files_created=[],
                errors=["Skill has no tools to export"],
            )

        # Calculate target path
        mcp_dir = output_dir / self.output_directory
        mcp_file = mcp_dir / f"{skill.name}.json"

        try:
            self._ensure_directory(mcp_dir)

            if mcp_file.exists() and not overwrite:
                errors.append(f"MCP file already exists: {mcp_file}")
                return ExportResult(
                    success=False,
                    platform="mcp",
                    skill_name=skill.name,
                    output_path=mcp_file,
                    errors=errors,
                )

            # Generate MCP tool definitions
            mcp_content = self._generate_mcp_content(skill)

            mcp_file.write_text(
                json.dumps(mcp_content, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            files_created.append(str(mcp_file))

            return ExportResult(
                success=True,
                platform="mcp",
                skill_name=skill.name,
                output_path=mcp_file,
                files_created=files_created,
            )

        except Exception as e:
            errors.append(str(e))
            return ExportResult(
                success=False,
                platform="mcp",
                skill_name=skill.name,
                output_path=mcp_file,
                files_created=files_created,
                errors=errors,
            )

    def _generate_mcp_content(self, skill: SkillSpec) -> dict[str, Any]:
        """Generate MCP-compatible content for a skill.

        Args:
            skill: Skill specification

        Returns:
            Dictionary with skill metadata and tool definitions
        """
        return {
            "skill": skill.name,
            "description": skill.description,
            "version": skill.metadata.version,
            "tools": skill.to_mcp_tools(),
        }

    def generate_mcp_server_stub(
        self,
        skill: SkillSpec,
        output_dir: Path,
    ) -> ExportResult:
        """Generate a Python MCP server stub for the skill.

        Creates a minimal MCP server implementation that can serve
        the skill's tools.

        Args:
            skill: Skill specification
            output_dir: Directory for the server file

        Returns:
            ExportResult with status and created files
        """
        if not skill.tools:
            return ExportResult(
                success=False,
                platform="mcp",
                skill_name=skill.name,
                errors=["Skill has no tools"],
            )

        server_file = output_dir / f"{skill.name}_mcp_server.py"

        server_code = self._generate_server_code(skill)

        try:
            self._ensure_directory(output_dir)
            server_file.write_text(server_code, encoding="utf-8")

            return ExportResult(
                success=True,
                platform="mcp",
                skill_name=skill.name,
                output_path=server_file,
                files_created=[str(server_file)],
            )

        except Exception as e:
            return ExportResult(
                success=False,
                platform="mcp",
                skill_name=skill.name,
                errors=[str(e)],
            )

    def _generate_server_code(self, skill: SkillSpec) -> str:
        """Generate Python MCP server code.

        Args:
            skill: Skill specification

        Returns:
            Python source code for MCP server
        """
        tools_list = []
        handlers = []

        for tool in skill.tools:
            # Tool definition
            tools_list.append(
                f"""    {{
        "name": "{tool.name}",
        "description": "{tool.description}",
        "inputSchema": {json.dumps(tool.input_schema, indent=8)}
    }}"""
            )

            # Handler stub
            handler_name = tool.name.replace("-", "_")
            handlers.append(
                f'''
async def handle_{handler_name}(params: dict) -> dict:
    """Handle {tool.name} tool call.

    Args:
        params: Tool parameters matching inputSchema

    Returns:
        Tool result
    """
    # TODO: Implement tool logic
    return {{"result": "Not implemented"}}
'''
            )

        tools_json = ",\n".join(tools_list)
        handlers_code = "\n".join(handlers)

        return f'''"""MCP Server for {skill.name} skill.

Auto-generated from Paracle skill definition.
Implements the Model Context Protocol for tool serving.

Usage:
    python {skill.name}_mcp_server.py
"""

import asyncio
import json
import sys
from typing import Any

# Tool definitions
TOOLS = [
{tools_json}
]

# Tool handlers
{handlers_code}

TOOL_HANDLERS = {{
{chr(10).join(f'    "{t.name}": handle_{t.name.replace("-", "_")},' for t in skill.tools)}
}}


async def handle_request(request: dict) -> dict:
    """Handle incoming MCP request.

    Args:
        request: JSON-RPC 2.0 request

    Returns:
        JSON-RPC 2.0 response
    """
    method = request.get("method", "")
    params = request.get("params", {{}})
    request_id = request.get("id")

    if method == "tools/list":
        return {{
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {{"tools": TOOLS}}
        }}

    if method == "tools/call":
        tool_name = params.get("name")
        tool_params = params.get("arguments", {{}})

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return {{
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {{"code": -32601, "message": f"Tool not found: {{tool_name}}"}}
            }}

        try:
            result = await handler(tool_params)
            return {{
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {{"content": [{{"type": "text", "text": json.dumps(result)}}]}}
            }}
        except Exception as e:
            return {{
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {{"content": [{{"type": "text", "text": str(e)}}], "isError": True}}
            }}

    return {{
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {{"code": -32601, "message": f"Unknown method: {{method}}"}}
    }}


async def main():
    """Run MCP server on stdio."""
    while True:
        line = sys.stdin.readline()
        if not line:
            break

        try:
            request = json.loads(line)
            response = await handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error_response = {{
                "jsonrpc": "2.0",
                "id": None,
                "error": {{"code": -32700, "message": "Parse error"}}
            }}
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
'''
