"""State change logging for audit trail.

Provides append-only logging of state changes for debugging and audit purposes.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def log_state_change(
    parac_root: Path,
    change_type: str,
    description: str,
    old_value: Any = None,
    new_value: Any = None,
    revision: int | None = None,
) -> None:
    """Log a state change to the audit trail.

    Creates an append-only log entry in .parac/memory/logs/state_changes.jsonl

    Args:
        parac_root: Path to .parac/ directory.
        change_type: Type of change (e.g., 'progress', 'phase', 'blocker').
        description: Human-readable description of the change.
        old_value: Previous value (optional).
        new_value: New value (optional).
        revision: State revision number after change (optional).
    """
    log_file = parac_root / "memory" / "logs" / "state_changes.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "process_id": os.getpid(),
        "change_type": change_type,
        "description": description,
    }

    if old_value is not None:
        entry["old_value"] = old_value
    if new_value is not None:
        entry["new_value"] = new_value
    if revision is not None:
        entry["revision"] = revision

    # Append to log file
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        # Fail silently - logging should not break operations
        pass


def get_recent_changes(parac_root: Path, limit: int = 100) -> list[dict[str, Any]]:
    """Get recent state changes from audit log.

    Args:
        parac_root: Path to .parac/ directory.
        limit: Maximum number of entries to return.

    Returns:
        List of change entries, most recent first.
    """
    log_file = parac_root / "memory" / "logs" / "state_changes.jsonl"

    if not log_file.exists():
        return []

    changes = []
    try:
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        changes.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except OSError:
        return []

    # Return most recent first
    return list(reversed(changes[-limit:]))


def clear_old_changes(parac_root: Path, keep_days: int = 30) -> int:
    """Remove log entries older than specified days.

    Args:
        parac_root: Path to .parac/ directory.
        keep_days: Number of days to keep.

    Returns:
        Number of entries removed.
    """
    log_file = parac_root / "memory" / "logs" / "state_changes.jsonl"

    if not log_file.exists():
        return 0

    cutoff = datetime.now().timestamp() - (keep_days * 86400)
    kept_entries = []
    removed_count = 0

    try:
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(entry["timestamp"]).timestamp()

                    if timestamp >= cutoff:
                        kept_entries.append(line)
                    else:
                        removed_count += 1
                except (json.JSONDecodeError, KeyError, ValueError):
                    # Keep entries we can't parse
                    kept_entries.append(line)

        # Rewrite file with kept entries
        if removed_count > 0:
            with open(log_file, "w", encoding="utf-8") as f:
                for entry in kept_entries:
                    f.write(entry + "\n")

        return removed_count
    except OSError:
        return 0
