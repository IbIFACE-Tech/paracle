# PyPI Publishing Setup Guide

## Overview

Your GitHub Actions workflow is already configured to publish to PyPI using **Trusted Publishers (OIDC)**, which is more secure than API tokens.

## Step 1: Register Project on PyPI

### Option A: First-time Publishing (Recommended)

1. Go to https://pypi.org/manage/account/publishing/
2. Click **"Add a new pending publisher"**
3. Fill in the form:
   - **PyPI Project Name**: `paracle`
   - **Owner**: `IbIFACE-Tech`
   - **Repository name**: `paracle`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`
4. Click **"Add"**

### Option B: If Project Already Exists

If you already own the `paracle` project on PyPI:

1. Go to https://pypi.org/manage/project/paracle/settings/publishing/
2. Click **"Add a new publisher"**
3. Fill in the same form as above

## Step 2: Configure TestPyPI (Optional but Recommended)

Test your release process on TestPyPI first:

1. Go to https://test.pypi.org/manage/account/publishing/
2. Add a pending publisher with the same settings:
   - **PyPI Project Name**: `paracle`
   - **Owner**: `IbIFACE-Tech`
   - **Repository name**: `paracle`
   - **Workflow name**: `release.yml`
   - **Environment name**: `testpypi`

## Step 3: Publishing Options

### Option A: Test Release (TestPyPI)

```bash
# Manually trigger workflow for TestPyPI
gh workflow run release.yml --ref develop -f publish_to=testpypi
```

### Option B: Production Release (PyPI)

#### Method 1: Create a Git Tag (Recommended)

```bash
# Ensure all changes are committed
git add .
git commit -m "chore: prepare release v1.0.3"
git push origin develop

# Create and push tag
git tag v1.0.3
git push origin v1.0.3
```

This will automatically:
- ✅ Run security scans
- ✅ Run all tests
- ✅ Build the package
- ✅ Publish to PyPI
- ✅ Create a GitHub release

#### Method 2: Manual Workflow Trigger

```bash
# Manually trigger workflow for PyPI
gh workflow run release.yml --ref main -f publish_to=pypi
```

## Current Version

- **Version in pyproject.toml**: `1.0.3`
- **Last Published**: (check https://pypi.org/project/paracle/)

## Pre-Release Checklist

Before publishing to PyPI, ensure:

- [ ] All tests pass (run `uv run pytest`)
- [ ] Version number is updated in `pyproject.toml`
- [ ] CHANGELOG.md is updated
- [ ] Documentation is up to date
- [ ] PR #11 is merged to main (if ready)
- [ ] Formatting is applied (`black packages/`)
- [ ] Security scan passes

## Troubleshooting

### Error: "Project name already exists"

If someone else owns `paracle` on PyPI, you'll need to:
1. Choose a different name (e.g., `paracle-ai`, `paracle-framework`)
2. Update `name` in `pyproject.toml`
3. Update the workflow accordingly

### Error: "Authentication failed"

- Ensure you've configured the Trusted Publisher on PyPI
- Verify the repository name, owner, and workflow name match exactly
- Check that the workflow is running from the correct branch/tag

### Error: "Environment protection rules"

If you see this error:
1. Go to: https://github.com/IbIFACE-Tech/paracle/settings/environments
2. Click on `pypi` environment
3. Add protection rules (optional: require reviewers)

## Next Steps After Publishing

1. Verify the package on PyPI: https://pypi.org/project/paracle/
2. Test installation: `pip install paracle`
3. Update documentation with installation instructions
4. Announce the release!

## Useful Commands

```bash
# Check workflow status
gh run list --workflow=release.yml --limit 5

# View workflow logs
gh run view

# Check latest release
gh release view --repo IbIFACE-Tech/paracle

# List all releases
gh release list --repo IbIFACE-Tech/paracle
```
