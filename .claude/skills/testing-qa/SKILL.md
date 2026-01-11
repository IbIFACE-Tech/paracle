---
name: testing-qa
description: Write comprehensive tests (unit, integration, e2e), manage test coverage, and ensure code quality. Use when writing tests, improving coverage, or debugging test failures.
license: Apache-2.0
compatibility: pytest, pytest-asyncio, pytest-cov, Python 3.10+
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: automation
  level: advanced
  display_name: "Testing & Quality Assurance"
  tags:
    - testing
    - pytest
    - coverage
    - qa
    - quality
  capabilities:
    - unit_testing
    - integration_testing
    - test_coverage
    - fixture_creation
    - mocking
allowed-tools: Read Write Bash(pytest:*) Bash(python:*)
---

# Testing & Quality Assurance Skill

## When to use this skill

Use this skill when:
- Writing unit tests for new code
- Creating integration or end-to-end tests
- Improving test coverage (target: >90%)
- Debugging test failures
- Setting up test fixtures and mocks
- Implementing test-driven development (TDD)
- Validating API endpoints
- Testing async code

## Paracle Testing Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_agent.py
│   ├── test_inheritance.py
│   ├── test_workflow.py
│   └── test_*.py
├── integration/             # Integration tests
│   ├── test_api_agents.py
│   ├── test_orchestrator.py
│   └── test_*.py
└── e2e/                     # End-to-end tests (future)
    └── test_full_workflow.py
```

## Testing Patterns

### Pattern 1: Unit Test Structure (AAA Pattern)

```python
# tests/unit/test_agent.py
import pytest
from paracle_domain import Agent, AgentSpec

def test_agent_creation_with_valid_spec():
    """Test that agent is created correctly with valid spec."""
    # Arrange
    spec = AgentSpec(
        name="test-agent",
        model="gpt-4",
        temperature=0.7,
        system_prompt="You are a helpful assistant",
    )

    # Act
    agent = Agent(spec=spec)

    # Assert
    assert agent.id is not None
    assert agent.spec.name == "test-agent"
    assert agent.spec.model == "gpt-4"
    assert agent.spec.temperature == 0.7

def test_agent_validation_invalid_temperature():
    """Test that invalid temperature raises ValidationError."""
    # Arrange & Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        AgentSpec(name="test", temperature=5.0)

    assert "temperature" in str(exc_info.value).lower()
```

### Pattern 2: Pytest Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path
from paracle_domain import AgentSpec, Agent
from paracle_store import AgentRepository

@pytest.fixture
def temp_dir(tmp_path):
    """Provide temporary directory for tests."""
    return tmp_path

@pytest.fixture
def sample_agent_spec():
    """Provide a sample agent spec for testing."""
    return AgentSpec(
        name="test-agent",
        model="gpt-4",
        temperature=0.7,
    )

@pytest.fixture
def sample_agent(sample_agent_spec):
    """Provide a sample agent instance."""
    return Agent(spec=sample_agent_spec)

@pytest.fixture
async def agent_repository(tmp_path):
    """Provide an in-memory agent repository."""
    repo = AgentRepository(storage_path=tmp_path / "test.db")
    await repo.initialize()
    yield repo
    await repo.close()

# Usage in tests
def test_agent_name(sample_agent):
    """Test using fixture."""
    assert sample_agent.spec.name == "test-agent"

@pytest.mark.asyncio
async def test_repository_save(agent_repository, sample_agent):
    """Test async repository."""
    saved = await agent_repository.save(sample_agent)
    assert saved.id == sample_agent.id
```

### Pattern 3: Parametrized Tests

```python
@pytest.mark.parametrize(
    "temperature,expected",
    [
        (0.0, 0.0),
        (0.5, 0.5),
        (1.0, 1.0),
        (2.0, 2.0),
    ],
)
def test_valid_temperatures(temperature, expected):
    """Test various valid temperatures."""
    spec = AgentSpec(name="test", temperature=temperature)
    assert spec.temperature == expected

@pytest.mark.parametrize(
    "invalid_temp",
    [-1.0, -0.1, 2.1, 5.0, 100.0],
)
def test_invalid_temperatures(invalid_temp):
    """Test various invalid temperatures."""
    with pytest.raises(ValidationError):
        AgentSpec(name="test", temperature=invalid_temp)

@pytest.mark.parametrize(
    "name,model,expected_id_prefix",
    [
        ("agent1", "gpt-4", "agent1-"),
        ("agent2", "claude-3", "agent2-"),
    ],
    ids=["gpt-4-agent", "claude-agent"],
)
def test_agent_id_generation(name, model, expected_id_prefix):
    """Test agent ID generation."""
    agent = Agent(spec=AgentSpec(name=name, model=model))
    assert agent.id.startswith(expected_id_prefix)
```

### Pattern 4: Mocking & Patching

```python
from unittest.mock import Mock, patch, AsyncMock
import pytest

def test_agent_with_mocked_llm():
    """Test agent with mocked LLM provider."""
    # Create mock
    mock_provider = Mock()
    mock_provider.generate.return_value = "Mocked response"

    # Use mock
    agent = Agent(spec=spec, provider=mock_provider)
    response = agent.generate("test prompt")

    # Verify
    assert response == "Mocked response"
    mock_provider.generate.assert_called_once_with("test prompt")

@pytest.mark.asyncio
async def test_async_operation_with_mock():
    """Test async operation with AsyncMock."""
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = Agent(spec=spec)

    agent = await mock_repo.get_by_id("test-id")

    assert agent.spec.name == "test-agent"
    mock_repo.get_by_id.assert_awaited_once_with("test-id")

@patch("paracle_providers.openai.OpenAIProvider")
def test_with_patch(mock_provider_class):
    """Test using @patch decorator."""
    mock_instance = Mock()
    mock_provider_class.return_value = mock_instance

    # Code that creates OpenAIProvider will use mock
    provider = OpenAIProvider(api_key="test")
    assert provider is mock_instance
```

### Pattern 5: Testing Async Code

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_agent_execution():
    """Test async agent execution."""
    agent = await create_agent_async(spec)
    result = await agent.execute("test task")
    assert result.status == "completed"

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test multiple concurrent operations."""
    agents = [
        create_agent_async(f"agent-{i}")
        for i in range(5)
    ]

    # Execute concurrently
    results = await asyncio.gather(*agents)

    assert len(results) == 5
    assert all(a.id for a in results)

@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager."""
    async with AgentRepository() as repo:
        agent = await repo.create(spec)
        assert agent.id is not None
```

### Pattern 6: Integration Testing (API)

```python
# tests/integration/test_api_agents.py
from fastapi.testclient import TestClient
from paracle_api.main import app

client = TestClient(app)

def test_create_agent_api():
    """Test agent creation via API."""
    response = client.post(
        "/api/v1/agents/",
        json={
            "name": "api-test-agent",
            "model": "gpt-4",
            "temperature": 0.7,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "api-test-agent"
    assert "id" in data

def test_agent_lifecycle():
    """Test full CRUD lifecycle."""
    # Create
    create_response = client.post(
        "/api/v1/agents/",
        json={"name": "lifecycle-agent"},
    )
    agent_id = create_response.json()["id"]

    # Read
    get_response = client.get(f"/api/v1/agents/{agent_id}")
    assert get_response.status_code == 200

    # Update
    update_response = client.put(
        f"/api/v1/agents/{agent_id}",
        json={"temperature": 0.8},
    )
    assert update_response.json()["temperature"] == 0.8

    # Delete
    delete_response = client.delete(f"/api/v1/agents/{agent_id}")
    assert delete_response.status_code == 204

    # Verify deletion
    get_after_delete = client.get(f"/api/v1/agents/{agent_id}")
    assert get_after_delete.status_code == 404
```

### Pattern 7: Testing with Fixtures and Database

```python
@pytest.fixture(scope="function")
def test_db():
    """Provide clean test database for each test."""
    from sqlalchemy import create_engine
    from paracle_store import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def db_session(test_db):
    """Provide database session."""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=test_db)
    session = Session()

    yield session

    session.rollback()
    session.close()

def test_database_operations(db_session):
    """Test database operations."""
    agent = AgentModel(name="test", model="gpt-4")
    db_session.add(agent)
    db_session.commit()

    retrieved = db_session.query(AgentModel).filter_by(name="test").first()
    assert retrieved.name == "test"
```

## Test Coverage

### Coverage Configuration

```ini
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=packages",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=90",
]

[tool.coverage.run]
source = ["packages"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/.venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### Running Coverage

```bash
# Run tests with coverage
pytest --cov=packages --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows

# Show missing lines
pytest --cov=packages --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=packages --cov-fail-under=90
```

### Coverage Targets

```
Overall Project:    >90%
Domain Layer:       >95%
Application Layer:  >90%
Infrastructure:     >85%
API Layer:          >90%
```

## Testing Best Practices

### 1. Test Naming

```python
# Good: Descriptive names
def test_agent_creation_with_valid_spec():
    ...

def test_agent_validation_when_temperature_exceeds_max():
    ...

def test_repository_saves_agent_and_generates_id():
    ...

# Bad: Vague names
def test_agent():
    ...

def test_1():
    ...
```

### 2. One Assert Per Test (when possible)

```python
# Good: Focused test
def test_agent_has_valid_id():
    agent = create_agent()
    assert agent.id is not None

def test_agent_has_correct_name():
    agent = create_agent(name="test")
    assert agent.name == "test"

# Acceptable: Related assertions
def test_agent_spec_properties():
    spec = AgentSpec(name="test", model="gpt-4", temperature=0.7)
    assert spec.name == "test"
    assert spec.model == "gpt-4"
    assert spec.temperature == 0.7
```

### 3. Test Independence

```python
# Good: Independent tests
def test_create_agent():
    agent = Agent(spec=spec)
    assert agent.id

def test_update_agent():
    agent = Agent(spec=spec)
    agent.update(temperature=0.8)
    assert agent.spec.temperature == 0.8

# Bad: Dependent tests (order matters!)
agent = None

def test_1_create():
    global agent
    agent = Agent(spec=spec)

def test_2_update():
    global agent
    agent.update(temperature=0.8)  # Fails if test_1 doesn't run first!
```

### 4. Use Fixtures for Common Setup

```python
# Good: Reusable fixture
@pytest.fixture
def configured_agent():
    spec = AgentSpec(name="test", model="gpt-4")
    return Agent(spec=spec)

def test_agent_execution(configured_agent):
    result = configured_agent.execute("task")
    assert result

def test_agent_state(configured_agent):
    assert configured_agent.state == "ready"

# Bad: Duplicated setup
def test_agent_execution():
    spec = AgentSpec(name="test", model="gpt-4")
    agent = Agent(spec=spec)
    result = agent.execute("task")
    assert result

def test_agent_state():
    spec = AgentSpec(name="test", model="gpt-4")
    agent = Agent(spec=spec)
    assert agent.state == "ready"
```

## Test-Driven Development (TDD)

### TDD Workflow

1. **Red**: Write failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code while keeping tests green

```python
# Step 1: RED - Write failing test
def test_agent_inherits_from_parent():
    parent_spec = AgentSpec(name="parent", temperature=0.7)
    child_spec = AgentSpec(name="child", inherits="parent")

    resolved = resolve_inheritance(child_spec, registry)

    assert resolved.temperature == 0.7  # FAILS - not implemented

# Step 2: GREEN - Implement minimal code
def resolve_inheritance(spec, registry):
    if spec.inherits:
        parent = registry.get(spec.inherits)
        return spec.copy(update={"temperature": parent.temperature})
    return spec

# Step 3: REFACTOR - Improve implementation
def resolve_inheritance(spec, registry):
    """Resolve agent inheritance chain."""
    if not spec.inherits:
        return spec

    parent = registry.get(spec.inherits)
    if not parent:
        raise AgentNotFoundError(spec.inherits)

    # Merge parent properties
    merged = parent.dict(exclude={"name"})
    merged.update(spec.dict(exclude_unset=True))

    return AgentSpec(**merged)
```

## Common Testing Pitfalls

❌ **Don't:**
- Test implementation details (test behavior, not code structure)
- Write tests that depend on execution order
- Use real external services (use mocks)
- Ignore test failures ("it works on my machine")
- Skip edge cases and error paths

✅ **Do:**
- Test public interfaces
- Use descriptive test names
- Keep tests fast (<1s for unit tests)
- Test both happy and sad paths
- Aim for >90% coverage

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agent.py

# Run specific test
pytest tests/unit/test_agent.py::test_agent_creation

# Run tests matching pattern
pytest -k "inheritance"

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=packages

# Run in parallel
pytest -n auto

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Effective Testing](https://testdriven.io/blog/testing-best-practices/)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- Paracle Tests: `tests/`