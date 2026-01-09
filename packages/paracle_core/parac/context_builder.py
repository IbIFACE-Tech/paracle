"""Context builder for IDE integration.

Collects and formats .parac/ context for embedding in IDE configuration files.
Implements priority-based truncation to respect token/size limits.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from paracle_core.parac.agent_discovery import AgentDiscovery, AgentMetadata
from paracle_core.parac.state import ParacState, load_state


@dataclass
class ContextSection:
    """A section of context with priority and metadata."""

    name: str
    content: str
    priority: int  # 1 = highest priority
    can_truncate: bool = True

    @property
    def size(self) -> int:
        """Return content size in characters."""
        return len(self.content)


@dataclass
class ContextData:
    """Collected context data from .parac/."""

    state: ParacState | None = None
    agents: list[AgentMetadata] = field(default_factory=list)
    governance_summary: str = ""
    recent_decisions: list[dict[str, str]] = field(default_factory=list)
    open_questions: list[dict[str, str]] = field(default_factory=list)
    skill_assignments: str = ""
    policies_available: list[str] = field(default_factory=list)
    config_files_guide: bool = False
    structure_guide: bool = False
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "current_state": self._state_to_dict() if self.state else {},
            "agents": [a.to_dict() for a in self.agents],
            "governance_summary": self.governance_summary,
            "recent_decisions": self.recent_decisions,
            "open_questions": self.open_questions,
            "skill_assignments": self.skill_assignments,
            "policies_available": self.policies_available,
            "config_files_guide": self.config_files_guide,
            "structure_guide": self.structure_guide,
            "generated_at": self.generated_at,
        }

    def _state_to_dict(self) -> dict[str, Any]:
        """Convert state to simplified dict for templates."""
        if not self.state:
            return {}
        return {
            "project_name": self.state.project_name,
            "project_version": self.state.project_version,
            "phase": {
                "id": self.state.current_phase.id,
                "name": self.state.current_phase.name,
                "status": self.state.current_phase.status,
                "progress": self.state.current_phase.progress,
                "focus_areas": self.state.current_phase.focus_areas,
            },
            "blockers_count": len(self.state.blockers),
            "next_actions": self.state.next_actions[:3],  # Top 3
        }


class ContextBuilder:
    """Builds optimized context for AI/IDE assistants.

    Collects context from .parac/ and formats it for embedding in
    IDE configuration files with priority-based truncation.
    """

    # Default size limits per IDE (in characters)
    IDE_SIZE_LIMITS = {
        "cursor": 100_000,
        "claude": 50_000,
        "cline": 50_000,
        "copilot": 30_000,
        "windsurf": 50_000,
        "default": 50_000,
    }

    def __init__(self, parac_root: Path, max_size: int | None = None):
        """Initialize context builder.

        Args:
            parac_root: Path to .parac/ directory
            max_size: Maximum context size in characters (optional)
        """
        self.parac_root = parac_root
        self.max_size = max_size or self.IDE_SIZE_LIMITS["default"]
        self._sections: list[ContextSection] = []

    def collect(self) -> ContextData:
        """Collect all context data from .parac/.

        Returns:
            ContextData with all collected information
        """
        data = ContextData()

        # Load state
        data.state = load_state(self.parac_root)

        # Discover agents
        try:
            discovery = AgentDiscovery(self.parac_root)
            data.agents = discovery.discover_agents()
        except FileNotFoundError:
            data.agents = []

        # Load governance summary
        data.governance_summary = self._load_governance_summary()

        # Load recent decisions
        data.recent_decisions = self._load_recent_decisions(count=3)

        # Load open questions
        data.open_questions = self._load_open_questions()

        # Load skill assignments summary
        data.skill_assignments = self._load_skill_assignments()

        # Check for available policies
        data.policies_available = self._list_available_policies()

        # Check for guide files
        data.config_files_guide = (self.parac_root / "CONFIG_FILES.md").exists()
        data.structure_guide = (self.parac_root / "STRUCTURE.md").exists()

        return data

    def _load_governance_summary(self) -> str:
        """Load and summarize governance rules."""
        governance_file = self.parac_root / "GOVERNANCE.md"
        if not governance_file.exists():
            return "No governance file found."

        content = governance_file.read_text(encoding="utf-8")

        # Extract key sections (first 2000 chars or until ## Usage)
        lines = content.split("\n")
        summary_lines = []
        in_summary = False

        for line in lines:
            if line.startswith("# "):
                in_summary = True
            elif line.startswith("## ") and "Usage" in line:
                break
            elif in_summary:
                summary_lines.append(line)

            if len("\n".join(summary_lines)) > 2000:
                break

        return "\n".join(summary_lines).strip()

    def _load_recent_decisions(self, count: int = 3) -> list[dict[str, str]]:
        """Load recent architecture decisions."""
        decisions_file = self.parac_root / "roadmap" / "decisions.md"
        if not decisions_file.exists():
            return []

        content = decisions_file.read_text(encoding="utf-8")
        decisions = []

        # Parse ADRs (format: ### ADR-XXX: Title)
        current_adr = None
        current_content: list[str] = []

        for line in content.split("\n"):
            if line.startswith("### ADR-"):
                if current_adr and current_content:
                    decisions.append(
                        {
                            "id": current_adr,
                            "summary": " ".join(current_content[:3]),
                        }
                    )
                # Extract ADR ID and title
                parts = line[4:].split(":", 1)
                current_adr = parts[0].strip()
                current_content = [parts[1].strip()] if len(parts) > 1 else []
            elif current_adr and line.strip():
                current_content.append(line.strip())

        # Add last ADR
        if current_adr and current_content:
            decisions.append(
                {
                    "id": current_adr,
                    "summary": " ".join(current_content[:3]),
                }
            )

        # Return most recent
        return decisions[-count:] if decisions else []

    def _load_open_questions(self) -> list[dict[str, str]]:
        """Load open questions."""
        questions_file = self.parac_root / "memory" / "context" / "open_questions.md"
        if not questions_file.exists():
            return []

        content = questions_file.read_text(encoding="utf-8")
        questions = []

        # Parse questions (format: ### Q#: Title or ### Title)
        for line in content.split("\n"):
            if line.startswith("### "):
                title = line[4:].strip()
                if title and not title.lower().startswith("resolved"):
                    questions.append({"question": title})

        return questions[:5]  # Top 5 open questions

    def _load_skill_assignments(self) -> str:
        """Load agent skill assignments summary."""
        skills_file = self.parac_root / "agents" / "SKILL_ASSIGNMENTS.md"
        if not skills_file.exists():
            return ""

        content = skills_file.read_text(encoding="utf-8")
        # Return first 1500 chars (summary section usually)
        lines = content.split("\n")
        summary = []
        for line in lines:
            summary.append(line)
            if len("\n".join(summary)) > 1500:
                break
        return "\n".join(summary).strip()

    def _list_available_policies(self) -> list[str]:
        """List available policy files in .parac/policies/."""
        policies_dir = self.parac_root / "policies"
        if not policies_dir.exists():
            return []

        policy_files = []
        for item in policies_dir.iterdir():
            if item.is_file() and item.suffix in [".md", ".yaml"]:
                policy_files.append(item.stem)
        return sorted(policy_files)

    def build_sections(self, data: ContextData) -> list[ContextSection]:
        """Build context sections with priorities.

        Args:
            data: Collected context data

        Returns:
            List of context sections sorted by priority
        """
        sections = []

        # Priority 1: Current state (always included)
        if data.state:
            state_content = self._format_state(data.state)
            sections.append(
                ContextSection(
                    name="current_state",
                    content=state_content,
                    priority=1,
                    can_truncate=False,
                )
            )

        # Priority 2: Agent list with capabilities
        if data.agents:
            agents_content = self._format_agents(data.agents)
            sections.append(
                ContextSection(
                    name="agents",
                    content=agents_content,
                    priority=2,
                    can_truncate=False,
                )
            )

        # Priority 3: Governance rules
        if data.governance_summary:
            sections.append(
                ContextSection(
                    name="governance",
                    content=data.governance_summary,
                    priority=3,
                    can_truncate=True,
                )
            )

        # Priority 4: Recent decisions
        if data.recent_decisions:
            decisions_content = self._format_decisions(data.recent_decisions)
            sections.append(
                ContextSection(
                    name="decisions",
                    content=decisions_content,
                    priority=4,
                    can_truncate=True,
                )
            )

        # Priority 5: Open questions
        if data.open_questions:
            questions_content = self._format_questions(data.open_questions)
            sections.append(
                ContextSection(
                    name="questions",
                    content=questions_content,
                    priority=5,
                    can_truncate=True,
                )
            )

        return sorted(sections, key=lambda s: s.priority)

    def _format_state(self, state: ParacState) -> str:
        """Format state for embedding."""
        phase = state.current_phase
        lines = [
            f"Project: {state.project_name} v{state.project_version}",
            f"Phase: {phase.id} - {phase.name} ({phase.progress})",
            f"Status: {phase.status}",
        ]
        if phase.focus_areas:
            lines.append(f"Focus: {', '.join(phase.focus_areas)}")
        if state.blockers:
            lines.append(f"Blockers: {len(state.blockers)}")
        return "\n".join(lines)

    def _format_agents(self, agents: list[AgentMetadata]) -> str:
        """Format agents for embedding."""
        lines = []
        for agent in agents:
            caps = ", ".join(agent.capabilities) if agent.capabilities else "general"
            lines.append(f"- **{agent.name}** ({agent.id}): {agent.role}")
            lines.append(f"  Capabilities: {caps}")
        return "\n".join(lines)

    def _format_decisions(self, decisions: list[dict[str, str]]) -> str:
        """Format decisions for embedding."""
        lines = []
        for d in decisions:
            lines.append(f"- {d['id']}: {d['summary'][:100]}")
        return "\n".join(lines)

    def _format_questions(self, questions: list[dict[str, str]]) -> str:
        """Format questions for embedding."""
        lines = []
        for q in questions:
            lines.append(f"- {q['question']}")
        return "\n".join(lines)

    def truncate_to_size(
        self,
        sections: list[ContextSection],
        max_size: int,
    ) -> tuple[list[ContextSection], list[str]]:
        """Truncate sections to fit within size limit.

        Uses priority-based truncation: lower priority sections are
        truncated or removed first.

        Args:
            sections: List of context sections
            max_size: Maximum total size

        Returns:
            Tuple of (truncated sections, list of truncated section names)
        """
        total_size = sum(s.size for s in sections)
        if total_size <= max_size:
            return sections, []

        truncated_names = []
        result = []

        # Process in reverse priority order (highest priority last)
        sorted_sections = sorted(sections, key=lambda s: -s.priority)
        remaining_size = max_size

        for section in sorted_sections:
            if section.size <= remaining_size:
                result.append(section)
                remaining_size -= section.size
            elif section.can_truncate and remaining_size > 100:
                # Truncate section
                truncated_content = section.content[: remaining_size - 50]
                truncated_content += "\n\n[Truncated. See .parac/ for full content]"
                result.append(
                    ContextSection(
                        name=section.name,
                        content=truncated_content,
                        priority=section.priority,
                        can_truncate=False,
                    )
                )
                truncated_names.append(section.name)
                remaining_size = 0
            elif not section.can_truncate:
                # Must include, will exceed limit
                result.append(section)
                remaining_size -= section.size
            else:
                # Skip entirely
                truncated_names.append(section.name)

        # Re-sort by priority for output
        return sorted(result, key=lambda s: s.priority), truncated_names

    def build(self, ide: str = "default") -> dict[str, Any]:
        """Build complete context for an IDE.

        Args:
            ide: Target IDE name for size limits

        Returns:
            Dictionary with context data ready for template rendering
        """
        max_size = self.IDE_SIZE_LIMITS.get(ide, self.IDE_SIZE_LIMITS["default"])

        # Collect data
        data = self.collect()

        # Build sections
        sections = self.build_sections(data)

        # Truncate if needed
        sections, truncated = self.truncate_to_size(sections, max_size)

        # Build result
        result = data.to_dict()
        result["sections"] = {s.name: s.content for s in sections}
        result["truncated_sections"] = truncated
        result["ide"] = ide

        return result

    def build_yaml(self, ide: str = "default") -> str:
        """Build context as YAML string.

        Args:
            ide: Target IDE name

        Returns:
            YAML-formatted context string
        """
        context = self.build(ide)
        return yaml.dump(context, default_flow_style=False, allow_unicode=True)
