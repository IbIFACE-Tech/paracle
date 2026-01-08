# Code Style Policy

## Python Style Guide

### PEP 8 Compliance
- Follow PEP 8 style guide
- Use `black` for formatting (line length: 88)
- Use `ruff` for linting
- Use `mypy` for type checking

### Type Hints
- Required for all function signatures
- Use Python 3.10+ type hints syntax
- Example:
```python
def process_data(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}
```

### Docstrings
- Use Google-style docstrings
- Required for all public functions/classes
- Example:
```python
def calculate_score(data: dict[str, float]) -> float:
    """Calculate weighted score from data.

    Args:
        data: Dictionary of metric names to values

    Returns:
        Weighted score as float

    Raises:
        ValueError: If data is empty
    """
    pass
```

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Import Organization
1. Standard library
2. Third-party packages
3. Local imports

Use `isort` for automatic sorting.

## Enforcement

- Pre-commit hooks run `black`, `ruff`, `mypy`
- CI pipeline fails on style violations
- Code review checks style compliance
