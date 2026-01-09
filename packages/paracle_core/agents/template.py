"""Agent specification template - SOURCE OF TRUTH.

This module defines the template structure for new agent specifications.
TEMPLATE.md in .parac/agents/specs/ is GENERATED from this.
"""

from dataclasses import dataclass, field
from typing import Optional

from paracle_core.agents.schema import ParacPaths


@dataclass
class TemplateSection:
    """A section in the agent template."""

    heading: str
    level: int  # 1 = #, 2 = ##, 3 = ###
    content: str
    required: bool = True
    placeholder: str = ""


@dataclass
class AgentTemplate:
    """Template for creating new agent specifications.

    This template includes all required sections with .parac/ governance
    awareness built in. Users can copy TEMPLATE.md to create new agents.
    """

    # Default values for template placeholders
    agent_id: str = "new-agent"
    agent_name: str = "New Agent"
    agent_role: str = "Description of what this agent does."

    # Sections
    sections: list[TemplateSection] = field(default_factory=list)

    def __post_init__(self):
        """Initialize template sections."""
        if not self.sections:
            self.sections = self._build_default_sections()

    def _build_default_sections(self) -> list[TemplateSection]:
        """Build the default template sections."""
        return [
            # Title
            TemplateSection(
                heading=f"{self.agent_name}",
                level=1,
                content="",
                required=True,
            ),
            # Role
            TemplateSection(
                heading="Role",
                level=2,
                content=self.agent_role,
                required=True,
                placeholder="[Describe the agent's primary function in 1-2 sentences]",
            ),
            # Governance Integration (CRITICAL)
            TemplateSection(
                heading="Governance Integration",
                level=2,
                content=self._governance_content(),
                required=True,
            ),
            # Skills
            TemplateSection(
                heading="Skills",
                level=2,
                content=self._skills_content(),
                required=True,
                placeholder="[List skills from .parac/skills/]",
            ),
            # Responsibilities
            TemplateSection(
                heading="Responsibilities",
                level=2,
                content=self._responsibilities_content(),
                required=True,
                placeholder="[Categorize agent responsibilities]",
            ),
            # Tools & Capabilities (optional)
            TemplateSection(
                heading="Tools & Capabilities",
                level=2,
                content=self._tools_content(),
                required=False,
                placeholder="[List available tools]",
            ),
            # Expertise Areas (optional)
            TemplateSection(
                heading="Expertise Areas",
                level=2,
                content=self._expertise_content(),
                required=False,
                placeholder="[List technical expertise]",
            ),
            # Examples (optional)
            TemplateSection(
                heading="Examples",
                level=2,
                content=self._examples_content(),
                required=False,
                placeholder="[Add example scenarios]",
            ),
        ]

    def _governance_content(self) -> str:
        """Generate the governance integration section content."""
        return f"""
### Before Starting Any Task

1. Read `{ParacPaths.CURRENT_STATE}` - Current phase & status
2. Check `{ParacPaths.ROADMAP}` - Priorities for current phase
3. Review `{ParacPaths.OPEN_QUESTIONS}` - Check for blockers
4. Consult relevant policies in `.parac/policies/`

### During Work

- Follow `.parac/GOVERNANCE.md` rules
- Check `{ParacPaths.SKILL_ASSIGNMENTS}` for available skills
- Reference `{ParacPaths.DECISIONS}` for architectural context

### After Completing Work

Log action to `{ParacPaths.ACTION_LOG}`:

```
[TIMESTAMP] [AGENT_ID] [ACTION_TYPE] Description of work done
```

**Action Types**: IMPLEMENTATION, TEST, BUGFIX, REFACTORING, REVIEW, DOCUMENTATION, DECISION, PLANNING, UPDATE

### Decision Recording

If making an architectural decision, document in `{ParacPaths.DECISIONS}`:

```markdown
### ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: Accepted
**Context**: [Why this decision was needed]
**Decision**: [What was decided]
**Consequences**: [Impact of the decision]
```
""".strip()

    def _skills_content(self) -> str:
        """Generate the skills section content."""
        return f"""
- skill-name-1
- skill-name-2
- skill-name-3

> See `{ParacPaths.SKILL_ASSIGNMENTS}` for available skills.
""".strip()

    def _responsibilities_content(self) -> str:
        """Generate the responsibilities section content."""
        return """
### Primary Responsibility

- First responsibility item
- Second responsibility item
- Third responsibility item

### Secondary Responsibility

- Additional responsibility
- Another responsibility
""".strip()

    def _tools_content(self) -> str:
        """Generate the tools section content."""
        return """
- Tool or capability 1
- Tool or capability 2
- Tool or capability 3
""".strip()

    def _expertise_content(self) -> str:
        """Generate the expertise section content."""
        return """
- Technology or domain 1
- Technology or domain 2
- Technology or domain 3
""".strip()

    def _examples_content(self) -> str:
        """Generate the examples section content."""
        return """
### Example: [Scenario Name]

**Context**: [Describe the situation]

**Actions**:
1. [First action taken]
2. [Second action taken]
3. [Third action taken]

**Outcome**: [Result of the actions]
""".strip()

    def render(self) -> str:
        """Render the complete template as markdown."""
        lines = []

        for section in self.sections:
            # Add heading
            prefix = "#" * section.level
            lines.append(f"{prefix} {section.heading}")
            lines.append("")

            # Add content or placeholder
            if section.content:
                lines.append(section.content)
            elif section.placeholder:
                lines.append(section.placeholder)

            lines.append("")

        return "\n".join(lines).strip() + "\n"

    def render_with_metadata(self) -> str:
        """Render template with metadata header for TEMPLATE.md."""
        header = """# Agent Specification Template

> **This file is auto-generated from `paracle_core.agents.template`.**
> **Do not edit directly - changes will be overwritten.**
>
> To create a new agent:
> 1. Copy this template to `your-agent.md` in the same folder
> 2. Replace placeholders with your agent's details
> 3. Run `paracle agents validate` to check your spec
> 4. Run `paracle agents format` to auto-fix issues

---

## Template Structure

Required sections are marked with **(required)**.
Optional sections can be removed if not needed.

---

"""
        # Add section markers
        template_content = []
        for section in self.sections:
            marker = "(required)" if section.required else "(optional)"
            prefix = "#" * section.level
            template_content.append(f"{prefix} {section.heading} {marker}")
            template_content.append("")

            if section.content:
                template_content.append(section.content)
            elif section.placeholder:
                template_content.append(section.placeholder)

            template_content.append("")

        return header + "\n".join(template_content).strip() + "\n"

    @classmethod
    def create_for_agent(
        cls,
        agent_id: str,
        agent_name: Optional[str] = None,
        agent_role: Optional[str] = None,
    ) -> "AgentTemplate":
        """Create a template pre-filled for a specific agent.

        Args:
            agent_id: Agent identifier (e.g., 'my-agent')
            agent_name: Human-readable name (defaults to title-cased id)
            agent_role: Role description (defaults to placeholder)

        Returns:
            AgentTemplate instance ready to render
        """
        if agent_name is None:
            # Convert 'my-agent' to 'My Agent Agent'
            agent_name = agent_id.replace("-", " ").title() + " Agent"

        if agent_role is None:
            agent_role = f"[Describe what {agent_name} does]"

        return cls(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_role=agent_role,
        )
