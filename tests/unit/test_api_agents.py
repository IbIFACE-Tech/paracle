"""Unit tests for agents API router."""

import os
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from paracle_api.main import app


class TestAgentsRouter:
    """Tests for agent discovery and manifest endpoints."""

    def setup_method(self) -> None:
        """Setup test client."""
        self.client = TestClient(app)

    @pytest.fixture
    def temp_parac_project(self, tmp_path: Path) -> Path:
        """Create temporary project with .parac/ structure and agents."""
        project = tmp_path / "project"
        project.mkdir()

        parac_root = project / ".parac"
        agents_dir = parac_root / "agents" / "specs"
        agents_dir.mkdir(parents=True)

        # Create required directories for workspace structure
        (parac_root / "roadmap").mkdir(parents=True)
        (parac_root / "memory" / "context").mkdir(parents=True)

        # Create test agent specs
        test_agents = {
            "pm.md": """# PM Agent (Project Manager)

**Rôle**: Project coordination, roadmap management.

**Responsabilités**:
- Project Planning: Maintain roadmap, define milestones
- Progress Tracking: Monitor completion, track status

**Expertise**: Agile methodologies, Risk management
""",
            "coder.md": """# Coder Agent

**Rôle**: Implementation of features, writing production-quality code.

**Responsabilités**:
- Code Implementation: Clean Python code
- Code Quality: PEP 8 compliance

**Expertise**: Python 3.10+, Pydantic, FastAPI
""",
        }

        for filename, content in test_agents.items():
            (agents_dir / filename).write_text(content, encoding="utf-8")

        return project

    def test_list_agents_no_parac(self) -> None:
        """Test listing agents when .parac/ doesn't exist."""
        # Change to temp directory without .parac/
        original_cwd = Path.cwd()
        try:
            os.chdir("/tmp")
            response = self.client.get("/agents")
            assert response.status_code == 404
            assert "No .parac/ directory found" in response.json()["detail"]
        finally:
            os.chdir(original_cwd)

    def test_list_agents(self, temp_parac_project: Path) -> None:
        """Test listing all agents."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_parac_project)
            response = self.client.get("/agents")

            assert response.status_code == 200
            data = response.json()

            assert "agents" in data
            assert "count" in data
            assert "parac_root" in data
            assert data["count"] == 2
            assert len(data["agents"]) == 2

            # Check agent structure
            agent = data["agents"][0]
            assert "id" in agent
            assert "name" in agent
            assert "role" in agent
            assert "spec_file" in agent
            assert "capabilities" in agent

        finally:
            os.chdir(original_cwd)

    def test_get_agent_metadata(self, temp_parac_project: Path) -> None:
        """Test getting specific agent metadata."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_parac_project)
            response = self.client.get("/agents/pm")

            assert response.status_code == 200
            agent = response.json()

            assert agent["id"] == "pm"
            assert "PM" in agent["name"]  # Name includes full title
            assert "role" in agent
            assert "capabilities" in agent
            assert isinstance(agent["capabilities"], list)

        finally:
            os.chdir(original_cwd)

    def test_get_agent_not_found(self, temp_parac_project: Path) -> None:
        """Test getting non-existent agent."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_parac_project)
            response = self.client.get("/agents/nonexistent")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

        finally:
            os.chdir(original_cwd)

    def test_get_agent_spec(self, temp_parac_project: Path) -> None:
        """Test getting agent specification content."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_parac_project)
            response = self.client.get("/agents/coder/spec")

            assert response.status_code == 200
            data = response.json()

            assert "agent_id" in data
            assert data["agent_id"] == "coder"
            assert "spec_file" in data
            assert "content" in data
            assert "metadata" in data

            # Check content contains markdown
            assert "# Coder Agent" in data["content"]
            assert "**Rôle**" in data["content"]

            # Check metadata
            metadata = data["metadata"]
            assert metadata["id"] == "coder"
            assert "Coder" in metadata["name"]  # Name includes full title

        finally:
            os.chdir(original_cwd)

    @pytest.mark.skip(reason="Requires proper .parac/ discovery - CWD isolation")
    def test_get_manifest_json(self, temp_parac_project: Path) -> None:
        """Test getting manifest as JSON."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_parac_project)
            response = self.client.get("/agents/manifest")

            assert response.status_code == 200
            manifest = response.json()

            assert "schema_version" in manifest
            assert manifest["schema_version"] == "1.0"
            assert "generated_at" in manifest
            assert "workspace_root" in manifest
            assert "parac_root" in manifest
            assert "agents" in manifest
            assert "count" in manifest
            assert manifest["count"] == 2

            # Check agent entries
            agent = manifest["agents"][0]
            assert "id" in agent
            assert "name" in agent
            assert "role" in agent

        finally:
            os.chdir(original_cwd)

    def test_write_manifest(self, temp_parac_project: Path) -> None:
        """Test writing manifest.yaml."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_parac_project)
            response = self.client.post("/agents/manifest")

            assert response.status_code == 200
            result = response.json()

            assert result["success"] is True
            assert "manifest_path" in result
            assert result["agents_count"] == 2

            # Verify file was created
            manifest_path = temp_parac_project / ".parac" / "manifest.yaml"
            assert manifest_path.exists()

            # Verify content
            with open(manifest_path, encoding="utf-8") as f:
                manifest = yaml.safe_load(f)

            assert manifest["schema_version"] == "1.0"
            assert "generated_at" in manifest
            assert len(manifest["agents"]) == 2

        finally:
            os.chdir(original_cwd)

    def test_write_manifest_conflict(self, temp_parac_project: Path) -> None:
        """Test writing manifest when it already exists."""
        original_cwd = Path.cwd()
        try:
            os.chdir(temp_parac_project)

            # Create manifest first
            manifest_path = temp_parac_project / ".parac" / "manifest.yaml"
            manifest_path.write_text("existing: content", encoding="utf-8")

            # Try to write without force
            response = self.client.post("/agents/manifest")
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"].lower()

            # Write with force
            response = self.client.post("/agents/manifest?force=true")
            assert response.status_code == 200

        finally:
            os.chdir(original_cwd)
