"""Agent discovery system for .parac/ workspace.

Scans and discovers agents defined in .parac/agents/specs/ directory.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AgentMetadata:
    """Metadata for a discovered agent."""

    id: str
    name: str
    role: str
    spec_file: str
    capabilities: list[str] = field(default_factory=list)
    description: str = ""

    @classmethod
    def from_markdown(cls, spec_path: Path) -> "AgentMetadata":
        """Extract metadata from agent markdown spec file.

        Parses the markdown file to extract:
        - Name from H1 heading
        - Role from ## Role section
        - Capabilities from various sections

        Args:
            spec_path: Path to agent specification markdown file

        Returns:
            AgentMetadata instance with extracted information
        """
        content = spec_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        name = ""
        role = ""
        capabilities = []
        description = ""

        in_role_section = False
        in_responsibilities_section = False

        for i, line in enumerate(lines):
            # Extract name from H1
            if line.startswith("# ") and not name:
                name = line[2:].strip()

            # Extract role section
            elif line.startswith("## Role"):
                in_role_section = True
                in_responsibilities_section = False
            elif line.startswith("## Responsibilities"):
                in_role_section = False
                in_responsibilities_section = True
            elif line.startswith("## ") and in_role_section:
                in_role_section = False
            elif line.startswith("## ") and in_responsibilities_section:
                in_responsibilities_section = False

            # Get role description (first paragraph after ## Role)
            elif in_role_section and line.strip() and not line.startswith("#"):
                if not role:
                    role = line.strip()
                    description = line.strip()

            # Extract capabilities from headings
            elif line.startswith("### "):
                capability = line[4:].strip().lower()
                if in_responsibilities_section and capability:
                    capabilities.append(capability)

        # Derive agent ID from filename
        agent_id = spec_path.stem

        return cls(
            id=agent_id,
            name=name or agent_id.title(),
            role=role or "Agent",
            spec_file=str(spec_path.relative_to(
                spec_path.parents[2])),  # Relative to .parac/
            capabilities=capabilities[:5],  # Limit to 5 main capabilities
            description=description,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "spec_file": self.spec_file,
            "capabilities": self.capabilities,
            "description": self.description,
        }


class AgentDiscovery:
    """Discovers agents in .parac/ workspace."""

    def __init__(self, parac_root: Path):
        """Initialize agent discovery.

        Args:
            parac_root: Root path of .parac/ directory
        """
        self.parac_root = parac_root
        self.agents_dir = parac_root / "agents" / "specs"

    def discover_agents(self) -> list[AgentMetadata]:
        """Discover all agents in .parac/agents/specs/.

        Returns:
            List of discovered agent metadata

        Raises:
            FileNotFoundError: If agents directory doesn't exist
        """
        if not self.agents_dir.exists():
            raise FileNotFoundError(
                f"Agents directory not found: {self.agents_dir}")

        agents = []
        for spec_file in sorted(self.agents_dir.glob("*.md")):
            if spec_file.stem.startswith("_"):
                continue  # Skip files starting with underscore

            try:
                agent = AgentMetadata.from_markdown(spec_file)
                agents.append(agent)
            except Exception as e:
                # Log warning but continue with other agents
                print(f"Warning: Could not parse {spec_file.name}: {e}")

        return agents

    def get_agent(self, agent_id: str) -> AgentMetadata | None:
        """Get specific agent by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentMetadata if found, None otherwise
        """
        spec_file = self.agents_dir / f"{agent_id}.md"
        if not spec_file.exists():
            return None

        return AgentMetadata.from_markdown(spec_file)

    def get_agent_spec_content(self, agent_id: str) -> str | None:
        """Get full content of agent specification.

        Args:
            agent_id: Agent identifier

        Returns:
            Full markdown content of agent spec, or None if not found
        """
        spec_file = self.agents_dir / f"{agent_id}.md"
        if not spec_file.exists():
            return None

        return spec_file.read_text(encoding="utf-8")
