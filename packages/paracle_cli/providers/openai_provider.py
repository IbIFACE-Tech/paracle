"""OpenAI provider adapter for AI-powered generation.

This adapter wraps the existing paracle_providers.openai_provider to implement
the AIProvider protocol for generation features.
"""

import logging
from typing import Any

from paracle_providers.openai_provider import OpenAIProvider as BaseOpenAIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI provider for AI-powered generation.

    Wraps paracle_providers.OpenAIProvider to provide generation capabilities.
    """

    def __init__(self):
        """Initialize OpenAI provider."""
        try:
            self._provider = BaseOpenAIProvider()
        except Exception as e:
            raise ImportError(
                f"Failed to initialize OpenAI provider: {e}\n"
                "Install with: pip install paracle[openai]"
            )

    @property
    def name(self) -> str:
        """Provider name."""
        return "openai"

    async def generate_agent(self, description: str, **kwargs: Any) -> dict[str, Any]:
        """Generate agent specification from description."""
        prompt = self._build_agent_prompt(description)
        response = await self._provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating AI agent specifications for the Paracle framework.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        yaml_spec = self._extract_yaml(response.content)
        agent_name = self._extract_name_from_yaml(yaml_spec, "generated_agent")

        return {
            "name": agent_name,
            "yaml": yaml_spec,
            "description": description,
        }

    async def generate_skill(self, description: str, **kwargs: Any) -> dict[str, Any]:
        """Generate skill from description."""
        prompt = self._build_skill_prompt(description)
        response = await self._provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating reusable skills for AI agents.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        content = response.content
        yaml_spec = self._extract_yaml(content)
        code = self._extract_python(content)
        skill_name = self._extract_name_from_yaml(yaml_spec, "generated_skill")

        return {
            "name": skill_name,
            "yaml": yaml_spec,
            "code": code,
        }

    async def generate_workflow(
        self, description: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Generate workflow from description."""
        prompt = self._build_workflow_prompt(description)
        response = await self._provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating AI agent workflows.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        yaml_spec = self._extract_yaml(response.content)
        workflow_name = self._extract_name_from_yaml(yaml_spec, "generated_workflow")

        return {
            "name": workflow_name,
            "yaml": yaml_spec,
        }

    async def enhance_documentation(self, code: str, **kwargs: Any) -> str:
        """Generate documentation for code."""
        prompt = f"""Generate comprehensive documentation for the following code:

```python
{code}
```

Return documentation in Markdown format including:
1. Overview and purpose
2. Function/class descriptions
3. Parameter documentation
4. Return value documentation
5. Usage examples
6. Error handling notes

Make it clear and comprehensive."""

        response = await self._provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical writer.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        return response.content

    def _build_agent_prompt(self, description: str) -> str:
        """Build agent generation prompt."""
        return f"""Generate a Paracle agent specification for: {description}

Return ONLY YAML following this format:

```yaml
# Agent Name

## Role
[Brief role description]

## Responsibilities
- [Responsibility 1]
- [Responsibility 2]

## Skills
- skill_1
- skill_2

## Configuration
mode: safe
approval_required: true

## Examples
### Example 1
Task: [Task]
Expected: [Behavior]
```

Make it specific and production-ready."""

    def _build_skill_prompt(self, description: str) -> str:
        """Build skill generation prompt."""
        return f"""Generate a Paracle skill for: {description}

Return YAML specification AND Python implementation:

```yaml
name: skill_name
description: Brief description
inputs:
  - name: input1
    type: str
    required: true
outputs:
  - name: output1
    type: str
```

```python
async def execute(inputs: dict) -> dict:
    # Implementation
    pass
```"""

    def _build_workflow_prompt(self, description: str) -> str:
        """Build workflow generation prompt."""
        return f"""Generate a Paracle workflow for: {description}

Return ONLY YAML:

```yaml
name: workflow_name
description: Brief description
steps:
  - name: step1
    agent: agent_name
    task: "Task description"
```"""

    def _extract_yaml(self, content: str) -> str:
        """Extract YAML from markdown code block."""
        lines = content.split("\n")
        in_yaml = False
        yaml_lines = []

        for line in lines:
            if "```yaml" in line.lower():
                in_yaml = True
                continue
            elif line.strip().startswith("```") and in_yaml:
                break
            elif in_yaml:
                yaml_lines.append(line)

        return "\n".join(yaml_lines) if yaml_lines else content

    def _extract_python(self, content: str) -> str | None:
        """Extract Python code from markdown code block."""
        lines = content.split("\n")
        in_python = False
        python_lines = []

        for line in lines:
            if "```python" in line.lower():
                in_python = True
                continue
            elif line.strip().startswith("```") and in_python:
                break
            elif in_python:
                python_lines.append(line)

        return "\n".join(python_lines) if python_lines else None

    def _extract_name_from_yaml(self, yaml_spec: str, default: str) -> str:
        """Extract name from YAML spec."""
        try:
            import yaml

            parsed = yaml.safe_load(yaml_spec)
            if isinstance(parsed, dict) and "name" in parsed:
                return parsed["name"]

            # Try first line comment
            first_line = yaml_spec.split("\n")[0]
            if first_line.startswith("#"):
                return first_line.replace("#", "").strip().lower().replace(" ", "_")
        except Exception:
            pass

        return default
