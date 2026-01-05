"""Governance validation tests.

Tests to ensure governance structure is maintained:
- AI instruction files have pre-flight checklist
- .parac/ structure is intact
- Roadmap and current_state are consistent
- ADR numbering is sequential
"""

import re
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def root_path():
    """Get project root path."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def parac_path(root_path):
    """Get .parac/ directory path."""
    return root_path / ".parac"


class TestAIInstructions:
    """Test AI instruction files have required sections."""
    
    def test_all_ide_configs_have_checklist(self, root_path, parac_path):
        """Ensure all IDE instruction files contain pre-flight checklist."""
        ide_files = [
            root_path / ".cursorrules",
            parac_path / "integrations/ide/.clinerules",
            parac_path / "integrations/ide/.windsurfrules",
            parac_path / "integrations/ide/CLAUDE.md",
            root_path / ".github/copilot-instructions.md",
        ]
        
        required_sections = [
            "MANDATORY PRE-FLIGHT CHECKLIST",
            "PRE_FLIGHT_CHECKLIST.md",
            "VALIDATE",
            "If Task NOT in Roadmap",
        ]
        
        for file_path in ide_files:
            if not file_path.exists():
                pytest.skip(f"File not found: {file_path}")
            
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            
            for section in required_sections:
                assert section in content, (
                    f"{file_path.name} missing section: {section}"
                )
    
    def test_pre_flight_checklist_exists(self, parac_path):
        """Ensure PRE_FLIGHT_CHECKLIST.md exists."""
        checklist_path = parac_path / "PRE_FLIGHT_CHECKLIST.md"
        assert checklist_path.exists(), "PRE_FLIGHT_CHECKLIST.md not found"
        
        content = checklist_path.read_text()
        assert "9-step" in content.lower() or "9 step" in content.lower()
        assert "VALIDATE" in content


class TestGovernanceStructure:
    """Test .parac/ directory structure."""
    
    def test_required_files_exist(self, parac_path):
        """Ensure all required governance files exist."""
        required_files = [
            "GOVERNANCE.md",
            "PRE_FLIGHT_CHECKLIST.md",
            "manifest.yaml",
            "project.yaml",
            "roadmap/roadmap.yaml",
            "roadmap/decisions.md",
            "memory/context/current_state.yaml",
            "memory/context/open_questions.md",
            "memory/logs/agent_actions.log",
            "agents/manifest.yaml",
        ]
        
        for file_rel in required_files:
            file_path = parac_path / file_rel
            assert file_path.exists(), f"Missing required file: .parac/{file_rel}"
    
    def test_required_directories_exist(self, parac_path):
        """Ensure all required directories exist."""
        required_dirs = [
            "agents/specs",
            "memory/context",
            "memory/knowledge",
            "memory/logs",
            "roadmap",
            "policies",
            "integrations/ide",
        ]
        
        for dir_rel in required_dirs:
            dir_path = parac_path / dir_rel
            assert dir_path.exists(), f"Missing required directory: .parac/{dir_rel}"
            assert dir_path.is_dir(), f"Not a directory: .parac/{dir_rel}"
    
    def test_yaml_files_valid(self, parac_path):
        """Ensure all YAML files have valid syntax."""
        yaml_files = list(parac_path.rglob("*.yaml")) + list(parac_path.rglob("*.yml"))
        
        # Skip snapshots and certain generated files
        skip_patterns = ["snapshots", "__pycache__"]
        
        for yaml_path in yaml_files:
            if any(pattern in yaml_path.parts for pattern in skip_patterns):
                continue
            
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {yaml_path.relative_to(parac_path)}: {e}")


class TestRoadmapConsistency:
    """Test roadmap and current_state consistency."""
    
    def test_current_state_matches_roadmap(self, parac_path):
        """Ensure current_state.yaml phase matches roadmap.yaml."""
        roadmap_path = parac_path / "roadmap/roadmap.yaml"
        state_path = parac_path / "memory/context/current_state.yaml"
        
        with open(roadmap_path, encoding="utf-8") as f:
            roadmap = yaml.safe_load(f)
        
        with open(state_path, encoding="utf-8") as f:
            state = yaml.safe_load(f)
        
        roadmap_phase = roadmap.get("current_phase")
        state_phase = state.get("current_phase", {}).get("id")
        
        assert roadmap_phase == state_phase, (
            f"Phase mismatch: roadmap has '{roadmap_phase}' but "
            f"current_state has '{state_phase}'"
        )
    
    def test_progress_valid_range(self, parac_path):
        """Ensure progress percentage is valid (0-100)."""
        state_path = parac_path / "memory/context/current_state.yaml"
        
        with open(state_path, encoding="utf-8") as f:
            state = yaml.safe_load(f)
        
        progress = state.get("current_phase", {}).get("progress", 0)
        
        # Handle percentage strings like "75%"
        if isinstance(progress, str):
            progress = int(progress.rstrip("%"))
        
        assert 0 <= progress <= 100, f"Invalid progress: {progress}% (must be 0-100)"


class TestADRGovernance:
    """Test Architecture Decision Records governance."""
    
    def test_adr_numbering_sequential(self, parac_path):
        """Ensure ADR numbers are sequential with no gaps."""
        decisions_path = parac_path / "roadmap/decisions.md"
        
        with open(decisions_path, encoding="utf-8") as f:
            content = f.read()
        
        adr_numbers = re.findall(r"## ADR-(\d+):", content)
        
        if not adr_numbers:
            pytest.skip("No ADRs found in decisions.md")
        
        adr_numbers = sorted([int(n) for n in adr_numbers])
        
        # Check sequential (1, 2, 3, ...)
        expected = list(range(1, len(adr_numbers) + 1))
        assert adr_numbers == expected, (
            f"ADR numbering not sequential. Found: {adr_numbers}, Expected: {expected}"
        )
    
    def test_adr_format(self, parac_path):
        """Ensure ADRs follow the required format."""
        decisions_path = parac_path / "roadmap/decisions.md"
        
        with open(decisions_path, encoding="utf-8") as f:
            content = f.read()
        
        # Find all ADRs
        adr_sections = re.findall(
            r"## ADR-\d+:.*?\n\n(.*?)(?=\n## ADR-|\n---|\Z)",
            content,
            re.DOTALL
        )
        
        if not adr_sections:
            pytest.skip("No ADRs found")
        
        required_fields = ["Date", "Status", "Context", "Decision", "Consequences"]
        
        for adr_content in adr_sections[:3]:  # Check first 3 ADRs
            for field in required_fields:
                assert f"**{field}**:" in adr_content or f"**{field}**" in adr_content, (
                    f"ADR missing required field: {field}"
                )


class TestPolicies:
    """Test policy files exist and are structured."""
    
    def test_core_policies_exist(self, parac_path):
        """Ensure core policy files exist."""
        policy_files = [
            "policies/CODE_STYLE.md",
            "policies/TESTING.md",
            "policies/SECURITY.md",
        ]
        
        for policy_file in policy_files:
            policy_path = parac_path / policy_file
            assert policy_path.exists(), f"Missing policy file: {policy_file}"
            
            # Check file has content
            content = policy_path.read_text()
            assert len(content) > 100, f"Policy file too short: {policy_file}"


class TestAgents:
    """Test agent configuration and specs."""
    
    def test_agent_specs_exist(self, parac_path):
        """Ensure agent spec files exist for registered agents."""
        manifest_path = parac_path / "agents/manifest.yaml"
        
        # Note: manifest.yaml might be in workspace manifest or separate file
        if not manifest_path.exists():
            # Check workspace manifest
            workspace_manifest = parac_path / "manifest.yaml"
            with open(workspace_manifest, encoding="utf-8") as f:
                manifest = yaml.safe_load(f)
            agents = manifest.get("agents", [])
        else:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = yaml.safe_load(f)
            agents = manifest.get("agents", [])
        
        if not agents:
            pytest.skip("No agents found in manifest")
        
        specs_dir = parac_path / "agents/specs"
        
        for agent in agents:
            agent_id = agent.get("id")
            spec_file = specs_dir / f"{agent_id}.md"
            
            assert spec_file.exists(), f"Missing spec file for agent: {agent_id}"
            
            # Check spec has required sections
            content = spec_file.read_text()
            assert "## Role" in content or "**Role**" in content
            assert "## Responsibilities" in content or "Responsibilities" in content
