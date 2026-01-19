# PyPI Publishing Guide for Paracle

## Overview

Paracle uses GitHub Actions with **Trusted Publishing** (OIDC) to securely publish to PyPI without storing API tokens.

## Prerequisites

### 1. Configure PyPI Trusted Publishing

#### For Production PyPI

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new publisher"
3. Fill in:
   - **PyPI project name**: `paracle`
   - **Owner**: `IbIFACE-Tech`
   - **Repository name**: `paracle`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`

#### For TestPyPI (Testing)

1. Go to https://test.pypi.org/manage/account/publishing/
2. Click "Add a new publisher"
3. Fill in (same as above but with):
   - **Environment name**: `testpypi`

> **Note**: You must be a maintainer/owner of the PyPI project to configure trusted publishing.

---

## Publishing Methods

### Method 1: Tag-Based Release (Recommended for Production)

This automatically publishes to PyPI when you push a version tag:

```bash
# Ensure all changes are committed
git add .
git commit -m "chore: prepare v1.0.3 release"
git push origin develop

# Create and push a version tag
git tag v1.0.3
git push origin v1.0.3
```

**What happens:**

1. ✅ Security scan runs (OWASP, Bandit, Safety)
2. ✅ Full test suite runs
3. ✅ Package is built
4. ✅ Published to PyPI automatically
5. ✅ GitHub Release is created with changelog

---

### Method 2: Manual Workflow Dispatch

For testing or manual releases:

#### A. Using GitHub Web Interface

1. Go to: https://github.com/IbIFACE-Tech/paracle/actions/workflows/release.yml
2. Click "Run workflow"
3. Select:
   - **Branch**: `develop` (for testing) or `main` (for production)
   - **Publish to**: `testpypi` (test) or `pypi` (production)
4. Click "Run workflow"

#### B. Using GitHub CLI

```bash
# Test on TestPyPI first
gh workflow run release.yml --ref develop -f publish_to=testpypi

# Publish to production PyPI
gh workflow run release.yml --ref main -f publish_to=pypi
```

---

## Pre-Publishing Checklist

Before publishing, ensure:

- [ ] **Version bumped** in [`pyproject.toml`](pyproject.toml)

  ```bash
  # Bump version
  python scripts/bump_version.py patch  # or minor, major
  ```

- [ ] **CHANGELOG.md updated**

  ```bash
  # Auto-generate changelog
  python scripts/generate_changelog.py
  ```

- [ ] **All tests passing**

  ```bash
  uv run pytest -v
  ```

- [ ] **Code formatted**

  ```bash
  uv run black packages/ tests/
  uv run ruff check --fix packages/ tests/
  ```

- [ ] **Security scan clean**

  ```bash
  ./scripts/run-owasp-scan.sh  # Linux/Mac
  ./scripts/run-owasp-scan.ps1  # Windows
  ```

- [ ] **Build succeeds locally**
  ```bash
  uv build
  uv run twine check dist/*
  ```

---

## Testing on TestPyPI First

**Always test on TestPyPI before publishing to production:**

1. **Publish to TestPyPI:**

   ```bash
   gh workflow run release.yml --ref develop -f publish_to=testpypi
   ```

2. **Wait for workflow to complete** (check status):

   ```bash
   gh run list --workflow=release.yml --limit 1
   gh run watch  # Watch latest run
   ```

3. **Install from TestPyPI to verify:**

   ```bash
   pip install --index-url https://test.pypi.org/simple/ paracle==1.0.3

   # Test basic functionality
   paracle --version
   paracle agents list
   ```

4. **If successful, proceed to production PyPI**

---

## Production Release Process

### Full Release Workflow

```bash
# 1. Ensure on develop branch with all changes
git checkout develop
git pull origin develop

# 2. Bump version
python scripts/bump_version.py minor  # or patch/major
# This updates pyproject.toml

# 3. Update changelog
python scripts/generate_changelog.py

# 4. Commit version bump
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to v1.0.4"
git push origin develop

# 5. Merge to main
git checkout main
git pull origin main
git merge develop
git push origin main

# 6. Create and push tag (triggers release)
git tag v1.0.4
git push origin v1.0.4

# 7. Monitor release
gh run list --workflow=release.yml --limit 1
gh run watch
```

---

## Workflow Stages

The release workflow runs these stages:

1. **Security Scan** (20 min timeout)
   - OWASP Dependency-Check
   - Bandit static analysis
   - Safety vulnerability check
   - pip-audit

2. **Tests** (depends on security-scan)
   - Governance validation
   - Full pytest suite
   - Coverage check (80% minimum)

3. **Build** (depends on tests)
   - Build wheel and sdist
   - Validate with twine check
   - Upload artifacts

4. **Publish to TestPyPI** (manual only)
   - If workflow_dispatch with `publish_to=testpypi`

5. **Publish to PyPI** (automatic)
   - If tag starts with `v*`
   - Or manual with `publish_to=pypi`

6. **GitHub Release** (automatic)
   - Creates GitHub release
   - Attaches distribution files
   - Generates changelog

---

## Monitoring & Troubleshooting

### Check Workflow Status

```bash
# List recent runs
gh run list --workflow=release.yml --limit 5

# Watch current run
gh run watch

# View specific run
gh run view <run-id>

# Download logs if failed
gh run download <run-id>
```

### Common Issues

#### 1. **Security Scan Fails**

```bash
# Run locally to debug
./scripts/run-owasp-scan.sh

# Check suppressions
cat .github/dependency-check-suppressions.xml
```

#### 2. **Tests Fail**

```bash
# Run tests locally
uv run pytest -v --cov=packages

# Check coverage
uv run pytest --cov=packages --cov-report=html
open htmlcov/index.html
```

#### 3. **Build Fails**

```bash
# Build locally
uv build

# Check package metadata
uv run twine check dist/*

# Validate pyproject.toml
uv run validate-pyproject pyproject.toml
```

#### 4. **PyPI Publishing Fails**

- **Error: "Project not found"**
  - First release must be done manually or project must exist
  - Create project on PyPI first

- **Error: "Invalid or non-existent authentication"**
  - Trusted publishing not configured
  - Follow "Configure PyPI Trusted Publishing" steps above

- **Error: "File already exists"**
  - Version already published
  - Bump version and try again

---

## Version Management

### Semantic Versioning

Paracle follows [SemVer](https://semver.org/):

- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features, backward compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, backward compatible

### Bump Version Script

```bash
# Patch release (1.0.3 → 1.0.4)
python scripts/bump_version.py patch

# Minor release (1.0.3 → 1.1.0)
python scripts/bump_version.py minor

# Major release (1.0.3 → 2.0.0)
python scripts/bump_version.py major

# Custom version
python scripts/bump_version.py --version 1.5.0
```

---

## Post-Release Tasks

After successful PyPI publication:

1. **Verify on PyPI**
   - Check: https://pypi.org/project/paracle/
   - Verify version, metadata, description

2. **Test installation**

   ```bash
   pip install --upgrade paracle
   paracle --version
   ```

3. **Update documentation**
   - Update getting-started.md with new version
   - Update examples if needed

4. **Announce release**
   - GitHub Discussions
   - Social media
   - Release notes blog post

5. **Monitor for issues**
   - Check GitHub issues
   - Monitor downloads
   - Watch for bug reports

---

## Quick Reference

```bash
# Test release to TestPyPI
gh workflow run release.yml --ref develop -f publish_to=testpypi

# Production release via tag
git tag v1.0.4 && git push origin v1.0.4

# Watch workflow
gh run watch

# Check PyPI
open https://pypi.org/project/paracle/
```

---

## Security Notes

- ✅ **No tokens stored**: Uses OIDC trusted publishing
- ✅ **Environment protection**: `pypi` environment can require reviewers
- ✅ **Automated security scans**: OWASP, Bandit, Safety before publish
- ✅ **Audit trail**: All publishes logged in GitHub Actions

---

## Support

- **Documentation**: https://docs.paracles.com/
- **Issues**: https://github.com/IbIFACE-Tech/paracle/issues
- **Email**: dev@ibiface.com

---

**Last Updated**: 2026-01-19
**Workflow File**: [`.github/workflows/release.yml`](.github/workflows/release.yml)
