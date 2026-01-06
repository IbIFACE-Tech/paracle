# Tools

Tool definitions and hooks for Paracle.

## Structure

- `custom/` - Custom tools you create
- `builtin/` - Built-in Paracle tools
- `registry.yaml` - Tool registry

## Creating Custom Tools

Create a YAML file in `custom/`:

```yaml
name: my_tool
description: What this tool does
parameters:
  - name: param1
    type: string
    required: true
```
