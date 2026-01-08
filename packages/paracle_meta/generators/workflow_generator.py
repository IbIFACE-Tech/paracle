"""Workflow Generator for Paracle Meta-Agent.

Generates workflow definitions from goal descriptions.
"""

from typing import Any

from paracle_core.logging import get_logger

from paracle_meta.generators.base import BaseGenerator, GenerationRequest

logger = get_logger(__name__)


class WorkflowGenerator(BaseGenerator):
    """Generates workflow definitions from goal descriptions.

    Creates complete workflow specs including:
    - Steps with proper DAG structure
    - Agent assignments per step
    - Input/output definitions
    - Error handling and approval gates

    Example:
        >>> generator = WorkflowGenerator(orchestrator)
        >>> result = await generator.generate(
        ...     request=GenerationRequest(
        ...         artifact_type="workflow",
        ...         name="deployment",
        ...         description="Deploy to production with tests, rollback on failure"
        ...     ),
        ...     provider="openai",
        ...     model="gpt-4o"
        ... )
    """

    ARTIFACT_TYPE = "workflow"

    SYSTEM_PROMPT = """You are an expert at creating Paracle workflow definitions.
Your task is to generate complete, production-ready workflows from goal descriptions.

You understand:
- DAG-based workflow structure (steps, dependencies, parallel execution)
- Agent coordination patterns
- Error handling and rollback strategies
- Human-in-the-loop approval gates

Always output valid YAML that follows Paracle workflow conventions.
Ensure proper dependency ordering and realistic step definitions.
"""

    def _build_prompt(
        self,
        request: GenerationRequest,
        best_practices: list[Any] | None = None,
    ) -> str:
        """Build the prompt for workflow generation.

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

        prompt = f"""Generate a complete Paracle workflow definition for:

## Workflow Goal

**Name**: {request.name}
**Goal**: {request.description}
{context_info}

## Requirements

1. Create a DAG with clear step dependencies
2. Assign appropriate agents to each step
3. Define inputs and outputs for each step
4. Include error handling where needed
5. Add approval gates for critical operations

## Output Format

Provide the workflow in this exact YAML format:

```yaml
id: {request.name.lower().replace(' ', '_')}
name: {request.name}
description: |
  {request.description}

inputs:
  - name: input_name
    type: string
    description: Description
    required: true

outputs:
  - name: output_name
    type: string
    from: step_id.result

steps:
  - id: step_1
    name: First Step
    agent: AgentName
    task: |
      Detailed task description
    inputs:
      param: ${{inputs.input_name}}

  - id: step_2
    name: Second Step
    agent: AnotherAgent
    depends_on:
      - step_1
    task: |
      Task that depends on step_1
    inputs:
      previous_result: ${{steps.step_1.result}}

  # Add approval gate for critical operations
  - id: approval
    name: Approval Gate
    type: approval
    depends_on:
      - step_2
    approvers:
      - role: lead
    timeout: 24h

  - id: final_step
    name: Final Step
    agent: AgentName
    depends_on:
      - approval
    task: |
      Final task after approval

on_failure:
  - action: notify
    channel: slack
    message: "Workflow {{{{workflow.name}}}} failed at step {{{{step.name}}}}"
  - action: rollback
    steps: [step_1, step_2]

metadata:
  created_by: paracle_meta
  version: 1.0
```

{practices_info}

## Available Agents

Consider using these agents:
- ArchitectAgent: System design, architecture decisions
- CoderAgent: Code implementation, feature development
- ReviewerAgent: Code review, quality checks
- TesterAgent: Test creation, test execution
- DocumenterAgent: Documentation writing
- SecurityAgent: Security analysis, vulnerability scanning
- ReleaseManagerAgent: Release management, deployments

## Step Types

- Regular step: Agent executes a task
- Approval step: Human approval gate (type: approval)
- Parallel steps: Steps with same depends_on run in parallel

Now generate the complete workflow definition:
"""

        return prompt

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse workflow generation response.

        Ensures output follows Paracle workflow format.
        """
        content = super()._parse_response(response)

        # Ensure we have required fields
        required_fields = ["steps:", "id:", "name:"]
        for field in required_fields:
            if field not in content:
                logger.warning(f"Missing required field in workflow: {field}")

        return content

    def _mock_response(self, prompt: str) -> dict[str, Any]:
        """Generate mock workflow for testing."""
        # Extract name from prompt
        name = "test_workflow"
        if "**Name**:" in prompt:
            start = prompt.find("**Name**:") + 9
            end = prompt.find("\n", start)
            name = prompt[start:end].strip().lower().replace(" ", "_")

        mock_content = f"""id: {name}
name: {name.replace('_', ' ').title()}
description: |
  Generated workflow for testing purposes.
  This workflow executes a series of steps.

inputs:
  - name: target
    type: string
    description: Target for the workflow
    required: true

outputs:
  - name: result
    type: string
    from: execute.result

steps:
  - id: analyze
    name: Analyze Requirements
    agent: ArchitectAgent
    task: |
      Analyze the requirements for the task.
      Identify key components and dependencies.
    inputs:
      target: ${{{{inputs.target}}}}

  - id: implement
    name: Implement Solution
    agent: CoderAgent
    depends_on:
      - analyze
    task: |
      Implement the solution based on analysis.
    inputs:
      analysis: ${{{{steps.analyze.result}}}}

  - id: review
    name: Review Implementation
    agent: ReviewerAgent
    depends_on:
      - implement
    task: |
      Review the implementation for quality.

  - id: execute
    name: Execute Final
    agent: CoderAgent
    depends_on:
      - review
    task: |
      Execute the final implementation.

on_failure:
  - action: notify
    message: "Workflow failed"

metadata:
  created_by: paracle_meta
  version: 1.0
"""

        return {
            "content": mock_content,
            "tokens_input": len(prompt.split()) * 2,
            "tokens_output": len(mock_content.split()) * 2,
            "reasoning": "Mock workflow generation for testing",
        }


__all__ = ["WorkflowGenerator"]
