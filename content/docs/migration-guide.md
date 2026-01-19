# Migration Guide

> **Complete guide for upgrading between Paracle versions**

This guide helps you migrate between major, minor, and patch versions of Paracle, handling breaking changes and taking advantage of new features.

---

## Table of Contents

- [Quick Reference](#quick-reference)
- [Upgrading to v1.0.x](#upgrading-to-v10x)
- [Breaking Changes by Version](#breaking-changes-by-version)
- [Deprecation Timeline](#deprecation-timeline)
- [Migration Checklist](#migration-checklist)
- [Common Issues](#common-issues)
- [Getting Help](#getting-help)

---

## Quick Reference

### Version Compatibility Matrix

| From Version  | To Version | Breaking Changes | Migration Time | Difficulty |
| ------------- | ---------- | ---------------- | -------------- | ---------- |
| 0.9.x → 1.0.0 | ✅ Safe     | Yes (3 items)    | ~30 min        | Easy       |
| 0.8.x → 1.0.0 | ⚠️ Review   | Yes (8 items)    | ~2 hours       | Medium     |
| 0.7.x → 1.0.0 | ❌ Complex  | Yes (15+ items)  | ~1 day         | Hard       |

### Upgrade Command

```bash
# Backup first!
paracle backup create --name "pre-v1.0-upgrade"

# Upgrade
pip install --upgrade paracle

# Verify
paracle --version
paracle validate structure
paracle doctor
```

---

## Upgrading to v1.0.x

### From v0.9.x to v1.0.0

**Release Date**: January 2026
**Breaking Changes**: 3 (Low impact)
**New Features**: MCP Full Coverage, Docker Dependency Management, Enhanced Logging

#### 1. **Breaking Changes**

##### BC-001: `.parac/` Structure Reorganization

**Impact**: Low - Automatic migration available

**What Changed**:
```diff
# Old structure (v0.9.x)
.parac/
├── costs.db              ❌ Moved
├── logs/agent.log        ❌ Moved
└── docs/                 ❌ Relocated

# New structure (v1.0.0)
.parac/
├── memory/
│   ├── data/
│   │   └── costs.db      ✅ New location
│   └── logs/
│       └── agent_actions.log  ✅ New location
└── config/               ✅ Configs here
```

**Migration**:
```bash
# Automatic migration
paracle migrate --from 0.9 --to 1.0

# Manual migration
mkdir -p .parac/memory/data .parac/memory/logs
mv .parac/costs.db .parac/memory/data/
mv .parac/logs/*.log .parac/memory/logs/
```

**Code Changes**: None required (paths auto-resolved)

---

##### BC-002: Docker Dependency Now Optional

**Impact**: None if Docker already installed

**What Changed**:
```python
# Old (v0.9.x) - Docker required
from paracle_sandbox import DockerSandbox

# New (v1.0.0) - Docker optional
from paracle_sandbox import DockerSandbox  # Works with or without Docker
```

**Migration**:
```bash
# If you use sandbox features, install Docker extras
pip install paracle[sandbox]

# Or install Docker separately
pip install docker psutil
```

**Behavior**:
- **Without Docker**: Core Paracle works, sandbox disabled with helpful message
- **With Docker**: All features work as before

---

##### BC-003: Logging Configuration Changes

**Impact**: Low - Defaults changed, manual config unaffected

**What Changed**:
```yaml
# Old default (v0.9.x)
logging:
  level: INFO
  file: logs/paracle.log

# New default (v1.0.0)
logging:
  level: INFO
  file: .parac/memory/logs/agent_actions.log
  dual_logging: true  # New: separate user/framework logs
```

**Migration**:
- **If using default**: No action needed (auto-upgraded)
- **If custom config**: Update `project.yaml`:
  ```yaml
  logging:
    file: .parac/memory/logs/agent_actions.log
    dual_logging: true
  ```

---

#### 2. **New Features to Adopt**

##### MCP Full Coverage (ADR-022)

**Benefit**: 100% API coverage via MCP, zero duplication

**Adoption**:
```python
# Old: Limited MCP tools
from paracle_mcp import MCPServer

# New: 56 tools auto-generated from API
server = MCPServer()
# All API endpoints now available as MCP tools!
```

**Documentation**: [mcp-full-coverage.md](mcp-full-coverage.md)

---

##### Enhanced Error Messages

**Benefit**: 350% better error clarity, step-by-step guidance

**Example**:
```python
# Old error (v0.9.x)
ModuleNotFoundError: No module named 'docker'

# New error (v1.0.0)
ImportError: Docker SDK not installed

Sandbox features require Docker. To enable:
1. Install Docker Desktop: https://docker.com/get-started
2. Install Paracle with sandbox extras:
   pip install paracle[sandbox]

Note: Sandbox features are optional. Core Paracle works without Docker.
```

---

##### Dual Logging Architecture

**Benefit**: Separate user logs (.parac/) from framework logs (system)

**Usage**:
```python
from paracle_core import get_logger

# User logs → .parac/memory/logs/agent_actions.log
user_log = get_logger("user")
user_log.info("My custom message")

# Framework logs → system logs
framework_log = get_logger("paracle")
framework_log.debug("Internal diagnostic")
```

**Documentation**: [logging-architecture.md](logging-architecture.md)

---

#### 3. **Migration Checklist**

- [ ] **Backup**: Create backup with `paracle backup create`
- [ ] **Upgrade**: Run `pip install --upgrade paracle`
- [ ] **Verify**: Check version with `paracle --version` (should be 1.0.x)
- [ ] **Migrate Structure**: Run `paracle migrate --from 0.9 --to 1.0`
- [ ] **Validate**: Run `paracle validate structure`
- [ ] **Health Check**: Run `paracle doctor`
- [ ] **Test**: Run agents/workflows to verify functionality
- [ ] **Update Config**: Review and update `project.yaml` if needed
- [ ] **Install Extras**: Add `[sandbox]` if using Docker features
- [ ] **Update CI/CD**: Update version pins in pipelines
- [ ] **Review Logs**: Check new log locations work correctly

---

### From v0.8.x to v1.0.0

**Additional Breaking Changes**: 5 more items

#### BC-004: Agent Spec Format Change

**Impact**: Medium - Requires spec file updates

**What Changed**:
```yaml
# Old format (v0.8.x)
agent:
  name: my_agent
  model: gpt-4
  tools: [tool1, tool2]

# New format (v1.0.0)
name: my_agent
model: claude-sonnet-4-20250514  # New default
temperature: 0.7
capabilities: [capability1]       # New: capabilities field
tools: [tool1, tool2]
skills: [skill1]                  # New: skills system
```

**Migration Script**:
```bash
# Auto-migrate agent specs
paracle agents migrate --from 0.8 --to 1.0
```

---

#### BC-005: Tool Registration API

**Impact**: Medium - Code changes required

**What Changed**:
```python
# Old API (v0.8.x)
@register_tool
def my_tool(param: str) -> str:
    return result

# New API (v1.0.0)
from paracle_tools import tool

@tool(name="my_tool", category="custom")
def my_tool(param: str) -> str:
    """Tool description."""
    return result
```

**Migration**:
```bash
# Find affected files
grep -r "@register_tool" packages/

# Update to new API
# Replace: @register_tool
# With: @tool(name="tool_name", category="category")
```

---

#### BC-006: Provider API Changes

**Impact**: Low - Affects custom providers only

**What Changed**:
```python
# Old (v0.8.x)
class MyProvider(Provider):
    async def complete(self, prompt):
        pass

# New (v1.0.0)
class MyProvider(LLMProvider):
    async def complete(self, messages, model, temperature):
        pass
```

**Documentation**: [developers/custom-providers.md](developers/custom-providers.md)

---

#### BC-007: Workflow YAML Schema

**Impact**: Low - Automated migration

**What Changed**:
```yaml
# Old (v0.8.x)
workflow:
  steps:
    - agent: coder
      task: "Implement"

# New (v1.0.0)
steps:
  - id: step1
    agent: coder
    task: "Implement"
    depends_on: []  # New: dependency tracking
```

**Migration**:
```bash
paracle workflows migrate --from 0.8 --to 1.0
```

---

#### BC-008: Configuration File Naming

**Impact**: None - Auto-detected

**What Changed**:
```diff
# Old (v0.8.x)
- config.yaml
- settings.yaml

# New (v1.0.0)
+ project.yaml      (user-editable)
+ manifest.yaml     (auto-generated)
```

**Migration**: Rename `config.yaml` → `project.yaml`

---

### From v0.7.x to v1.0.0

**Status**: Complex migration - contact support

This migration involves significant architectural changes. We recommend:

1. **Review Migration Path**: Read [v0.7-to-v0.8.md](migrations/v0.7-to-v0.8.md) first
2. **Incremental Upgrade**: v0.7 → v0.8 → v0.9 → v1.0
3. **Professional Support**: Contact support@paracles.com for assistance
4. **Testing Environment**: Test migration in dev environment first

**Key Changes**:
- Complete `.parac/` restructure
- New agent inheritance system
- Event bus architecture
- Store layer refactoring
- MCP integration

---

## Breaking Changes by Version

### v1.0.0 (January 2026)

| Change              | Type       | Impact | Auto-Migration |
| ------------------- | ---------- | ------ | -------------- |
| `.parac/` structure | Structure  | Low    | ✅ Yes          |
| Docker optional     | Dependency | None   | ✅ Auto         |
| Logging paths       | Config     | Low    | ✅ Yes          |

### v0.9.0 (December 2025)

| Change          | Type         | Impact | Auto-Migration |
| --------------- | ------------ | ------ | -------------- |
| Skills system   | Feature      | None   | ✅ Additive     |
| MCP integration | Feature      | None   | ✅ Additive     |
| API-first CLI   | Architecture | None   | ✅ Compatible   |

### v0.8.0 (November 2025)

| Change            | Type      | Impact | Auto-Migration |
| ----------------- | --------- | ------ | -------------- |
| Agent spec format | Structure | Medium | ✅ Yes          |
| Tool registration | API       | Medium | ❌ Manual       |
| Provider API      | API       | Low    | ❌ Manual       |
| Workflow schema   | Structure | Low    | ✅ Yes          |
| Config naming     | Files     | None   | ✅ Auto         |

---

## Deprecation Timeline

### Currently Deprecated (Remove in v2.0.0)

| Feature            | Deprecated In | Remove In | Alternative         |
| ------------------ | ------------- | --------- | ------------------- |
| `@register_tool`   | v0.9.0        | v2.0.0    | `@tool(name=...)`   |
| Old logging config | v1.0.0        | v2.0.0    | Dual logging system |
| `config.yaml`      | v0.8.0        | v2.0.0    | `project.yaml`      |

### Deprecation Warnings

Enable deprecation warnings in development:
```python
import warnings
warnings.filterwarnings("default", category=DeprecationWarning)
```

---

## Migration Checklist

### Pre-Migration

- [ ] **Backup Everything**
  ```bash
  paracle backup create --name "pre-migration-$(date +%Y%m%d)"
  ```
- [ ] **Review Breaking Changes** for your version
- [ ] **Test in Dev Environment** first
- [ ] **Document Current State** (configs, customizations)
- [ ] **Check Custom Code** (tools, providers, adapters)

### During Migration

- [ ] **Upgrade Package**
  ```bash
  pip install --upgrade paracle
  ```
- [ ] **Run Migration Scripts**
  ```bash
  paracle migrate --from X.X --to Y.Y
  ```
- [ ] **Validate Structure**
  ```bash
  paracle validate structure --fix
  ```
- [ ] **Update Configuration** (`project.yaml`)
- [ ] **Test Core Features** (agents, workflows)
- [ ] **Check Logs** (new locations)

### Post-Migration

- [ ] **Run Health Check**
  ```bash
  paracle doctor
  ```
- [ ] **Update Documentation** (READMEs, guides)
- [ ] **Update CI/CD Pipelines** (version pins)
- [ ] **Notify Team Members**
- [ ] **Monitor Logs** for 24-48 hours
- [ ] **Rollback Plan Ready**
  ```bash
  paracle backup restore --name "pre-migration-YYYYMMDD"
  ```

---

## Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'docker'"

**Cause**: Docker SDK not installed (v1.0.0 makes it optional)

**Solution**:
```bash
pip install paracle[sandbox]
# OR
pip install docker psutil
```

**If you don't need sandbox**: Ignore - core Paracle works fine!

---

### Issue 2: "FileNotFoundError: .parac/costs.db"

**Cause**: Old database location (v1.0.0 moved to `memory/data/`)

**Solution**:
```bash
# Run migration
paracle migrate --from 0.9 --to 1.0

# Or manually
mkdir -p .parac/memory/data
mv .parac/costs.db .parac/memory/data/
```

---

### Issue 3: "Agent spec validation failed"

**Cause**: Old agent spec format (v0.8.0 changes)

**Solution**:
```bash
# Auto-migrate all agent specs
paracle agents migrate --from 0.8 --to 1.0

# Validate
paracle agents validate
```

---

### Issue 4: "Workflow execution failed: Unknown field 'depends_on'"

**Cause**: Old workflow schema (v0.8.0 changes)

**Solution**:
```bash
# Migrate workflows
paracle workflows migrate --from 0.8 --to 1.0

# Validate
paracle workflows validate
```

---

### Issue 5: "DeprecationWarning: @register_tool is deprecated"

**Cause**: Using old tool registration API

**Solution**:
```python
# Update to new API
from paracle_tools import tool

@tool(name="my_tool", category="custom")
def my_tool(param: str) -> str:
    """Description."""
    return result
```

---

## Getting Help

### Automated Diagnostics

```bash
# Run health check
paracle doctor

# Validate installation
paracle validate structure --strict

# Check migration status
paracle migrate --status
```

### Documentation

- **Migration Guides**: [content/docs/migrations/](migrations/)
- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)
- **API Changes**: [api/CHANGELOG.md](api/CHANGELOG.md)
- **Architecture**: [architecture.md](architecture.md)

### Community Support

- **GitHub Issues**: [github.com/IbIFACE-Tech/paracle/issues](https://github.com/IbIFACE-Tech/paracle/issues)
- **Discussions**: [github.com/IbIFACE-Tech/paracle/discussions](https://github.com/IbIFACE-Tech/paracle/discussions)
- **Discord**: [discord.gg/paracle](https://discord.gg/paracle) (coming soon)

### Professional Support

For enterprise migrations or complex scenarios:
- **Email**: support@paracles.com
- **Migration Service**: Professional migration assistance available
- **Training**: Team training sessions for major upgrades

---

## Best Practices

### 1. Incremental Upgrades

**✅ Recommended**:
```
v0.7.x → v0.8.x → v0.9.x → v1.0.x
```

**❌ Not Recommended**:
```
v0.7.x → v1.0.x (skipping versions)
```

### 2. Testing Strategy

```bash
# 1. Dev environment
python -m pytest tests/

# 2. Staging environment
paracle agents run test_agent --task "Verification"

# 3. Production (after 48h in staging)
# Deploy with rollback plan ready
```

### 3. Rollback Plan

Always have a rollback plan:
```bash
# Before upgrade
paracle backup create --name "pre-v1.0-upgrade"

# If issues occur
paracle backup restore --name "pre-v1.0-upgrade"
pip install paracle==0.9.5  # Previous version
```

### 4. Version Pinning

In production, pin exact versions:
```toml
# pyproject.toml
[tool.poetry.dependencies]
paracle = "1.0.2"  # Exact version, not "^1.0.0"
```

---

## Version History

| Version | Release Date | Major Changes                      | Migration Guide                                   |
| ------- | ------------ | ---------------------------------- | ------------------------------------------------- |
| 1.0.3   | Jan 2026     | DX: Migration, Doctor, Watch mode  | None needed                                       |
| 1.0.2   | Jan 2026     | Patch: Dependency fixes            | None needed                                       |
| 1.0.0   | Jan 2026     | MCP Full Coverage, Docker optional | [This guide](#upgrading-to-v10x)                  |
| 0.9.5   | Dec 2025     | Skills system                      | [v0.9-migration.md](migrations/v0.9-migration.md) |
| 0.8.0   | Nov 2025     | Agent specs refactor               | [v0.8-migration.md](migrations/v0.8-migration.md) |

---

**Last Updated**: January 10, 2026
**Version**: 1.0
**Status**: Active
