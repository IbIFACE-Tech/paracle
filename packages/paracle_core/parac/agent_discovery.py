"""Agent discovery system for .parac/ workspace.

Scans and discovers agents defined in .parac/agents/specs/ directory.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from paracle_profiling import cached, profile

    PROFILING_AVAILABLE = True
except ImportError:
    # Profiling not available - use no-op decorators
    PROFILING_AVAILABLE = False

    def cached(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def profile(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


@dataclass
class AgentMetadata:
    """Metadata for a discovered agent."""

    id: str
    name: str
    role: str
    spec_file: str
    capabilities: list[str] = field(default_factory=list)
    description: str = ""
    tools: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)

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

        for line in lines:
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
            spec_file=str(
                spec_path.relative_to(spec_path.parents[2])
            ),  # Relative to .parac/
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
            "tools": self.tools,
            "skills": self.skills,
        }


class AgentDiscovery:
    """Discovers agents in .parac/ workspace.

    Reads agent specs from .parac/agents/specs/*.md and enriches them
    with tools and skills from .parac/agents/manifest.yaml.
    """

    def __init__(self, parac_root: Path):
        """Initialize agent discovery.

        Args:
            parac_root: Root path of .parac/ directory
        """
        self.parac_root = parac_root
        self.agents_dir = parac_root / "agents" / "specs"
        self.manifest_file = parac_root / "agents" / "manifest.yaml"
        self._manifest_cache: dict[str, Any] | None = None

    def discover_agents(self) -> list[AgentMetadata]:
        """Discover all agents in .parac/agents/specs/.

        Enriches metadata with tools and skills from manifest.yaml.

        Returns:
            List of discovered agent metadata

        Raises:
            FileNotFoundError: If agents directory doesn't exist
        """
        if not self.agents_dir.exists():
            raise FileNotFoundError(f"Agents directory not found: {self.agents_dir}")

        # Load manifest for tools/skills enrichment
        manifest_data = self._load_manifest()

        agents = []
        for spec_file in sorted(self.agents_dir.glob("*.md")):
            if spec_file.stem.startswith("_"):
                continue  # Skip files starting with underscore

            try:
                agent = AgentMetadata.from_markdown(spec_file)
                # Enrich with tools and skills from manifest
                self._enrich_from_manifest(agent, manifest_data)
                agents.append(agent)
            except Exception as e:
                # Log warning but continue with other agents
                print(f"Warning: Could not parse {spec_file.name}: {e}")

        return agents

    def _load_manifest(self) -> dict[str, Any]:
        """Load and cache manifest.yaml.

        Returns:
            Manifest data as dictionary
        """
        if self._manifest_cache is not None:
            return self._manifest_cache

        if not self.manifest_file.exists():
            self._manifest_cache = {}
            return self._manifest_cache

        try:
            import yaml

            content = self.manifest_file.read_text(encoding="utf-8")
            self._manifest_cache = yaml.safe_load(content) or {}
        except Exception as e:
            print(f"Warning: Could not load manifest.yaml: {e}")
            self._manifest_cache = {}

        return self._manifest_cache

    def _enrich_from_manifest(
        self, agent: AgentMetadata, manifest_data: dict[str, Any]
    ) -> None:
        """Enrich agent metadata with tools and skills from manifest.

        Args:
            agent: Agent metadata to enrich
            manifest_data: Loaded manifest data
        """
        agents_list = manifest_data.get("agents", [])

        for manifest_agent in agents_list:
            if manifest_agent.get("id") == agent.id:
                # Extract tools (strip comments)
                tools = manifest_agent.get("tools", [])
                agent.tools = [
                    t.split("#")[0].strip() for t in tools if t.split("#")[0].strip()
                ]

                # Extract skills (strip comments)
                skills = manifest_agent.get("skills", [])
                agent.skills = [
                    s.split("#")[0].strip() for s in skills if s.split("#")[0].strip()
                ]
                break

    @cached(ttl=300)  # Cache for 5 minutes
    @profile(track_memory=True)
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

        agent = AgentMetadata.from_markdown(spec_file)

        # Enrich with tools and skills from manifest
        manifest_data = self._load_manifest()
        self._enrich_from_manifest(agent, manifest_data)

        return agent

    @cached(ttl=300)  # Cache for 5 minutes
    @profile()
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
