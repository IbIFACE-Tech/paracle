"""Skill injection for enhancing agent prompts with skill knowledge."""

import logging

from paracle_orchestration.skill_loader import Skill

logger = logging.getLogger(__name__)


class SkillInjector:
    """Injects skill knowledge into agent system prompts."""

    def __init__(self, injection_mode: str = "full"):
        """Initialize skill injector.

        Args:
            injection_mode: How to inject skills:
                - "full": Include full skill content
                - "summary": Include only descriptions
                - "references": Include references only
                - "minimal": Just skill names
        """
        self.injection_mode = injection_mode

    def inject_skills(
        self,
        system_prompt: str | None,
        skills: list[Skill],
    ) -> str:
        """Inject skills into system prompt.

        Args:
            system_prompt: Original system prompt (can be None)
            skills: List of skills to inject

        Returns:
            Enhanced system prompt with skill knowledge
        """
        if not skills:
            return system_prompt or ""

        base_prompt = system_prompt or ""

        if self.injection_mode == "full":
            return self._inject_full(base_prompt, skills)
        elif self.injection_mode == "summary":
            return self._inject_summary(base_prompt, skills)
        elif self.injection_mode == "references":
            return self._inject_references(base_prompt, skills)
        else:  # minimal
            return self._inject_minimal(base_prompt, skills)

    def _inject_full(self, base_prompt: str, skills: list[Skill]) -> str:
        """Inject full skill content."""
        skill_section = "\n\n## Available Skills\n\n"
        skill_section += "You have access to the following specialized skills:\n\n"

        for skill in skills:
            skill_section += f"### {skill.name}\n\n"
            skill_section += f"{skill.content}\n\n"

            if skill.assets:
                skill_section += "**Available Assets:**\n"
                for asset_name in skill.assets.keys():
                    skill_section += f"- {asset_name}\n"
                skill_section += "\n"

            if skill.scripts:
                skill_section += "**Available Scripts:**\n"
                for script_name in skill.scripts.keys():
                    skill_section += f"- {script_name}\n"
                skill_section += "\n"

        skill_section += "---\n\n"
        skill_section += "Use these skills to enhance your capabilities and provide better assistance.\n"

        return base_prompt + skill_section

    def _inject_summary(self, base_prompt: str, skills: list[Skill]) -> str:
        """Inject skill summaries only."""
        skill_section = "\n\n## Available Skills\n\n"

        for skill in skills:
            skill_section += f"- **{skill.name}**: {skill.description}\n"

        skill_section += "\n"
        return base_prompt + skill_section

    def _inject_references(self, base_prompt: str, skills: list[Skill]) -> str:
        """Inject skill references only."""
        skill_section = "\n\n## Skill References\n\n"

        for skill in skills:
            if skill.references:
                skill_section += f"### {skill.name}\n\n"
                for ref_name, ref_content in skill.references.items():
                    skill_section += (
                        f"**{ref_name}:**\n```\n{ref_content[:500]}...\n```\n\n"
                    )

        return base_prompt + skill_section

    def _inject_minimal(self, base_prompt: str, skills: list[Skill]) -> str:
        """Inject minimal skill information."""
        skill_names = [skill.name for skill in skills]
        skill_section = f"\n\nAvailable skills: {', '.join(skill_names)}\n"
        return base_prompt + skill_section

    def create_skill_context(self, skills: list[Skill]) -> dict:
        """Create a skill context dictionary for providers.

        Args:
            skills: List of skills

        Returns:
            Dictionary with skill information
        """
        return {
            "skills_enabled": True,
            "skills": [skill.to_dict() for skill in skills],
            "skill_count": len(skills),
            "skill_ids": [skill.skill_id for skill in skills],
        }
