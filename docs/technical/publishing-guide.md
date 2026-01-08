# Release Guide

This guide explains how to publish Paracle to PyPI using GitHub Actions.

## Prerequisites

1. **PyPI Account**: Create account at https://pypi.org
2. **GitHub Secrets**: Configure in repository settings
3. **Permissions**: Write access to repository

## Setup PyPI Publishing

### 1. Create PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `paracle-github-actions`
4. Scope: "Entire account" (or specific to `paracle` project)
5. Copy the token (starts with `pypi-`)

### 2. Add GitHub Secret

1. Go to repository: https://github.com/IbIFACE-Tech/paracle-lite/settings/secrets/actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Paste the PyPI token
5. Click "Add secret"

### 3. Configure TestPyPI (Optional)

For testing releases before publishing to PyPI:

1. Create account at https://test.pypi.org
2. Generate API token
3. Add as GitHub secret: `TEST_PYPI_API_TOKEN`

## Release Process

### Method 1: Automated (Recommended)

**Using GitHub Tags:**

**Unix/Linux/Mac:**
```bash
# 1. Bump version
make release-patch    # 0.0.1 → 0.0.2
# or
make release-minor    # 0.0.1 → 0.1.0
# or
make release-major    # 0.0.1 → 1.0.0

# 2. Push tag to trigger release
git push origin develop
git push origin v0.0.2  # Replace with your version
```

**Windows (PowerShell):**
```powershell
# 1. Bump version
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 patch   # 0.0.1 → 0.0.2
# or
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 minor   # 0.0.1 → 0.1.0
# or
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 major   # 0.0.1 → 1.0.0

# 2. Push tag to trigger release
git push origin develop
git push origin v0.0.2  # Replace with your version
```

**What happens automatically:**
1. GitHub Actions triggered by tag push
2. Runs tests (pytest + governance + coverage)
3. Validates governance health
4. Builds package (uv build)
5. Validates package (twine check)
6. Publishes to PyPI
7. Creates GitHub release with changelog

**Check Progress:**
- GitHub Actions: https://github.com/IbIFACE-Tech/paracle-lite/actions
- PyPI: https://pypi.org/project/paracle/

### Method 2: Manual Trigger

**For testing or hotfixes:**

```bash
# 1. Go to GitHub Actions
https://github.com/IbIFACE-Tech/paracle-lite/actions/workflows/release.yml

# 2. Click "Run workflow"
# 3. Select:
#    - Branch: develop (or main)
#    - Publish to: testpypi (for testing) or pypi (for production)
# 4. Click "Run workflow"
```

### Method 3: Local Publishing (Not Recommended)

**Only use for emergencies:**

```bash
# 1. Build package
make build

# 2. Publish to TestPyPI (test first!)
make publish-test

# 3. Test installation
pip install --index-url https://test.pypi.org/simple/ paracle

# 4. If OK, publish to PyPI
make publish
```

## Release Checklist

Before releasing, ensure:

- [ ] All tests passing (`make test`)
- [ ] Governance health OK (`paracle governance health`)
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG updated
- [ ] Documentation up to date
- [ ] No uncommitted changes
- [ ] On correct branch (`develop` or `main`)

**Automated checks run on CI:**
```bash
# Run locally before pushing
make release-check
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **Patch** (0.0.X): Bug fixes, small changes
- **Minor** (0.X.0): New features, backward compatible
- **Major** (X.0.0): Breaking changes

**Current version:** `0.0.1` (alpha)

**Roadmap:**
- `0.1.0` - Beta release (API stable)
- `0.5.0` - Release candidate
- `1.0.0` - Production release

## GitHub Actions Workflow

The release workflow (`.github/workflows/release.yml`) does:

1. **Test Job**:
   - Runs full test suite
   - Validates governance structure
   - Checks code coverage (80% minimum)

2. **Build Job**:
   - Builds wheel and sdist
   - Validates package with `twine check`

3. **Publish Jobs**:
   - **TestPyPI**: For manual testing
   - **PyPI**: For production releases

4. **GitHub Release**:
   - Creates release notes from commits
   - Attaches distribution files
   - Tags release with version

## Troubleshooting

### Build Fails

```bash
# Check locally
uv build

# Common issues:
# - Missing files in MANIFEST.in
# - Import errors
# - Version conflicts
```

### Tests Fail in CI

```bash
# Run same test matrix locally
uv run pytest -v

# Check governance
paracle governance health --verbose
```

### PyPI Upload Fails

**Authentication errors:**
- Check `PYPI_API_TOKEN` secret is set
- Verify token has correct scope
- Token may have expired (regenerate)

**Package already exists:**
- Can't overwrite existing version
- Must bump version number
- Delete from PyPI not recommended

**Invalid package:**
```bash
# Validate before upload
uv run twine check dist/*

# Common issues:
# - Long description rendering (README.md)
# - Missing metadata
# - Invalid classifiers
```

### TestPyPI vs PyPI

**TestPyPI** (https://test.pypi.org):
- For testing releases
- Separate from production
- Can upload same version multiple times (after deleting)
- Install: `pip install --index-url https://test.pypi.org/simple/ paracle`

**PyPI** (https://pypi.org):
- Production registry
- Cannot delete/replace versions
- Version numbers are permanent
- Install: `pip install paracle`

## Post-Release

After successful release:

1. **Verify Installation**:
   ```bash
   # Create fresh virtual environment
   python -m venv test-env
   source test-env/bin/activate  # or test-env\Scripts\activate on Windows

   # Install from PyPI
   pip install paracle

   # Test CLI
   paracle --version
   paracle hello
   ```

2. **Update Documentation**:
   - Update version in docs
   - Add release notes
   - Update installation guide

3. **Announce Release**:
   - GitHub Discussions
   - Twitter/LinkedIn
   - Dev.to/Medium blog post
   - Reddit (r/Python, r/MachineLearning)

4. **Monitor Issues**:
   - Check GitHub issues
   - Monitor PyPI download stats
   - Respond to community feedback

## Quick Reference

```bash
# Check what will be released
make release-check

# Bump version and create tag
make release-patch    # Patch: 0.0.1 → 0.0.2
make release-minor    # Minor: 0.0.1 → 0.1.0
make release-major    # Major: 0.0.1 → 1.0.0

# Push to trigger release
git push origin develop
git push origin v0.0.2

# Manual publish (not recommended)
make publish-test     # TestPyPI
make publish          # PyPI

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ paracle

# Install from PyPI
pip install paracle
```

## Security

**Never commit:**
- PyPI API tokens
- Credentials
- Private keys

**Use GitHub Secrets for:**
- `PYPI_API_TOKEN`
- `TEST_PYPI_API_TOKEN`
- Other sensitive data

## Support

- **Issues**: https://github.com/IbIFACE-Tech/paracle-lite/issues
- **Discussions**: https://github.com/IbIFACE-Tech/paracle-lite/discussions
- **Email**: team@ibiface-tech.com

---

**Ready to release?**

```bash
# 1. Ensure everything is committed
git status

# 2. Run release checks
make release-check

# 3. Bump version (choose one)
make release-patch    # Most common for fixes
make release-minor    # For new features
make release-major    # For breaking changes

# 4. Push tag to trigger automated release
git push origin develop
git push origin v<version>

# 5. Watch GitHub Actions
# https://github.com/IbIFACE-Tech/paracle-lite/actions
```

🎉 **Your package will be live on PyPI in ~5 minutes!**
