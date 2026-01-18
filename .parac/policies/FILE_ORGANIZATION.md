# File Organization Policy

> **Status**: Active
> **Version**: 1.1
> **Last Updated**: 2026-01-11
> **Enforcement**: Mandatory for `.parac/`, Configurable for project root

---

## Fundamental Principle: Two-Tier Governance

### `.parac/` Structure: **IMMUTABLE** ✅

> **The `.parac/` directory structure is SACRED and IMMUTABLE.**
>
> `.parac/` is the **single source of truth** for project governance, memory, and operational data. Its structure MUST be respected to ensure Paracle framework functions correctly.

**Why `.parac/` Structure Cannot Change**:

1. **Framework Dependency**: Paracle tools (`paracle` CLI, API, agents) rely on this exact structure
2. **Governance Integrity**: Traceability requires consistent file locations
3. **Tool Integration**: IDE sync, MCP tools, validation commands expect this structure
4. **Multi-Project Consistency**: All Paracle projects share this structure

**Result**: `.parac/` file placement rules are **MANDATORY and NON-NEGOTIABLE**.

### Project Root: **CONFIGURABLE** ⚙️

> **Root directory organization is USER-CONFIGURABLE.**
>
> While we provide opinionated defaults (README.md, CHANGELOG.md, etc.), users can customize their root structure based on project needs.

**Default Root Files** (Recommended but not enforced):

- `README.md` - Project overview
- `CHANGELOG.md` - Version history
- `LICENSE` / `LICENSE.md` - License information
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Community guidelines
- `SECURITY.md` - Security policy
- `.gitignore`, `.editorconfig`, `.pre-commit-config.yaml` - Development configs
- `pyproject.toml`, `setup.py`, `setup.cfg` - Python packaging
- `Makefile`, `docker-compose.yml`, `Dockerfile` - Build/deployment
- `package.json`, `tsconfig.json` - If TypeScript/Node.js present

**Users CAN Add** (if needed for their project):

- Additional root-level documentation files
- Project-specific configuration files
- Custom build scripts
- Other standard project files

**⚠️ Strong Recommendation** (but not enforced):

Avoid cluttering root with:

- Technical documentation (better in `docs/` or `content/docs/`)
- Implementation summaries (better in `.parac/memory/summaries/`)
- Test reports (better in `.parac/memory/summaries/`)
- Code examples (better in `examples/` or `content/examples/`)

---

## The Golden Rule

```text
┌─────────────────────────────────────────────────────────┐
│         .parac/ Structure = IMMUTABLE                   │
│         Enforced by Paracle Framework                   │
│         ✅ MUST follow this policy exactly              │
│                                                         │
│         Root Structure = CONFIGURABLE                   │
│         Controlled by User                              │
│         💡 SHOULD follow best practices                 │
└─────────────────────────────────────────────────────────┘
```

**For AI Agents**:

- **MUST**: Always respect `.parac/` file placement rules (non-negotiable)
- **SHOULD**: Follow root organization recommendations (best practice, not enforced)
- **MAY**: Create additional root files if user explicitly requests

---

## File Placement Matrix

| File Type | Correct Location | Examples |
|-----------|------------------|----------|
| **User Documentation** | `content/docs/` | User guides, tutorials, API docs |
| **Technical Documentation** | `content/docs/technical/` | Architecture, design docs |
| **Feature Documentation** | `content/docs/features/` | Feature specifications |
| **Troubleshooting** | `content/docs/troubleshooting/` | Common issues, FAQs |
| **Code Examples** | `content/examples/` | Sample code, demos |
| **Project Templates** | `content/templates/` | Starter templates |
| **Agent Specs** | `.parac/agents/specs/` | Agent definitions |
| **Agent Skills** | `.parac/agents/skills/` | Skill definitions |
| **Workflows** | `.parac/workflows/` | Workflow YAML files |
| **Policies** | `.parac/policies/` | Governance policies |
| **Knowledge Base** | `.parac/memory/knowledge/` | Architecture, patterns, glossary |
| **Summaries** | `.parac/memory/summaries/` | Weekly/phase summaries |
| **Decisions (ADRs)** | `.parac/roadmap/decisions.md` | Architecture decisions |
| **Operational Data** | `.parac/memory/data/` | Databases, metrics |
| **Logs** | `.parac/memory/logs/` | All log files |
| **Execution Artifacts** | `.parac/runs/` | Runtime outputs (gitignored) |

---

## Decision Tree: Where Does This File Belong?

```
START: Need to create a file

1. Is it README.md, CHANGELOG.md, LICENSE, CONTRIBUTING.md,
   CODE_OF_CONDUCT.md, or SECURITY.md?
   ├─ YES → Project root ✅
   └─ NO  → Go to step 2

2. Is it a standard build/packaging file?
   (pyproject.toml, setup.py, Makefile, Dockerfile, etc.)
   ├─ YES → Project root ✅
   └─ NO  → Go to step 3

3. Is it user-facing documentation?
   ├─ YES → content/docs/ (or subdirectory) ✅
   └─ NO  → Go to step 4

4. Is it a code example or demo?
   ├─ YES → content/examples/ ✅
   └─ NO  → Go to step 5

5. Is it a project template?
   ├─ YES → content/templates/ ✅
   └─ NO  → Go to step 6

6. Is it governance, knowledge, or operational data?
   ├─ Agent spec → .parac/agents/specs/ ✅
   ├─ Workflow → .parac/workflows/ ✅
   ├─ Policy → .parac/policies/ ✅
   ├─ Knowledge → .parac/memory/knowledge/ ✅
   ├─ Summary → .parac/memory/summaries/ ✅
   ├─ Decision → .parac/roadmap/decisions.md ✅
   ├─ Database → .parac/memory/data/ ✅
   ├─ Log file → .parac/memory/logs/ ✅
   └─ Runtime → .parac/runs/ ✅

7. Still unsure?
   → Ask in .parac/memory/context/open_questions.md
   → Do NOT place in project root ❌
```

---

## Rules for AI Agents

### Rule 1: Root Files Are Sacred

**Before creating ANY file in project root**:

1. ✅ Check: Is it in the "Allowed Root Files" list?
2. ❌ If NO → Find correct location using Decision Tree
3. ✅ If YES → Proceed

**Example**:

```python
# ❌ WRONG
with open("IMPLEMENTATION_SUMMARY.md", "w") as f:
    f.write("...")

# ✅ CORRECT
summary_path = Path(".parac/memory/summaries/phase10_implementation.md")
summary_path.parent.mkdir(parents=True, exist_ok=True)
with open(summary_path, "w") as f:
    f.write("...")
```

### Rule 2: Documentation Separation

**Two types of documentation**:

1. **User-Facing** (public, for users of Paracle)
   - Location: `content/docs/`
   - Examples: Getting Started, API Reference, Tutorials
   - Audience: Framework users

2. **Project Governance** (internal, for Paracle development)
   - Location: `.parac/memory/knowledge/`
   - Examples: Architecture decisions, implementation patterns
   - Audience: Paracle contributors

**Example**:

```bash
# ✅ User wants to learn about agents
content/docs/users/guides/agents.md

# ✅ Team needs to understand agent implementation
.parac/memory/knowledge/agent_architecture.md
```

### Rule 3: Always Use Helpers

```python
from paracle_core.parac import find_parac_root
from pathlib import Path

def get_doc_path(doc_name: str, category: str = "technical") -> Path:
    """Get path for user documentation.

    Args:
        doc_name: Name of document
        category: Category (users, technical, features, etc.)

    Returns:
        Path in content/docs/{category}/
    """
    return Path("content") / "docs" / category / doc_name

def get_knowledge_path(topic: str) -> Path:
    """Get path for knowledge base document.

    Args:
        topic: Topic name (e.g., "api_design")

    Returns:
        Path in .parac/memory/knowledge/
    """
    parac_dir = find_parac_root()
    return parac_dir / "memory" / "knowledge" / f"{topic}.md"

def get_summary_path(summary_name: str) -> Path:
    """Get path for summary document.

    Args:
        summary_name: Summary identifier (e.g., "phase10_completion")

    Returns:
        Path in .parac/memory/summaries/
    """
    parac_dir = find_parac_root()
    return parac_dir / "memory" / "summaries" / f"{summary_name}.md"

# Usage
doc_path = get_doc_path("agents.md", "users/guides")
knowledge_path = get_knowledge_path("agent_architecture")
summary_path = get_summary_path("week_2026_02")
```

---

## Common Violations & Fixes

### Violation 1: Technical Documentation in Root

```bash
# ❌ WRONG
PROJECT_ROOT/
├── API_DESIGN.md
├── TESTING_REPORT.md
└── FEATURE_IMPLEMENTATION.md

# ✅ CORRECT
content/docs/technical/
├── api-design.md
├── testing-report.md
└── feature-implementation.md

# OR (if internal knowledge)
.parac/memory/knowledge/
├── api_design.md
├── testing_patterns.md
└── implementation_notes.md
```

### Violation 2: Examples in Root

```bash
# ❌ WRONG
PROJECT_ROOT/
├── example_agent.py
└── demo_workflow.py

# ✅ CORRECT
content/examples/
├── agents/
│   └── 01_basic_agent.py
└── workflows/
    └── 01_simple_workflow.py
```

### Violation 3: Summaries/Reports in Root

```bash
# ❌ WRONG
PROJECT_ROOT/
├── PHASE_10_SUMMARY.md
├── TEST_RESULTS.md
└── MIGRATION_REPORT.md

# ✅ CORRECT
.parac/memory/summaries/
├── phase_10_completion.md
├── test_results_2026_01.md
└── migration_v1_to_v2.md
```

### Violation 4: Configuration Files Scattered

```bash
# ❌ WRONG
PROJECT_ROOT/
├── agent_config.yaml
├── my_settings.yaml
└── custom.yaml

# ✅ CORRECT
.parac/project.yaml           # Main config
.parac/config/
├── agents.yaml              # Agent-specific
├── providers.yaml           # Provider config
└── custom_settings.yaml     # Custom configs
```

---

## Agent-Specific Guidelines

### For CoderAgent

When implementing features that create files:

```python
from paracle_core.parac import find_parac_root
from pathlib import Path

class CoderAgent:
    def create_documentation(self, content: str, doc_type: str):
        """Create documentation in correct location."""

        if doc_type == "user_guide":
            # User-facing documentation
            path = Path("content/docs/users/guides") / f"{self.feature_name}.md"

        elif doc_type == "technical":
            # Technical documentation
            path = Path("content/docs/technical") / f"{self.feature_name}.md"

        elif doc_type == "knowledge":
            # Internal knowledge base
            parac_dir = find_parac_root()
            path = parac_dir / "memory" / "knowledge" / f"{self.feature_name}.md"

        else:
            raise ValueError(f"Unknown doc_type: {doc_type}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

        return path
```

### For TesterAgent

```python
class TesterAgent:
    def save_test_report(self, report: str):
        """Save test report in correct location."""

        # ❌ NEVER do this
        # path = Path("TEST_REPORT.md")

        # ✅ ALWAYS do this
        parac_dir = find_parac_root()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = parac_dir / "memory" / "summaries" / f"test_report_{timestamp}.md"

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report)

        return path
```

### For DocumenterAgent

```python
class DocumenterAgent:
    def create_api_documentation(self, api_spec: dict):
        """Create API documentation for users."""

        # User-facing API docs go to content/docs/
        path = Path("content/docs/api") / "reference.md"
        path.parent.mkdir(parents=True, exist_ok=True)

        # Generate markdown from spec
        markdown = self.generate_api_markdown(api_spec)
        path.write_text(markdown)

        return path

    def document_architecture_decision(self, decision: dict):
        """Document an architecture decision (ADR)."""

        # ADRs go to .parac/roadmap/decisions.md
        parac_dir = find_parac_root()
        decisions_path = parac_dir / "roadmap" / "decisions.md"

        # Append to decisions.md
        with open(decisions_path, "a") as f:
            f.write(self.format_adr(decision))

        return decisions_path
```

---

## Enforcement Mechanisms

### 1. Pre-Commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: check-root-files
      name: Check for unauthorized root files
      entry: python .parac/tools/hooks/check_root_files.py
      language: system
      pass_filenames: false
```

Hook script (`.parac/tools/hooks/check_root_files.py`):

```python
#!/usr/bin/env python3
"""Pre-commit hook to prevent unauthorized root files."""

import sys
from pathlib import Path

ALLOWED_ROOT_FILES = {
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "LICENSE.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    ".gitignore",
    ".editorconfig",
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "package.json",
    "tsconfig.json",
}

ALLOWED_ROOT_PATTERNS = {
    ".git*",  # .gitignore, .github, etc.
    ".*",     # Hidden files
}

def check_root_files():
    """Check for unauthorized files in root."""
    root = Path(".")
    violations = []

    for item in root.iterdir():
        if item.is_file() and item.name not in ALLOWED_ROOT_FILES:
            # Check if matches allowed pattern
            if not any(item.match(pattern) for pattern in ALLOWED_ROOT_PATTERNS):
                violations.append(item.name)

    if violations:
        print("❌ POLICY VIOLATION: Unauthorized files in project root")
        print()
        print("The following files should not be in the root directory:")
        for file in violations:
            print(f"  - {file}")
        print()
        print("See .parac/policies/FILE_ORGANIZATION.md for correct locations.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(check_root_files())
```

### 2. CLI Validation

```bash
# Check file organization
paracle validate structure

# Show violations
paracle validate structure --show-violations

# Auto-fix (move files to correct locations)
paracle validate structure --fix

# Dry-run (show what would be moved)
paracle validate structure --fix --dry-run
```

### 3. Agent Self-Check

All agents MUST check file placement before creating files:

```python
from paracle_core.validation import validate_file_path

def create_file(path: Path, content: str):
    """Create file with validation."""

    # Validate path
    is_valid, message = validate_file_path(path)
    if not is_valid:
        raise ValueError(f"Invalid file path: {message}")

    # Create file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
```

---

## Migration Checklist

If you find files in wrong locations:

- [ ] Identify all misplaced files
- [ ] Determine correct location for each
- [ ] Move files to correct locations
- [ ] Update all references in code
- [ ] Update documentation links
- [ ] Commit with message: `refactor: organize files per FILE_ORGANIZATION.md policy`
- [ ] Update `.parac/memory/logs/agent_actions.log`

---

## Examples

### ✅ Correct File Organization

```
paracle-lite/
├── README.md                                    ✅ Standard root file
├── CHANGELOG.md                                 ✅ Standard root file
├── CONTRIBUTING.md                              ✅ Standard root file
├── pyproject.toml                               ✅ Python packaging
├── Makefile                                     ✅ Build automation
│
├── content/
│   ├── docs/                                    ✅ User documentation
│   │   ├── OVERVIEW.md                          ✅ Comprehensive overview
│   │   ├── users/
│   │   │   └── guides/
│   │   │       └── agents.md                    ✅ User guide
│   │   ├── technical/
│   │   │   └── architecture.md                  ✅ Technical docs
│   │   └── troubleshooting/
│   │       └── common-issues.md                 ✅ Troubleshooting
│   │
│   ├── examples/                                ✅ Code examples
│   │   ├── agents/
│   │   │   └── 01_basic_agent.py                ✅ Example code
│   │   └── workflows/
│   │       └── 01_simple_workflow.py            ✅ Example workflow
│   │
│   └── templates/                               ✅ Project templates
│       └── .parac-template/
│
├── .parac/
│   ├── GOVERNANCE.md                            ✅ Governance doc
│   ├── STRUCTURE.md                             ✅ Structure reference
│   ├── project.yaml                             ✅ Project config
│   ├── manifest.yaml                            ✅ Auto-generated state
│   │
│   ├── agents/
│   │   ├── specs/
│   │   │   └── coder.md                         ✅ Agent spec
│   │   └── skills/
│   │       └── paracle-development/             ✅ Skill definition
│   │
│   ├── memory/
│   │   ├── knowledge/
│   │   │   └── agent_architecture.md            ✅ Internal knowledge
│   │   ├── summaries/
│   │   │   └── phase10_completion.md            ✅ Summary
│   │   ├── logs/
│   │   │   └── agent_actions.log                ✅ Activity log
│   │   └── data/
│   │       └── costs.db                         ✅ Operational data
│   │
│   ├── roadmap/
│   │   ├── roadmap.yaml                         ✅ Master roadmap
│   │   └── decisions.md                         ✅ ADRs
│   │
│   └── policies/
│       ├── FILE_ORGANIZATION.md                 ✅ This policy
│       ├── CODE_STYLE.md                        ✅ Code style
│       └── TESTING.md                           ✅ Testing policy
│
└── packages/                                    ✅ Source code
    └── paracle_*/
```

---

## Frequently Asked Questions

### Q: Where should I put a new feature guide?

**A**: `content/docs/features/{feature-name}.md`

### Q: Where should I put implementation notes for a feature?

**A**: `.parac/memory/knowledge/{feature}_implementation.md`

### Q: Where should I put test results?

**A**: `.parac/memory/summaries/test_results_{timestamp}.md`

### Q: Where should I put a weekly progress summary?

**A**: `.parac/memory/summaries/week_{year}_{week}.md`

### Q: Where should I put API documentation?

**A**: `content/docs/api/` (user-facing) or `content/docs/technical/` (technical deep-dive)

### Q: Where should I put agent execution logs?

**A**: `.parac/memory/logs/agent_actions.log` (activity log) or `.parac/runs/` (execution artifacts)

### Q: Can I create a folder in the root for my feature?

**A**: ❌ **NO**. Use `content/` for user-facing content or `.parac/` for governance/operational data.

---

## Consequences of Violations

**Violations of this policy will result in**:

1. ⚠️ **Pre-commit hook failure** (if enabled)
2. ⚠️ **CI build failure** (validation in CI pipeline)
3. ⚠️ **Code review rejection** (reviewers will request changes)
4. ⚠️ **Automated cleanup** (files may be moved automatically)

**The policy is automatically enforced**:
- ✅ Pre-commit hooks
- ✅ CI/CD validation
- ✅ Code review checklist
- ✅ CLI validation commands

---

## See Also

- [.parac/STRUCTURE.md](.parac/STRUCTURE.md) - Complete .parac/ structure reference
- [.parac/GOVERNANCE.md](.parac/GOVERNANCE.md) - Governance protocol
- [.parac/policies/CODE_STYLE.md](.parac/policies/CODE_STYLE.md) - Code style policy
- [content/docs/README.md](../content/docs/README.md) - Documentation index

---

**Version**: 1.0
**Status**: Active
**Enforcement**: Mandatory
**Last Updated**: 2026-01-11
