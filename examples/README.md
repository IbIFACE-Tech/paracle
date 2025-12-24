# Paracle Examples

This directory contains examples demonstrating Paracle's features.

## Quick Start Examples

### 1. Hello World Agent

Basic agent creation example.

```bash
python examples/hello_world_agent.py
```

**Features demonstrated**:

- Agent specification
- Agent instantiation
- Basic configuration

### 2. Agent Inheritance

Demonstrates Paracle's unique inheritance feature.

```bash
python examples/agent_inheritance.py
```

**Features demonstrated**:

- Base agent creation
- Child agent inheritance
- Multi-level inheritance
- Property overriding

## Coming Soon

### Phase 1 Examples

- Agent persistence
- Repository pattern usage
- Event handling

### Phase 2 Examples

- Multi-provider agents (OpenAI, Anthropic, Local)
- Framework integration (MSAF, LangChain)
- MCP tool integration

### Phase 3 Examples

- Workflow creation
- Multi-agent orchestration
- API usage

## Running Examples

### Prerequisites

```bash
# Install Paracle
uv pip install paracle

# Or in development
make install-dev
```

### Run an Example

```bash
# From project root
python examples/hello_world_agent.py

# Or with uv
uv run python examples/hello_world_agent.py
```

## Example Structure

Each example follows this pattern:

```python
"""Example: [Name]"""

def main() -> None:
    """Main example logic."""
    print("Example description")

    # Example code here

if __name__ == "__main__":
    main()
```

## Contributing Examples

Want to add an example? Please:

1. Follow the structure above
2. Add clear comments
3. Include print statements for clarity
4. Update this README
5. Test the example

## Need Help?

- See [Getting Started](../docs/getting-started.md) for basics
- See [Architecture](../docs/architecture.md) for design
- Open an [Issue](https://github.com/IbIFACE-Tech/paracle-lite/issues) for problems

---

**Happy coding with Paracle!** 🚀
