"""Agent Card Generator.

Generates A2A Agent Cards from Paracle agent specifications.
"""

from pathlib import Path
from typing import Any

import yaml

from paracle_a2a.config import A2AServerConfig
from paracle_a2a.models import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    SecurityScheme,
)


class AgentCardGenerator:
    """Generates A2A Agent Cards from Paracle agent specs.

    Reads agent definitions from .parac/agents/specs/ and converts
    them to A2A-compatible Agent Cards.
    """

    def __init__(
        self,
        parac_root: Path,
        config: A2AServerConfig | None = None,
    ):
        """Initialize Agent Card generator.

        Args:
            parac_root: Path to .parac directory
            config: A2A server configuration
        """
        self.parac_root = Path(parac_root)
        self.config = config or A2AServerConfig()
        self._agents_dir = self.parac_root / "agents"
        self._specs_dir = self._agents_dir / "specs"
        self._manifest_path = self._agents_dir / "manifest.yaml"

    def get_available_agents(self) -> list[str]:
        """Get list of available agent IDs.

        Returns:
            List of agent IDs from manifest or spec files
        """
        agents = []

        # Try manifest first
        if self._manifest_path.exists():
            try:
                with open(self._manifest_path) as f:
                    manifest = yaml.safe_load(f)
                if manifest and "agents" in manifest:
                    for agent in manifest["agents"]:
                        if isinstance(agent, dict) and "id" in agent:
                            agents.append(agent["id"])
                        elif isinstance(agent, str):
                            agents.append(agent)
            except Exception:
                pass

        # Fall back to spec files
        if not agents and self._specs_dir.exists():
            for spec_file in self._specs_dir.glob("*.md"):
                agents.append(spec_file.stem)

        # Filter by config if specified
        if self.config.agent_ids and not self.config.expose_all_agents:
            agents = [a for a in agents if a in self.config.agent_ids]

        return agents

    def _load_agent_spec(self, agent_id: str) -> dict[str, Any] | None:
        """Load agent specification from file.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent spec dictionary or None if not found
        """
        spec_path = self._specs_dir / f"{agent_id}.md"
        if not spec_path.exists():
            return None

        try:
            content = spec_path.read_text(encoding="utf-8")

            # Parse YAML frontmatter
            if content.startswith("---"):
                _, frontmatter, body = content.split("---", 2)
                spec = yaml.safe_load(frontmatter)
                spec["body"] = body.strip()
                return spec
        except Exception:
            pass

        return None

    def _load_skills(self, agent_id: str) -> list[AgentSkill]:
        """Load skills assigned to an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of AgentSkill objects
        """
        skills = []

        # Check skill assignments file
        assignments_path = self._agents_dir / "SKILL_ASSIGNMENTS.md"
        if not assignments_path.exists():
            return skills

        # Load skill definitions from skills directory
        skills_dir = self._agents_dir / "skills"
        if not skills_dir.exists():
            return skills

        # Parse assignments (simplified - in real impl, parse markdown properly)
        try:
            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue

                content = skill_md.read_text(encoding="utf-8")
                if content.startswith("---"):
                    _, frontmatter, body = content.split("---", 2)
                    skill_spec = yaml.safe_load(frontmatter)

                    # Check if assigned to this agent
                    assigned_agents = skill_spec.get("assigned_agents", [])
                    if agent_id in assigned_agents or not assigned_agents:
                        skills.append(
                            AgentSkill(
                                id=skill_spec.get("name", skill_dir.name),
                                name=skill_spec.get("metadata", {}).get(
                                    "display_name", skill_dir.name
                                ),
                                description=skill_spec.get("description", ""),
                                tags=skill_spec.get("metadata", {}).get("tags", []),
                            )
                        )
        except Exception:
            pass

        return skills

    def generate_card(
        self,
        agent_id: str,
        base_url: str,
    ) -> AgentCard | None:
        """Generate Agent Card for a specific agent.

        Args:
            agent_id: Agent identifier
            base_url: Base URL for the A2A server

        Returns:
            AgentCard or None if agent not found
        """
        spec = self._load_agent_spec(agent_id)
        if not spec:
            return None

        # Build agent URL
        agent_url = f"{base_url.rstrip('/')}{self.config.base_path}/agents/{agent_id}"

        # Build capabilities
        capabilities = AgentCapabilities(
            streaming=self.config.enable_streaming,
            push_notifications=self.config.enable_push_notifications,
            state_transition_history=self.config.enable_state_transition_history,
        )

        # Build provider
        provider = AgentProvider(
            organization=self.config.provider_name,
            url=self.config.provider_url,
        )

        # Load skills
        skills = self._load_skills(agent_id)

        # Build security schemes
        security_schemes = None
        security = None
        if self.config.require_authentication and self.config.security_schemes:
            security_schemes = {}
            security = []
            for scheme_config in self.config.security_schemes:
                scheme_name = f"{scheme_config.scheme}Auth"
                security_schemes[scheme_name] = SecurityScheme(
                    type=scheme_config.type,
                    scheme=scheme_config.scheme,
                    bearer_format=scheme_config.bearer_format,
                )
                security.append({scheme_name: []})

        return AgentCard(
            name=spec.get("name", agent_id),
            description=spec.get("description", f"Paracle {agent_id} agent"),
            url=agent_url,
            version=spec.get("version", "0.1.0"),
            default_input_modes=["text/plain", "application/json"],
            default_output_modes=["text/plain", "application/json"],
            provider=provider,
            capabilities=capabilities,
            skills=skills,
            security_schemes=security_schemes,
            security=security,
        )

    def generate_all_cards(
        self,
        base_url: str,
    ) -> dict[str, AgentCard]:
        """Generate Agent Cards for all available agents.

        Args:
            base_url: Base URL for the A2A server

        Returns:
            Dictionary mapping agent ID to AgentCard
        """
        cards = {}
        for agent_id in self.get_available_agents():
            card = self.generate_card(agent_id, base_url)
            if card:
                cards[agent_id] = card
        return cards

    def generate_root_card(
        self,
        base_url: str,
    ) -> AgentCard:
        """Generate root-level Agent Card.

        This card represents the overall Paracle server and lists
        all available agents as skills.

        Args:
            base_url: Base URL for the A2A server

        Returns:
            Root AgentCard
        """
        agent_cards = self.generate_all_cards(base_url)

        # Convert agents to skills
        skills = []
        for agent_id, card in agent_cards.items():
            skills.append(
                AgentSkill(
                    id=agent_id,
                    name=card.name,
                    description=card.description,
                    tags=["agent"],
                )
            )

        return AgentCard(
            name="Paracle Multi-Agent Framework",
            description="A2A gateway for Paracle agents",
            url=f"{base_url.rstrip('/')}{self.config.base_path}",
            version="0.1.0",
            default_input_modes=["text/plain", "application/json"],
            default_output_modes=["text/plain", "application/json"],
            provider=AgentProvider(
                organization=self.config.provider_name,
                url=self.config.provider_url,
            ),
            capabilities=AgentCapabilities(
                streaming=self.config.enable_streaming,
                push_notifications=self.config.enable_push_notifications,
                state_transition_history=self.config.enable_state_transition_history,
            ),
            skills=skills,
        )
