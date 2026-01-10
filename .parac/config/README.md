# Configuration Directory

This directory contains **optional** configuration files for advanced Paracle features.

## Files

| File                   | Purpose                                   | When to Use                               |
| ---------------------- | ----------------------------------------- | ----------------------------------------- |
| `logging.yaml`         | Enterprise logging, rotation, retention   | Need custom log levels or log aggregation |
| `cost-tracking.yaml`   | LLM cost monitoring and budgets           | Want to track spending and set limits     |
| `file-management.yaml` | Log limits, ADR templates, roadmap config | Need fine-grained control over files      |

## How It Works

### Simple Setup (Default)

If you don't include these files, Paracle uses sensible defaults:
- Basic logging to console and files
- No cost tracking
- Standard file management

**Your `project.yaml`**:
```yaml
name: my-project
version: 0.1.0

defaults:
  model_provider: openai
  default_model: gpt-4o-mini

# No includes = use defaults
```

### Advanced Setup (Opt-in)

Enable features by adding `include:` section to your `project.yaml`:

```yaml
name: my-project
version: 0.1.0

defaults:
  model_provider: openai
  default_model: gpt-4

# Load optional configs
include:
  - config/logging.yaml           # <- Enable advanced logging
  - config/cost-tracking.yaml     # <- Enable cost tracking
  - config/file-management.yaml   # <- Enable file management
```

## Editing Configuration Files

### 1. Logging Configuration (`logging.yaml`)

**Common Changes**:
```yaml
logging:
  level: DEBUG  # Change log level (DEBUG, INFO, WARNING, ERROR)
  format: plain # Change from JSON to plain text

  rotation:
    strategy: weekly  # Change from daily to weekly
    backup_count: 60  # Keep more backups
```

### 2. Cost Tracking (`cost-tracking.yaml`)

**Enable Tracking**:
```yaml
cost:
  tracking:
    enabled: true  # <- Set to true

  budget:
    enabled: true       # <- Enable budgets
    monthly_limit: 50.0 # <- Set your limit (USD)
    warning_threshold: 0.8  # Alert at 80%
```

**Update Pricing** (if you have custom rates):
```yaml
cost:
  default_pricing:
    openai:
      gpt-4:
        input: 25.0   # Your negotiated rate
        output: 50.0
```

### 3. File Management (`file-management.yaml`)

**Adjust Log Limits**:
```yaml
file_management:
  logs:
    global:
      max_line_length: 2000  # Increase if needed
      max_file_size_mb: 100  # Increase file size limit
```

**Enable ADRs**:
```yaml
file_management:
  adr:
    enabled: true
    format: markdown
```

## Enable/Disable Features

### Enable a Feature

**1. Add to project.yaml**:
```yaml
include:
  - config/logging.yaml  # <- Add this line
```

**2. Validate**:
```bash
paracle config validate
```

**3. Verify**:
```bash
paracle config show
```

### Disable a Feature

**1. Comment out in project.yaml**:
```yaml
include:
  # - config/logging.yaml  # <- Comment out
```

**2. Restart services** (if running):
```bash
paracle api restart
```

## Best Practices

### Start Minimal
- Don't include any config files initially
- Use defaults (they work for 90% of users)
- Add features only when you need them

### Enable Progressively
1. **First**: Just use `project.yaml` (essentials only)
2. **When debugging**: Add `config/logging.yaml`
3. **When scaling**: Add `config/cost-tracking.yaml`
4. **When customizing**: Add `config/file-management.yaml`

### Keep It Simple
- Each config file is independent
- Enable/disable without affecting others
- Comment out unused sections

## Troubleshooting

### "Config file not found"

**Error**: `config/logging.yaml not found`

**Solution**: File is included but doesn't exist
```bash
# Option 1: Create from template
cp content/templates/.parac-template-advanced/config/logging.yaml .parac/config/

# Option 2: Comment out in project.yaml
# include:
#   - config/logging.yaml  # <- Commented out
```

### "Configuration not taking effect"

**Problem**: Changes not applied

**Solution**:
```bash
# 1. Validate syntax
paracle config validate

# 2. Check effective config
paracle config show

# 3. Restart services
paracle api restart
```

### "Too many configuration options"

**Problem**: Overwhelmed by options

**Solution**: Start with minimal config
```yaml
# project.yaml - ONLY essentials
name: my-project
version: 0.1.0
defaults:
  model: gpt-4o-mini
  provider: openai

# No includes = use defaults
```

## Documentation

- **Complete Guide**: [content/docs/configuration-guide.md](../../content/docs/configuration-guide.md)
- **Logging**: [content/docs/log-management.md](../../content/docs/log-management.md)
- **Cost Tracking**: [content/docs/cost-management.md](../../content/docs/cost-management.md)
- **CLI Reference**: [content/docs/cli-reference.md](../../content/docs/cli-reference.md)

## Examples

### Example 1: Minimal (Beginner)
```yaml
# project.yaml only - no config files
name: my-first-project
version: 0.1.0
defaults:
  model: gpt-4o-mini
  provider: openai
```

### Example 2: Standard (Most Users)
```yaml
# project.yaml with logging
name: my-production-app
version: 1.0.0
defaults:
  model: gpt-4
  provider: openai

include:
  - config/logging.yaml  # Only logging
```

### Example 3: Advanced (Enterprise)
```yaml
# project.yaml with all features
name: enterprise-ai-platform
version: 2.0.0
defaults:
  model: gpt-4
  provider: openai

include:
  - config/logging.yaml
  - config/cost-tracking.yaml
  - config/file-management.yaml
```

---

**Remember**: You can always start simple and add configuration files later as your needs grow!
