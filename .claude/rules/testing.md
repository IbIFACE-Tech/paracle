# Testing Guidelines

## Test Structure

### Arrange-Act-Assert Pattern
```python
def test_agent_creation():
    # Arrange
    name = "test-agent"
    model = "gpt-4"

    # Act
    spec = AgentSpec(name=name, model=model)

    # Assert
    assert spec.name == name
    assert spec.model == model
    assert spec.temperature == 0.7  # default
```

### File Organization
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── domain/
│   │   ├── test_agent.py
│   │   └── test_workflow.py
│   ├── core/
│   └── cli/
├── integration/             # Tests with real dependencies
│   ├── test_repository.py
│   └── test_api.py
└── e2e/                     # Full system tests
    └── test_workflows.py
```

### Naming Conventions
- Test files: `test_<module>.py`
- Test functions: `test_<what>_<when>_<expected>`
- Test classes: `Test<Class>`

```python
def test_agent_spec_validates_temperature_when_above_max():
    ...

def test_agent_inherits_tools_from_parent():
    ...

class TestAgentRepository:
    def test_save_creates_new_agent(self):
        ...
```

## Fixtures

### Common Fixtures
```python
import pytest
from paracle_domain.models import AgentSpec, Agent

@pytest.fixture
def base_agent_spec() -> AgentSpec:
    """Create a basic agent specification."""
    return AgentSpec(
        name="base-agent",
        model="gpt-4",
        temperature=0.7,
        system_prompt="You are a helpful assistant."
    )

@pytest.fixture
def agent(base_agent_spec) -> Agent:
    """Create an agent instance."""
    return Agent(spec=base_agent_spec)

@pytest.fixture
async def repository(tmp_path) -> AgentRepository:
    """Create an in-memory repository for testing."""
    db_path = tmp_path / "test.db"
    repo = SQLiteAgentRepository(str(db_path))
    yield repo
    # Cleanup handled by tmp_path fixture
```

### Fixture Scope
```python
@pytest.fixture(scope="module")
def expensive_resource():
    """Shared across all tests in module."""
    resource = create_expensive_resource()
    yield resource
    resource.cleanup()
```

## Async Testing

```python
import pytest

@pytest.mark.asyncio
async def test_agent_execution():
    # Arrange
    spec = AgentSpec(name="test", model="gpt-4")
    agent = Agent(spec=spec)

    # Act
    result = await agent.execute({"task": "hello"})

    # Assert
    assert result is not None
```

## Mocking

### Use Fixtures Over Mocks When Possible
```python
# Prefer: In-memory implementation
@pytest.fixture
def repository() -> AgentRepository:
    return InMemoryAgentRepository()

# Avoid: Heavy mocking
@pytest.fixture
def repository(mocker):
    mock_repo = mocker.Mock(spec=AgentRepository)
    mock_repo.get_by_id.return_value = Agent(...)
    return mock_repo
```

### When Mocking Is Needed
```python
from unittest.mock import AsyncMock, patch

async def test_provider_called_correctly(mocker):
    mock_provider = AsyncMock()
    mock_provider.complete.return_value = "response"

    agent = Agent(spec=spec, provider=mock_provider)
    await agent.execute({"prompt": "hello"})

    mock_provider.complete.assert_called_once()
```

## Edge Cases

Always test:
- Empty inputs
- Boundary values (0, max, min)
- None/null handling
- Invalid inputs (validation errors)
- Error conditions

```python
class TestAgentSpecValidation:
    def test_empty_name_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            AgentSpec(name="", model="gpt-4")

    def test_temperature_at_max_boundary(self):
        spec = AgentSpec(name="test", model="gpt-4", temperature=2.0)
        assert spec.temperature == 2.0

    def test_temperature_above_max_raises_error(self):
        with pytest.raises(ValueError):
            AgentSpec(name="test", model="gpt-4", temperature=2.1)
```

## Coverage

- Target: 80%+ code coverage
- Focus on domain logic first
- Don't test implementation details
- Run: `make coverage`

```bash
pytest --cov=packages --cov-report=html
```

## Markers

```python
@pytest.mark.slow
def test_large_workflow_execution():
    ...

@pytest.mark.integration
async def test_database_persistence():
    ...

# Run specific markers
# pytest -m "not slow"
# pytest -m integration
```
