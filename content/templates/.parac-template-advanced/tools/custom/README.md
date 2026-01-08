# Custom Tools

Place your custom Python tools in this directory.

## Example Tool

```python
# .parac/tools/custom/my_tool.py

from paracle_domain.models import Tool, ToolParameter

my_tool = Tool(
    id="my_custom_tool",
    name="My Custom Tool",
    description="Does something useful",
    category="custom",
    parameters=[
        ToolParameter(
            name="input",
            type="string",
            required=True,
            description="Input data"
        )
    ]
)

async def _execute(input: str) -> dict:
    """Execute the tool."""
    result = process(input)
    return {"result": result}

my_tool._execute = _execute
```

## Auto-Discovery

Custom tools are automatically discovered and registered when the MCP server starts.

## Usage

```python
# In agent workflow
result = await agent.use_tool("my_custom_tool", input="data")
```
