# AGENTS.md - Paracle Multi-Agent Framework

## Repository Overview

This project uses the Paracle multi-agent framework. Agents are defined in `.parac/agents/`.

## Available Agents

| Agent | Role | Invoke When |
|-------|------|-------------|
| `architect` | System Architect | Designs system architecture, modules, and interfac... |
| `coder` | Core Developer | Implements features following architecture and bes... |
| `reviewer` | Code Reviewer | Reviews code for quality, security, and best pract... |
| `tester` | Test Engineer | Creates and maintains test suites |
| `pm` | Project Manager | Manages project progress, priorities, and coordina... |
| `documenter` | Documentation Writer | Creates and maintains project documentation |
| `releasemanager` | Release Manager | Manages git workflows, versioning, releases, and d... |
| `security` | Security Expert | Security auditing, vulnerability detection, and co... |

## Agent Invocation

Prefix your request with the agent name:
- `@architect [task description]`
- `@coder [task description]`
- `@reviewer [task description]`
- `@tester [task description]`
- `@pm [task description]`
- `@documenter [task description]`
- `@releasemanager [task description]`
- `@security [task description]`

## Before Any Task

1. Read `.parac/memory/context/current_state.yaml` - Current project state
2. Check `.parac/roadmap/roadmap.yaml` - Phase and priorities
3. Review `.parac/policies/` - Coding standards

## Coding Conventions

- Run `make lint` before commits
- Follow `.parac/policies/CODE_STYLE.md`
- Document decisions in `.parac/roadmap/decisions.md`

## Testing

- Run `make test` for unit tests
- Run `make coverage` for coverage report
- Target: 80%+ coverage

## MCP Integration

Tools available via MCP server:
```bash
paracle mcp serve --stdio
```

### Available Tools
- `code_analysis` - Analyze code structure, dependencies, and complexity metrics
- `diagram_generation` - Generate architecture and design diagrams (Mermaid, PlantUML, ASCII)
- `pattern_matching` - Detect design patterns and anti-patterns in code
- `code_generation` - Generate code from templates or specifications
- `refactoring` - Refactor code with extract method, rename, and formatting
- `testing` - Run pytest tests and analyze coverage
- `git_add` - Stage files for git commit using 'git add'
- `git_commit` - Create a git commit with a message
- `git_status` - Get git repository status
- `git_push` - Push commits to remote repository
- `git_tag` - Create an annotated git tag
- `git_branch` - List, create, or delete git branches
- `git_checkout` - Switch branches or restore working tree files
- `git_diff` - Show changes between commits, branches, or working tree
- `git_log` - View git commit history
- `git_stash` - Stash changes in working directory
- `terminal_execute` - Execute shell commands cross-platform (Windows/Linux/macOS)
- `terminal_info` - Get terminal environment information (OS, shells, paths)
- `terminal_which` - Find executable location in PATH (cross-platform 'which')
- `static_analysis` - Run static analysis with ruff, mypy, or pylint
- `security_scan` - Scan for security vulnerabilities with bandit and safety
- `code_review` - Review code quality and style
- `test_generation` - Generate test cases for code
- `test_execution` - Execute pytest tests with options
- `coverage_analysis` - Analyze test coverage with pytest-cov
- `task_tracking` - Track and manage tasks
- `milestone_management` - Manage project milestones and roadmap
- `team_coordination` - Coordinate team activities and assignments
- `markdown_generation` - Generate markdown documentation
- `api_doc_generation` - Generate API documentation
- `diagram_creation` - Create diagrams for documentation
- `git_merge` - Merge a branch into current branch
- `git_pull` - Fetch and merge changes from remote repository
- `git_reset` - Reset current HEAD to specified state
- `git_fetch` - Fetch branches and tags from remote repository
- `git_remote` - Manage remote repositories
- `version_management` - Manage semantic versioning (bump, validate, compare, get_current)
- `changelog_generation` - Generate changelog from git commits using conventional commit format
- `cicd_integration` - Integrate with CI/CD pipelines (trigger, status, wait, deploy)
- `package_publishing` - Publish packages to registries (PyPI, Docker, npm, GitHub)
- `terminal_interactive` - Start interactive terminal session for REPL-style interactions

### Context Tools
- `context.current_state` - Get current project state
- `context.roadmap` - Get project roadmap
- `context.policies` - Get active policies
- `context.decisions` - Get architectural decisions

### Workflow Tools
- `workflow.run(workflow_id, inputs)` - Execute Paracle workflows
- `workflow.list` - List available workflows

**Available Workflows:**
- `feature_development` - Full feature cycle (design → code → test → review → docs)
- `bugfix` - Streamlined bugfix flow
- `code_review` - Comprehensive code review (quality, security, tests)
- `refactoring` - Safe refactoring with baseline tests
- `release` - Release management (version, changelog, publish)
- `documentation` - Documentation generation workflow

**Workflow Examples:**

@coder - Run code review:
```
workflow.run(workflow_id="code_review", inputs={changed_files: ["src/api.py"]})
```

@architect - Start feature development:
```
workflow.run(workflow_id="feature_development", inputs={feature_name: "authentication"})
```

@releasemanager - Create a release:
```
workflow.run(workflow_id="release", inputs={version_type: "minor"})
```

### Memory Tools
- `memory.log_action(agent, action, description)` - Log agent actions

## Logging Actions

After significant work, log to `.parac/memory/logs/agent_actions.log`:
```
[TIMESTAMP] [AGENT] [ACTION] Description
```

## Reference

- `.parac/` - Project governance and state
- `.parac/agents/specs/` - Full agent specifications
- `.parac/policies/` - Coding policies
- `.parac/roadmap/` - Roadmap and decisions