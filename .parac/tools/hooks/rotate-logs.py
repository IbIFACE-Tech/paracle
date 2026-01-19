#!/usr/bin/env python3
"""
Rotate Agent Actions Log

Manually rotate the agent actions log file, archiving old entries.
"""

import sys
from datetime import datetime
from pathlib import Path


def rotate_log():
    """Rotate agent_actions.log manually"""
    # Find .parac directory
    current = Path.cwd()
    while current != current.parent:
        if (current / ".parac").exists():
            parac_dir = current / ".parac"
            break
        current = current.parent
    else:
        print("❌ Cannot find .parac directory")
        sys.exit(1)

    logs_dir = parac_dir / "memory" / "logs"
    actions_log = logs_dir / "agent_actions.log"
    archive_dir = logs_dir / "archives"

    # Create archive directory
    archive_dir.mkdir(parents=True, exist_ok=True)

    if not actions_log.exists():
        print("❌ No log file found")
        sys.exit(1)

    # Read all lines
    with open(actions_log, encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) == 0:
        print("✓ Log file is empty, nothing to rotate")
        return

    # Create archive filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_path = archive_dir / f"agent_actions.{timestamp}.log"

    # Archive all current lines
    with open(archive_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # Keep last 1000 lines for continuity
    KEEP_RECENT_LINES = 1_000
    recent_lines = lines[-KEEP_RECENT_LINES:] if len(
        lines) > KEEP_RECENT_LINES else lines

    with open(actions_log, "w", encoding="utf-8") as f:
        f.writelines(recent_lines)

    # Print summary
    print("✓ Log rotated successfully")
    print(f"  Original lines: {len(lines):,}")
    print(f"  Kept recent: {len(recent_lines):,}")
    print(f"  Archived: {len(lines):,} lines")
    print(f"  Archive file: {archive_path.name}")
    print(f"  Location: {archive_path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    rotate_log()
