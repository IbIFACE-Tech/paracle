# Publishing Paracle to PyPI - Action Items

## 📋 Current Status

✅ **Infrastructure Complete**
- GitHub Actions workflow enhanced with quality gates
- Version bump scripts created (bash + PowerShell)
- Make targets added for easy releases
- Complete documentation (750+ lines across 3 guides)
- Cross-platform support (Windows/Linux/Mac)

⏳ **Pending User Actions**
- Configure PyPI API token
- Test publish to TestPyPI
- First production release

## 🎯 Next Steps (In Order)

### Step 1: Configure PyPI Token (5 minutes)

**Required Before Publishing**

1. **Create PyPI Account** (if you don't have one):
   - Go to: https://pypi.org/account/register/
   - Verify email

2. **Generate API Token**:
   - Login to PyPI
   - Go to: https://pypi.org/manage/account/token/
   - Click "Add API token"
   - Name: `paracle-github-actions`
   - Scope: Entire account (can scope to project after first upload)
   - **Copy the token** (starts with `pypi-`, you'll only see it once!)

3. **Add Token to GitHub Secrets**:
   - Go to: https://github.com/IbIFACE-Tech/paracle-lite/settings/secrets/actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your token
   - Click "Add secret"

4. **Verify Secret**:
   - Go back to secrets page
   - You should see `PYPI_API_TOKEN` listed

**Status**: ⏳ USER ACTION REQUIRED

---

### Step 2: Test Locally (5 minutes)

**Verify everything works before releasing**

**On Windows:**
```powershell
# Navigate to project directory
cd c:\Projets\paracle\paracle-lite

# Run tests
uv run pytest -v

# Check governance
uv run paracle governance health --verbose

# Build package
uv build

# Validate package
uv run twine check dist/*
```

**Expected Output:**
```
✅ All tests pass
✅ Governance health: OK
✅ Package built: dist/paracle-0.0.1-py3-none-any.whl
✅ Package valid: dist/paracle-0.0.1.tar.gz
```

**Status**: ⏳ READY TO EXECUTE

---

### Step 3: Test on TestPyPI (10 minutes) - OPTIONAL BUT RECOMMENDED

**Test the release process safely**

**Why Test on TestPyPI?**
- Same as PyPI but for testing
- Can delete and retry if issues
- Validates entire publishing process
- No risk to production PyPI

**Steps:**

1. **Create TestPyPI Account** (if you don't have one):
   - Go to: https://test.pypi.org/account/register/

2. **Generate TestPyPI Token**:
   - Go to: https://test.pypi.org/manage/account/token/
   - Name: `paracle-test`
   - Copy token

3. **Add to GitHub Secrets**:
   - Secret name: `TEST_PYPI_API_TOKEN`
   - Value: Your TestPyPI token

4. **Publish to TestPyPI**:

   **Windows:**
   ```powershell
   # Set environment variable
   $env:TWINE_USERNAME = "__token__"
   $env:TWINE_PASSWORD = "pypi-..."  # Your TestPyPI token

   # Clean old builds
   Remove-Item dist -Recurse -Force -ErrorAction SilentlyContinue

   # Build
   uv build

   # Publish to TestPyPI
   uv run twine upload --repository testpypi dist/*
   ```

5. **Verify Installation**:
   ```powershell
   # Create test environment
   python -m venv test-env
   .\test-env\Scripts\activate

   # Install from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ paracle

   # Test CLI
   paracle --version
   paracle hello

   # Clean up
   deactivate
   Remove-Item test-env -Recurse -Force
   ```

**Expected:**
- ✅ Package uploads to TestPyPI
- ✅ Package visible at: https://test.pypi.org/project/paracle/
- ✅ CLI installs and runs correctly

**Status**: ⏳ OPTIONAL (but recommended)

---

### Step 4: First Production Release (15 minutes)

**Ready for the real thing!**

**Choose Version Number:**
- Current: `0.0.1`
- Suggested: `0.1.0` (beta release)
- Rationale: 0.1.0 signals "usable beta", 0.0.1 is too low

**Release Process:**

1. **Bump Version**:

   **Windows:**
   ```powershell
   # Navigate to project
   cd c:\Projets\paracle\paracle-lite

   # Bump to 0.1.0 (minor version)
   powershell -ExecutionPolicy Bypass -File scripts\bump-version.ps1 minor
   ```

   **Expected Output:**
   ```
   Current version: 0.0.1
   New version: 0.1.0
   Proceed with version bump? (y/n): y
   Updating pyproject.toml...
   Updating package __version__...
   Creating git commit and tag...
   ✅ Version bumped to 0.1.0

   Next steps:
     1. Review the changes: git show
     2. Push to GitHub: git push origin develop && git push origin v0.1.0
   ```

2. **Review Changes**:
   ```powershell
   git show
   git log --oneline -3
   ```

3. **Push to GitHub** (triggers automated release):
   ```powershell
   # Push branch
   git push origin develop

   # Push tag (this triggers GitHub Actions)
   git push origin v0.1.0
   ```

4. **Monitor GitHub Actions**:
   - Go to: https://github.com/IbIFACE-Tech/paracle-lite/actions
   - Click on the running workflow
   - Watch the jobs:
     * ✅ Test (pytest + governance + coverage)
     * ✅ Build (uv build + twine check)
     * ✅ Publish to PyPI
     * ✅ Create GitHub Release

5. **Verify on PyPI**:
   - Package page: https://pypi.org/project/paracle/
   - Should show version 0.1.0
   - Should have README and documentation

6. **Test Installation**:
   ```powershell
   # Create fresh environment
   python -m venv verify-env
   .\verify-env\Scripts\activate

   # Install from PyPI
   pip install paracle

   # Verify
   paracle --version  # Should show 0.1.0
   paracle hello      # Should work

   # Clean up
   deactivate
   Remove-Item verify-env -Recurse -Force
   ```

**Expected:**
- ✅ GitHub Actions completes successfully
- ✅ Package published to PyPI: https://pypi.org/project/paracle/
- ✅ GitHub release created: https://github.com/IbIFACE-Tech/paracle-lite/releases
- ✅ CLI installable: `pip install paracle`
- ✅ CLI works correctly

**Status**: ⏳ READY AFTER STEP 1

---

### Step 5: Post-Release Tasks (15 minutes)

**After successful release**

1. **Announce Release**:
   - Update README.md with installation instructions
   - Post in GitHub Discussions
   - Tweet/social media announcement

2. **Create CHANGELOG.md**:
   ```markdown
   # Changelog

   ## [0.1.0] - 2026-01-07

   ### Added
   - Complete 5-layer governance system
   - Layer 5: Continuous monitoring with auto-repair
   - Automated PyPI publishing via GitHub Actions
   - CLI commands for governance management
   - Cross-platform support (Windows/Linux/Mac)

   ### Changed
   - Enhanced release workflow with quality gates

   ### Fixed
   - Async issues in monitor auto-repair
   - File locking race conditions
   ```

3. **Update Documentation**:
   - Add installation instructions to docs
   - Update getting started guide
   - Add PyPI badge to README

4. **Monitor Issues**:
   - Watch for installation problems
   - Respond to user feedback
   - Fix critical bugs quickly

**Status**: ⏳ AFTER STEP 4

---

## 📚 Documentation Reference

All guides are in the `docs/` directory:

1. **docs/publishing-guide.md** (350+ lines)
   - Complete PyPI publishing guide
   - All three release methods
   - Troubleshooting section

2. **docs/windows-publishing-guide.md** (400+ lines)
   - Windows-specific instructions
   - PowerShell commands
   - Windows troubleshooting

3. **docs/publishing-setup-summary.md** (200+ lines)
   - What we built
   - How it works
   - Benefits and status

## 🐛 Troubleshooting

### "powershell scripts disabled"

**Problem:** Can't run PowerShell scripts

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or bypass for single command
powershell -ExecutionPolicy Bypass -File scripts\bump-version.ps1 patch
```

### "Authentication failed" on publish

**Problem:** PyPI token not configured or incorrect

**Solution:**
1. Verify token in GitHub Secrets
2. Regenerate token if needed
3. Check token hasn't expired

### GitHub Actions fails

**Problem:** Workflow fails during execution

**Common Causes:**
- Tests failing → Fix tests and retry
- Governance check fails → Run `paracle governance health`
- Coverage too low → Add more tests
- Build fails → Check pyproject.toml syntax

**Solution:**
1. Check workflow logs in GitHub Actions
2. Fix the issue locally
3. Delete tag: `git push origin --delete v0.1.0`
4. Delete local tag: `git tag -d v0.1.0`
5. Retry release after fix

### Package won't install from PyPI

**Problem:** Users can't install the package

**Possible Causes:**
- Package not yet indexed (wait 5 minutes)
- Dependency issues
- Python version incompatibility

**Solution:**
1. Wait a few minutes for PyPI indexing
2. Check package page for errors
3. Test locally: `pip install paracle`

## ✅ Success Criteria

You'll know everything is working when:

- ✅ `pip install paracle` works from any machine
- ✅ `paracle --version` shows correct version
- ✅ `paracle hello` executes successfully
- ✅ Package visible on PyPI: https://pypi.org/project/paracle/
- ✅ GitHub release created with changelog
- ✅ Downloads counter starts increasing on PyPI

## 🎉 What You'll Have

After completing all steps:

1. **Automated Publishing**
   - Tag-based releases
   - Quality gates enforced
   - No manual uploads needed

2. **Cross-Platform Support**
   - Works on Windows, Mac, Linux
   - PowerShell and Bash scripts
   - Clear documentation

3. **Quality Assurance**
   - Tests run before every release
   - Governance validation required
   - 80% coverage enforced
   - Package validation

4. **Professional Distribution**
   - Published on PyPI
   - Users can `pip install paracle`
   - GitHub releases with changelogs
   - Semantic versioning

## 📞 Questions?

- **Publishing Guide**: See `docs/publishing-guide.md`
- **Windows Guide**: See `docs/windows-publishing-guide.md`
- **Setup Summary**: See `docs/publishing-setup-summary.md`
- **GitHub Issues**: https://github.com/IbIFACE-Tech/paracle-lite/issues

---

## Quick Commands Cheat Sheet

### Windows PowerShell

```powershell
# Run tests
uv run pytest -v

# Check governance
uv run paracle governance health

# Build package
uv build

# Validate package
uv run twine check dist/*

# Bump version
powershell -ExecutionPolicy Bypass -File scripts\bump-version.ps1 patch

# Push release
git push origin develop
git push origin v0.1.0
```

### Unix/Linux/Mac

```bash
# Run tests
uv run pytest -v

# Check governance
uv run paracle governance health

# Build package
uv build

# Bump and release
make release-minor
git push origin develop
git push origin v0.1.0
```

---

**Ready to publish?** Start with Step 1: Configure PyPI Token! 🚀

**Status**: Publishing infrastructure complete, awaiting PyPI configuration

