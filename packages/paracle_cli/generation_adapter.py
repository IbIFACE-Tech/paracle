"""AI generation provider adapter.

Adapts paracle_providers.LLMProvider to AIProvider protocol for generation tasks.
"""

import logging
from typing import Any

from paracle_providers.base import ChatMessage, LLMProvider

logger = logging.getLogger(__name__)


class GenerationAdapter:
    """Adapts LLMProvider to AIProvider protocol for generation tasks."""

    def __init__(self, llm_provider: LLMProvider, provider_name: str):
        """Initialize adapter.

        Args:
            llm_provider: The underlying LLM provider
            provider_name: Name of the provider (openai, anthropic, etc.)
        """
        self._provider = llm_provider
        self._provider_name = provider_name

    @property
    def name(self) -> str:
        """Provider name."""
        return self._provider_name

    async def generate_agent(self, description: str, **kwargs: Any) -> dict[str, Any]:
        """Generate agent specification from description.

        Args:
            description: Natural language description of agent.
            **kwargs: Provider-specific options.

        Returns:
            dict with keys: name, yaml, description
        """
        prompt = f"""Generate a Paracle agent specification in YAML format for the following agent:

Description: {description}

Please provide a complete agent specification in YAML format with the following structure:

```yaml
# Agent Name

## Role
Brief description of the agent's role

## Capabilities
- capability_1
- capability_2
- capability_3

## Responsibilities
- responsibility_1
- responsibility_2

## Skills
- skill_1
- skill_2

## Configuration
temperature: 0.7
max_tokens: 2000
```

Only output the YAML specification, nothing else."""

        messages = [
            ChatMessage(
                role="system",
                content="You are an expert at creating AI agent specifications for the Paracle framework. Output only valid YAML.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        response = await self._provider.chat(
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        yaml_spec = self._extract_yaml(response.content)
        agent_name = self._extract_name_from_yaml(yaml_spec, "generated_agent")

        return {"name": agent_name, "yaml": yaml_spec, "description": description}

    async def generate_skill(self, description: str, **kwargs: Any) -> dict[str, Any]:
        """Generate skill from description.

        Args:
            description: Natural language description of skill.
            **kwargs: Provider-specific options.

        Returns:
            dict with keys: name, yaml, code (optional)
        """
        prompt = f"""Generate a Paracle skill specification for the following skill:

Description: {description}

Please provide:
1. A skill YAML specification
2. A Python implementation (if applicable)

YAML format:
```yaml
name: skill_name
description: Brief description
category: category
parameters:
  - name: param1
    type: string
    description: Parameter description
    required: true
returns:
  type: string
  description: Return value description
```

Python implementation (optional):
```python
async def skill_name(param1: str) -> str:
    \"\"\"Brief description.\"\"\"
    # Implementation
    return result
```
"""

        messages = [
            ChatMessage(
                role="system",
                content="You are an expert at creating skills for the Paracle framework.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        response = await self._provider.chat(
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        yaml_spec = self._extract_yaml(response.content)
        code = self._extract_code(response.content, "python")
        skill_name = self._extract_name_from_yaml(yaml_spec, "generated_skill")

        result = {"name": skill_name, "yaml": yaml_spec}
        if code:
            result["code"] = code

        return result

    async def generate_workflow(
        self, description: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Generate workflow from description.

        Args:
            description: Natural language description of workflow.
            **kwargs: Provider-specific options.

        Returns:
            dict with keys: name, yaml
        """
        prompt = f"""Generate a Paracle workflow specification for:

Description: {description}

Please provide a complete workflow YAML specification:

```yaml
name: workflow_name
description: Brief description
steps:
  - name: step_1
    agent: agent_name
    task: Task description
    depends_on: []
  - name: step_2
    agent: agent_name
    task: Task description
    depends_on: [step_1]
```
"""

        messages = [
            ChatMessage(
                role="system",
                content="You are an expert at creating workflows for the Paracle framework.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        response = await self._provider.chat(
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000),
        )

        yaml_spec = self._extract_yaml(response.content)
        workflow_name = self._extract_name_from_yaml(yaml_spec, "generated_workflow")

        return {"name": workflow_name, "yaml": yaml_spec}

    async def enhance_documentation(self, code: str, **kwargs: Any) -> str:
        """Generate documentation for code.

        Args:
            code: Source code to document.
            **kwargs: Provider-specific options.

        Returns:
            Generated documentation (markdown).
        """
        prompt = f"""Generate comprehensive documentation for the following code:

```python
{code}
```

Please provide:
1. Overview
2. Function/class descriptions
3. Parameter documentation
4. Return value documentation
5. Usage examples
6. Notes and caveats

Format as Markdown."""

        messages = [
            ChatMessage(
                role="system",
                content="You are an expert technical writer creating clear, comprehensive documentation.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        response = await self._provider.chat(
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 3000),
        )

        return response.content

    def _extract_yaml(self, content: str) -> str:
        """Extract YAML from markdown code blocks."""
        import re

        # Try to find YAML code block
        yaml_match = re.search(r"```ya?ml\s*\n(.*?)\n```", content, re.DOTALL)
        if yaml_match:
            return yaml_match.group(1).strip()

        # Try to find any code block
        code_match = re.search(r"```\s*\n(.*?)\n```", content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Return as-is if no code blocks
        return content.strip()

    def _extract_code(self, content: str, language: str = "python") -> str | None:
        """Extract code block of specific language."""
        import re

        pattern = rf"```{language}\s*\n(.*?)\n```"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _extract_name_from_yaml(self, yaml_content: str, default: str) -> str:
        """Extract name field from YAML content."""
        import re

        # Try to find name: field
        name_match = re.search(r"^name:\s*(.+)$", yaml_content, re.MULTILINE)
        if name_match:
            return name_match.group(1).strip().strip('"').strip("'")

        # Try to find # heading
        heading_match = re.search(r"^#\s+(.+)$", yaml_content, re.MULTILINE)
        if heading_match:
            name = heading_match.group(1).strip()
            # Convert to snake_case
            name = re.sub(r"[^\w\s]", "", name)
            name = re.sub(r"\s+", "_", name).lower()
            return name

        return default
