"""Azure OpenAI provider adapter for AI-powered generation."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AzureProvider:
    """Azure OpenAI provider for AI-powered generation."""

    def __init__(self):
        """Initialize Azure provider."""
        try:
            import os

            from paracle_providers.openai_provider import OpenAIProvider

            # Azure OpenAI uses the OpenAI SDK with different endpoint
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_KEY")

            if not endpoint or not api_key:
                raise ValueError(
                    "Azure OpenAI credentials not found. "
                    "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY environment variables."
                )

            # Initialize with Azure configuration
            self._provider = OpenAIProvider()
            # Note: Full Azure integration would configure endpoint here
        except Exception as e:
            raise ImportError(
                f"Failed to initialize Azure provider: {e}\n"
                "Install with: pip install paracle[azure]"
            )

    @property
    def name(self) -> str:
        """Provider name."""
        return "azure"

    async def generate_agent(self, description: str, **kwargs: Any) -> dict[str, Any]:
        """Generate agent specification from description."""
        prompt = f"""Generate a Paracle agent specification for: {description}

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
```"""

        response = await self._provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating AI agent specifications.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        yaml_spec = self._extract_yaml(response.content)
        agent_name = self._extract_name(yaml_spec, "generated_agent")

        return {
            "name": agent_name,
            "yaml": yaml_spec,
            "description": description,
        }

    async def generate_skill(self, description: str, **kwargs: Any) -> dict[str, Any]:
        """Generate skill from description."""
        prompt = f"Generate a Paracle skill for: {description}\n\nReturn YAML and Python code."

        response = await self._provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating reusable skills.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        content = response.content
        yaml_spec = self._extract_yaml(content)
        code = self._extract_python(content)
        skill_name = self._extract_name(yaml_spec, "generated_skill")

        return {
            "name": skill_name,
            "yaml": yaml_spec,
            "code": code,
        }

    async def generate_workflow(
        self, description: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Generate workflow from description."""
        prompt = f"Generate a Paracle workflow for: {description}\n\nReturn ONLY YAML."

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
        workflow_name = self._extract_name(yaml_spec, "generated_workflow")

        return {
            "name": workflow_name,
            "yaml": yaml_spec,
        }

    async def enhance_documentation(self, code: str, **kwargs: Any) -> str:
        """Generate documentation for code."""
        prompt = f"Generate documentation for:\n\n```python\n{code}\n```"

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

    def _extract_yaml(self, content: str) -> str:
        """Extract YAML from content."""
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
        """Extract Python code from content."""
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

    def _extract_name(self, yaml_spec: str, default: str) -> str:
        """Extract name from YAML."""
        try:
            import yaml

            parsed = yaml.safe_load(yaml_spec)
            if isinstance(parsed, dict) and "name" in parsed:
                return parsed["name"]
        except Exception:
            pass
        return default
