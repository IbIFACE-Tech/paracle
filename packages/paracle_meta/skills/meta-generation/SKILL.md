---
name: meta-generation
description: AI-powered generation of Paracle artifacts (agents, workflows, skills, policies) from natural language descriptions. Use when you need to create new framework components programmatically.
license: Apache-2.0
compatibility: Python 3.10+, requires LLM provider (OpenAI/Anthropic/Ollama)
metadata:
  author: paracle-team
  version: "1.0.0"
  category: creation
  level: advanced
  display_name: "Meta Generation"
  tags:
    - ai
    - generation
    - meta
    - agents
    - workflows
  capabilities:
    - generate-agents
    - generate-workflows
    - generate-skills
    - generate-policies
allowed-tools: Read Write Bash(python:*) WebSearch
---

# Meta Generation Skill

## Overview

This skill enables AI-powered generation of Paracle framework artifacts from natural language descriptions. It leverages the `paracle_meta` engine to create well-structured, validated components.

## When to Use

Use this skill when you need to:
- Create new agent specifications from requirements
- Generate workflow definitions from process descriptions
- Build skill templates from capability descriptions
- Draft policy documents from compliance requirements

## Prerequisites

1. LLM provider configured (one of):
   - `ANTHROPIC_API_KEY` for Claude
   - `OPENAI_API_KEY` for GPT models
   - Ollama running locally

2. `paracle_meta` package available

## Generation Commands

### Generate an Agent

```python
from paracle_meta import MetaAgent, GenerationRequest

async with MetaAgent() as meta:
    result = await meta.generate_agent(
        name="SecurityAuditor",
        description="Reviews code for security vulnerabilities following OWASP guidelines"
    )
    print(result.content)
```

### Generate a Workflow

```python
result = await meta.generate_workflow(
    name="code-review-pipeline",
    description="Multi-stage code review with security and quality checks"
)
```

### Generate a Skill

```python
result = await meta.generate_skill(
    name="api-testing",
    description="Automated REST API testing with validation"
)
```

### Generate a Policy

```python
result = await meta.generate_policy(
    name="data-retention",
    description="GDPR-compliant data retention policy"
)
```

## Provider Selection

```python
# Use specific provider
result = await meta.generate_agent(
    name="MyAgent",
    description="...",
    provider="anthropic",  # or "openai", "ollama"
    model="claude-sonnet-4-20250514"
)

# Cost-optimized (uses cheapest suitable provider)
result = await meta.generate_agent(
    name="MyAgent",
    description="...",
    optimize_cost=True
)
```

## Output Locations

Generated artifacts are saved to:
- Agents: `.parac/agents/specs/{name}.md`
- Workflows: `.parac/workflows/{name}.yaml`
- Skills: `.parac/agents/skills/{name}/SKILL.md`
- Policies: `.parac/policies/{name}.md`

## Quality Scoring

Each generation includes quality metrics:

```python
result = await meta.generate_agent(...)

print(f"Quality Score: {result.quality_score}")
print(f"Tokens Used: {result.tokens_input + result.tokens_output}")
print(f"Cost: ${result.cost:.4f}")
```

## Best Practices

1. **Be Specific**: Detailed descriptions produce better results
2. **Provide Context**: Include domain-specific requirements
3. **Review Output**: Always review and validate generated artifacts
4. **Iterate**: Use feedback to improve generations
5. **Track Costs**: Monitor token usage and costs

## Error Handling

```python
try:
    result = await meta.generate_agent(...)
except ProviderError as e:
    print(f"Provider error: {e}")
    # Try fallback provider
except GenerationError as e:
    print(f"Generation failed: {e}")
```

## Integration with CLI

```bash
# Generate via CLI (future)
paracle generate agent SecurityAuditor \
    --description "Reviews code for security vulnerabilities"

paracle generate workflow review-pipeline \
    --description "Multi-stage code review"
```

## Related Skills

- [workflow-orchestration](../workflow-orchestration/): Execute generated workflows
- [agent-configuration](../agent-configuration/): Configure generated agents
- [tool-integration](../tool-integration/): Add tools to generated agents
