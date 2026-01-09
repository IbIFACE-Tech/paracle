---
name: tool-integration
description: Create custom tools, integrate external APIs, and manage tool registry. Use when extending agent capabilities with new tools.
license: Apache-2.0
compatibility: Python 3.10+, Pydantic
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: integration
  level: advanced
  display_name: "Tool Integration"
  tags:
    - tools
    - integration
    - api
    - custom-tools
  capabilities:
    - tool_creation
    - api_integration
    - tool_registration
allowed-tools: Read Write Bash(python:*)
---

# Tool Integration Skill

## When to use this skill

Use when:
- Creating custom tools for agents
- Integrating external APIs
- Adding MCP (Model Context Protocol) servers
- Managing tool registry
- Testing tool implementations

## Tool Structure

```python
# .parac/tools/custom/weather_tool.py
from pydantic import BaseModel, Field
from paracle_tools import Tool, ToolResult

class WeatherInput(BaseModel):
    \"\"\"Input for weather tool.\"\"\"
    location: str = Field(..., description=\"City name\")
    units: str = Field(default=\"metric\", description=\"Temperature units\")

class WeatherTool(Tool):
    \"\"\"Get current weather for a location.\"\"\"

    name = \"get-weather\"
    description = \"Get current weather conditions for a location\"
    input_schema = WeatherInput

    async def execute(self, input_data: WeatherInput) -> ToolResult:
        \"\"\"Execute weather lookup.\"\"\"
        # Call external API
        weather_data = await fetch_weather_api(
            location=input_data.location,
            units=input_data.units,
        )

        return ToolResult(
            success=True,
            output=f\"Temperature in {input_data.location}: {weather_data['temp']}°\",
            metadata=weather_data,
        )
```

## Tool Registration

```yaml
# .parac/tools/registry.yaml
tools:
  - name: get-weather
    path: .parac/tools/custom/weather_tool.py
    class: WeatherTool
    enabled: true

  - name: web-search
    type: mcp
    server: search-mcp
    enabled: true
```

## MCP Server Integration

```json
// .parac/mcp-servers.json
{
  \"mcpServers\": {
    \"filesystem\": {
      \"command\": \"npx\",
      \"args\": [\"-y\", \"@modelcontextprotocol/server-filesystem\", \"/workspace\"]
    },
    \"github\": {
      \"command\": \"mcp-server-github\",
      \"env\": {
        \"GITHUB_TOKEN\": \"${GITHUB_TOKEN}\"
      }
    }
  }
}
```

## Best Practices

1. **Clear tool descriptions** - Help agents understand when to use
2. **Validate inputs** - Use Pydantic for type safety
3. **Handle errors gracefully** - Return clear error messages
4. **Test thoroughly** - Unit test each tool
5. **Document usage** - Provide examples

## Resources

- Built-in Tools: `packages/paracle_tools/builtin/`
- MCP Integration: `packages/paracle_mcp/`
- Tool Examples: `examples/*_tools.py`
