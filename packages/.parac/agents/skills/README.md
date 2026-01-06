# Agent Skills

Reusable skills that can be assigned to agents.

## What are Skills?

Skills are reusable capabilities that can be shared across multiple agents.
They define specific behaviors, prompts, or tool configurations.

## Structure

Each skill is a folder with its definition:

```
skills/
└── my-first-skill/
    └── skill.yaml  (or README.md)
```

## Using Skills

Assign skills to agents in their spec files:

```markdown
## Skills

- my-first-skill
- another-skill
```
