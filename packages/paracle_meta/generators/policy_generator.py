"""Policy Generator for Paracle Meta-Agent.

Generates policy definitions from requirements.
"""

from typing import Any

from paracle_core.logging import get_logger

from paracle_meta.generators.base import BaseGenerator, GenerationRequest

logger = get_logger(__name__)


class PolicyGenerator(BaseGenerator):
    """Generates policy definitions from requirements.

    Creates complete policy specs including:
    - Rules and conditions
    - Enforcement levels
    - Exceptions and overrides
    - Compliance mapping

    Example:
        >>> generator = PolicyGenerator(orchestrator)
        >>> result = await generator.generate(
        ...     request=GenerationRequest(
        ...         artifact_type="policy",
        ...         name="security-policy",
        ...         description="Enforce security best practices for all code changes",
        ...         context={"policy_type": "security"}
        ...     ),
        ...     provider="anthropic",
        ...     model="claude-sonnet-4-20250514"
        ... )
    """

    ARTIFACT_TYPE = "policy"

    SYSTEM_PROMPT = """You are an expert at creating Paracle policy definitions.
Your task is to generate complete, enforceable policies from requirements.

You understand:
- Paracle policy structure (rules, conditions, enforcement, exceptions)
- Different policy types (security, code_style, testing, compliance)
- Enforcement levels (warn, block, audit)
- Compliance standards (ISO 42001, GDPR, SOC2, OWASP)

Always output valid YAML that follows Paracle policy conventions.
Ensure rules are measurable and automatically verifiable where possible.
"""

    def _build_prompt(
        self,
        request: GenerationRequest,
        best_practices: list[Any] | None = None,
    ) -> str:
        """Build the prompt for policy generation.

        Args:
            request: Generation request
            best_practices: Best practices to include

        Returns:
            Formatted prompt
        """
        policy_type = request.context.get("policy_type", "custom")

        context_info = "\n## Additional Context\n"
        for key, value in request.context.items():
            context_info += f"- {key}: {value}\n"

        practices_info = self._format_best_practices(best_practices)

        prompt = f"""Generate a complete Paracle policy definition for:

## Policy Request

**Name**: {request.name}
**Type**: {policy_type}
**Requirements**: {request.description}
{context_info}

## Requirements

1. Define clear, measurable rules
2. Specify enforcement level for each rule
3. Include applicable conditions
4. Define exceptions where appropriate
5. Map to compliance standards if relevant

## Output Format

Provide the policy in this exact YAML format:

```yaml
id: {request.name.lower().replace(' ', '_')}
name: {request.name}
type: {policy_type}
description: |
  {request.description}

version: 1.0
enabled: true

rules:
  - id: rule_1
    name: Rule Name
    description: What this rule enforces
    enforcement: block  # warn | block | audit
    condition:
      type: [pattern_match | value_check | custom]
      # For pattern_match:
      pattern: "regex_pattern"
      # For value_check:
      field: "field_name"
      operator: [equals | not_equals | greater_than | less_than | contains]
      value: "expected_value"
    message: "Error message when rule is violated"
    exceptions:
      - reason: "Why this exception exists"
        condition:
          field: "context_field"
          equals: "exception_value"

  - id: rule_2
    name: Another Rule
    description: Another enforcement rule
    enforcement: warn
    condition:
      type: custom
      function: custom_check_function
    message: "Warning message"

# Default action when no rule matches
default_action: allow  # allow | deny | audit

# Compliance mapping
compliance:
  - standard: ISO_42001
    controls:
      - "4.1": "rule_1"
      - "5.2": "rule_2"
  - standard: OWASP_TOP_10
    controls:
      - "A01:2021": "rule_1"

# Notification settings
notifications:
  on_violation:
    - channel: log
      level: warning
    - channel: slack
      webhook_env: SLACK_WEBHOOK
      when: enforcement == "block"

# Audit settings
audit:
  enabled: true
  retention_days: 90
  include_context: true

metadata:
  created_by: paracle_meta
  policy_type: {policy_type}
  version: 1.0
```

{practices_info}

## Policy Types

- **security**: Security enforcement (code scanning, secrets detection, vulnerability checks)
- **code_style**: Code formatting and style (linting, naming conventions)
- **testing**: Test requirements (coverage thresholds, test types)
- **compliance**: Regulatory compliance (ISO, GDPR, SOC2)
- **custom**: Custom business rules

## Enforcement Levels

- **warn**: Log warning but allow action
- **block**: Prevent action from completing
- **audit**: Log for later review, don't block

## Compliance Standards

Consider mapping to:
- ISO 42001: AI Management System
- GDPR: Data protection
- SOC2: Security controls
- OWASP: Web security
- CWE: Common weaknesses

Now generate the complete policy definition:
"""

        return prompt

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse policy generation response.

        Ensures output follows Paracle policy format.
        """
        content = super()._parse_response(response)

        # Basic validation
        if "rules:" not in content:
            logger.warning("Policy response missing rules section")

        return content

    def _mock_response(self, prompt: str) -> dict[str, Any]:
        """Generate mock policy for testing."""
        # Extract name and type from prompt
        name = "test_policy"
        if "**Name**:" in prompt:
            start = prompt.find("**Name**:") + 9
            end = prompt.find("\n", start)
            name = prompt[start:end].strip().lower().replace(" ", "_")

        policy_type = "custom"
        if "**Type**:" in prompt:
            start = prompt.find("**Type**:") + 9
            end = prompt.find("\n", start)
            policy_type = prompt[start:end].strip()

        mock_content = f"""id: {name}
name: {name.replace('_', ' ').title()}
type: {policy_type}
description: |
  Generated policy for testing purposes.
  This policy defines rules for the specified requirements.

version: 1.0
enabled: true

rules:
  - id: rule_1
    name: Basic Compliance Rule
    description: Ensures basic compliance with requirements
    enforcement: warn
    condition:
      type: value_check
      field: "compliance_status"
      operator: equals
      value: "compliant"
    message: "Compliance check failed"

  - id: rule_2
    name: Critical Security Rule
    description: Blocks actions that violate security requirements
    enforcement: block
    condition:
      type: pattern_match
      pattern: "^(password|secret|key)="
    message: "Potential secret detected in content"
    exceptions:
      - reason: "Test environment exception"
        condition:
          field: "environment"
          equals: "test"

default_action: allow

compliance:
  - standard: ISO_42001
    controls:
      - "4.1": "rule_1"
      - "5.2": "rule_2"

notifications:
  on_violation:
    - channel: log
      level: warning

audit:
  enabled: true
  retention_days: 90
  include_context: true

metadata:
  created_by: paracle_meta
  policy_type: {policy_type}
  version: 1.0
"""

        return {
            "content": mock_content,
            "tokens_input": len(prompt.split()) * 2,
            "tokens_output": len(mock_content.split()) * 2,
            "reasoning": "Mock policy generation for testing",
        }


__all__ = ["PolicyGenerator"]
