"""Agent Generator for Paracle Meta-Agent.

Generates agent specifications from natural language descriptions.
"""

from typing import Any

from paracle_core.logging import get_logger

from paracle_meta.generators.base import BaseGenerator, GenerationRequest

logger = get_logger(__name__)


class AgentGenerator(BaseGenerator):
    """Generates agent specifications from natural language.

    Creates complete agent specs including:
    - Role and capabilities
    - System prompt
    - Tools and skills
    - Configuration (model, temperature, etc.)

    Example:
        >>> generator = AgentGenerator(orchestrator)
        >>> result = await generator.generate(
        ...     request=GenerationRequest(
        ...         artifact_type="agent",
        ...         name="SecurityAuditor",
        ...         description="Reviews Python code for security vulnerabilities"
        ...     ),
        ...     provider="anthropic",
        ...     model="claude-sonnet-4-20250514"
        ... )
    """

    ARTIFACT_TYPE = "agent"

    SYSTEM_PROMPT = """You are an expert at creating Paracle agent specifications.
Your task is to generate complete, production-ready agent specs from user descriptions.

You understand:
- Paracle agent structure (name, role, system_prompt, capabilities, tools, skills)
- Best practices for agent design (single responsibility, clear roles, minimal tools)
- LLM capabilities and appropriate configurations

Always output valid YAML or Markdown that follows Paracle conventions.
Be specific and detailed in system prompts and capability definitions.
"""

    # Agent specification template
    AGENT_TEMPLATE = """# {name}

## Overview

**Role**: {role}
**Description**: {description}

## Agent Specification

```yaml
id: {id}
name: {name}
role: {role}

model: {model}
temperature: {temperature}

system_prompt: |
{system_prompt}

capabilities:
{capabilities}

tools:
{tools}

skills:
{skills}

metadata:
  created_by: paracle_meta
  generated: true
```

## Usage

```bash
# Run this agent
paracle agent run {name} --task "your task here"
```

## Notes

{notes}
"""

    def _build_prompt(
        self,
        request: GenerationRequest,
        best_practices: list[Any] | None = None,
    ) -> str:
        """Build the prompt for agent generation.

        Args:
            request: Generation request
            best_practices: Best practices to include

        Returns:
            Formatted prompt
        """
        context_info = ""
        if request.context:
            context_info = "\n## Additional Context\n"
            for key, value in request.context.items():
                context_info += f"- {key}: {value}\n"

        practices_info = self._format_best_practices(best_practices)

        prompt = f"""Generate a complete Paracle agent specification for:

## Agent Request

**Name**: {request.name}
**Description**: {request.description}
{context_info}

## Requirements

1. Create a clear, specific role definition
2. Write an effective system prompt (2-3 paragraphs)
3. List 4-6 specific capabilities
4. Select appropriate tools (3-5 relevant tools)
5. Assign relevant skills (2-4 skills)
6. Choose appropriate model and temperature

## Output Format

Provide the agent spec in this exact format:

```yaml
id: {request.name.lower().replace(' ', '_')}
name: {request.name}
role: [Specific role description]

model: claude-sonnet-4-20250514
temperature: 0.3

system_prompt: |
  [Detailed system prompt - 2-3 paragraphs]
  [Include: role, capabilities, constraints, output format]

capabilities:
  - [Capability 1]
  - [Capability 2]
  - [Capability 3]
  - [Capability 4]

tools:
  - [tool_name_1]
  - [tool_name_2]
  - [tool_name_3]

skills:
  - [skill-name-1]
  - [skill-name-2]

metadata:
  created_by: paracle_meta
  generated: true
```

{practices_info}

## Available Tools

Common tools to consider:
- read_file: Read file contents
- write_file: Write file contents
- grep: Search file contents
- execute_shell: Execute shell commands
- http_get/http_post: HTTP requests
- static_analysis: Code analysis
- test_runner: Run tests
- security_scan: Security scanning
- documentation_generator: Generate docs

## Available Skills

Common skills to consider:
- security-hardening: Security analysis
- testing-qa: Test creation and QA
- paracle-development: Paracle framework development
- api-development: API design and implementation
- git-management: Git operations
- technical-documentation: Documentation writing
- performance-optimization: Performance tuning
- provider-integration: LLM provider setup

Now generate the complete agent specification:
"""

        return prompt

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse agent generation response.

        Ensures output follows Paracle agent spec format.
        """
        content = super()._parse_response(response)

        # Ensure we have required fields
        required_fields = ["name:", "role:", "system_prompt:"]
        for field in required_fields:
            if field not in content:
                logger.warning(f"Missing required field in agent spec: {field}")

        return content

    def _mock_response(self, prompt: str) -> dict[str, Any]:
        """Generate mock agent specification for testing."""
        # Extract name from prompt
        name = "TestAgent"
        if "**Name**:" in prompt:
            start = prompt.find("**Name**:") + 9
            end = prompt.find("\n", start)
            name = prompt[start:end].strip()

        mock_content = f"""id: {name.lower().replace(' ', '_')}
name: {name}
role: AI assistant specialized in the requested task domain

model: claude-sonnet-4-20250514
temperature: 0.3

system_prompt: |
  You are {name}, a specialized AI assistant.

  Your primary responsibilities include:
  - Analyzing and understanding the task requirements
  - Providing accurate and helpful responses
  - Following best practices and conventions

  Always be clear, concise, and thorough in your responses.

capabilities:
  - Task analysis and planning
  - Code review and improvement
  - Documentation generation
  - Problem solving

tools:
  - read_file
  - write_file
  - grep

skills:
  - technical-documentation
  - paracle-development

metadata:
  created_by: paracle_meta
  generated: true
"""

        return {
            "content": mock_content,
            "tokens_input": len(prompt.split()) * 2,
            "tokens_output": len(mock_content.split()) * 2,
            "reasoning": "Mock agent generation for testing",
        }


__all__ = ["AgentGenerator"]
