# Paracle Framework Development Skills

This directory contains specialized skills for developing the Paracle framework itself, following the Agent Skills specification from agentskills.io.

## Available Skills

### Architecture & Design

#### framework-architecture/
Expert-level skill for designing and evolving the Paracle architecture:
- System design and component structure
- Architecture decision records (ADRs)
- Design patterns and best practices
- Integration planning and scalability
- Hexagonal architecture implementation

#### paracle-development/
Advanced skill for implementing and maintaining Paracle code:
- Feature implementation
- Bug fixing and debugging
- Test-driven development
- Code quality standards (PEP 8, Black, type hints)
- Conventional commits

### Implementation Skills

#### api-development/
Comprehensive skill for building REST APIs with FastAPI:
- Endpoint design and implementation
- Request/response schema validation with Pydantic
- Error handling and status codes
- Middleware and dependency injection
- OpenAPI documentation
- API testing with TestClient

#### workflow-orchestration/
Advanced skill for building multi-step agent workflows:
- DAG-based workflow design
- Parallel execution patterns
- Error handling and retries
- Workflow monitoring
- Context management
- Conditional execution

### Quality & Testing

#### testing-qa/
Expert-level skill for comprehensive testing:
- pytest patterns (Arrange-Act-Assert)
- Fixtures and parametrization
- Mocking with AsyncMock
- Test coverage configuration (>90% target)
- Integration testing
- TDD workflow

#### technical-documentation/
Specialized skill for creating clear documentation:
- README structure and best practices
- Tutorial and guide patterns
- API reference documentation
- Architecture documentation
- Google-style docstrings
- Progressive disclosure

### Operations & Deployment

#### cicd-devops/
Advanced skill for CI/CD and containerization:
- GitHub Actions workflows
- Docker multi-stage builds
- docker-compose orchestration
- Health checks and monitoring
- Deployment strategies
- Structured logging

#### git-management/
Expert-level skill for git workflow management:
- Conventional commits enforcement
- Branching strategies (Gitflow)
- Merge operations and conflict resolution
- Git hooks automation
- Pull request management
- Tag and reference management

#### release-automation/
Expert-level skill for release orchestration:
- Semantic versioning (major.minor.patch)
- Changelog generation from commits
- PyPI package publishing
- Docker image publishing
- GitHub release creation
- Pre-release and hotfix workflows

#### performance-optimization/
Expert-level skill for system performance:
- Profiling and bottleneck identification
- Database query optimization
- Caching strategies (in-memory, Redis)
- Async optimization patterns
- API response optimization
- Monitoring and metrics (<500ms p95 target)

#### security-hardening/
Critical skill for securing the platform:
- JWT authentication implementation
- Role-based access control (RBAC)
- Input validation and SQL injection prevention
- Rate limiting
- Secret management
- CORS and security headers
- Security testing

### Configuration & Integration

#### agent-configuration/
Intermediate skill for configuring agents:
- Agent spec structure
- Inheritance setup
- Skill assignment
- Tool configuration
- Configuration best practices

#### tool-integration/
Advanced skill for extending agent capabilities:
- Custom tool creation
- External API integration
- MCP server integration
- Tool registry management
- Tool testing

#### provider-integration/
Intermediate skill for managing LLM providers:
- Provider configuration (OpenAI, Anthropic, Azure, Ollama)
- Provider switching
- API key management
- Custom provider implementation
- Multi-provider support

### Maintenance & Evolution

#### migration-upgrading/
Critical skill for version management:
- Database schema migrations (Alembic)
- Data migration strategies
- Configuration file conversion
- Breaking change handling
- Version compatibility checking
- Rollback procedures

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

3. **API Development**: Use `api-development` skill
   - Creating new endpoints
   - Schema validation
   - Error handling
   - Testing APIs

4. **Workflow Design**: Use `workflow-orchestration` skill
   - Building agent workflows
   - DAG implementation
   - Parallel execution

5. **Quality Assurance**: Use `testing-qa` skill
   - Writing comprehensive tests
   - Achieving coverage targets
   - Integration testing

6. **Documentation**: Use `technical-documentation` skill
   - Writing clear docs
   - API references
   - Tutorials

7. **Deployment**: Use `cicd-devops` skill
   - CI/CD pipelines
   - Docker configuration
   - Deployment automation

8. **Git Workflows**: Use `git-management` skill
   - Conventional commits
   - Branch management
   - Merge strategies
   - Git hooks

9. **Release Management**: Use `release-automation` skill
   - Version bumping
   - Changelog generation
   - Package publishing
   - Release orchestration

10. **Performance**: Use `performance-optimization` skill
    - Profiling code
    - Optimizing queries
    - Implementing caching

11. **Security**: Use `security-hardening` skill
    - Authentication/authorization
    - Input validation
    - Security testing

12. **Configuration**: Use `agent-configuration`, `tool-integration`, `provider-integration`
    - Configuring agents
    - Adding tools
    - Managing providers

13. **Upgrades**: Use `migration-upgrading` skill
    - Version migrations
    - Schema changes
    - Breaking changes

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
