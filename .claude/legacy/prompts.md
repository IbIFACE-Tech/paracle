# Paracle Project Prompts

This file contains helpful prompts for common development tasks on Paracle.

## Quick Start Prompts

### Understanding the Project
```
I'm working on Paracle, a multi-agent AI framework. Can you help me understand:
- The current architecture (see docs/architecture.md)
- The roadmap and current phase (see .parac/roadmap/)
- Key domain models (see packages/paracle_domain/models.py)
```

### Starting Development
```
I want to start working on Phase 1 features. Please review:
- Current state: .parac/memory/context/current_state.yaml
- Phase 1 requirements: .parac/roadmap/PHASE1_CORE_DOMAIN.md
- Architecture decisions: .parac/roadmap/decisions.md

What should I focus on first?
```

## Feature Implementation Prompts

### Agent Inheritance
```
I need to implement the agent inheritance resolution algorithm for Paracle. 

Requirements:
- Resolve parent chain for any agent
- Merge properties from parents (system_prompt, tools, metadata)
- Override child properties take precedence
- Detect circular dependencies
- Validate all agents in chain exist

Context:
- AgentSpec model in packages/paracle_domain/models.py
- Current implementation only has parent field
- Should support multi-level inheritance (grandparent → parent → child)

Please provide:
1. Algorithm design
2. Implementation code
3. Unit tests
4. Example usage
```

### Repository Pattern
```
Implement a Repository pattern for Agent persistence with:
- Abstract base class: AgentRepository
- SQLite implementation: SQLiteAgentRepository  
- Methods: get_by_id, get_by_name, list_all, save, delete
- Async/await support
- Transaction support via Unit of Work

Location: packages/paracle_store/
Follow: Hexagonal architecture principles
Testing: Include unit tests with in-memory SQLite
```

### Event Bus
```
Create an in-memory event bus for domain events:
- EventBus class with subscribe/publish
- DomainEvent base class
- Event types: agent.created, agent.updated, workflow.started, workflow.completed
- Support async event handlers
- Include event metadata and timestamps
- Add logging for all events

Location: packages/paracle_events/
Include: Unit tests and usage examples
```

## Testing Prompts

### Unit Tests
```
Write comprehensive unit tests for [feature/class]:
- Use pytest with fixtures
- Follow arrange-act-assert pattern
- Include happy path and edge cases
- Test validation and error handling
- Target 80%+ coverage

Location: tests/unit/
Context: [provide file path and class name]
```

### Integration Tests
```
Create integration tests for [feature]:
- Test with real database (SQLite in-memory)
- Test full workflow end-to-end
- Include setup and teardown
- Use pytest-asyncio for async tests

Location: tests/integration/
```

## Refactoring Prompts

### Code Review
```
Review this code for:
- Type hints completeness
- Pydantic validation
- Error handling
- Code organization
- Performance issues
- Security concerns
- Adherence to hexagonal architecture

[paste code]
```

### Improve Code Quality
```
Refactor this code to:
- Add proper type hints
- Improve error handling
- Enhance readability
- Follow SOLID principles
- Add documentation
- Optimize performance

Current code:
[paste code]
```

## Documentation Prompts

### API Documentation
```
Generate API documentation for:
- Class: [ClassName]
- Location: [file path]

Include:
- Class description
- Method signatures with types
- Parameter descriptions
- Return value descriptions
- Usage examples
- Exceptions raised

Format: Google-style docstrings
```

### Architecture Decision Record (ADR)
```
Create an Architecture Decision Record for [decision]:

Context: [background and problem]
Decision: [chosen solution]
Consequences: [positive and negative impacts]
Alternatives: [other options considered]

Save to: .parac/roadmap/decisions.md
```

## Debugging Prompts

### Analyze Error
```
I'm getting this error:
[paste error message and traceback]

Context:
- What I'm trying to do: [description]
- Relevant code: [paste code]
- Project structure: See .parac/ and packages/

Please help me:
1. Understand the root cause
2. Provide a solution
3. Suggest preventive measures
```

### Performance Issue
```
This code is slow:
[paste code]

Context:
- Input size: [description]
- Expected performance: [target]
- Measured performance: [actual]

Please:
1. Identify bottlenecks
2. Suggest optimizations
3. Provide improved code
```

## CLI & Tools Prompts

### Add CLI Command
```
Add a new CLI command to paracle:

Command: paracle agent [subcommand]
Subcommands:
- list: List all agents
- show <name>: Show agent details
- delete <name>: Delete an agent

Requirements:
- Use Click framework
- Add rich console output
- Include error handling
- Add --help documentation
- Add to packages/paracle_cli/main.py
```

### Create Workflow Template
```
Create a workflow template for [use case]:

Requirements:
- YAML format in .parac/workflows/templates/
- Include inputs, steps, outputs
- Add to catalog.yaml
- Create example usage
- Document in .parac/workflows/README.md
```

## Maintenance Prompts

### Update Dependencies
```
Review and update project dependencies:
- Check pyproject.toml
- Identify outdated packages
- Suggest updates with rationale
- Check for security vulnerabilities
- Ensure compatibility
```

### Code Cleanup
```
Clean up [directory/file]:
- Remove unused imports
- Fix formatting issues
- Update docstrings
- Remove dead code
- Improve naming
- Add missing type hints
```

## Project Management Prompts

### Progress Check
```
Review current project status:
- Current phase progress (.parac/memory/context/current_state.yaml)
- Completed deliverables
- Remaining tasks
- Blockers or issues
- Next priorities

Provide summary and recommendations.
```

### Planning Next Phase
```
Plan Phase [N] implementation:
- Review phase requirements (.parac/roadmap/PHASE[N]_*.md)
- Break down into tasks
- Estimate effort
- Identify dependencies
- Suggest implementation order
- Create checklist
```
