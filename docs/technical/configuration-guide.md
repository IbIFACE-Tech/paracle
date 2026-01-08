# Paracle Configuration Guide

Complete guide to configuring your Paracle project for different use cases.

## 📋 Table of Contents

1. [Quick Start (5 minutes)](#quick-start)
2. [Configuration Levels](#configuration-levels)
3. [Essential Settings](#essential-settings)
4. [Optional Features](#optional-features)
5. [Common Tasks](#common-tasks)
6. [Configuration Commands](#configuration-commands)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Topics](#advanced-topics)

---

## Quick Start

### New Projects

**Option 1: Interactive (Recommended)**
```bash
paracle init -i
# Prompts for: template, name, provider
# Creates minimal configuration automatically
```

**Option 2: Template-based**
```bash
# Minimal setup (17 lines)
paracle init --template lite

# Production ready (17 lines)
paracle init --template standard

# Enterprise (72 lines + optional configs)
paracle init --template advanced
```

### Existing Projects

```bash
# Validate current configuration
paracle config validate

# View effective configuration
paracle config show

# Show changes from defaults
paracle config diff
```

---

## Configuration Levels

Paracle uses **progressive disclosure** - start simple, add complexity when needed.

### Level 1: Minimal (Beginners)

**File**: `.parac/project.yaml` (20-30 lines)

```yaml
name: my-project
version: 0.1.0

defaults:
  model_provider: openai
  default_model: gpt-4o-mini
```

**What you get**:
- ✅ Basic project setup
- ✅ Single agent
- ✅ File-based persistence
- ✅ Default logging

**Use for**: Learning, prototyping, quick tests

### Level 2: Standard (Most Users)

**File**: `.parac/project.yaml` (20-30 lines)

```yaml
name: my-project
version: 0.1.0

defaults:
  model_provider: openai
  default_model: gpt-4

include:
  - config/logging.yaml  # Optional: Advanced logging
```

**What you get**:
- ✅ Multiple agents
- ✅ SQLite persistence
- ✅ Basic policies
- ✅ Optional logging config

**Use for**: Production apps, team projects

### Level 3: Advanced (Enterprises)

**Files**:
- `.parac/project.yaml` (30 lines)
- `.parac/config/logging.yaml` (80 lines)
- `.parac/config/cost-tracking.yaml` (75 lines)
- `.parac/config/file-management.yaml` (330 lines)

```yaml
name: my-project
version: 0.1.0

defaults:
  model_provider: openai
  default_model: gpt-4

include:
  - config/logging.yaml
  - config/cost-tracking.yaml
  - config/file-management.yaml
```

**What you get**:
- ✅ All agents (8 total)
- ✅ PostgreSQL + Redis
- ✅ Docker deployment
- ✅ CI/CD pipelines
- ✅ Full policies
- ✅ Cost tracking
- ✅ Enterprise logging

**Use for**: Large teams, compliance requirements, production scale

---

## Essential Settings

### Minimal project.yaml

```yaml
# ============================================
# ESSENTIAL (Edit these)
# ============================================

name: my-project              # Your project name
version: 0.1.0                # Semantic version
description: My awesome app   # Short description

defaults:
  model_provider: openai      # openai, anthropic, google, groq, ollama
  default_model: gpt-4o-mini  # Model name
  python_version: "3.10"      # Python version

# ============================================
# OPTIONAL (Comment out if not needed)
# ============================================

include:
  # - config/logging.yaml
  # - config/cost-tracking.yaml
  # - config/file-management.yaml
```

---

## Optional Features

### 1. Logging Configuration

**When to use**: Need custom log levels, rotation, or retention

**Enable**:
```yaml
# In project.yaml
include:
  - config/logging.yaml
```

**Configure** (`.parac/config/logging.yaml`):
```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: json # json or plain

  rotation:
    strategy: daily
    backup_count: 30
```

**See**: [Log Management Guide](log-management.md)

### 2. Cost Tracking

**When to use**: Monitor LLM API spending, set budgets

**Enable**:
```yaml
# In project.yaml
include:
  - config/cost-tracking.yaml
```

**Configure** (`.parac/config/cost-tracking.yaml`):
```yaml
cost:
  tracking:
    enabled: true
    persist_to_db: true

  budget:
    enabled: true
    monthly_limit: 100.0  # USD
    warning_threshold: 0.8  # 80%
```

**See**: [Cost Management Guide](cost-management.md)

### 3. File Management

**When to use**: Custom log limits, ADR templates, roadmap validation

**Enable**:
```yaml
# In project.yaml
include:
  - config/file-management.yaml
```

**Configure** (`.parac/config/file-management.yaml`):
```yaml
file_management:
  logs:
    global:
      max_line_length: 1000
      max_file_size_mb: 50

  adr:
    enabled: true
    format: markdown
```

**See**: This guide (Advanced Topics section)

---

## Common Tasks

### Change Model Provider

**OpenAI → Anthropic**:
```yaml
defaults:
  model_provider: anthropic
  default_model: claude-3.5-sonnet
```

**OpenAI → Google**:
```yaml
defaults:
  model_provider: google
  default_model: gemini-pro
```

**OpenAI → Self-hosted (Ollama)**:
```yaml
defaults:
  model_provider: ollama
  default_model: llama2
```

### Enable Cost Tracking

1. Uncomment in `project.yaml`:
   ```yaml
   include:
     - config/cost-tracking.yaml
   ```

2. Edit `.parac/config/cost-tracking.yaml`:
   ```yaml
   cost:
     tracking:
       enabled: true
     budget:
       enabled: true
       monthly_limit: 100.0
   ```

3. Validate:
   ```bash
   paracle config validate
   ```

### Disable Optional Features

**Remove logging config**:
```yaml
include:
  # - config/logging.yaml  # ← Comment out
  - config/cost-tracking.yaml
  - config/file-management.yaml
```

### Set Up Multiple Environments

**Development**:
```bash
cp .parac/project.yaml .parac/project.dev.yaml
# Edit project.dev.yaml
paracle config use development
```

**Production**:
```bash
cp .parac/project.yaml .parac/project.prod.yaml
# Edit project.prod.yaml
paracle config use production
```

---

## Configuration Commands

### Validation

```bash
# Validate all configuration files
paracle config validate

# Validate specific file
paracle config validate project.yaml

# Check YAML syntax only
paracle config validate --syntax-only
```

### Viewing Configuration

```bash
# Show effective configuration (merged from all includes)
paracle config show

# Show specific section
paracle config show defaults
paracle config show logging

# Show as JSON
paracle config show --format json

# Show differences from defaults
paracle config diff
```

### Management

```bash
# Use configuration profile
paracle config use <profile>  # development, production, testing

# List available profiles
paracle config list

# Create new profile
paracle config create <profile>

# Copy current to profile
paracle config save-as <profile>
```

### Interactive Configuration

```bash
# Interactive configuration wizard
paracle config init --interactive

# Update specific settings interactively
paracle config set --interactive
```

---

## Troubleshooting

### "Config file not found"

**Problem**: `.parac/project.yaml` missing

**Solution**:
```bash
# Re-initialize project
paracle init --template lite --force

# Or copy from template
cp templates/.parac-template-lite/project.yaml .parac/
```

### "YAML syntax error"

**Problem**: Invalid YAML in configuration file

**Solution**:
```bash
# Validate and see exact error
paracle config validate

# Common issues:
# - Incorrect indentation (use spaces, not tabs)
# - Missing colons after keys
# - Unquoted special characters
# - Wrong line endings (use LF, not CRLF)
```

### "Include file not found"

**Problem**: Referenced config file doesn't exist

**Solution**:
```yaml
# Option 1: Create missing file
cp templates/.parac-template-advanced/config/*.yaml .parac/config/

# Option 2: Comment out in project.yaml
include:
  # - config/logging.yaml  # ← Comment if not needed
```

### "Invalid model or provider"

**Problem**: Model name or provider not recognized

**Solution**:
```bash
# List supported providers
paracle providers list

# List models for provider
paracle providers list-models openai
paracle providers list-models anthropic

# Check API key is set
echo $OPENAI_API_KEY
```

### Configuration not taking effect

**Problem**: Changes not applied

**Solution**:
```bash
# 1. Validate configuration
paracle config validate

# 2. Check effective config
paracle config show

# 3. Restart any running services
paracle api restart

# 4. Clear cache
paracle cache clear
```

---

## Advanced Topics

### Configuration Loading Order

Paracle loads configuration in this order:

1. **System defaults** (built-in)
2. **`.parac/project.yaml`** (main config)
3. **Included files** (in order specified)
4. **Environment variables** (override all)

**Example**:
```yaml
# project.yaml
defaults:
  model: gpt-4o-mini

include:
  - config/overrides.yaml  # May override defaults.model
```

Environment variable wins:
```bash
export PARACLE_DEFAULT_MODEL=gpt-4
# Uses gpt-4, not gpt-4o-mini
```

### Using Environment Variables

Override any setting via environment variables:

```bash
# Naming: PARACLE_<SECTION>_<KEY>
export PARACLE_DEFAULTS_MODEL_PROVIDER=anthropic
export PARACLE_DEFAULTS_DEFAULT_MODEL=claude-3-opus
export PARACLE_COST_BUDGET_MONTHLY_LIMIT=200.0

# Run paracle (uses env vars)
paracle agent run coder --task "..."
```

### Configuration Validation Schema

Paracle validates configuration against JSON Schema:

```bash
# See full schema
paracle config schema

# Validate against custom schema
paracle config validate --schema custom-schema.json
```

### Configuration Profiles

**Setup profiles** for different environments:

```bash
# Create profiles
paracle config create development
paracle config create staging
paracle config create production

# Switch between profiles
paracle config use development  # ~/.parac/project.dev.yaml
paracle config use production   # ~/.parac/project.prod.yaml

# Current profile
paracle config current
```

**Profile-specific settings**:
```yaml
# project.dev.yaml
defaults:
  model: gpt-4o-mini  # Cheaper for dev

# project.prod.yaml
defaults:
  model: gpt-4  # Best quality for prod
```

### Configuration Templates

**Create reusable templates**:

```bash
# Save current config as template
paracle config save-template my-template

# Use template for new project
paracle init --config-template my-template

# List templates
paracle config list-templates
```

### Merging Configurations

**Merge multiple config files**:

```yaml
# project.yaml
include:
  - config/base.yaml       # Base settings
  - config/team.yaml       # Team-specific
  - config/personal.yaml   # Your overrides
```

**Merge strategy**:
- **Scalars**: Later value wins
- **Lists**: Later list replaces earlier
- **Dicts**: Deep merge (keys combined)

### Configuration Security

**Best practices**:

1. **Never commit secrets** to project.yaml
   ```yaml
   # ❌ BAD
   api_key: sk-1234567890

   # ✅ GOOD
   api_key: ${OPENAI_API_KEY}  # Use env var
   ```

2. **Use `.env` files** for secrets
   ```bash
   # .env (in .gitignore)
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Encrypt sensitive configs**
   ```bash
   # Encrypt production config
   paracle config encrypt project.prod.yaml

   # Decrypt when needed
   paracle config decrypt project.prod.yaml.enc
   ```

---

## Configuration File Reference

### Minimal Structure (17 lines)

```yaml
name: my-project
version: 0.1.0
description: My project

defaults:
  model: gpt-4o-mini
  provider: openai
  temperature: 0.7
  max_tokens: 2000

metadata:
  created_at: "2026-01-06"
```

### Standard Structure (20-30 lines)

```yaml
name: my-project
version: 0.1.0
description: My project
schema_version: "1.0"

identity:
  organization: MyOrg
  repository: my-project
  license: Apache-2.0

defaults:
  model_provider: openai
  default_model: gpt-4
  python_version: "3.10"

metadata:
  created_at: "2026-01-06"
  status: active
  tags: [ai, agents]

include:
  - config/logging.yaml
```

### Advanced Structure (30+ lines)

```yaml
name: my-project
version: 1.0.0
description: Enterprise AI project
schema_version: "1.0"

identity:
  organization: MyEnterprise
  repository: my-ai-app
  license: Proprietary
  homepage: https://example.com

team:
  maintainers:
    - role: lead
      contact: tech@example.com

defaults:
  python_version: "3.11"
  model_provider: openai
  default_model: gpt-4
  orchestrator: internal

metadata:
  created_at: "2026-01-06"
  phase: "Production"
  status: active
  compliance: [SOC2, GDPR, ISO27001]
  tags: [ai, enterprise, agents]

include:
  - config/logging.yaml
  - config/cost-tracking.yaml
  - config/file-management.yaml
```

---

## Migration Guide

### From Old project.yaml (512 lines) → New Split Config

**Step 1: Backup**
```bash
cp .parac/project.yaml .parac/project.yaml.backup
```

**Step 2: Create new minimal project.yaml**
```bash
# Copy minimal template
cp .parac/project-minimal.yaml .parac/project.yaml

# Edit essentials only
nano .parac/project.yaml
```

**Step 3: Split optional configs**
```bash
# Already done! Files exist:
ls .parac/config/
# logging.yaml
# cost-tracking.yaml
# file-management.yaml
```

**Step 4: Enable features selectively**
```yaml
# In project.yaml, uncomment what you need:
include:
  - config/logging.yaml           # ← Uncomment
  # - config/cost-tracking.yaml   # ← Keep commented
  # - config/file-management.yaml # ← Keep commented
```

**Step 5: Validate**
```bash
paracle config validate
paracle config show  # See effective config
```

---

## Next Steps

1. **Start simple**: Use lite template (17 lines)
2. **Add features**: Enable optional configs as needed
3. **Monitor costs**: Add cost-tracking.yaml
4. **Scale up**: Migrate to advanced template for production

**Related Documentation**:
- [Getting Started](getting-started.md)
- [API Keys Setup](api-keys.md)
- [Cost Management](cost-management.md)
- [Log Management](log-management.md)
- [CLI Reference](cli-reference.md)

---

**Questions?** File an issue: https://github.com/IbIFACE-Tech/paracle-lite/issues
