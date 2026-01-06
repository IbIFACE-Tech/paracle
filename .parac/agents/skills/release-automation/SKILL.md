---
name: release-automation
description: Expert-level semantic versioning, package publishing, changelog generation, and release orchestration. Use for version management, PyPI/Docker releases, and deployment automation.
license: Apache-2.0
compatibility: Python 3.10+, PyPI, Docker Hub
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: automation
  level: advanced
  display_name: "Release Automation"
  tags:
    - release
    - versioning
    - packaging
    - publishing
    - automation
  capabilities:
    - semantic_versioning
    - changelog_generation
    - pypi_publishing
    - docker_publishing
    - release_orchestration
  requirements:
    - skill_name: git-management
      min_level: intermediate
    - skill_name: cicd-devops
      min_level: intermediate
allowed-tools: Read Write Bash(python:*) Bash(docker:*) Bash(git:*)
---

# Release Automation Skill

## When to use this skill

Use this skill when:

- Bumping project version (major, minor, patch)
- Generating changelogs from git history
- Publishing Python packages to PyPI
- Building and pushing Docker images
- Creating GitHub releases
- Coordinating multi-step release processes
- Managing pre-release and beta versions

## Semantic Versioning (SemVer)

Paracle follows **Semantic Versioning 2.0.0**: `MAJOR.MINOR.PATCH`

```
v0.1.0 → v0.2.0 → v0.2.1 → v1.0.0
```

### Version Components

**MAJOR** (breaking changes):

- Incompatible API changes
- Removed features
- Changed behavior that breaks existing code

**MINOR** (new features):

- New functionality (backward compatible)
- New features added
- Deprecation of features (but not removal)

**PATCH** (bug fixes):

- Bug fixes
- Performance improvements
- Documentation updates
- Security patches

### Pre-Release Versions

```
v0.1.0-alpha.1    ← Alpha release
v0.1.0-beta.2     ← Beta release
v0.1.0-rc.1       ← Release candidate
v0.1.0            ← Stable release
```

### Version Bump Decision Tree

```
┌─────────────────────────────────────────────────┐
│ What changed?                                   │
├─────────────────────────────────────────────────┤
│ Breaking API changes?                           │
│ ├─ YES → MAJOR bump (0.1.0 → 1.0.0)           │
│ └─ NO → Continue                               │
│                                                 │
│ New features (backward compatible)?            │
│ ├─ YES → MINOR bump (0.1.0 → 0.2.0)           │
│ └─ NO → Continue                               │
│                                                 │
│ Bug fixes only?                                │
│ └─ YES → PATCH bump (0.1.0 → 0.1.1)           │
└─────────────────────────────────────────────────┘
```

### Paracle Version Examples

```bash
# Current: v0.0.1 (initial development)

# Add new feature (Phase 1-3)
v0.0.1 → v0.1.0  # First feature-complete version

# Add minor feature (Phase 4)
v0.1.0 → v0.2.0  # API server added

# Fix bug
v0.2.0 → v0.2.1  # Bug fix

# Add Phase 5 features
v0.2.1 → v0.3.0  # Sandbox execution

# Breaking API change
v0.3.0 → v1.0.0  # Stable release
```

## Version Management

### Version Bump Script

Located at: `scripts/bump_version.py`

```bash
# Bump version
python scripts/bump_version.py <major|minor|patch>

# Examples
python scripts/bump_version.py major   # 0.1.0 → 1.0.0
python scripts/bump_version.py minor   # 0.1.0 → 0.2.0
python scripts/bump_version.py patch   # 0.1.0 → 0.1.1

# Pre-release
python scripts/bump_version.py minor --pre alpha  # 0.1.0 → 0.2.0-alpha.1
python scripts/bump_version.py patch --pre beta   # 0.1.0 → 0.1.1-beta.1
```

**What it updates**:

- `pyproject.toml` - Project version
- `packages/paracle_core/__version__.py` - Runtime version
- `docs/VERSION` - Documentation version

### Manual Version Update

If script unavailable, update manually:

**1. pyproject.toml**:

```toml
[project]
name = "paracle"
version = "0.2.0"  # ← Update here
```

**2. **version**.py**:

```python
# packages/paracle_core/__version__.py
__version__ = "0.2.0"  # ← Update here
```

**3. Verify consistency**:

```bash
# Check all versions match
grep -r "version = " pyproject.toml
grep -r "__version__ = " packages/paracle_core/__version__.py
```

## Changelog Management

### Changelog Generation

Located at: `scripts/generate_changelog.py`

```bash
# Generate changelog from git commits
python scripts/generate_changelog.py

# Generate for specific version
python scripts/generate_changelog.py --version v0.2.0

# Generate from tag range
python scripts/generate_changelog.py --from v0.1.0 --to v0.2.0

# Output to file
python scripts/generate_changelog.py --output CHANGELOG.md
```

### Changelog Format (Keep a Changelog)

```markdown
# Changelog

All notable changes to Paracle will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in develop, not yet released

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future

### Removed
- Features removed in this version

### Fixed
- Bug fixes

### Security
- Security fixes

## [0.2.0] - 2026-01-06

### Added
- REST API server with FastAPI
- Workflow execution endpoints (sync/async)
- CLI workflow management commands
- Support for xAI, DeepSeek, Groq providers

### Changed
- Refactored CLI to use API-first architecture
- Improved error handling in orchestration engine

### Fixed
- Agent inheritance resolution bug
- Memory leak in workflow execution

## [0.1.0] - 2026-01-04

### Added
- Initial release
- Core agent framework
- Basic workflow orchestration
- SQLite persistence
- OpenAI and Anthropic providers

[Unreleased]: https://github.com/IbIFACE-Tech/paracle-lite/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/IbIFACE-Tech/paracle-lite/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/IbIFACE-Tech/paracle-lite/releases/tag/v0.1.0
```

### Manual Changelog Entry

If automatic generation fails:

```markdown
## [0.2.0] - 2026-01-06

### Added
- feat(api): add workflow execution endpoints
- feat(cli): add workflow management commands
- feat(providers): support xAI, DeepSeek, Groq

### Changed
- refactor(cli): migrate to API-first architecture

### Fixed
- fix(domain): resolve agent inheritance bug
- fix(orchestration): patch memory leak in execution
```

**Guidelines**:

- Group by commit type (Added/Changed/Fixed)
- Use past tense ("Added" not "Add")
- Be specific but concise
- Link to issues when applicable
- Include breaking changes prominently

## Package Publishing

### PyPI Publishing

#### Prerequisites

```bash
# Install build tools
pip install build twine

# Configure PyPI credentials
# Create ~/.pypirc
[pypi]
username = __token__
password = pypi-your-api-token-here

# Or use environment variable
export TWINE_PASSWORD=pypi-your-api-token
```

#### Build Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
python -m build

# Verify contents
tar -tzf dist/paracle-0.2.0.tar.gz
unzip -l dist/paracle-0.2.0-py3-none-any.whl
```

#### Publish to PyPI

```bash
# Test on PyPI Test first
twine upload --repository testpypi dist/*

# Verify installation from test
pip install --index-url https://test.pypi.org/simple/ paracle

# Publish to production PyPI
twine upload dist/*

# Verify published
pip install paracle==0.2.0
```

#### Automated Publishing (GitHub Actions)

```yaml
# .github/workflows/publish-pypi.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

### Docker Publishing

#### Build Docker Images

```bash
# Build API server image
docker build -f docker/Dockerfile.api -t paracle/api:0.2.0 .
docker tag paracle/api:0.2.0 paracle/api:latest

# Build worker image
docker build -f docker/Dockerfile.worker -t paracle/worker:0.2.0 .
docker tag paracle/worker:0.2.0 paracle/worker:latest

# Build dev image
docker build -f docker/Dockerfile.dev -t paracle/dev:0.2.0 .
```

#### Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push versioned images
docker push paracle/api:0.2.0
docker push paracle/worker:0.2.0

# Push latest tags
docker push paracle/api:latest
docker push paracle/worker:latest
```

#### Automated Docker Publishing

```yaml
# .github/workflows/publish-docker.yml
name: Publish Docker Images

on:
  release:
    types: [published]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Build and push API image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.api
          push: true
          tags: |
            paracle/api:${{ steps.version.outputs.VERSION }}
            paracle/api:latest
          cache-from: type=registry,ref=paracle/api:buildcache
          cache-to: type=registry,ref=paracle/api:buildcache,mode=max
```

## GitHub Release Creation

### Manual Release

```bash
# After merging release branch to main

# Create and push tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# Go to GitHub → Releases → Draft new release
# - Tag: v0.2.0
# - Title: "Paracle v0.2.0 - API Server & Enhanced CLI"
# - Description: Copy from CHANGELOG.md
# - Attach artifacts if any
# - Publish release
```

### Automated Release (GitHub Actions)

```yaml
# .github/workflows/release.yml
name: Create Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Generate changelog
        id: changelog
        run: |
          python scripts/generate_changelog.py --version v${{ steps.version.outputs.VERSION }} > release_notes.md

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          body_path: release_notes.md
          draft: false
          prerelease: ${{ contains(steps.version.outputs.VERSION, '-') }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Release Orchestration

### Complete Release Workflow

#### 1. Pre-Release Preparation

```bash
# Ensure all tests pass
make test
make lint
make typecheck

# Ensure develop is up to date
git checkout develop
git pull origin develop

# Verify current version
grep version pyproject.toml
```

#### 2. Create Release Branch

```bash
# Create release branch
git checkout -b release/v0.2.0

# Bump version
python scripts/bump_version.py minor  # 0.1.0 → 0.2.0

# Generate changelog
python scripts/generate_changelog.py --version v0.2.0 --output CHANGELOG.md

# Commit changes
git add pyproject.toml packages/paracle_core/__version__.py CHANGELOG.md
git commit -m "chore(release): prepare v0.2.0 release"

# Push release branch
git push origin release/v0.2.0
```

#### 3. Release Testing

```bash
# Build package locally
python -m build

# Test installation
pip install dist/paracle-0.2.0-py3-none-any.whl

# Run smoke tests
paracle --version
paracle agent list
paracle workflow run examples/hello_world_agent.py

# Test Docker images
docker build -f docker/Dockerfile.api -t paracle/api:test .
docker run -p 8000:8000 paracle/api:test
curl http://localhost:8000/health
```

#### 4. Merge to Main

```bash
# Create PR: release/v0.2.0 → main
# After approval:

git checkout main
git pull origin main
git merge --no-ff release/v0.2.0

# Create tag
git tag -a v0.2.0 -m "Release v0.2.0 - API Server & Enhanced CLI

Features:
- REST API server with FastAPI
- Workflow execution endpoints
- Enhanced CLI commands
- Multi-provider support

Full changelog: https://github.com/IbIFACE-Tech/paracle-lite/blob/main/CHANGELOG.md"

# Push to main
git push origin main --tags
```

#### 5. Publish Artifacts

```bash
# Publish to PyPI
twine upload dist/*

# Build and push Docker images
docker build -f docker/Dockerfile.api -t paracle/api:0.2.0 .
docker tag paracle/api:0.2.0 paracle/api:latest
docker push paracle/api:0.2.0
docker push paracle/api:latest

docker build -f docker/Dockerfile.worker -t paracle/worker:0.2.0 .
docker tag paracle/worker:0.2.0 paracle/worker:latest
docker push paracle/worker:0.2.0
docker push paracle/worker:latest
```

#### 6. Create GitHub Release

```bash
# Manual: GitHub UI → Releases → Draft new release
# Or automated via GitHub Actions (triggered by tag push)
```

#### 7. Backport to Develop

```bash
# Merge release changes back to develop
git checkout develop
git pull origin develop
git merge --no-ff release/v0.2.0
git push origin develop

# Delete release branch
git branch -d release/v0.2.0
git push origin --delete release/v0.2.0
```

#### 8. Post-Release

```bash
# Update .parac/memory/context/current_state.yaml
project:
  version: 0.2.0  # ← Update

# Log release
echo "[$(date)] [ReleaseManager] [RELEASE] Published v0.2.0" >> .parac/memory/logs/agent_actions.log

# Create release summary
cat > .parac/memory/summaries/v0.2.0_release.md << EOF
# Release v0.2.0 Summary

**Date**: $(date +%Y-%m-%d)
**Type**: Minor release

## Highlights
- REST API server with FastAPI
- Async/sync workflow execution
- Enhanced CLI commands
- Multi-provider support (xAI, DeepSeek, Groq)

## Metrics
- Commits: 42
- PRs merged: 8
- Tests: 127 passing
- Coverage: 92%

## Links
- [GitHub Release](https://github.com/IbIFACE-Tech/paracle-lite/releases/tag/v0.2.0)
- [PyPI Package](https://pypi.org/project/paracle/0.2.0/)
- [Docker Images](https://hub.docker.com/r/paracle/api/tags)
EOF

# Announce release (if applicable)
# - Twitter/X
# - Discord
# - Email list
# - Blog post
```

### Hotfix Release Workflow

#### 1. Create Hotfix Branch

```bash
# Branch from main
git checkout main
git pull origin main
git checkout -b hotfix/v0.2.1-critical-fix

# Fix the issue
# ... edit files ...

# Commit fix
git add .
git commit -m "fix(orchestration): resolve memory leak in agent cleanup

Critical fix for memory leak causing high memory usage in long-running workflows.

Closes #456"
```

#### 2. Bump Patch Version

```bash
# Bump patch version
python scripts/bump_version.py patch  # 0.2.0 → 0.2.1

# Update changelog
python scripts/generate_changelog.py --version v0.2.1 --output CHANGELOG.md

# Commit version bump
git add pyproject.toml packages/paracle_core/__version__.py CHANGELOG.md
git commit -m "chore: bump version to v0.2.1"
```

#### 3. Merge and Release

```bash
# Merge to main
git checkout main
git merge --no-ff hotfix/v0.2.1-critical-fix

# Tag and push
git tag -a v0.2.1 -m "Release v0.2.1 - Critical Hotfix"
git push origin main --tags

# Publish artifacts (automated via CI)
```

#### 4. Backport to Develop

```bash
# Merge hotfix to develop
git checkout develop
git merge --no-ff hotfix/v0.2.1-critical-fix
git push origin develop

# Clean up
git branch -d hotfix/v0.2.1-critical-fix
```

## Release Checklist

Use this checklist for every release:

```markdown
## Pre-Release
- [ ] All tests passing
- [ ] Lint and typecheck clean
- [ ] Documentation updated
- [ ] CHANGELOG.md reviewed
- [ ] Version bumped correctly
- [ ] Release notes drafted

## Release
- [ ] Release branch created
- [ ] Version bumped in all files
- [ ] Changelog generated
- [ ] PR to main created and approved
- [ ] Merged to main with --no-ff
- [ ] Tag created and pushed
- [ ] GitHub release created

## Publishing
- [ ] PyPI package published
- [ ] Docker images built and pushed
- [ ] Release announcement sent
- [ ] Documentation site updated

## Post-Release
- [ ] Changes backported to develop
- [ ] Release branch deleted
- [ ] current_state.yaml updated
- [ ] Release summary created
- [ ] Monitoring metrics checked
```

## Common Patterns

### Pattern 1: Version Bump with Validation

```bash
#!/bin/bash
# scripts/safe_version_bump.sh

set -e  # Exit on error

# Validate current state
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ Working directory not clean!"
    exit 1
fi

# Run tests
echo "🧪 Running tests..."
make test || exit 1

# Bump version
echo "⬆️  Bumping version..."
python scripts/bump_version.py "$1"

# Verify
echo "✅ Version bumped successfully!"
grep version pyproject.toml
```

### Pattern 2: Changelog with Validation

```bash
#!/bin/bash
# scripts/safe_changelog_gen.sh

set -e

VERSION="$1"

if [[ -z "$VERSION" ]]; then
    echo "Usage: $0 <version>"
    exit 1
fi

# Generate changelog
python scripts/generate_changelog.py --version "$VERSION" > CHANGELOG_NEW.md

# Review changes
echo "📝 Review changelog:"
cat CHANGELOG_NEW.md

read -p "Accept changes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mv CHANGELOG_NEW.md CHANGELOG.md
    echo "✅ Changelog updated!"
else
    rm CHANGELOG_NEW.md
    echo "❌ Changelog generation cancelled"
    exit 1
fi
```

### Pattern 3: Rollback Release

```bash
#!/bin/bash
# scripts/rollback_release.sh

set -e

VERSION="$1"

echo "🚨 Rolling back release $VERSION"

# Delete tag locally
git tag -d "v$VERSION"

# Delete tag remotely
git push --delete origin "v$VERSION"

# Delete GitHub release (requires gh CLI)
gh release delete "v$VERSION" --yes

# Yank PyPI release (doesn't delete, marks as unavailable)
pip install yank
yank "paracle==$VERSION" --reason "Rollback due to critical issue"

echo "✅ Release $VERSION rolled back"
echo "⚠️  Manual steps required:"
echo "  - Delete Docker images from Docker Hub"
echo "  - Notify users via announcement"
```

## Examples

### Example 1: Minor Release (0.1.0 → 0.2.0)

```bash
# 1. Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v0.2.0

# 2. Bump version
python scripts/bump_version.py minor
# Updated: 0.1.0 → 0.2.0

# 3. Generate changelog
python scripts/generate_changelog.py --version v0.2.0 --output CHANGELOG.md

# 4. Commit changes
git add pyproject.toml packages/paracle_core/__version__.py CHANGELOG.md
git commit -m "chore(release): prepare v0.2.0 release"
git push origin release/v0.2.0

# 5. Create PR to main, get approval, merge

# 6. Tag and push
git checkout main
git pull origin main
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags

# 7. Publish (automated by CI)
# - PyPI package
# - Docker images
# - GitHub release

# 8. Backport to develop
git checkout develop
git merge --no-ff release/v0.2.0
git push origin develop
```

### Example 2: Patch Release (Hotfix 0.2.0 → 0.2.1)

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/v0.2.1-auth-fix

# 2. Fix issue
git add packages/paracle_api/auth.py
git commit -m "fix(api): patch authentication bypass vulnerability"

# 3. Bump patch version
python scripts/bump_version.py patch
# Updated: 0.2.0 → 0.2.1

# 4. Update changelog
python scripts/generate_changelog.py --version v0.2.1 --output CHANGELOG.md

# 5. Commit version bump
git add pyproject.toml packages/paracle_core/__version__.py CHANGELOG.md
git commit -m "chore: bump version to v0.2.1"

# 6. Merge to main
git checkout main
git merge --no-ff hotfix/v0.2.1-auth-fix
git tag -a v0.2.1 -m "Release v0.2.1 - Security Fix"
git push origin main --tags

# 7. Backport to develop
git checkout develop
git merge --no-ff hotfix/v0.2.1-auth-fix
git push origin develop

# 8. Clean up
git branch -d hotfix/v0.2.1-auth-fix
```

### Example 3: Pre-Release (0.2.0-beta.1)

```bash
# 1. Create pre-release branch
git checkout develop
git checkout -b release/v0.2.0-beta.1

# 2. Bump to pre-release version
python scripts/bump_version.py minor --pre beta
# Updated: 0.1.0 → 0.2.0-beta.1

# 3. Generate changelog
python scripts/generate_changelog.py --version v0.2.0-beta.1

# 4. Commit and tag
git add pyproject.toml packages/paracle_core/__version__.py CHANGELOG.md
git commit -m "chore: prepare v0.2.0-beta.1 pre-release"
git tag -a v0.2.0-beta.1 -m "Pre-release v0.2.0-beta.1"
git push origin release/v0.2.0-beta.1 --tags

# 5. Publish pre-release to PyPI
twine upload dist/* --repository-url https://test.pypi.org/legacy/

# 6. Create GitHub pre-release
gh release create v0.2.0-beta.1 --prerelease --notes "Beta release for testing"

# Note: Do NOT merge to main or develop yet
# After beta testing, create final release
```

## Related Skills

- [Git Management](../git-management/SKILL.md) - Git workflows and branching
- [CI/CD & DevOps](../cicd-devops/SKILL.md) - Automated pipelines
- [Paracle Development](../paracle-development/SKILL.md) - Framework development

## References

- [Paracle Git Workflow Policy](../../../policies/GIT_WORKFLOW.md)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [PyPI Publishing Guide](../../../../.docs-private/pypi-publishing-guide.md) (Internal)
- [PyPI Publishing Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Docker Hub Publishing](https://docs.docker.com/docker-hub/publish/)
