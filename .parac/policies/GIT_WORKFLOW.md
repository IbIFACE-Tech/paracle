# Git Workflow Policy

## Purpose

This document defines the git workflow, branching strategy, commit conventions, and release process for the Paracle project.

## Branching Strategy

### Git Flow Model

Paracle uses a **Git Flow** branching model with the following branches:

```
main (production)
  ├─ develop (integration)
  │   ├─ feature/* (new features)
  │   ├─ bugfix/* (non-critical bugs)
  │   └─ docs/* (documentation)
  ├─ release/* (release preparation)
  └─ hotfix/* (critical production fixes)
```

### Branch Types

#### `main`
- **Purpose**: Production-ready code
- **Protection**: Protected, requires PR + review
- **Deployment**: Auto-deploys to production
- **Tags**: All releases tagged here

#### `develop`
- **Purpose**: Integration branch for ongoing work
- **Protection**: Protected, requires PR
- **Deployment**: Auto-deploys to staging
- **Source**: All feature branches merge here

#### `feature/*`
- **Purpose**: New features or enhancements
- **Naming**: `feature/short-description` or `feature/issue-123-description`
- **Branch from**: `develop`
- **Merge to**: `develop`
- **Lifespan**: Short-lived (1-2 weeks)

#### `bugfix/*`
- **Purpose**: Non-critical bug fixes
- **Naming**: `bugfix/issue-456-description`
- **Branch from**: `develop`
- **Merge to**: `develop`
- **Lifespan**: Short-lived (1-3 days)

#### `release/*`
- **Purpose**: Prepare for production release
- **Naming**: `release/0.1.0`
- **Branch from**: `develop`
- **Merge to**: `main` AND `develop`
- **Lifespan**: Short-lived (1-2 days)
- **Activities**: Version bumping, changelog, final testing

#### `hotfix/*`
- **Purpose**: Critical production bug fixes
- **Naming**: `hotfix/0.0.2-critical-bug`
- **Branch from**: `main`
- **Merge to**: `main` AND `develop`
- **Lifespan**: Very short (hours)
- **Priority**: Highest

### Branch Lifecycle

#### Feature Development

```bash
# 1. Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/agent-skills

# 2. Work on feature
git add .
git commit -m "feat(agents): implement skill discovery system"

# 3. Keep updated with develop
git fetch origin
git rebase origin/develop

# 4. Push and create PR
git push origin feature/agent-skills
gh pr create --base develop --title "feat: Agent skill discovery"

# 5. After approval, squash merge to develop
# (Done via GitHub UI)

# 6. Delete branch
git branch -d feature/agent-skills
git push origin --delete feature/agent-skills
```

#### Release Process

```bash
# 1. Create release branch
git checkout develop
git pull origin develop
git checkout -b release/0.1.0

# 2. Version bump and changelog
python scripts/bump_version.py minor  # 0.0.1 → 0.1.0
python scripts/generate_changelog.py
git add .
git commit -m "chore(release): bump version to 0.1.0"

# 3. Final testing
make test
make lint
make typecheck

# 4. Merge to main
git checkout main
git merge --no-ff release/0.1.0
git tag -a v0.1.0 -m "Release v0.1.0: Agent Skills & Phase 5"
git push origin main --tags

# 5. Merge back to develop
git checkout develop
git merge --no-ff release/0.1.0
git push origin develop

# 6. Delete release branch
git branch -d release/0.1.0
git push origin --delete release/0.1.0

# 7. Publish
python -m build
twine upload dist/*
gh release create v0.1.0 --title "Paracle v0.1.0" --notes-file CHANGELOG.md
```

#### Hotfix Process

```bash
# 1. Create hotfix branch
git checkout main
git pull origin main
git checkout -b hotfix/0.1.1-security-fix

# 2. Apply fix
# ... fix code ...
git add .
git commit -m "fix(security): patch XSS vulnerability in API"

# 3. Quick validation
pytest tests/
ruff check .

# 4. Version bump
python scripts/bump_version.py patch  # 0.1.0 → 0.1.1

# 5. Merge to main
git checkout main
git merge --no-ff hotfix/0.1.1-security-fix
git tag -a v0.1.1 -m "Hotfix v0.1.1: Security patch"
git push origin main --tags

# 6. Merge to develop
git checkout develop
git merge --no-ff hotfix/0.1.1-security-fix
git push origin develop

# 7. Delete hotfix branch
git branch -d hotfix/0.1.1-security-fix

# 8. Emergency publish
python -m build
twine upload dist/*
gh release create v0.1.1 --title "Hotfix v0.1.1 - Security Patch"
```

## Conventional Commits

### Format

All commits MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

| Type         | Description                             | Version Impact | Example                                       |
| ------------ | --------------------------------------- | -------------- | --------------------------------------------- |
| `feat`       | New feature                             | MINOR          | `feat(api): add workflow execution endpoint`  |
| `fix`        | Bug fix                                 | PATCH          | `fix(orchestration): handle null responses`   |
| `docs`       | Documentation only                      | None           | `docs(readme): update installation guide`     |
| `style`      | Formatting, no code change              | None           | `style(core): format with black`              |
| `refactor`   | Code restructuring (no behavior change) | None           | `refactor(domain): simplify agent factory`    |
| `perf`       | Performance improvement                 | PATCH          | `perf(db): add index on agent_id`             |
| `test`       | Adding/updating tests                   | None           | `test(api): add workflow endpoint tests`      |
| `chore`      | Build/tooling changes                   | None           | `chore(deps): update pydantic to v2.5`        |
| `ci`         | CI configuration changes                | None           | `ci(github): add coverage reporting`          |
| `build`      | Build system changes                    | None           | `build(docker): optimize image layers`        |
| `revert`     | Revert previous commit                  | Special        | `revert: "feat(api): add broken endpoint"`    |
| `!` (suffix) | Breaking change indicator               | MAJOR          | `feat(domain)!: migrate to Pydantic v2`       |
| `BREAKING`   | Breaking change in footer               | MAJOR          | `BREAKING CHANGE: removed Agent.run() method` |

### Scopes

Common scopes in Paracle:

- `api` - REST API (`paracle_api`)
- `cli` - Command-line interface (`paracle_cli`)
- `core` - Core utilities (`paracle_core`)
- `domain` - Domain models (`paracle_domain`)
- `orchestration` - Workflow execution (`paracle_orchestration`)
- `providers` - LLM providers (`paracle_providers`)
- `adapters` - Framework adapters (`paracle_adapters`)
- `tools` - Tool definitions (`paracle_tools`)
- `events` - Event system (`paracle_events`)
- `store` - Persistence (`paracle_store`)
- `sandbox` - Sandbox execution (`paracle_sandbox`)
- `isolation` - Resource isolation (`paracle_isolation`)
- `review` - Artifact review (`paracle_review`)
- `rollback` - Rollback mechanisms (`paracle_rollback`)
- `docs` - Documentation
- `tests` - Test files
- `deps` - Dependencies
- `config` - Configuration

### Examples

#### Good Commits

```bash
# Feature with description
git commit -m "feat(api): add workflow execution endpoint

Implements POST /workflows/{id}/execute with sync/async modes.
Includes request validation and error handling.

Closes #42"

# Bug fix
git commit -m "fix(orchestration): handle null tool responses gracefully

Previously crashed when tool returned None. Now logs warning
and continues execution with default value.

Fixes #87"

# Breaking change
git commit -m "feat(domain)!: migrate to Pydantic v2

BREAKING CHANGE: All models now use Pydantic v2 API.
Field definitions changed from = Field() to : Annotated[type, Field()].

Migration guide: docs/migrations/pydantic-v2.md
Closes #123"

# Documentation
git commit -m "docs(readme): add API key configuration guide

Explains how to set up OpenAI, Anthropic, and other providers.
Includes troubleshooting section."

# Chore
git commit -m "chore(deps): update dependencies to latest versions

- pydantic: 2.4 → 2.5
- fastapi: 0.104 → 0.105
- click: 8.1.6 → 8.1.7"
```

#### Bad Commits (Don't Do This)

```bash
# Too vague
git commit -m "fix bug"
git commit -m "update code"
git commit -m "WIP"

# No type/scope
git commit -m "added new feature"
git commit -m "Fixed the issue"

# Multiple unrelated changes
git commit -m "feat(api): add endpoint, fix bug, update docs"

# Imperative tense wrong
git commit -m "feat(api): adds new endpoint"  # Use "add" not "adds"
```

## Commit Best Practices

### 1. Atomic Commits
- One logical change per commit
- Commit compiles and tests pass
- Can be reverted independently

### 2. Clear Messages
- **Subject**: Imperative mood, lowercase, no period, < 72 chars
- **Body**: Explain WHAT and WHY, not HOW
- **Footer**: Reference issues, breaking changes

### 3. Commit Frequency
- Commit early and often (locally)
- Rebase/squash before pushing
- One feature = one PR = multiple commits OK

### 4. Commit Hygiene
```bash
# Before pushing, clean up history
git rebase -i origin/develop

# Squash "fix typo" commits
# Reorder logical commits
# Edit commit messages for clarity
```

## Pull Request Guidelines

### PR Title

Must follow conventional commit format:

```
feat(api): add workflow execution endpoint
fix(orchestration): handle null tool responses
docs(readme): update installation guide
```

### PR Description Template

```markdown
## Description
Brief summary of changes.

## Type of Change
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Added X
- Modified Y
- Removed Z

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests pass locally

## Related Issues
Closes #42
Refs #87
```

### PR Review Requirements

- **develop**: 1 approval required
- **main**: 2 approvals required + all checks pass
- **Checks**:
  - Tests pass (pytest)
  - Linting clean (ruff)
  - Type checking (mypy)
  - Coverage >= 80%

### Merge Strategy

- **feature → develop**: Squash merge (clean history)
- **develop → main**: Merge commit (preserve context)
- **hotfix → main**: Fast-forward (if possible)

## Semantic Versioning

Paracle follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH-prerelease+build

Example: 1.2.3-beta.1+20260106
```

### Version Components

- **MAJOR**: Breaking changes (incompatible API)
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)
- **Pre-release**: alpha, beta, rc (optional)
- **Build**: Build metadata (optional)

### Version Bumping Rules

Based on commits since last release:

```
If any commit has "BREAKING CHANGE:" or "!" → MAJOR bump
Else if any commit has "feat:" → MINOR bump
Else if any commit has "fix:" or "perf:" → PATCH bump
Else → No release needed (docs/chore only)
```

### Pre-release Versions

```
0.1.0-alpha.1    # Early development, unstable
0.1.0-beta.2     # Feature complete, testing
0.1.0-rc.3       # Release candidate, final testing
0.1.0            # Stable release
```

### Version 0.x.x (Pre-1.0)

- Breaking changes allowed in MINOR versions
- 0.1.0 → 0.2.0 can have breaking changes
- Use carefully, document thoroughly

### Version 1.0.0+

- MAJOR version only for breaking changes
- Maintain backward compatibility in MINOR/PATCH
- Deprecate features before removing (1 MAJOR version notice)

## Release Checklist

### Pre-release

- [ ] All planned features merged to `develop`
- [ ] All tests passing (unit + integration)
- [ ] Code coverage >= 80%
- [ ] Linting clean (ruff)
- [ ] Type checking clean (mypy)
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] Migration guides written (if breaking changes)
- [ ] No critical/high bugs open
- [ ] Performance benchmarks acceptable

### Release Preparation

- [ ] Create `release/X.Y.Z` branch from `develop`
- [ ] Bump version in `pyproject.toml`
- [ ] Update `__version__` in packages
- [ ] Generate changelog from commits
- [ ] Update `CHANGELOG.md`
- [ ] Update version refs in docs
- [ ] Run full test suite
- [ ] Build package (`python -m build`)
- [ ] Test package installation

### Release Execution

- [ ] Merge `release/X.Y.Z` to `main`
- [ ] Tag release `vX.Y.Z` on `main`
- [ ] Push main and tags
- [ ] Publish to PyPI (`twine upload`)
- [ ] Build and push Docker images
- [ ] Create GitHub release with notes
- [ ] Merge `release/X.Y.Z` back to `develop`
- [ ] Delete `release/X.Y.Z` branch
- [ ] Announce release (blog, Discord, Twitter)

### Post-release

- [ ] Monitor error tracking
- [ ] Check download metrics
- [ ] Gather user feedback
- [ ] Update project tracking (`.parac/memory/context/current_state.yaml`)
- [ ] Close related milestones
- [ ] Plan next release

## Changelog Management

### Format

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in progress

## [0.1.0] - 2026-01-06

### Added
- Agent sandbox execution with Docker isolation
- Rollback mechanism on task failure
- Artifact review and approval workflow
- Multi-provider support (xAI, DeepSeek, Groq)

### Changed
- API now requires authentication tokens for all endpoints
- Workflow execution defaults to async mode

### Fixed
- Memory leak in workflow orchestration
- Race condition in event bus

### Security
- Patched XSS vulnerability in API responses

### Breaking Changes
- Removed deprecated `Agent.run()` method, use `Orchestrator.execute()` instead
- Changed `AgentSpec` field validation to use Pydantic v2 API

### Migration Guide
See [docs/migrations/v0.1.0.md](docs/migrations/v0.1.0.md) for upgrade instructions.

## [0.0.1] - 2026-01-04

### Added
- Initial release
- Basic agent definition and execution
- CLI commands for agent management
- SQLite-based persistence
```

### Sections

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes
- **Breaking Changes**: Incompatible changes (MAJOR version)
- **Migration Guide**: Link to upgrade instructions

### Automation

Changelog is generated from conventional commits:

```bash
python scripts/generate_changelog.py v0.0.1 v0.1.0
```

## Git Hooks

### Pre-commit

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run linting
ruff check .
if [ $? -ne 0 ]; then
    echo "❌ Linting failed. Fix errors before committing."
    exit 1
fi

# Run type checking
mypy packages/
if [ $? -ne 0 ]; then
    echo "❌ Type checking failed. Fix errors before committing."
    exit 1
fi

# Check commit message format (if amending)
# python scripts/check_commit_msg.py

echo "✅ Pre-commit checks passed"
```

### Commit-msg

```bash
#!/bin/sh
# .git/hooks/commit-msg

# Validate conventional commit format
python scripts/validate_commit_msg.py "$1"
if [ $? -ne 0 ]; then
    echo "❌ Commit message doesn't follow conventional commit format"
    echo "Format: <type>(<scope>): <subject>"
    echo "Example: feat(api): add new endpoint"
    exit 1
fi

echo "✅ Commit message validated"
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/ci.yaml
name: CI

on:
  pull_request:
    branches: [develop, main]
  push:
    branches: [develop, main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: make test
      - run: make lint
      - run: make typecheck
      - run: make coverage

  validate-commits:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - run: python scripts/validate_commit_history.py
```

## Troubleshooting

### Merge Conflicts

```bash
# If conflict on merge to main
git checkout main
git merge --no-ff develop

# Conflict! Fix manually
# Edit conflicted files
git add .
git commit  # Will use merge commit message

# Push
git push origin main
```

### Wrong Branch

```bash
# Committed to main instead of feature branch
git branch feature/my-work
git reset --hard origin/main
git checkout feature/my-work
# Now commits are on feature branch
```

### Revert Release

```bash
# Bad release pushed to main
git checkout main
git revert v0.1.0  # Creates revert commit
git tag v0.1.1
git push origin main --tags

# Publish fixed version
python -m build
twine upload dist/*
```

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)

---

**Last Updated**: 2026-01-06
**Version**: 1.0
**Maintained By**: Release Manager Agent
**Status**: Active
