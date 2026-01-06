# Testing Policy

## Coverage Requirements

- Minimum coverage: 80%
- Critical paths: 95%+
- New code: 100%

## Test Types

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution (< 1s per test)

### Integration Tests
- Test component interactions
- Use test database/Redis
- Medium execution (< 10s per test)

### End-to-End Tests
- Test complete workflows
- Use staging environment
- Longer execution acceptable

## Test Structure

```python
def test_feature_name():
    """Test description."""
    # Arrange
    setup_data = create_test_data()

    # Act
    result = function_under_test(setup_data)

    # Assert
    assert result == expected_value
```

## Fixtures

Use pytest fixtures for reusable test data:

```python
@pytest.fixture
def sample_agent():
    return Agent(id="test", name="Test Agent")
```

## Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_agent_creation
```

## CI Integration

- All tests run on every PR
- Coverage report published
- Failing tests block merge
