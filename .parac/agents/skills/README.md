# Paracle Framework Development Skills

This directory contains skills specifically for developing the Paracle framework itself.

## Skills for Framework Development

### framework-architecture/
Expert-level skill for designing and evolving the Paracle architecture:
- System design and component structure
- Architecture decision records (ADRs)
- Design patterns and best practices
- Integration planning and scalability

### paracle-development/
Advanced skill for implementing and maintaining Paracle code:
- Feature implementation
- Bug fixing and debugging
- Test-driven development
- Code quality standards
- Conventional commits

## Usage

These skills are used by the development team working on Paracle itself, not by end users of the framework.

### For Framework Developers

When working on Paracle:

1. **Architecture Decisions**: Use `framework-architecture` skill
   - Designing new subsystems
   - Evaluating trade-offs
   - Writing ADRs
   - Refactoring major components

2. **Daily Development**: Use `paracle-development` skill
   - Implementing features
   - Writing tests
   - Fixing bugs
   - Code reviews

### Loading Skills

These skills are loaded automatically when working in the `.parac/` directory:

```python
from paracle_domain.skills import SkillLoader

# Load framework development skills
skills = SkillLoader.load_from_directory(".parac/agents/skills")

# Returns: framework-architecture, paracle-development
```

## Difference from User Skills

| Aspect       | Framework Skills (.parac/)      | User Skills (templates/.parac-template/) |
| ------------ | ------------------------------- | ---------------------------------------- |
| **Audience** | Paracle developers              | Paracle users                            |
| **Purpose**  | Build the framework             | Use the framework                        |
| **Scope**    | Internal architecture           | Application development                  |
| **Examples** | Add new provider, refactor core | Build agents, create workflows           |

## Contributing New Skills

To add a new framework development skill:

1. Create skill directory: `.parac/agents/skills/skill-name/`
2. Add SKILL.md with frontmatter and instructions
3. Optional: Add scripts/, references/, assets/
4. Update this README
5. Test with framework development workflows

## Skill Categories

Framework development skills typically fall into:

- **Architecture**: System design, patterns, decisions
- **Implementation**: Coding, testing, refactoring
- **DevOps**: CI/CD, deployment, monitoring
- **Documentation**: ADRs, API docs, guides

---

**Note**: These skills complement the user-facing skills in `templates/.parac-template/agents/skills/`, which are for building applications with Paracle.
