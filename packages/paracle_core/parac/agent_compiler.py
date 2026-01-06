"""Agent Compiler - Compiles .parac/agents/ to IDE-native formats.

This module provides functionality to compile Paracle agent definitions
from .parac/agents/ to native formats recognized by various IDEs:
- VS Code Copilot (.github/agents/*.agent.md)
- Claude Code (.claude/agents/*.md)
- Cursor (.cursorrules with agent router)
- Windsurf (.windsurfrules + mcp_config.json)
- Codex (AGENTS.md)
"""

import json
import logging
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger("paracle.core.parac.agent_compiler")


@dataclass
class CompiledAgent:
    """Compiled agent ready for IDE output."""

    id: str
    name: str
    role: str
    description: str
    tools: list[str]
    skills: list[str]
    responsibilities: dict[str, list[str]]
    spec_content: str
    handoffs: list[dict] = field(default_factory=list)
    custom_tools: list[dict] = field(default_factory=list)
    external_mcp_tools: list[dict] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)


@dataclass
class ToolInfo:
    """Information about a tool for templates."""

    name: str
    description: str


class AgentCompiler:
    """Compiles .parac/agents/ to IDE-native formats.

    Uses Jinja2 templates to generate IDE-specific files, with optional
    AI-assisted optimization for more accurate format compliance.
    """

    TEMPLATES_DIR = Path(__file__).parent / "templates" / "ide"

    # Handoff definitions for multi-agent collaboration
    AGENT_HANDOFFS = {
        "architect": [
            {"label": "Implement", "agent": "coder", "prompt": "Implement the architecture design according to specifications."},
            {"label": "Review", "agent": "reviewer", "prompt": "Review the architectural decision for correctness."},
        ],
        "coder": [
            {"label": "Review", "agent": "reviewer", "prompt": "Review the implementation for quality and security."},
            {"label": "Test", "agent": "tester", "prompt": "Create comprehensive tests for this implementation."},
            {"label": "Document", "agent": "documenter", "prompt": "Document this implementation."},
        ],
        "reviewer": [
            {"label": "Fix Issues", "agent": "coder", "prompt": "Fix the issues identified in the review."},
            {"label": "Add Tests", "agent": "tester", "prompt": "Add tests to cover the reviewed scenarios."},
        ],
        "tester": [
            {"label": "Fix Failures", "agent": "coder", "prompt": "Fix the failing tests."},
            {"label": "Review Coverage", "agent": "reviewer", "prompt": "Review the test coverage."},
        ],
        "pm": [
            {"label": "Design", "agent": "architect", "prompt": "Design the architecture for this task."},
            {"label": "Implement", "agent": "coder", "prompt": "Implement this planned feature."},
        ],
        "documenter": [
            {"label": "Clarify Code", "agent": "coder", "prompt": "Clarify the code for documentation purposes."},
            {"label": "Review Docs", "agent": "reviewer", "prompt": "Review the documentation for accuracy."},
        ],
        "releasemanager": [
            {"label": "Review Changes", "agent": "reviewer", "prompt": "Review the changes before release."},
            {"label": "Run Tests", "agent": "tester", "prompt": "Run full test suite before release."},
        ],
    }

    def __init__(self, parac_root: Path):
        """Initialize the agent compiler.

        Args:
            parac_root: Path to the .parac/ directory
        """
        self.parac_root = parac_root
        self.manifest_path = parac_root / "agents" / "manifest.yaml"
        self.specs_dir = parac_root / "agents" / "specs"
        self.skills_file = parac_root / "agents" / "SKILL_ASSIGNMENTS.md"
        self.workflows_catalog = parac_root / "workflows" / "catalog.yaml"
        self.tools_registry = parac_root / "tools" / "registry.yaml"
        self.mcp_servers_config = parac_root / "tools" / "mcp" / "servers.yaml"

        # Output directories
        self.output_base = parac_root / "integrations" / "ide"
        self.agents_output = self.output_base / "agents"
        self.mcp_output = self.output_base / "mcp"
        self.vscode_output = self.output_base / "vscode"

        # Initialize Jinja2 environment
        if self.TEMPLATES_DIR.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.TEMPLATES_DIR),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            logger.warning(f"Templates directory not found: {self.TEMPLATES_DIR}")
            self.jinja_env = None

    def load_agents(self) -> list[CompiledAgent]:
        """Load all agents from manifest + specs.

        Returns:
            List of compiled agents with all resolved data
        """
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Agent manifest not found: {self.manifest_path}")

        with open(self.manifest_path, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        # Load workflows
        workflows = self._load_workflows()

        # Load custom tools
        custom_tools = self._load_custom_tools()

        # Load external MCP servers
        external_mcp = self._load_external_mcp_servers()

        agents = []
        for agent_def in manifest.get("agents", []):
            agent_id = agent_def["id"]
            spec_path = self.specs_dir / f"{agent_id}.md"
            spec_content = ""
            if spec_path.exists():
                spec_content = spec_path.read_text(encoding="utf-8")

            agents.append(
                CompiledAgent(
                    id=agent_id,
                    name=agent_def["name"],
                    role=agent_def.get("role", ""),
                    description=agent_def.get("description", ""),
                    tools=agent_def.get("tools", []),
                    skills=self._get_agent_skills(agent_id),
                    responsibilities=self._parse_responsibilities(
                        agent_def.get("responsibilities", [])
                    ),
                    spec_content=spec_content,
                    handoffs=self.AGENT_HANDOFFS.get(agent_id, []),
                    custom_tools=custom_tools,
                    external_mcp_tools=external_mcp,
                    workflows=workflows,
                )
            )

        return agents

    def _get_agent_skills(self, agent_id: str) -> list[str]:
        """Extract skills for an agent from SKILL_ASSIGNMENTS.md.

        Args:
            agent_id: Agent ID to get skills for

        Returns:
            List of skill names
        """
        if not self.skills_file.exists():
            return []

        content = self.skills_file.read_text(encoding="utf-8")

        # Find the section for this agent
        pattern = rf"### .+ {agent_id.title()}.*?Agent\s*\n.*?\*\*Skills\*\*:\s*\n((?:- `.+`.*\n)+)"
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)

        if not match:
            # Try alternative pattern
            pattern = rf"### .+ {agent_id.capitalize()} Agent\s*\n.*?\*\*Skills\*\*:\s*\n((?:- `.+`.*\n)+)"
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)

        if match:
            skills_text = match.group(1)
            skills = re.findall(r"`([^`]+)`", skills_text)
            return skills

        return []

    def _parse_responsibilities(
        self, responsibilities: list[str] | dict
    ) -> dict[str, list[str]]:
        """Parse responsibilities into categorized dict.

        Args:
            responsibilities: List or dict of responsibilities

        Returns:
            Dict mapping category to list of items
        """
        if isinstance(responsibilities, dict):
            return responsibilities

        if isinstance(responsibilities, list):
            # Group as 'Core Responsibilities'
            return {"Core Responsibilities": responsibilities}

        return {}

    def _load_workflows(self) -> list[str]:
        """Load available workflow IDs from catalog.

        Returns:
            List of workflow IDs
        """
        if not self.workflows_catalog.exists():
            return []

        with open(self.workflows_catalog, encoding="utf-8") as f:
            catalog = yaml.safe_load(f)

        workflows = []
        for wf in catalog.get("workflows", []):
            if wf.get("status") == "active":
                workflows.append(wf["name"])

        return workflows

    def _load_custom_tools(self) -> list[dict]:
        """Load custom tools from registry.

        Returns:
            List of custom tool definitions
        """
        if not self.tools_registry.exists():
            return []

        with open(self.tools_registry, encoding="utf-8") as f:
            registry = yaml.safe_load(f)

        return registry.get("custom", []) if registry else []

    def _load_external_mcp_servers(self) -> list[dict]:
        """Load external MCP server configurations.

        Returns:
            List of MCP server definitions
        """
        if not self.mcp_servers_config.exists():
            return []

        with open(self.mcp_servers_config, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        servers = []
        for server in config.get("servers", []):
            if server.get("enabled", True):
                servers.append(
                    {
                        "prefix": server.get("id", server.get("name", "")),
                        "name": server.get("name", ""),
                        "description": server.get("description", ""),
                    }
                )

        return servers

    def _get_all_tools_info(self) -> list[ToolInfo]:
        """Get info about all available tools.

        Returns:
            List of ToolInfo objects
        """
        # Core agent tools from manifest
        tools = []
        try:
            from paracle_orchestration.agent_tool_registry import agent_tool_registry

            for agent_id in agent_tool_registry.list_agents():
                agent_tools = agent_tool_registry.get_tools_for_agent(agent_id)
                for name, tool in agent_tools.items():
                    description = getattr(tool, "description", f"Paracle {name} tool")
                    if not any(t.name == name for t in tools):
                        tools.append(ToolInfo(name=name, description=description))
        except ImportError:
            logger.warning("Could not import agent_tool_registry")
            # Fallback to manifest tools
            if self.manifest_path.exists():
                with open(self.manifest_path, encoding="utf-8") as f:
                    manifest = yaml.safe_load(f)
                for agent in manifest.get("agents", []):
                    for tool_name in agent.get("tools", []):
                        if not any(t.name == tool_name for t in tools):
                            tools.append(
                                ToolInfo(name=tool_name, description=f"{tool_name} tool")
                            )

        return tools

    def _get_existing_ide_content(self, ide: str) -> str:
        """Get existing IDE-specific rules content to preserve.

        Args:
            ide: IDE name (cursor, windsurf)

        Returns:
            Existing rules content (after agent router section)
        """
        ide_files = {
            "cursor": self.output_base / ".cursorrules",
            "windsurf": self.output_base / ".windsurfrules",
        }

        file_path = ide_files.get(ide)
        if not file_path or not file_path.exists():
            return ""

        content = file_path.read_text(encoding="utf-8")

        # Find the marker for existing rules (after the agent system section)
        marker = "---\n\n"
        if marker in content:
            # Return content after the last marker
            parts = content.split(marker)
            if len(parts) > 1:
                return parts[-1]

        return ""

    def compile_for_vscode(self) -> dict[str, str]:
        """Generate .agent.md files for VS Code Copilot.

        Returns:
            Dict mapping filename to content
        """
        agents = self.load_agents()
        result = {}

        if not self.jinja_env:
            logger.error("Jinja2 environment not initialized")
            return result

        try:
            template = self.jinja_env.get_template("vscode_agent.md.j2")
        except TemplateNotFound:
            logger.error("VS Code agent template not found")
            return result

        for agent in agents:
            content = template.render(agent=agent)
            result[f"{agent.id}.agent.md"] = content

        return result

    def compile_for_claude(self) -> dict[str, str]:
        """Generate .md files for Claude Code subagents.

        Returns:
            Dict mapping filename to content
        """
        agents = self.load_agents()
        result = {}

        if not self.jinja_env:
            logger.error("Jinja2 environment not initialized")
            return result

        try:
            template = self.jinja_env.get_template("claude_agent.md.j2")
        except TemplateNotFound:
            logger.error("Claude agent template not found")
            return result

        for agent in agents:
            content = template.render(agent=agent)
            result[f"{agent.id}.md"] = content

        return result

    def compile_for_cursor(self) -> str:
        """Generate .cursorrules with agent router.

        Returns:
            Generated rules content
        """
        agents = self.load_agents()
        all_tools = self._get_all_tools_info()
        existing_rules = self._get_existing_ide_content("cursor")

        if not self.jinja_env:
            logger.error("Jinja2 environment not initialized")
            return ""

        try:
            template = self.jinja_env.get_template("cursor_rules.md.j2")
        except TemplateNotFound:
            logger.error("Cursor rules template not found")
            return ""

        return template.render(
            agents=agents, all_tools=all_tools, existing_rules=existing_rules
        )

    def compile_for_windsurf(self) -> tuple[str, str]:
        """Generate .windsurfrules and mcp_config.json.

        Returns:
            Tuple of (rules content, mcp_config JSON)
        """
        agents = self.load_agents()
        all_tools = self._get_all_tools_info()
        existing_rules = self._get_existing_ide_content("windsurf")

        rules = ""
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template("windsurf_rules.md.j2")
                rules = template.render(
                    agents=agents, all_tools=all_tools, existing_rules=existing_rules
                )
            except TemplateNotFound:
                logger.error("Windsurf rules template not found")

        mcp_config = {
            "mcpServers": {
                "paracle": {
                    "command": "paracle",
                    "args": ["mcp", "serve", "--stdio"],
                    "env": {},
                }
            }
        }

        return rules, json.dumps(mcp_config, indent=2)

    def compile_for_codex(self) -> str:
        """Generate AGENTS.md for Codex.

        Returns:
            Generated AGENTS.md content
        """
        agents = self.load_agents()
        all_tools = self._get_all_tools_info()

        if not self.jinja_env:
            logger.error("Jinja2 environment not initialized")
            return ""

        try:
            template = self.jinja_env.get_template("codex_agents.md.j2")
        except TemplateNotFound:
            logger.error("Codex agents template not found")
            return ""

        return template.render(agents=agents, all_tools=all_tools)

    def compile_vscode_tasks(self) -> dict:
        """Generate VS Code tasks.json with Paracle workflow tasks.

        Returns:
            Dict representing tasks.json content
        """
        agents = self.load_agents()
        workflows = self._load_workflows()

        tasks = {
            "version": "2.0.0",
            "tasks": [
                # MCP Server
                {
                    "label": "Paracle: Start MCP Server",
                    "type": "shell",
                    "command": "paracle mcp serve --stdio",
                    "problemMatcher": [],
                    "group": "none",
                    "presentation": {
                        "reveal": "always",
                        "panel": "new"
                    }
                },
                # Agent commands
                {
                    "label": "Paracle: List Agents",
                    "type": "shell",
                    "command": "paracle agents list",
                    "problemMatcher": [],
                    "group": "none"
                },
                {
                    "label": "Paracle: Run Agent",
                    "type": "shell",
                    "command": "paracle agents run ${input:agentId} --task \"${input:agentTask}\"",
                    "problemMatcher": [],
                    "group": "none"
                },
                # Workflow commands
                {
                    "label": "Paracle: List Workflows",
                    "type": "shell",
                    "command": "paracle workflows list",
                    "problemMatcher": [],
                    "group": "none"
                },
                {
                    "label": "Paracle: Run Workflow",
                    "type": "shell",
                    "command": "paracle workflows run ${input:workflowId}",
                    "problemMatcher": [],
                    "group": "none"
                },
                # Common workflow shortcuts
                {
                    "label": "Paracle: Code Review Workflow",
                    "type": "shell",
                    "command": "paracle workflows run code_review",
                    "problemMatcher": [],
                    "group": "test"
                },
                {
                    "label": "Paracle: Feature Development Workflow",
                    "type": "shell",
                    "command": "paracle workflows run feature_development",
                    "problemMatcher": [],
                    "group": "build"
                },
                {
                    "label": "Paracle: Bugfix Workflow",
                    "type": "shell",
                    "command": "paracle workflows run bugfix",
                    "problemMatcher": [],
                    "group": "build"
                },
                # IDE sync
                {
                    "label": "Paracle: IDE Build",
                    "type": "shell",
                    "command": "paracle ide build --target all --copy",
                    "problemMatcher": [],
                    "group": "build"
                },
                {
                    "label": "Paracle: IDE Sync",
                    "type": "shell",
                    "command": "paracle ide sync --copy",
                    "problemMatcher": [],
                    "group": "build"
                },
            ],
            "inputs": [
                {
                    "id": "agentId",
                    "description": "Select an agent to run",
                    "type": "pickString",
                    "options": [agent.id for agent in agents]
                },
                {
                    "id": "agentTask",
                    "description": "Describe the task for the agent",
                    "type": "promptString",
                    "default": ""
                },
                {
                    "id": "workflowId",
                    "description": "Select a workflow to run",
                    "type": "pickString",
                    "options": workflows
                }
            ]
        }

        return tasks

    def compile_vscode_mcp(self, dev_mode: bool = False) -> dict:
        """Generate VS Code mcp.json for Copilot MCP integration.

        VS Code expects the format:
        {
          "servers": {
            "server-name": {
              "type": "stdio",
              "command": "...",
              "args": [...]
            }
          }
        }

        Args:
            dev_mode: If True, use 'uv run paracle' for development.
                      If False, use 'paracle' directly (production).

        Returns:
            Dict representing mcp.json content
        """
        # Load external MCP servers
        external_mcp = self._load_external_mcp_servers()

        # Production: use 'paracle' directly (installed globally)
        # Development: use 'uv run paracle' (project venv)
        if dev_mode:
            mcp_config: dict = {
                "servers": {
                    "paracle": {
                        "type": "stdio",
                        "command": "uv",
                        "args": ["run", "paracle", "mcp", "serve", "--stdio"]
                    }
                }
            }
        else:
            mcp_config: dict = {
                "servers": {
                    "paracle": {
                        "type": "stdio",
                        "command": "paracle",
                        "args": ["mcp", "serve", "--stdio"]
                    }
                }
            }

        # Add external MCP servers if configured
        for server in external_mcp:
            server_id = server.get("prefix", "")
            if server_id and server_id != "paracle":
                # Read full server config from mcp servers.yaml
                if self.mcp_servers_config.exists():
                    with open(self.mcp_servers_config, encoding="utf-8") as f:
                        config = yaml.safe_load(f)
                    for srv in config.get("servers", []):
                        if srv.get("id") == server_id and srv.get("enabled", True):
                            mcp_config["servers"][server_id] = {
                                "type": "stdio",
                                "command": srv.get("command", ""),
                                "args": srv.get("args", [])
                            }
                            if srv.get("env"):
                                mcp_config["servers"][server_id]["env"] = srv["env"]
                            break

        return mcp_config

    def build(self, target: str, output_dir: Path | None = None) -> dict[str, Any]:
        """Build for target IDE(s).

        Args:
            target: IDE target (vscode, claude, cursor, windsurf, codex, all)
            output_dir: Optional custom output directory

        Returns:
            Dict with 'files' list and 'output_dir'
        """
        if output_dir is None:
            output_dir = self.agents_output

        targets = (
            ["vscode", "claude", "cursor", "windsurf", "codex"]
            if target == "all"
            else [target]
        )
        result: dict[str, Any] = {"files": [], "output_dir": str(output_dir)}

        for t in targets:
            result["files"].extend(self._build_target(t, output_dir))

        return result

    def _build_target(self, target: str, output_dir: Path) -> list[str]:
        """Build files for a single target IDE.

        Args:
            target: IDE target name
            output_dir: Output directory for agent files

        Returns:
            List of generated file paths
        """
        files: list[str] = []

        if target == "vscode":
            files.extend(self._build_vscode(output_dir))
        elif target == "claude":
            files.extend(self._build_claude(output_dir))
        elif target == "cursor":
            files.extend(self._build_cursor())
        elif target == "windsurf":
            files.extend(self._build_windsurf())
        elif target == "codex":
            files.extend(self._build_codex(output_dir))

        return files

    def _build_vscode(self, output_dir: Path) -> list[str]:
        """Build VS Code agent files and configs."""
        files: list[str] = []

        # Agent files
        target_dir = output_dir / "vscode"
        target_dir.mkdir(parents=True, exist_ok=True)
        for name, content in self.compile_for_vscode().items():
            file_path = target_dir / name
            file_path.write_text(content, encoding="utf-8")
            files.append(str(file_path))

        # VS Code tasks.json
        self.vscode_output.mkdir(parents=True, exist_ok=True)
        tasks = self.compile_vscode_tasks()
        tasks_path = self.vscode_output / "tasks.json"
        tasks_path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
        files.append(str(tasks_path))

        # VS Code mcp.json
        # Detect dev mode: if .venv exists in project root, use uv run
        project_root = self.parac_root.parent
        dev_mode = (project_root / ".venv").exists()
        mcp = self.compile_vscode_mcp(dev_mode=dev_mode)
        mcp_path = self.vscode_output / "mcp.json"
        mcp_path.write_text(json.dumps(mcp, indent=2), encoding="utf-8")
        files.append(str(mcp_path))

        return files

    def _build_claude(self, output_dir: Path) -> list[str]:
        """Build Claude Code agent files."""
        files: list[str] = []
        target_dir = output_dir / "claude"
        target_dir.mkdir(parents=True, exist_ok=True)
        for name, content in self.compile_for_claude().items():
            file_path = target_dir / name
            file_path.write_text(content, encoding="utf-8")
            files.append(str(file_path))
        return files

    def _build_cursor(self) -> list[str]:
        """Build Cursor rules file."""
        files: list[str] = []
        rules = self.compile_for_cursor()
        if rules:
            rules_path = self.output_base / ".cursorrules"
            rules_path.write_text(rules, encoding="utf-8")
            files.append(str(rules_path))
        return files

    def _build_windsurf(self) -> list[str]:
        """Build Windsurf rules and MCP config."""
        files: list[str] = []
        rules, mcp_config = self.compile_for_windsurf()
        if rules:
            rules_path = self.output_base / ".windsurfrules"
            rules_path.write_text(rules, encoding="utf-8")
            files.append(str(rules_path))

        self.mcp_output.mkdir(parents=True, exist_ok=True)
        mcp_path = self.mcp_output / "windsurf.mcp.json"
        mcp_path.write_text(mcp_config, encoding="utf-8")
        files.append(str(mcp_path))
        return files

    def _build_codex(self, output_dir: Path) -> list[str]:
        """Build Codex AGENTS.md file."""
        files: list[str] = []
        content = self.compile_for_codex()
        if content:
            codex_dir = output_dir / "codex"
            codex_dir.mkdir(parents=True, exist_ok=True)
            file_path = codex_dir / "AGENTS.md"
            file_path.write_text(content, encoding="utf-8")
            files.append(str(file_path))
        return files

    def copy_to_destinations(self, target: str) -> list[Path]:
        """Copy generated files to expected IDE locations.

        Args:
            target: IDE target (vscode, claude, cursor, windsurf, codex, all)

        Returns:
            List of destination paths
        """
        copied = []
        project_root = self.parac_root.parent

        targets = (
            ["vscode", "claude", "cursor", "windsurf", "codex"]
            if target == "all"
            else [target]
        )

        for t in targets:
            if t == "vscode":
                # Agent files
                src_dir = self.agents_output / "vscode"
                dest_dir = project_root / ".github" / "agents"
                if src_dir.exists():
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    for file in src_dir.glob("*.agent.md"):
                        dest = dest_dir / file.name
                        shutil.copy2(file, dest)
                        copied.append(dest)

                # VS Code config files (tasks.json, mcp.json)
                vscode_dest = project_root / ".vscode"
                vscode_dest.mkdir(parents=True, exist_ok=True)

                tasks_src = self.vscode_output / "tasks.json"
                if tasks_src.exists():
                    tasks_dest = vscode_dest / "tasks.json"
                    shutil.copy2(tasks_src, tasks_dest)
                    copied.append(tasks_dest)

                mcp_src = self.vscode_output / "mcp.json"
                if mcp_src.exists():
                    mcp_dest = vscode_dest / "mcp.json"
                    shutil.copy2(mcp_src, mcp_dest)
                    copied.append(mcp_dest)

            elif t == "claude":
                src_dir = self.agents_output / "claude"
                dest_dir = project_root / ".claude" / "agents"
                if src_dir.exists():
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    for file in src_dir.glob("*.md"):
                        dest = dest_dir / file.name
                        shutil.copy2(file, dest)
                        copied.append(dest)

            elif t == "cursor":
                src = self.output_base / ".cursorrules"
                if src.exists():
                    dest = project_root / ".cursorrules"
                    shutil.copy2(src, dest)
                    copied.append(dest)

            elif t == "windsurf":
                src = self.output_base / ".windsurfrules"
                if src.exists():
                    dest = project_root / ".windsurfrules"
                    shutil.copy2(src, dest)
                    copied.append(dest)

                # MCP config - note: user may need to copy to ~/.codeium/windsurf/
                mcp_src = self.mcp_output / "windsurf.mcp.json"
                if mcp_src.exists():
                    mcp_dest = project_root / "mcp_config.json"
                    shutil.copy2(mcp_src, mcp_dest)
                    copied.append(mcp_dest)

            elif t == "codex":
                src = self.agents_output / "codex" / "AGENTS.md"
                if src.exists():
                    dest = project_root / "AGENTS.md"
                    shutil.copy2(src, dest)
                    copied.append(dest)

        return copied


__all__ = ["AgentCompiler", "CompiledAgent", "ToolInfo"]
