# Paracle Logging - Visual Guide

> Quick visual reference for understanding Paracle's dual logging system.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      PARACLE LOGGING                            │
│                                                                 │
│  ┌─────────────────────────┐   ┌─────────────────────────────┐ │
│  │   USER LOGS             │   │   FRAMEWORK LOGS            │ │
│  │   (.parac/)             │   │   (System Paths)            │ │
│  │                         │   │                             │ │
│  │  📊 Project-specific    │   │  🔧 Framework-wide          │ │
│  │  ✅ Your project only   │   │  ✅ All projects            │ │
│  │  ✅ Text format         │   │  ✅ JSON format             │ │
│  │  ✅ 10k lines max       │   │  ✅ 10 MB max               │ │
│  │  ✅ CLI managed         │   │  ✅ Auto-managed            │ │
│  └─────────────────────────┘   └─────────────────────────────┘ │
│                                                                 │
│  🎯 USE: paracle logs ...       🎯 USE: get_logger()           │
└─────────────────────────────────────────────────────────────────┘
```

## File Locations

```
YOUR PROJECT                    SYSTEM INSTALLATION
==============                  ===================

project-folder/                 Windows:
└── .parac/                     C:\Users\<user>\AppData\Local\Paracle\logs\
    └── memory/                 
        └── logs/               Linux:
            ├── agent_actions.log      ~/.local/share/paracle/logs/
            ├── decisions.log          
            ├── archives/              macOS:
            │   └── *.log              ~/Library/Logs/Paracle/
            └── runtime/               
                                Docker:
                                /var/log/paracle/
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR CODE                               │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ Calls
                         ▼
            ┌────────────────────────┐
            │  Which logging API?    │
            └────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ USER LOGGING     │            │ FRAMEWORK LOGGING │
│                  │            │                   │
│ from parac.logger│            │ from logging      │
│ import log_action│            │ import get_logger │
│                  │            │                   │
│ log_action(...)  │            │ logger = get...   │
│                  │            │ logger.info(...)  │
└──────────────────┘            └──────────────────┘
        │                                 │
        ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ .parac/memory/   │            │ System logs/     │
│ logs/            │            │ paracle.log      │
│ agent_actions.log│            │ (JSON)           │
│ (Text)           │            │                  │
└──────────────────┘            └──────────────────┘
```

## When to Use What

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION TREE                                │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  What am I logging?  │
              └──────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ PROJECT ACTIVITY │            │ FRAMEWORK ISSUES │
│                  │            │                   │
│ • Agent actions  │            │ • Internal errors │
│ • Decisions      │            │ • Performance     │
│ • Progress       │            │ • Debug info      │
│ • Governance     │            │ • Security events │
│ • Audit trail    │            │ • ISO compliance  │
└──────────────────┘            └──────────────────┘
        │                                 │
        ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ USE USER LOGS    │            │ USE FRAMEWORK    │
│ ✅ log_action()   │            │ ✅ get_logger()   │
│ ✅ paracle logs   │            │ ✅ LogConfig      │
└──────────────────┘            └──────────────────┘
```

## Example Scenarios

### Scenario 1: Agent Implementation

```python
# ✅ USER LOG (Project activity)
from paracle_core.parac.logger import log_action

log_action(
    action="IMPLEMENTATION",
    description="Added user authentication",
    agent="CoderAgent"
)
# → .parac/memory/logs/agent_actions.log
```

### Scenario 2: Framework Error

```python
# ✅ FRAMEWORK LOG (Internal error)
from paracle_core.logging import get_logger

logger = get_logger(__name__)
logger.error("Failed to connect to provider", exc_info=True)
# → /var/log/paracle/paracle.log (JSON)
```

### Scenario 3: Both Together

```python
from paracle_core.logging import get_logger, correlation_id
from paracle_core.parac.logger import log_action

logger = get_logger(__name__)

with correlation_id() as cid:
    # Framework: debug internal execution
    logger.info("Starting task execution")
    
    try:
        result = execute_task()
        
        # User: log project progress
        log_action(
            action="IMPLEMENTATION",
            description="Task completed successfully",
            details={"correlation_id": cid}
        )
    except Exception as e:
        # Framework: log error details
        logger.error("Task failed", exc_info=True)
        
        # User: log project incident
        log_action(
            action="BUGFIX",
            description=f"Task failed: {e}",
            details={"correlation_id": cid}
        )
```

## Log Formats Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER LOG FORMAT                              │
│                    (Text Simple)                                │
└─────────────────────────────────────────────────────────────────┘

[2026-01-10 15:30:00] [CoderAgent] [IMPLEMENTATION] Added auth

┌─────────────────────────────────────────────────────────────────┐
│                    FRAMEWORK LOG FORMAT                         │
│                    (JSON Structuré)                             │
└─────────────────────────────────────────────────────────────────┘

{
  "timestamp": "2026-01-10T15:30:00Z",
  "level": "INFO",
  "logger": "paracle.orchestration",
  "message": "Agent execution started",
  "correlation_id": "01HN8X3...",
  "context": {
    "agent_id": "coder",
    "task": "Add authentication"
  }
}
```

## CLI Commands (User Logs Only)

```
┌─────────────────────────────────────────────────────────────────┐
│                 paracle logs COMMANDS                           │
│                 (User Logs Only)                                │
└─────────────────────────────────────────────────────────────────┘

paracle logs analyze      # Check log health
paracle logs show         # View content
paracle logs rotate       # Manual rotation
paracle logs cleanup      # Remove old archives
paracle logs list         # List all logs
paracle logs export       # Export to file

⚠️  NO CLI for framework logs (use system tools)
```

## Configuration Files

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER LOGS CONFIG                             │
└─────────────────────────────────────────────────────────────────┘

File: .parac/project.yaml

file_management:
  logs:
    global:
      max_file_size_mb: 1
      compress_rotated: true
    predefined:
      actions:
        enabled: true
        rotation: "size"

┌─────────────────────────────────────────────────────────────────┐
│                    FRAMEWORK LOGS CONFIG                        │
└─────────────────────────────────────────────────────────────────┘

File: ~/.paracle/config.yaml
OR Environment variables:

export PARACLE_LOG_LEVEL=INFO
export PARACLE_LOG_JSON=true
export PARACLE_LOG_FILE=/var/log/paracle/paracle.log
```

## Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════╗
║                    QUICK REFERENCE                            ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  NEED                  USE                        OUTPUT      ║
║  ────────────────────  ──────────────────────  ─────────────  ║
║  Track project work    log_action()           .parac/logs/   ║
║  Debug framework       get_logger()           /var/log/      ║
║  Check log health      paracle logs analyze   (terminal)     ║
║  View logs             paracle logs show      (terminal)     ║
║  Rotate logs           paracle logs rotate    (archives)     ║
║                                                               ║
║  REMEMBER:                                                    ║
║  • User logs = Your project                                  ║
║  • Framework logs = Paracle itself                           ║
║  • Use 'paracle logs' for user logs                          ║
║  • Use system tools for framework logs                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

## Common Mistakes

```
❌ WRONG                          ✅ RIGHT
─────────────────────             ─────────────────────
Using get_logger() for            Use log_action() for
project tracking                  project tracking

Using log_action() for            Use get_logger() for
framework errors                  framework errors

Looking for user logs in          User logs are in
/var/log/paracle/                 .parac/memory/logs/

Using 'paracle logs' for          No CLI for framework logs
framework logs                    (use cat, jq, etc.)

Configuring user logs in          Configure in
~/.paracle/config.yaml            .parac/project.yaml
```

---

**🎯 Remember**: 
- `.parac/` = Your project logs (CLI managed)
- System paths = Framework logs (auto-managed)
- Use the right tool for the right job!
