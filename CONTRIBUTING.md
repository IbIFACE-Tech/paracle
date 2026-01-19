# Contributing to Paracle

Thank you for your interest in contributing to Paracle! This document provides guidelines and instructions for contributing.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/IbIFACE-Tech/paracle/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version)
   - Code samples if applicable

### Suggesting Features

1. Check [Roadmap](../.roadmap/) to see if it's already planned
2. Open a new issue with:
   - Clear use case
   - Expected behavior
   - Why it would be valuable
   - Possible implementation approach

### Pull Requests

1. **Fork** the repository
2. **Clone** your fork
3. **Create a branch** from `develop`
4. **Make your changes**
5. **Test** your changes
6. **Commit** with clear messages
7. **Push** to your fork
8. **Open a PR** to `develop` branch

## Development Setup

### Prerequisites

- Python 3.10+
- uv (recommended) or pip
- Git

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/paracle.git
cd paracle

# Add upstream remote
git remote add upstream https://github.com/IbIFACE-Tech/paracle.git

# Install dependencies
make install-dev
# Or: uv sync --all-extras

# Install pre-commit hooks
make pre-commit-install
```

### Branch Strategy

- `main`: Stable releases
- `develop`: Active development
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

## Coding Standards

### Style Guide

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Use type hints
- Docstrings for all public APIs

### Code Quality Tools

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Run all checks
make all
```

### Required Checks

Before submitting a PR, ensure:

- [ ] Tests pass (`make test`)
- [ ] Linters pass (`make lint`)
- [ ] Code is formatted (`make format`)
- [ ] Coverage > 80% for new code
- [ ] Documentation updated
- [ ] CHANGELOG updated

## Testing

### Writing Tests

```python
# tests/unit/test_agent.py
import pytest
from paracle_domain.models import AgentSpec

def test_agent_creation():
    """Test agent can be created with valid spec."""
    spec = AgentSpec(
        name="test-agent",
        provider="openai",
        model="gpt-4"
    )
    assert spec.name == "test-agent"
```

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Watch mode
make test-watch

# Specific test
uv run pytest tests/unit/test_agent.py
```

## Documentation

### Docstrings

Use Google style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

### Documentation Files

- Update relevant `.md` files in `content/docs/`
- Add examples if appropriate
- Update README if needed

## Commit Messages

Follow conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:

```
feat(agents): add agent inheritance validation

fix(cli): correct help text for workflow command

docs(readme): update installation instructions
```

## Review Process

### What We Look For

1. **Correctness**: Does it work as intended?
2. **Tests**: Are there adequate tests?
3. **Documentation**: Is it well documented?
4. **Style**: Does it follow our standards?
5. **Design**: Is it well architected?

### Review Timeline

- Initial review: Within 3 days
- Follow-up: Within 2 days
- Merge: After approval from 1+ maintainers

## Release Process

Releases follow semantic versioning (SemVer):

- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes

Maintainers handle releases.

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/IbIFACE-Tech/paracle/discussions)
- **Bugs**: Open an [Issue](https://github.com/IbIFACE-Tech/paracle/issues)
- **Security**: Email security@ibiface-tech.com

## Recognition

Contributors are recognized in:

- `CONTRIBUTORS.md`
- Release notes
- Project README

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

**Thank you for contributing to Paracle!** 🎉
