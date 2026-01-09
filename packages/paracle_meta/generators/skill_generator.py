"""Skill Generator for Paracle Meta-Agent.

Generates skill definitions from descriptions.
"""

from typing import Any

from paracle_core.logging import get_logger

from paracle_meta.generators.base import BaseGenerator, GenerationRequest

logger = get_logger(__name__)


class SkillGenerator(BaseGenerator):
    """Generates skill definitions from descriptions.

    Creates complete skill specs including:
    - Skill description and purpose
    - Input/output specifications
    - Examples of usage
    - Integration guidelines

    Example:
        >>> generator = SkillGenerator(orchestrator)
        >>> result = await generator.generate(
        ...     request=GenerationRequest(
        ...         artifact_type="skill",
        ...         name="api-testing",
        ...         description="Test REST APIs with automated validation"
        ...     ),
        ...     provider="anthropic",
        ...     model="claude-sonnet-4-20250514"
        ... )
    """

    ARTIFACT_TYPE = "skill"

    SYSTEM_PROMPT = """You are an expert at creating Paracle skill definitions.
Your task is to generate complete, well-documented skills from descriptions.

You understand:
- Paracle skill structure (id, name, description, examples, references)
- How skills enhance agent capabilities
- Best practices for skill design (single responsibility, clear examples)
- Agent Skills specification format

Always output valid Markdown that follows Paracle skill conventions.
Include practical examples that demonstrate skill usage.
"""

    def _build_prompt(
        self,
        request: GenerationRequest,
        best_practices: list[Any] | None = None,
    ) -> str:
        """Build the prompt for skill generation.

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

        prompt = f"""Generate a complete Paracle skill definition for:

## Skill Request

**Name**: {request.name}
**Description**: {request.description}
{context_info}

## Requirements

1. Create a clear skill description
2. Define inputs and outputs
3. Include 2-3 practical examples
4. Document usage guidelines
5. Specify applicable agents

## Output Format

Provide the skill in this exact Markdown format:

```markdown
# {request.name}

## Overview

**ID**: {request.name.lower().replace(' ', '-')}
**Category**: [category]
**Complexity**: [simple|medium|complex]

## Description

[Detailed description of what this skill does and when to use it.
Explain the value it provides to agents.]

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| input_1 | string | Yes | Description |
| input_2 | object | No | Description |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| result | string | Description |

## Examples

### Example 1: [Use Case Name]

**Input:**
```yaml
input_1: "example value"
```

**Output:**
```yaml
result: "example result"
```

### Example 2: [Another Use Case]

**Input:**
```yaml
input_1: "another value"
```

**Output:**
```yaml
result: "another result"
```

## Usage Guidelines

- [Guideline 1]
- [Guideline 2]
- [Guideline 3]

## Applicable Agents

- [AgentName1]: [How this agent uses the skill]
- [AgentName2]: [How this agent uses the skill]

## References

- [Related documentation or resources]
```

{practices_info}

## Skill Categories

Common categories:
- security: Security analysis and hardening
- testing: Test creation and quality assurance
- development: Code development patterns
- documentation: Documentation creation
- operations: DevOps and operations
- analysis: Data and code analysis

Now generate the complete skill definition:
"""

        return prompt

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse skill generation response.

        Ensures output follows Paracle skill format.
        """
        content = super()._parse_response(response)

        # Basic validation
        if "## Overview" not in content and "# " not in content:
            logger.warning("Skill response may be missing structure")

        return content

    def _mock_response(self, prompt: str) -> dict[str, Any]:
        """Generate mock skill for testing."""
        # Extract name from prompt
        name = "test-skill"
        if "**Name**:" in prompt:
            start = prompt.find("**Name**:") + 9
            end = prompt.find("\n", start)
            name = prompt[start:end].strip().lower().replace(" ", "-")

        mock_content = f"""# {name}

## Overview

**ID**: {name}
**Category**: development
**Complexity**: medium

## Description

This skill enables agents to perform the task described.
It provides structured approaches and best practices for the domain.

Use this skill when you need to:
- Accomplish tasks in the specified domain
- Follow established patterns and practices
- Produce consistent, high-quality output

## Inputs

| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | The target to process |
| options | object | No | Additional options |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| result | string | The processed result |
| metadata | object | Additional metadata |

## Examples

### Example 1: Basic Usage

**Input:**
```yaml
target: "example_target"
```

**Output:**
```yaml
result: "Processed: example_target"
metadata:
  processed_at: "2026-01-08T12:00:00Z"
```

### Example 2: With Options

**Input:**
```yaml
target: "another_target"
options:
  verbose: true
```

**Output:**
```yaml
result: "Verbose processed: another_target"
metadata:
  processed_at: "2026-01-08T12:00:00Z"
  verbose: true
```

## Usage Guidelines

- Use this skill for appropriate tasks in its domain
- Provide clear and specific inputs
- Review outputs before using them

## Applicable Agents

- CoderAgent: Primary user for development tasks
- ReviewerAgent: For quality review processes

## References

- Paracle Documentation: https://paracle.dev/docs/skills
"""

        return {
            "content": mock_content,
            "tokens_input": len(prompt.split()) * 2,
            "tokens_output": len(mock_content.split()) * 2,
            "reasoning": "Mock skill generation for testing",
        }


__all__ = ["SkillGenerator"]
