"""Tests for Agent Skills system.

Tests skill discovery, loading, validation, and integration with agents.
"""

from pathlib import Path

import pytest

# Test utilities for skill system
SKILLS_DIR = Path(__file__).parent.parent.parent / \
    ".parac" / "agents" / "skills"
SPECS_DIR = Path(__file__).parent.parent.parent / ".parac" / "agents" / "specs"


class TestSkillDiscovery:
    """Test skill discovery and file structure."""

    def test_skills_directory_exists(self):
        """Skills directory should exist."""
        assert SKILLS_DIR.exists(), f"Skills directory not found: {SKILLS_DIR}"
        assert SKILLS_DIR.is_dir(), "Skills path is not a directory"

    def test_skill_directories_exist(self):
        """All expected skill directories should exist."""
        expected_skills = [
            "agent-configuration",
            "api-development",
            "cicd-devops",
            "framework-architecture",
            "migration-upgrading",
            "paracle-development",
            "performance-optimization",
            "provider-integration",
            "security-hardening",
            "technical-documentation",
            "testing-qa",
            "tool-integration",
            "workflow-orchestration",
        ]

        for skill_name in expected_skills:
            skill_dir = SKILLS_DIR / skill_name
            assert skill_dir.exists(
            ), f"Skill directory not found: {skill_name}"
            assert skill_dir.is_dir(
            ), f"Skill path is not a directory: {skill_name}"

    def test_skill_readme_exists(self):
        """Skills README should exist and document all skills."""
        readme = SKILLS_DIR / "README.md"
        assert readme.exists(), "Skills README.md not found"

        content = readme.read_text(encoding="utf-8")
        assert "skills" in content.lower()
        assert "api-development" in content
        assert "testing-qa" in content


class TestSkillStructure:
    """Test individual skill file structure."""

    @pytest.fixture
    def all_skills(self) -> list[str]:
        """Return list of all skill directory names."""
        return [
            d.name
            for d in SKILLS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

    def test_each_skill_has_skill_md(self, all_skills):
        """Each skill directory must have a SKILL.md file."""
        for skill_name in all_skills:
            skill_file = SKILLS_DIR / skill_name / "SKILL.md"
            assert skill_file.exists(
            ), f"SKILL.md missing for skill: {skill_name}"

    def test_skill_md_has_required_sections(self, all_skills):
        """SKILL.md files must have required sections."""
        required_sections = ["name:", "description:"]

        for skill_name in all_skills:
            skill_file = SKILLS_DIR / skill_name / "SKILL.md"
            content = skill_file.read_text(encoding="utf-8")

            # Check for YAML frontmatter
            assert content.startswith(
                "---"), f"Missing YAML frontmatter: {skill_name}"
            assert "---" in content[3:
                                    ], f"Incomplete YAML frontmatter: {skill_name}"

            # Check required fields
            for section in required_sections:
                assert (
                    section in content
                ), f"Missing {section} in {skill_name}/SKILL.md"

    def test_skill_md_content_not_empty(self, all_skills):
        """SKILL.md files must have actual content after frontmatter."""
        for skill_name in all_skills:
            skill_file = SKILLS_DIR / skill_name / "SKILL.md"
            content = skill_file.read_text(encoding="utf-8")

            # Split frontmatter and content
            parts = content.split("---")
            assert len(parts) >= 3, f"Invalid SKILL.md structure: {skill_name}"

            # Content after frontmatter should exist
            markdown_content = parts[2].strip()
            assert len(markdown_content) > 100, (
                f"SKILL.md content too short for {skill_name}: "
                f"{len(markdown_content)} chars"
            )


class TestSkillOptionalDirectories:
    """Test optional directories (scripts, references, assets)."""

    def test_scripts_directory_structure(self):
        """Skills with scripts/ should have executable examples."""
        skills_with_scripts = [
            "api-development",
            "testing-qa",
            "cicd-devops",
            "workflow-orchestration",
            "tool-integration",
            "performance-optimization",
            "security-hardening",
            "migration-upgrading",
        ]

        for skill_name in skills_with_scripts:
            scripts_dir = SKILLS_DIR / skill_name / "scripts"
            if scripts_dir.exists():
                # Should have at least one script file
                script_files = list(scripts_dir.glob("*"))
                assert len(script_files) > 0, (
                    f"Empty scripts/ directory: {skill_name}"
                )

    def test_references_directory_structure(self):
        """Skills with references/ should have documentation."""
        skills_with_references = [
            "api-development",
            "provider-integration",
            "performance-optimization",
            "security-hardening",
        ]

        for skill_name in skills_with_references:
            refs_dir = SKILLS_DIR / skill_name / "references"
            if refs_dir.exists():
                # Should have at least one reference file
                ref_files = list(refs_dir.glob("*.md"))
                assert len(ref_files) > 0, (
                    f"Empty references/ directory: {skill_name}"
                )

    def test_assets_directory_structure(self):
        """Skills with assets/ should have templates."""
        skills_with_assets = [
            "technical-documentation",
            "cicd-devops",
            "workflow-orchestration",
            "agent-configuration",
            "migration-upgrading",
        ]

        for skill_name in skills_with_assets:
            assets_dir = SKILLS_DIR / skill_name / "assets"
            if assets_dir.exists():
                # Should have at least one asset file
                asset_files = list(assets_dir.glob("*"))
                assert len(asset_files) > 0, (
                    f"Empty assets/ directory: {skill_name}"
                )


class TestAgentSkillIntegration:
    """Test agent specifications correctly reference skills."""

    @pytest.fixture
    def agent_specs(self) -> list[Path]:
        """Return all agent spec files."""
        return list(SPECS_DIR.glob("*.md"))

    def test_agent_specs_exist(self, agent_specs):
        """Agent specification files should exist."""
        expected_agents = [
            "architect.md",
            "coder.md",
            "documenter.md",
            "pm.md",
            "reviewer.md",
            "tester.md",
        ]

        spec_names = [spec.name for spec in agent_specs]
        for agent_name in expected_agents:
            assert agent_name in spec_names, f"Agent spec not found: {agent_name}"

    def test_agent_specs_have_skills_section(self, agent_specs):
        """Agent specs should have Skills section."""
        for spec_file in agent_specs:
            content = spec_file.read_text(encoding="utf-8")
            assert "## Skills" in content, (
                f"Missing Skills section in {spec_file.name}"
            )

    def test_agent_skills_are_valid(self, agent_specs):
        """Skills referenced in agent specs should exist."""
        valid_skills = {
            d.name
            for d in SKILLS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        }

        for spec_file in agent_specs:
            content = spec_file.read_text(encoding="utf-8")

            # Find Skills section
            if "## Skills" not in content:
                continue

            # Extract skills (lines starting with - after ## Skills)
            lines = content.split("\n")
            in_skills_section = False
            agent_skills = []

            for line in lines:
                if "## Skills" in line:
                    in_skills_section = True
                    continue
                elif line.startswith("## ") and in_skills_section:
                    # Next section, stop
                    break
                elif in_skills_section and line.strip().startswith("-"):
                    # Extract skill name
                    skill = line.strip()[1:].strip()
                    agent_skills.append(skill)

            # Validate each skill exists
            for skill in agent_skills:
                assert skill in valid_skills, (
                    f"Invalid skill '{skill}' in {spec_file.name}. "
                    f"Available: {sorted(valid_skills)}"
                )


class TestSkillAssignments:
    """Test SKILL_ASSIGNMENTS.md accuracy."""

    def test_skill_assignments_file_exists(self):
        """SKILL_ASSIGNMENTS.md should exist."""
        assignments_file = SKILLS_DIR.parent / "SKILL_ASSIGNMENTS.md"
        assert assignments_file.exists(), "SKILL_ASSIGNMENTS.md not found"

    def test_skill_assignments_documents_all_agents(self):
        """SKILL_ASSIGNMENTS.md should document all agents."""
        assignments_file = SKILLS_DIR.parent / "SKILL_ASSIGNMENTS.md"
        content = assignments_file.read_text(encoding="utf-8")

        expected_agents = [
            "Architect Agent",
            "Coder Agent",
            "Documenter Agent",
            "PM Agent",
            "Reviewer Agent",
            "Tester Agent",
        ]

        for agent in expected_agents:
            assert agent in content, (
                f"Agent '{agent}' not documented in SKILL_ASSIGNMENTS.md"
            )

    def test_skill_assignments_documents_all_skills(self):
        """SKILL_ASSIGNMENTS.md should reference all skills."""
        assignments_file = SKILLS_DIR.parent / "SKILL_ASSIGNMENTS.md"
        content = assignments_file.read_text(encoding="utf-8")

        # Get all skill directories
        all_skills = [
            d.name
            for d in SKILLS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        for skill in all_skills:
            assert skill in content, (
                f"Skill '{skill}' not documented in SKILL_ASSIGNMENTS.md"
            )


class TestProgressiveDisclosure:
    """Test progressive disclosure pattern compliance."""

    def test_skill_md_discovery_size(self):
        """SKILL.md discovery metadata should be ~100 tokens."""
        skill_file = SKILLS_DIR / "api-development" / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        parts = content.split("---")
        if len(parts) >= 2:
            frontmatter = parts[1]
            # Rough token estimate: ~4 chars per token
            token_count = len(frontmatter) / 4
            assert 50 < token_count < 300, (
                f"Discovery metadata too large: ~{token_count} tokens "
                "(should be ~100-250 tokens)"
            )

    def test_skill_md_activation_size(self):
        """Full SKILL.md should be 2000-5000 tokens for activation."""
        skill_file = SKILLS_DIR / "api-development" / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        # Rough token estimate: ~4 chars per token
        token_count = len(content) / 4
        assert 500 < token_count < 10000, (
            f"SKILL.md size out of range: ~{token_count} tokens "
            "(should be 2000-5000 tokens for activation)"
        )


class TestManifestIntegration:
    """Test manifest.yaml references agent specs."""

    def test_manifest_exists(self):
        """manifest.yaml should exist."""
        manifest_file = SPECS_DIR.parent / "manifest.yaml"
        assert manifest_file.exists(), "manifest.yaml not found"

    def test_manifest_references_specs(self):
        """manifest.yaml should reference all agent spec files."""
        manifest_file = SPECS_DIR.parent / "manifest.yaml"
        content = manifest_file.read_text(encoding="utf-8")

        expected_specs = [
            "specs/architect.md",
            "specs/coder.md",
            "specs/documenter.md",
            "specs/pm.md",
            "specs/reviewer.md",
            "specs/tester.md",
        ]

        for spec_path in expected_specs:
            assert spec_path in content, (
                f"Spec file '{spec_path}' not referenced in manifest.yaml"
            )

    def test_manifest_has_agent_ids(self):
        """manifest.yaml should define agent IDs."""
        manifest_file = SPECS_DIR.parent / "manifest.yaml"
        content = manifest_file.read_text(encoding="utf-8")

        expected_ids = ["architect", "coder",
                        "reviewer", "tester", "pm", "documenter"]

        for agent_id in expected_ids:
            assert f"id: {agent_id}" in content, (
                f"Agent ID '{agent_id}' not found in manifest.yaml"
            )
