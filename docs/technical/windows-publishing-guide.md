# Windows Setup Guide for Publishing

This guide provides Windows-specific instructions for publishing Paracle to PyPI.

## Prerequisites

### 1. Install Required Tools

**Python and uv:**
```powershell
# Install Python 3.10+ from python.org
# Then install uv
pip install uv
```

**Git:**
```powershell
# Download from https://git-scm.com/download/win
# Or use winget:
winget install Git.Git
```

**GitHub CLI (Optional but Recommended):**
```powershell
# Download from https://cli.github.com/
# Or use winget:
winget install GitHub.cli
```

### 2. Configure PowerShell Execution Policy

Allow running local scripts:

```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Quick Release Process

### Step 1: Prepare Release

**Check everything is ready:**
```powershell
# Run tests
uv run pytest -v

# Check governance
uv run paracle governance health

# Validate package
uv build
uv run twine check dist/*
```

### Step 2: Bump Version

**Choose version bump type:**

```powershell
# Patch version (0.0.X) - Bug fixes
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 patch

# Minor version (0.X.0) - New features
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 minor

# Major version (X.0.0) - Breaking changes
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 major
```

**Example output:**
```
Current version: 0.0.1
New version: 0.0.2
Proceed with version bump? (y/n): y
Updating pyproject.toml...
Updating package __version__...
Creating git commit and tag...
✅ Version bumped to 0.0.2

Next steps:
  1. Review the changes: git show
  2. Push to GitHub: git push origin develop && git push origin v0.0.2
  3. GitHub Actions will automatically build and publish
```

### Step 3: Push and Release

```powershell
# Review changes
git show

# Push to GitHub
git push origin develop
git push origin v0.0.2  # Replace with your version

# Watch GitHub Actions
# https://github.com/IbIFACE-Tech/paracle-lite/actions
```

## Manual Commands

### Build Package Locally

```powershell
# Clean previous builds
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Build with uv
uv build

# Validate
uv run twine check dist/*

# List artifacts
Get-ChildItem dist -Recurse
```

### Publish to TestPyPI

```powershell
# First, set TestPyPI token
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-..."  # Your TestPyPI token

# Publish
uv run twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ paracle
```

### Publish to PyPI

```powershell
# Set PyPI token
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-..."  # Your PyPI token

# Publish (with confirmation)
uv run twine upload dist/*

# Verify
pip install paracle
paracle --version
```

## Troubleshooting

### "Scripts is disabled on this system"

**Problem:** PowerShell execution policy blocks scripts

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or bypass for single command:
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 patch
```

### "uv: command not found"

**Problem:** uv not in PATH

**Solution:**
```powershell
# Reinstall uv
pip install --upgrade uv

# Verify
uv --version
```

### "No module named 'twine'"

**Problem:** twine not installed in uv environment

**Solution:**
```powershell
# Install twine
uv pip install twine

# Or use uv run
uv run --with twine twine check dist/*
```

### Git Commands Fail

**Problem:** Git not in PATH

**Solution:**
```powershell
# Add Git to PATH
$env:Path += ";C:\Program Files\Git\cmd"

# Or reinstall Git with "Add to PATH" option
```

### "Authentication failed"

**Problem:** PyPI token incorrect or not set

**Solution:**
```powershell
# Check token is set
Write-Host $env:TWINE_PASSWORD

# Generate new token
# https://pypi.org/manage/account/token/

# Set token
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-..."  # Paste your token
```

## Using Make on Windows

### Option 1: Install Make via Chocolatey

```powershell
# Install Chocolatey first: https://chocolatey.org/install
# Then install make
choco install make
```

### Option 2: Use WSL (Windows Subsystem for Linux)

```powershell
# Install WSL
wsl --install

# Open Ubuntu terminal
wsl

# Run make commands in Linux
make release-patch
```

### Option 3: Use PowerShell Directly (Recommended)

Instead of `make` commands, use PowerShell equivalents:

| Make Command         | PowerShell Equivalent                                                     |
| -------------------- | ------------------------------------------------------------------------- |
| `make build`         | `uv build`                                                                |
| `make test`          | `uv run pytest -v`                                                        |
| `make release-patch` | `powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 patch` |
| `make publish-test`  | `uv run twine upload --repository testpypi dist/*`                        |
| `make publish`       | `uv run twine upload dist/*`                                              |

## Best Practices

### 1. Use Git Bash for Better Compatibility

Git Bash provides a Unix-like environment on Windows:

```bash
# Open Git Bash
# Then use Unix commands
make release-patch
git push origin v0.0.2
```

### 2. Always Test on TestPyPI First

```powershell
# 1. Publish to TestPyPI
uv run twine upload --repository testpypi dist/*

# 2. Test installation
python -m venv test-env
.\test-env\Scripts\activate
pip install --index-url https://test.pypi.org/simple/ paracle
paracle --version

# 3. If OK, publish to PyPI
deactivate
uv run twine upload dist/*
```

### 3. Use Environment Variables for Tokens

**Create a `.env` file:**
```ini
TWINE_USERNAME=__token__
TWINE_PASSWORD=pypi-...
```

**Load in PowerShell:**
```powershell
# Read .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

# Now TWINE_* variables are set
uv run twine upload dist/*
```

### 4. Automate with PowerShell Scripts

**Create `publish.ps1`:**
```powershell
# Full release automation
param([string]$BumpType = "patch")

# 1. Run tests
Write-Host "Running tests..." -ForegroundColor Yellow
uv run pytest -v
if ($LASTEXITCODE -ne 0) { exit 1 }

# 2. Check governance
Write-Host "Checking governance..." -ForegroundColor Yellow
uv run paracle governance health
if ($LASTEXITCODE -ne 0) { exit 1 }

# 3. Bump version
Write-Host "Bumping version..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 $BumpType

# 4. Push changes
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
$version = (Select-String -Path pyproject.toml -Pattern 'version = "([^"]+)"').Matches.Groups[1].Value
git push origin develop
git push origin "v$version"

Write-Host "✅ Release v$version initiated!" -ForegroundColor Green
Write-Host "Check progress: https://github.com/IbIFACE-Tech/paracle-lite/actions"
```

**Usage:**
```powershell
.\publish.ps1 patch   # For patch releases
.\publish.ps1 minor   # For minor releases
.\publish.ps1 major   # For major releases
```

## Security Notes

### Protect Your Tokens

**Never commit tokens to git:**
```powershell
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.token" >> .gitignore

# Check what would be committed
git status
git diff
```

**Use GitHub Secrets for CI/CD:**
- Don't set tokens in scripts
- Use GitHub repository secrets
- Workflow uses OIDC trusted publishing (no tokens needed!)

### Verify Package Before Publishing

```powershell
# 1. Build
uv build

# 2. Check
uv run twine check dist/*

# 3. Inspect contents
Expand-Archive dist\paracle-0.0.2-py3-none-any.whl -DestinationPath temp
Get-ChildItem temp -Recurse

# 4. Clean up
Remove-Item temp -Recurse
```

## Quick Reference

### Complete Release Workflow

```powershell
# 1. Prepare
git checkout develop
git pull origin develop
uv run pytest -v
uv run paracle governance health

# 2. Bump version
powershell -ExecutionPolicy Bypass -File scripts/bump-version.ps1 patch

# 3. Review
git show
git log --oneline -5

# 4. Push
git push origin develop
git push origin v0.0.2

# 5. Monitor
# https://github.com/IbIFACE-Tech/paracle-lite/actions

# 6. Verify
pip install --upgrade paracle
paracle --version
```

### Emergency Rollback

If release fails:

```powershell
# 1. Delete remote tag
git push origin --delete v0.0.2

# 2. Delete local tag
git tag -d v0.0.2

# 3. Reset version
git reset --hard HEAD~1

# 4. Force push (careful!)
git push origin develop --force
```

## See Also

- [Publishing Guide](publishing-guide.md) - Complete publishing documentation
- [PyPI Publishing](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) - Official guide
- [PowerShell Documentation](https://docs.microsoft.com/en-us/powershell/) - PowerShell reference

---

**Last Updated**: 2026-01-07
**Version**: 1.0
**Platform**: Windows 10/11, PowerShell 5.1+

