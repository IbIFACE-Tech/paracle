# Custom Skills

This directory is for project-specific custom skills.

## Creating a Custom Skill

1. Create a new YAML file in this directory
2. Follow the skill template structure
3. Register the skill in your agent specifications
4. Test thoroughly before production use

## Example: Custom Skill

```yaml
# custom/domain-expert.yaml
name: domain-expert
display_name: "Domain Expert"
category: analysis
description: |
  Expert knowledge in specific domain area.
  Provides detailed, accurate information.

level: expert

tools:
  - web_search
  - file_system

capabilities:
  - domain_knowledge
  - expert_advice
  - research

requirements:
  - skill_name: question-answering
    min_level: intermediate

tags:
  - domain
  - expert
  - specialized

version: "1.0.0"
enabled: true
```

## Best Practices

- Keep skills focused and specific
- Document use cases clearly
- Specify all tool dependencies
- Test with multiple agents
- Version your skills properly

---

For more information, see [Skills Documentation](../README.md)
