# Agent Skills

Agent skills define specific capabilities that agents can possess and utilize to perform tasks effectively.

## Overview

Paracle supports **two complementary skill formats**:

1. **YAML format** (Paracle native) - Lightweight, metadata-focused
2. **Agent Skills format** (SKILL.md) - Open standard with rich instructions

Both formats work seamlessly together and can coexist in the same project.

## Structure

```
.parac/agents/skills/
├── README.md                  # This file
├── builtin/                   # Built-in skills
│   ├── question-answering/    # Agent Skills format (SKILL.md)
│   │   └── SKILL.md
│   ├── code-generation/
│   │   └── SKILL.md
│   ├── data-analysis/
│   │   └── SKILL.md
│   ├── text-summarization.yaml  # YAML format
│   └── api-integration.yaml     # YAML format
└── custom/                    # Custom project skills
    ├── my-skill.yaml          # YAML format
    └── pdf-processing/        # Agent Skills format
        ├── SKILL.md
        ├── scripts/
        ├── references/
        └── assets/
```

## Format Comparison

### YAML Format (Paracle Native)

**Best for:**

- Quick capability declarations
- Simple skills with minimal documentation
- Fast loading and parsing
- Configuration-focused use cases

**Example:**

```yaml
# custom/email-validation.yaml
name: email-validation
display_name: "Email Validation"
category: transformation
description: Validate email addresses using regex patterns
level: basic
tools: []
capabilities:
  - regex_validation
  - format_checking
tags:
  - email
  - validation
version: "1.0.0"
enabled: true
```

**Pros:**

- ✓ Compact (~10-20 lines)
- ✓ Fast to load
- ✓ Easy to edit
- ✓ Structured metadata

**Cons:**

- ✗ No detailed instructions
- ✗ Cannot include code examples
- ✗ Limited to metadata only

### Agent Skills Format (SKILL.md)

**Best for:**

- Complex workflows with step-by-step instructions
- Skills requiring code examples
- Bundling scripts and tools
- Rich documentation with best practices
- Cross-platform compatibility (Cursor, VS Code, Claude, etc.)

**Example:**

```markdown
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF documents.
license: Apache-2.0
metadata:
  category: transformation
  level: intermediate
allowed-tools: Read Write Bash(pypdf2:*)
---

# PDF Processing Skill

## When to use this skill
...detailed instructions...

## How to extract text

...code examples...
```

**Pros:**
<https://agentskills.io>

- ✓ Rich Markdown documentation
- ✓ Code examples included
- ✓ Executable scripts (scripts/ directory)

- ✓ Progressive disclosure (load on demand)
- ✓ Open standard (<https://agentskills.io>)
- ✓ Compatible with multiple AI IDEs

**Cons:**

- ✗ Larger files (~100-500 lines)

- ✗ More complex structure
- ✗ Slower to load

## Skill Categories

### 1. Communication

- Question answering
- Conversation management
- Text summarization
- Language translation

### 2. Analysis

- Data analysis
- Pattern recognition
- Reasoning and logic
- Problem diagnosis

### 3. Creation

- Content generation
- Code generation
- Design creation

- Document creation

### 4. Transformation

- Data processing
- Format conversion

- Text reformatting
- Code refactoring

### 5. Integration

- API integration
- Tool usage
- Service interaction
- External system communication

### 6. Memory

- Context management
- Information recall
- Learning from interactons
- Knowledge retention

## Skill Levels

- **Basic** (0-25%): Fundamental capability, requires guidance
- **Intermediate** (25-50%): Competent execution, some autonomy
- **Advanced** (50-75%): Proficient execution, high autonomy
- **Expert** (75-100%): Mastery leve, innovative application

## When to Use Each Format

### Use YAML Format When

- ✓ Declaring simple agent capabilities
- ✓ Need fast loading/parsing
- ✓ Metadata-only requirements
- ✓ Configuration management
- ✓ Lightweight skill definitions

### Use Agent Skills (SKILL.md) When

- ✓ Detailed step-by-step instructions needed
- ✓ Including code examples and scripts
- ✓ Rich documentation required
- ✓ Sharing across multiple agents/IDEs
- ✓ Complex multi-step workflows
- ✓ Need progressive disclosure

## Creating Skills

### Option 1: YAML Format (Quick)

Create a YAML file in `custom/` directory:

```yaml
# custom/my-skill.yaml
name: my-skill
display_name: "My Custom Skill"
category: creation  # communication, analysis, creation, transformation, integration, memory
description: |
  Detailed description of what this skill enables the agent to do.
  Include use cases and examples.

level: intermediate  # basic, intermediate, advanced, expert

# Tools required for this skill
tools:
  - tool-name-1
  - tool-name-2

# Specific capabilities enabled by this skill
capabilities:
  - capability-1
  - capability-2
  - capability-3

# Prerequisites
requirements:
  - skill_name: prerequisite-skill
    min_level: basic

# Metadata
tags:
  - tag1
  - tag2
  - category-specific

version: "1.0.0"
enabled: true
```

## Assigning Skills to Agents

In your agent specification file:

```yaml
# .parac/agents/specs/my-agent.yaml
name: my-agent
provider: openai
model: gpt-4

# Assign skills
skills:
  - question-answering
  - data-analysis
  - my-custom-skill

# System prompt should reference skills

system_prompt: |
  You are an AI agent with the following skills:
  - Question answering
  - Data analysis
  - Custom domain-specific tasks

```

## Built-in Skills

Paracle includes several built-in skills:

### question-answering

- **Category**: Communication
- **Level**: Intermediate
- **Description**: Answer questions accurately and concisely

### code-generation

- **Category**: Creation
- **Level**: Advanced

- **Description**: Generate code in various programming languages
- **Tools**: code_executor, file_system

### data-analysis

- **Category**: Analysis
- **Level**: Advanced
- **Description**: Analyze and interpret data, generate insights

### text-summarization

- **Category**: Transformation
- **Level**: Intermediate
- **Description**: Summarize long texts into concise summaries

### api-integration

- **Category**: Integration
- **Level**: Advanced
- **Description**: Interact with external APIs and services
- **Tools**: web_search, http_client

## Skill Validation

Skills are validated against:

- Required tools availability
- Prerequisite skills presence
- Level appropriateness
- Tool permissions compatibility

## Best Practices

### 1. Skill Granularity

- Keep skills focused and specific
- Avoid overly broad capabilities

- Combine multiple skills for complex tasks

### 2. Skill Naming

- Use lowercase-with-hyphens
- Be descriptive and clear
- Follow domain conventions

### 3. Skill Dependencies

- Declare all prerequisites
- Specify minimum levels
- Document tool requirements

### 4. Skill Documentation

- Write clear descriptions
- Include use cases
- Add practical examples
- Tag appropriately

### 5. Skill Versioning

- Use semantic versioning
- Document breaking changes
- Maintain backward compatibility

## Advanced Usage

### Skill Inheritance

Agents can inherit skills from parent agents:

```yaml
# Parent agent
name: base-agent
skills:
  - question-answering
  - text-summarization

# Child agent (inherits parent skills)
name: specialized-agent
extends: base-agent
skills:
  - code-generation  # Adds to parent skills
```

### Skill Profiles

View agent skill profile:

```python
from paracle_domain.models import AgentSkillProfile

profile = AgentSkillProfile(agent_id="my-agent")
print(f"Total skills: {profile.total_skills}")
print(f"Skills by category: {profile.skills_by_category}")
print(f"Average level: {profile.average_level}")
```

### Skill Search

Find agents by required skills:

```python
from paracle_domain.skills import SkillRegistry

# Search skills
skills = SkillRegistry.search_skills("code")

# List by category
analysis_skills = SkillRegistry.list_skills(category=SkillCategory.ANALYSIS)
```

## Skill Composition

Combine skills to create complex capabilities:

```yaml
name: full-stack-developer
skills:
  # Frontend

  - html-css-generation
  - javascript-coding
  - ui-design

  # Backend

  - api-development
  - database-design
  - server-management

  # DevOps
  - deployment
  - monitoring
  - troubleshooting
```

## Troubleshooting

### Skill Not Found

- Verify skill file exists in `builtin/` or `custom/`
- Check skill name matches filename
- Ensure YAML is valid

### Tool Not Available

- Check tool is registered in `tools/registry.yaml`
- Verify tool is enabled
- Ensure proper permissions

### Prerequisite Not Met

- Install required prerequisite skills
- Check minimum level requirements
- Validate skill dependencies

## Examples

### Example 1: Data Science Agent

```yaml
name: data-scientist
skills:
  - data-analysis
  - statistical-modeling
  - data-visualization
  - python-coding

tools:
  - file_system
  - code_executor
  - data_processor
```

### Example 2: Content Creator Agent

```yaml
name: content-creator
skills:
  - creative-writing
  - text-summarization
  - seo-optimization
  - image-generation

tools:
  - web_search
  - image_generator
```

### Example 3: DevOps Agent

```yaml
name: devops-engineer
skills:
  - infrastructure-automation
  - monitoring-setup
  - troubleshooting
  - security-scanning

tools:
  - cloud_provider
  - kubectl
  - terraform
```

## Roadmap

Future skill enhancements:

- [ ] Skill marketplace
- [ ] Skill certification levels
- [ ] Skill learning and improvement
- [ ] Skill recommendations
- [ ] Multi-agent skill coordination
- [ ] Skill performance metrics

## Contributing

To contribute new skills:

1. Create skill YAML in `custom/`
2. Test with multiple agents
3. Document use cases
4. Submit for review
5. Share with community

## Resources

- [Agent Documentation](../specs/)
- [Tool Registry](../../tools/registry.yaml)
- [Security Policies](../../policies/security.yaml)
- [Workflow Templates](../../workflows/templates/)

---

**Note**: Skills are declarative and help define agent capabilities, but actual implementation depends on the underlying model, tools, and configuration.
