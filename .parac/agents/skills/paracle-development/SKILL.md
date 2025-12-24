---
name: paracle-development
description: Develop, test, and maintain the Paracle framework codebase. Use when implementing features, fixing bugs, writing tests, or refactoring framework code.
license: Apache-2.0
compatibility: Python 3.10+, pytest, black, mypy, uv package manager
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: creation
  level: advanced
  display_name: "Paracle Framework Development"
  tags:
    - development
    - framework
    - python
    - testing
    - paracle
  capabilities:
    - framework_development
    - test_writing
    - code_refactoring
    - bug_fixing
    - feature_implementation
  requirements:
    - skill_name: code-generation
      min_level: advanced
allowed-tools: Read Write Bash(python:*) Bash(pytest:*) Bash(git:*)
---

# Paracle Framework Development Skill

## When to use this skill

Use this skill when:
- Implementing new features in Paracle framework
- Writing or updating tests
- Fixing bugs in framework code
- Refactoring existing code
- Adding new providers or adapters
- Updating documentation
- Managing dependencies

## Paracle Project Structure

```
paracle-lite/
├── .parac/                    # Framework development config
│   ├── project.yaml
│   ├── agents/specs/
│   └── workflows/
├── packages/                  # Framework packages
│   ├── paracle_core/         # Core utilities
│   ├── paracle_domain/       # Domain models
│   ├── paracle_api/          # FastAPI application
│   ├── paracle_cli/          # CLI interface
│   ├── paracle_store/        # Persistence layer
│   ├── paracle_events/       # Event system
│   ├── paracle_orchestration/# Orchestrator
│   ├── paracle_providers/    # LLM providers
│   ├── paracle_adapters/     # External adapters
│   └── paracle_tools/        # Built-in tools
├── tests/                    # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/                     # Documentation
├── examples/                 # Usage examples
├── templates/                # User templates
│   └── .parac-template/
├── pyproject.toml            # Project config
├── Makefile                  # Common tasks
└── README.md

```

## Development Workflow

### Step 1: Set up environment

```bash
# Install dependencies
uv sync

# Activate virtual environment (if needed)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Verify installation
python -c "import paracle_core; print('OK')"
```

### Step 2: Create a branch

```bash
# For features
git checkout -b feature/agent-skills-system

# For bugs
git checkout -b fix/config-validation-error

# For documentation
git checkout -b docs/update-readme
```

### Step 3: Implement changes

Follow TDD (Test-Driven Development):

```python
# 1. Write test first (tests/unit/test_skills.py)
import pytest
from paracle_domain.models import SkillSpec, SkillCategory, SkillLevel

def test_skill_creation():
    """Test creating a skill specification."""
    skill = SkillSpec(
        name="test-skill",
        display_name="Test Skill",
        category=SkillCategory.COMMUNICATION,
        description="A test skill",
        level=SkillLevel.BASIC
    )

    assert skill.name == "test-skill"
    assert skill.category == SkillCategory.COMMUNICATION
    assert skill.enabled is True

def test_skill_validation():
    """Test skill name validation."""
    with pytest.raises(ValueError):
        SkillSpec(
            name="Invalid Name",  # Should fail: uppercase and space
            display_name="Invalid",
            category=SkillCategory.COMMUNICATION,
            description="Invalid"
        )

# 2. Run test (should fail)
pytest tests/unit/test_skills.py -v

# 3. Implement feature (packages/paracle_domain/models.py)
from pydantic import BaseModel, Field, field_validator

class SkillSpec(BaseModel):
    name: str
    display_name: str
    category: SkillCategory
    description: str
    level: SkillLevel = SkillLevel.BASIC

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate skill name format."""
        if not v.islower():
            raise ValueError("Skill name must be lowercase")
        if ' ' in v:
            raise ValueError("Skill name cannot contain spaces")
        if not all(c.isalnum() or c == '-' for c in v):
            raise ValueError("Skill name must be alphanumeric with hyphens")
        return v

# 4. Run test (should pass)
pytest tests/unit/test_skills.py -v
```

### Step 4: Format and lint

```bash
# Format code with black
make format

# Sort imports
make format  # includes isort

# Type check
make typecheck

# Lint
make lint

# Run all checks
make check
```

### Step 5: Run tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_skills.py -v

# Run with coverage
make coverage

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v
```

### Step 6: Commit changes

```bash
# Add files
git add packages/paracle_domain/models.py
git add tests/unit/test_skills.py

# Commit with conventional commit message
git commit -m "feat(domain): add skill specification model

- Add SkillSpec model with validation
- Support YAML and Agent Skills formats
- Add tests for skill creation and validation

Refs: #42"
```

## Conventional Commits

Use structured commit messages:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Scopes:**
- `core`: paracle_core package
- `domain`: paracle_domain package
- `api`: paracle_api package
- `cli`: paracle_cli package
- `store`: paracle_store package
- `events`: paracle_events package
- `orchestration`: paracle_orchestration package
- `providers`: paracle_providers package
- `adapters`: paracle_adapters package
- `tools`: paracle_tools package

**Examples:**

```bash
# Feature
git commit -m "feat(domain): add agent inheritance system"

# Bug fix
git commit -m "fix(cli): resolve config validation error

When loading .parac/project.yaml, the schema validation
was failing due to missing default values.

Fixes: #123"

# Documentation
git commit -m "docs: update README with agent skills examples"

# Refactoring
git commit -m "refactor(orchestration): simplify workflow execution logic"
```

## Writing Tests

### Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_config_loader.py
import pytest
from pathlib import Path
from paracle_core.config import ConfigLoader

def test_load_valid_config(tmp_path):
    """Test loading valid configuration."""
    config_file = tmp_path / "project.yaml"
    config_file.write_text("""
    schema_version: "1.0"
    name: test-project
    """)

    config = ConfigLoader.load(config_file)
    assert config.name == "test-project"

def test_load_missing_file():
    """Test loading non-existent file."""
    with pytest.raises(FileNotFoundError):
        ConfigLoader.load(Path("nonexistent.yaml"))

def test_invalid_schema():
    """Test loading config with invalid schema."""
    with pytest.raises(ValueError, match="Invalid schema"):
        ConfigLoader.load_from_dict({"invalid": "data"})
```

### Integration Tests

Test multiple components working together:

```python
# tests/integration/test_agent_execution.py
import pytest
from paracle_domain.models import Agent, AgentConfig
from paracle_providers import OpenAIProvider

@pytest.mark.integration
def test_agent_executes_task(test_config):
    """Test complete agent execution flow."""
    # Setup
    config = AgentConfig(
        name="test-agent",
        provider="openai",
        model="gpt-4",
    )
    provider = OpenAIProvider(api_key=test_config.api_key)
    agent = Agent(config, provider)

    # Execute
    result = agent.execute("Say hello")

    # Verify
    assert result is not None
    assert "hello" in result.lower()
```

### Fixtures (conftest.py)

Share test setup across tests:

```python
# tests/conftest.py
import pytest
from pathlib import Path
from paracle_core.config import Config

@pytest.fixture
def test_config():
    """Provide test configuration."""
    return Config(
        project_name="test-project",
        api_key="test-key"
    )

@pytest.fixture
def temp_parac_dir(tmp_path):
    """Create temporary .parac directory structure."""
    parac_dir = tmp_path / ".parac"
    parac_dir.mkdir()

    # Create subdirectories
    (parac_dir / "agents" / "specs").mkdir(parents=True)
    (parac_dir / "workflows").mkdir()
    (parac_dir / "tools").mkdir()

    # Create project.yaml
    project_yaml = parac_dir / "project.yaml"
    project_yaml.write_text("""
    schema_version: "1.0"
    name: test-project
    """)

    return parac_dir
```

## Common Development Tasks

### Adding a New Provider

```python
# 1. Create provider class
# packages/paracle_providers/anthropic_provider.py
from anthropic import Anthropic
from .base import Provider

class AnthropicProvider(Provider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get('max_tokens', 1024),
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

# 2. Register provider
# packages/paracle_providers/__init__.py
from .registry import ProviderRegistry
from .anthropic_provider import AnthropicProvider

ProviderRegistry.register("anthropic", AnthropicProvider)

# 3. Add tests
# tests/unit/test_anthropic_provider.py
def test_anthropic_provider():
    provider = AnthropicProvider(api_key="test-key")
    assert provider.model == "claude-3-opus-20240229"
```

### Adding a New Tool

```python
# 1. Create tool
# packages/paracle_tools/web_search.py
from .base import Tool, ToolResult

class WebSearchTool(Tool):
    """Search the web using API."""

    name = "web_search"
    description = "Search the web for information"

    def execute(self, query: str, max_results: int = 5) -> ToolResult:
        """Execute web search."""
        try:
            results = self._search_api(query, max_results)
            return ToolResult(
                success=True,
                data=results
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )

# 2. Register tool
# packages/paracle_tools/__init__.py
from .registry import ToolRegistry
from .web_search import WebSearchTool

ToolRegistry.register(WebSearchTool())

# 3. Add to template
# templates/.parac-template/tools/registry.yaml
- name: web_search
  display_name: "Web Search"
  description: "Search the web for information"
  enabled: false
  permissions:
    - read
```

## Code Quality Standards

### Type Hints

Always use type hints:

```python
from typing import List, Dict, Optional
from pathlib import Path

def load_agents(directory: Path) -> Dict[str, AgentConfig]:
    """Load all agent configurations from directory.

    Args:
        directory: Path to agents directory

    Returns:
        Dictionary mapping agent names to configurations

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    agents: Dict[str, AgentConfig] = {}
    # implementation...
    return agents
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0.0 and 1.0

    Examples:
        >>> calculate_similarity("hello", "hello")
        1.0
        >>> calculate_similarity("hello", "world")
        0.0

    Note:
        Uses cosine similarity of character n-grams.
    """
    pass
```

### Error Handling

Be specific and helpful:

```python
# ❌ Bad
def load_config(path):
    try:
        return yaml.load(open(path))
    except:
        return None

# ✓ Good
def load_config(path: Path) -> Config:
    """Load configuration from YAML file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}\n"
            f"Expected location: .parac/project.yaml"
        )

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(
            f"Invalid YAML in {path}: {e}\n"
            f"Check syntax at line {e.problem_mark.line}"
        )

    try:
        return Config(**data)
    except ValidationError as e:
        raise ValueError(
            f"Invalid configuration in {path}:\n{e}"
        )
```

## Debugging Tips

### Use logging

```python
import logging

logger = logging.getLogger(__name__)

def process_agent(agent: Agent):
    logger.debug(f"Processing agent: {agent.name}")
    logger.info(f"Agent {agent.name} started")

    try:
        result = agent.execute()
        logger.info(f"Agent {agent.name} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Agent {agent.name} failed: {e}", exc_info=True)
        raise
```

### Use pdb for debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint (Python 3.7+)
breakpoint()
```

### Use pytest debugging

```bash
# Drop into pdb on failure
pytest --pdb

# Show print statements
pytest -s

# Run last failed tests
pytest --lf

# Verbose output
pytest -vv
```

## Performance Optimization

### Profile code

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here
    result = expensive_operation()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10
```

### Use caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def load_skill(skill_name: str) -> SkillSpec:
    """Load skill with caching."""
    return SkillLoader.load(skill_name)
```

## Related Skills

- **framework-architecture**: For design decisions
- **code-review**: For reviewing PRs
- **documentation-writing**: For docs updates

## References

- [Python Best Practices](https://docs.python-guide.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [Conventional Commits](https://www.conventionalcommits.org/)
