---
name: git-management
description: Expert-level git workflow management, conventional commits, branching strategies, and merge operations. Use for git operations, branch management, and commit standardization.
license: Apache-2.0
compatibility: Git 2.x+, GitHub, GitLab
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: version-control
  level: advanced
  display_name: "Git Management"
  tags:
    - git
    - version-control
    - conventional-commits
    - branching-strategy
    - merge-management
  capabilities:
    - conventional_commits
    - branch_management
    - merge_strategies
    - conflict_resolution
    - git_hooks
  requirements:
    - skill_name: paracle-development
      min_level: intermediate
allowed-tools: Read Write Bash(git:*)
---

# Git Management Skill

## When to use this skill

Use this skill when:

- Managing git branches and merges
- Enforcing conventional commit standards
- Coordinating feature/bugfix/hotfix workflows
- Resolving merge conflicts
- Setting up git hooks for automation
- Managing git tags and references
- Creating and reviewing pull requests

## Git Workflow for Paracle

### Branch Strategy

Paracle uses a **modified Gitflow** with two main branches:

```
main                  ← Production releases (v0.1.0, v0.2.0)
  ↓
develop               ← Integration branch (default)
  ↓
├── feature/*         ← New features
├── bugfix/*          ← Bug fixes
├── hotfix/*          ← Urgent production fixes
└── release/*         ← Release preparation
```

**Branch Lifecycle**:

```bash
# Feature branch
develop → feature/add-webhook-support → develop

# Bugfix branch
develop → bugfix/fix-agent-inheritance → develop

# Release branch
develop → release/v0.2.0 → main + develop

# Hotfix branch
main → hotfix/v0.1.1-critical-fix → main + develop
```

### Conventional Commits

**Format**: `<type>(<scope>): <description>`

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding/updating tests
- `chore`: Tooling, dependencies
- `ci`: CI/CD changes

- `build`: Build system changes

**Scopes** (Paracle-specific):

- `core`: paracle_core package
- `domain`: paracle_domain package
- `api`: paracle_api package
- `cli`: paracle_cli package
- `orchestration`: paracle_orchestration
- `providers`: paracle_providers
- `adapters`: paracle_adapters
- `tools`: paracle_tools
- `sandbox`: paracle_sandbox
- `review`: paracle_review
- `rollback`: paracle_rollback
- `store`: paracle_store

- `events`: paracle_events
- `isolation`: paracle_isolation

**Examples**:

```bash
# Good commits
feat(api): add workflow execution endpoints
fix(orchestration): resolve agent inheritance bug
docs(readme): update installation instructions
refactor(domain): simplify agent factory logic
perf(store): optimize repository queries with indexes
test(cli): add integration tests for workflow commands
chore(deps): bump pydantic to v2.10.0
ci(github): add automated release workflow

# Bad commits (avoid)
update stuff
fixed bug

WIP
asdfasdf
```

**Breaking Changes**:

```bash
feat(api)!: change workflow response structure

BREAKING CHANGE: WorkflowResponse now returns `result` instead of `output`
Migrate by updating response handling to use `.result` attribute.
```

### Git Operations

#### Creating a Feature Branch

```bash
# Always branch from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/webhook-integration

# Work on feature...
git add packages/paracle_events/webhooks.py
git commit -m "feat(events): implement webhook delivery system"

# Keep feature updated with develop
git fetch origin
git rebase origin/develop

# Push and create PR
git push origin feature/webhook-integration
```

#### Creating a Release Branch

```bash
# Branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v0.2.0

# Bump version
python scripts/bump_version.py minor  # 0.1.0 → 0.2.0

# Generate changelog
python scripts/generate_changelog.py

# Commit release prep
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): prepare v0.2.0 release"

# Push release branch
git push origin release/v0.2.0
```

#### Creating a Hotfix Branch

```bash
# Branch from main (production)
git checkout main
git pull origin main
git checkout -b hotfix/v0.1.1-security-fix

# Fix the issue
git add packages/paracle_api/auth.py
git commit -m "fix(api)!: patch authentication bypass vulnerability

BREAKING CHANGE: API key validation now requires bearer token format"

# Bump patch version
python scripts/bump_version.py patch  # 0.1.0 → 0.1.1

# Merge to main
git checkout main
git merge --no-ff hotfix/v0.1.1-security-fix
git tag -a v0.1.1 -m "Release v0.1.1 - Security Fix"
git push origin main --tags

# Backport to develop
git checkout develop
git merge --no-ff hotfix/v0.1.1-security-fix

git push origin develop
```

#### Merge Strategies

**Feature → Develop** (Squash merge):

```bash
# Squash commits for cleaner history
git checkout develop
git merge --squash feature/webhook-integration
git commit -m "feat(events): add webhook integration system

- Implement webhook delivery
- Add retry logic with exponential backoff

- Support custom headers and authentication
- Add webhook logging and monitoring

Closes #123"
```

**Release → Main** (No-fast-forward):

```bash

# Preserve release history
git checkout main
git merge --no-ff release/v0.2.0
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags
```

**Develop → Release** (Fast-forward):

```bash
# Keep linear history for releases
git checkout release/v0.2.0
git merge --ff develop
```

### Git Hooks

#### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run linting
make lint || {
    echo "❌ Linting failed. Fix issues and try again."
    exit 1
}

# Run type checking
make typecheck || {
    echo "❌ Type checking failed. Fix issues and try again."
    exit 1
}

# Run tests
make test || {
    echo "❌ Tests failed. Fix issues and try again."
    exit 1
}

echo "✅ Pre-commit checks passed!"
```

#### Commit-Msg Hook

```bash
#!/bin/bash
# .git/hooks/commit-msg

# Validate conventional commit format
commit_msg=$(cat "$1")

# Pattern: type(scope): description
pattern="^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\(.+\))?: .{1,100}$"

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "❌ Invalid commit message format!"
    echo ""
    echo "Expected: <type>(<scope>): <description>"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, perf, test, chore, ci, build"
    echo "Example: feat(api): add webhook endpoints"
    exit 1
fi

echo "✅ Commit message format valid!"
```

#### Pre-Push Hook

```bash
#!/bin/bash
# .git/hooks/pre-push

# Get current branch
branch=$(git rev-parse --abbrev-ref HEAD)

# Protected branches
protected_branches="main|master"

if echo "$branch" | grep -qE "$protected_branches"; then
    echo "❌ Direct push to $branch is not allowed!"
    echo "Create a pull request instead."
    exit 1
fi


echo "✅ Push allowed!"
```

### Conflict Resolution

#### Common Conflicts in Paracle

**1. pyproject.toml (version conflicts)**:

```toml
<<<<<<< HEAD

version = "0.1.0"
=======
version = "0.2.0"
>>>>>>> feature/new-feature

# Resolution: Keep higher version or semantic version
version = "0.2.0"
```

**2. CHANGELOG.md (merge conflicts)**:

```markdown
<<<<<<< HEAD
## [0.1.0] - 2026-01-05
### Added
- Feature A
=======
## [0.2.0] - 2026-01-06
### Added
- Feature B
>>>>>>> feature/new-feature


# Resolution: Merge both entries chronologically
## [0.2.0] - 2026-01-06
### Added
- Feature B

## [0.1.0] - 2026-01-05
### Added
- Feature A
```

**3. Manifest files (.parac/agents/manifest.yaml)**:

```yaml
<<<<<<< HEAD
agents:
  - id: coder
  - id: tester
=======
agents:
  - id: coder
  - id: reviewer
>>>>>>> feature/add-reviewer

# Resolution: Merge both additions
agents:
  - id: coder
  - id: reviewer
  - id: tester
```

#### Conflict Resolution Workflow

```bash
# Start merge/rebase and encounter conflicts
git rebase develop
# CONFLICT (content): Merge conflict in pyproject.toml

# Check conflicted files
git status

# Edit files to resolve conflicts
# Remove markers: <<<<<<<, =======, >>>>>>>

# Mark as resolved
git add pyproject.toml

# Continue rebase
git rebase --continue

# Or abort if needed
git rebase --abort
```

### Git Best Practices for Paracle

#### Commit Guidelines

**DO**:
✅ Write clear, descriptive commi**message**
✅ Use conventional commit format
✅ Keep commits atomic (one logical change)
✅ Reference issue numbers (`Closes #123`)
✅ Include breaking change notes when applicable
✅ Test before committing

**DON'T**:
❌ Commit broken code
❌ Use vague messages ("fix bug", "update")
❌ Mix unrelated changes in one commit
❌ Commit secrets or API keys
❌ Commit generated files (.pyc, **pycache**)
❌ Force push to shared branches

#### Branch Guidelines

**DO**:
✅ Use descriptive branch names
✅ Keep branches short-lived (< 1 week)
✅ Rebase regularly to stay updated
✅ Delete merged branches
✅ Protect main and develop branches

**DON'T**:
❌ Create long-lived feature branches
❌ Push directly to main/develop
❌ Leave stale branches
❌ Use generic names ("fix", "test")

#### PR Guidelines

**DO**:
✅ Provide clear PR descriptions
✅ Link related issues
✅ Add screenshots for UI changes
✅ Request specific reviewers
✅ Address review comments
✅ Ensure CI passes

**DON'T**:
❌ Create massive PRs (>500 lines)
❌ Ignore review feedback
❌ Merge with failing tests
❌ Skip PR template sections

### Git Maintenance

#### Clean Up Local Branches

```bash
# List merged branches
git branch --merged develop

# Delete merged branches
git branch -d feature/old-feature

# Prune remote references
git remote prune origin

# Clean up stale branches
git fetch --prune
```

#### Rewrite History (Use with Caution)

```bash
# Interactive rebase (last 3 commits)
git rebase -i HEAD~3

# Squash commits
# Change 'pick' to 'squash' for commits to combine

# Amend last commit
git commit --amend -m "new message"

# ⚠️ NEVER rewrite history on shared branches!
```

#### Recover from Mistakes

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Recover deleted commits
git reflog
git checkout <commit-hash>

# Restore deleted files
git restore <file>
```

## Examples

### Example 1: Feature Development Workflow

```bash
# Start feature
git checkout develop
git pull origin develop
git checkout -b feature/add-mcp-protocol

# Implement feature
git add packages/paracle_providers/mcp.py
git commit -m "feat(providers): add MCP protocol support"

git add tests/unit/providers/test_mcp.py
git commit -m "test(providers): add MCP provider tests"

git add docs/mcp-integration.md
git commit -m "docs: add MCP integration guide"

# Update with develop
git fetch origin
git rebase origin/develop

# Push and create PR
git push origin feature/add-mcp-protocol

# After PR approval and merge, clean up
git checkout develop
git pull origin develop
git branch -d feature/add-mcp-protocol
```

### Example 2: Release Workflow

```bash
# Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v0.3.0

# Prepare release
python scripts/bump_version.py minor
python scripts/generate_changelog.py

# Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): bump version to v0.3.0"

# Push release branch
git push origin release/v0.3.0

# Create release PR to main
# After approval:

# Merge to main
git checkout main
git pull origin main
git merge --no-ff release/v0.3.0
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin main --tags

# Backport to develop
git checkout develop
git merge --no-ff release/v0.3.0
git push origin develop

# Delete release branch
git branch -d release/v0.3.0
git push origin --delete release/v0.3.0
```

### Example 3: Hotfix Workflow

```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/v0.2.1-memory-leak

# Fix issue
git add packages/paracle_orchestration/engine.py
git commit -m "fix(orchestration): resolve memory leak in agent cleanup"

# Bump version
python scripts/bump_version.py patch
git add pyproject.toml
git commit -m "chore: bump version to v0.2.1"

# Merge to main
git checkout main
git merge --no-ff hotfix/v0.2.1-memory-leak
git tag -a v0.2.1 -m "Release v0.2.1 - Hotfix"
git push origin main --tags

# Backport to develop
git checkout develop
git merge --no-ff hotfix/v0.2.1-memory-leak
git push origin develop

# Clean up
git branch -d hotfix/v0.2.1-memory-leak
```

## Common Patterns

### Pattern 1: Keeping Feature Branch Updated

```bash
# Rebase strategy (recommended)
git checkout feature/my-feature
git fetch origin
git rebase origin/develop

# Or merge strategy (if conflicts expected)
git merge origin/develop
```

### Pattern 2: Interactive Commit Cleanup

```bash
# Before pushing, clean up commit history
git rebase -i HEAD~5

# Options:
# pick = use commit
# reword = edit message
# squash = combine with previous
# fixup = squash without message
# drop = remove commit
```

### Pattern 3: Cherry-Pick Specific Commits

```bash
# Pick commit from another branch
git cherry-pick <commit-hash>

# Cherry-pick range
git cherry-pick commit1^..commit2
```

## Related Skills

- [CI/CD & DevOps](../cicd-devops/SKILL.md) - Automated workflows
- [Release Automation](../release-automation/SKILL.md) - Version management
- [Paracle Development](../paracle-development/SKILL.md) - Framework development

## References

- [Paracle Git Workflow Policy](../../../policies/GIT_WORKFLOW.md)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Gitflow Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
- [Semantic Versioning](https://semver.org/)
