"""Tests for skill loading and injection system."""


import pytest
from paracle_orchestration.skill_injector import SkillInjector
from paracle_orchestration.skill_loader import Skill, SkillLoader


class TestSkillLoader:
    """Tests for SkillLoader."""

    def test_skill_loader_init(self):
        """Test skill loader initialization."""
        loader = SkillLoader()
        assert loader.skills_dir.name == "skills"
        assert loader._skill_cache == {}

    def test_discover_skills(self):
        """Test skill discovery."""
        loader = SkillLoader()
        skills = loader.discover_skills()
        assert isinstance(skills, list)
        # Should find skills if .parac/agents/skills/ exists
        if loader.skills_dir.exists():
            assert len(skills) > 0

    def test_load_skill(self):
        """Test loading a specific skill."""
        loader = SkillLoader()
        skills = loader.discover_skills()
        if skills:
            skill = loader.load_skill(skills[0])
            assert skill is not None
            assert isinstance(skill, Skill)
            assert skill.skill_id == skills[0]

    def test_load_nonexistent_skill(self):
        """Test loading a skill that doesn't exist."""
        loader = SkillLoader()
        skill = loader.load_skill("nonexistent-skill")
        assert skill is None

    def test_load_agent_skills(self):
        """Test loading skills for an agent."""
        loader = SkillLoader()
        skills = loader.load_agent_skills("coder")
        assert isinstance(skills, list)

    def test_get_agent_skill_ids(self):
        """Test getting skill IDs for an agent."""
        loader = SkillLoader()
        skill_ids = loader.get_agent_skill_ids("coder")
        assert isinstance(skill_ids, list)

    def test_skill_caching(self):
        """Test that skills are cached."""
        loader = SkillLoader()
        skills = loader.discover_skills()
        if skills:
            skill1 = loader.load_skill(skills[0])
            skill2 = loader.load_skill(skills[0])
            # Should be the same object (cached)
            assert skill1 is skill2

    def test_clear_cache(self):
        """Test cache clearing."""
        loader = SkillLoader()
        skills = loader.discover_skills()
        if skills:
            loader.load_skill(skills[0])
            assert len(loader._skill_cache) > 0
            loader.clear_cache()
            assert len(loader._skill_cache) == 0


class TestSkill:
    """Tests for Skill model."""

    def test_skill_creation(self):
        """Test skill creation."""
        skill = Skill(
            skill_id="test-skill",
            name="Test Skill",
            description="A test skill",
            content="# Test Content",
        )
        assert skill.skill_id == "test-skill"
        assert skill.name == "Test Skill"
        assert skill.description == "A test skill"
        assert skill.content == "# Test Content"

    def test_skill_to_dict(self):
        """Test skill serialization."""
        skill = Skill(
            skill_id="test-skill",
            name="Test Skill",
            description="A test skill",
            content="# Test Content",
            assets={"template.py": "code"},
            scripts={"script.sh": "bash"},
        )
        data = skill.to_dict()
        assert data["skill_id"] == "test-skill"
        assert data["name"] == "Test Skill"
        assert data["has_assets"] is True
        assert data["has_scripts"] is True


class TestSkillInjector:
    """Tests for SkillInjector."""

    def test_injector_init(self):
        """Test injector initialization."""
        injector = SkillInjector()
        assert injector.injection_mode == "full"

        injector = SkillInjector(injection_mode="summary")
        assert injector.injection_mode == "summary"

    def test_inject_skills_empty(self):
        """Test injecting empty skills list."""
        injector = SkillInjector()
        prompt = injector.inject_skills("Original prompt", [])
        assert prompt == "Original prompt"

    def test_inject_skills_full_mode(self):
        """Test full injection mode."""
        injector = SkillInjector(injection_mode="full")
        skills = [
            Skill(
                skill_id="skill1",
                name="Skill 1",
                description="First skill",
                content="# Skill 1 Content",
            )
        ]
        prompt = injector.inject_skills("Original", skills)
        assert "Original" in prompt
        assert "## Available Skills" in prompt
        assert "Skill 1" in prompt
        assert "# Skill 1 Content" in prompt

    def test_inject_skills_summary_mode(self):
        """Test summary injection mode."""
        injector = SkillInjector(injection_mode="summary")
        skills = [
            Skill(
                skill_id="skill1",
                name="Skill 1",
                description="First skill",
                content="# Skill 1 Content",
            )
        ]
        prompt = injector.inject_skills("Original", skills)
        assert "Original" in prompt
        assert "## Available Skills" in prompt
        assert "Skill 1" in prompt
        assert "First skill" in prompt
        # Should NOT include full content
        assert "# Skill 1 Content" not in prompt

    def test_inject_skills_minimal_mode(self):
        """Test minimal injection mode."""
        injector = SkillInjector(injection_mode="minimal")
        skills = [
            Skill(
                skill_id="skill1",
                name="Skill 1",
                description="First skill",
                content="# Skill 1 Content",
            ),
            Skill(
                skill_id="skill2",
                name="Skill 2",
                description="Second skill",
                content="# Skill 2 Content",
            ),
        ]
        prompt = injector.inject_skills("Original", skills)
        assert "Original" in prompt
        assert "Skill 1, Skill 2" in prompt

    def test_create_skill_context(self):
        """Test skill context creation."""
        injector = SkillInjector()
        skills = [
            Skill(
                skill_id="skill1",
                name="Skill 1",
                description="First skill",
                content="Content",
            )
        ]
        context = injector.create_skill_context(skills)
        assert context["skills_enabled"] is True
        assert context["skill_count"] == 1
        assert context["skill_ids"] == ["skill1"]
        assert len(context["skills"]) == 1


@pytest.mark.integration
class TestSkillIntegration:
    """Integration tests for skill system."""

    def test_load_and_inject_workflow(self):
        """Test complete load and inject workflow."""
        # Load skills
        loader = SkillLoader()
        skills = loader.discover_skills()

        if not skills:
            pytest.skip("No skills found in .parac/agents/skills/")

        # Load first skill
        skill = loader.load_skill(skills[0])
        assert skill is not None

        # Inject into prompt
        injector = SkillInjector(injection_mode="full")
        prompt = injector.inject_skills("Base prompt", [skill])

        assert "Base prompt" in prompt
        assert skill.name in prompt

    def test_agent_skill_assignment_loading(self):
        """Test loading skills based on agent assignments."""
        loader = SkillLoader()

        # Test known agents
        agents = ["coder", "architect", "tester", "documenter"]

        for agent_name in agents:
            skills = loader.load_agent_skills(agent_name)
            # Should return a list (may be empty if no skills assigned)
            assert isinstance(skills, list)
