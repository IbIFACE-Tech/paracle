#!/usr/bin/env python3
"""
Analyze Agent Actions Log

Provides statistics and recommendations for log rotation.
"""

import sys
from datetime import datetime
from pathlib import Path


def analyze_log_size(log_path: Path | None = None):
    """Analyze current log size and recommend rotation"""
    if log_path is None:
        # Find .parac directory
        current = Path.cwd()
        while current != current.parent:
            if (current / ".parac").exists():
                log_path = current / ".parac" / "memory" / "logs" / "agent_actions.log"
                break
            current = current.parent
        else:
            print("❌ Cannot find .parac directory")
            sys.exit(1)

    if not log_path.exists():
        print("❌ No log file found")
        sys.exit(1)

    # Read log file
    with open(log_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Calculate sizes
    size_bytes = log_path.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024

    # Calculate growth rate (if possible)
    first_date = None
    last_date = None
    if len(lines) > 0:
        # Parse first and last timestamps
        try:
            first_line = lines[0]
            last_line = lines[-1]
            # Format: [YYYY-MM-DD HH:MM:SS]
            first_date_str = first_line[1:20]  # [YYYY-MM-DD HH:MM:SS]
            last_date_str = last_line[1:20]
            first_date = datetime.strptime(first_date_str, "%Y-%m-%d %H:%M:%S")
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, IndexError):
            pass

    # Print statistics
    print("📊 Agent Actions Log Statistics")
    print("=" * 50)
    print(f"📄 File: {log_path.relative_to(Path.cwd())}")
    print(f"📏 Lines: {len(lines):,}")
    print(f"💾 Size: {size_mb:.2f} MB ({size_kb:.2f} KB)")

    if first_date and last_date:
        days_span = (last_date - first_date).days
        if days_span > 0:
            lines_per_day = len(lines) / days_span
            print(f"📅 Date range: {first_date.date()} → {last_date.date()}")
            print(f"⏱️  Duration: {days_span} days")
            print(f"📈 Growth rate: ~{lines_per_day:.1f} lines/day")

    print()

    # Recommendations
    MAX_LINES = 10_000
    MAX_SIZE_MB = 1.0

    warnings = []
    if len(lines) > MAX_LINES:
        warnings.append(f"⚠️  CRITICAL: Log exceeds {MAX_LINES:,} lines")
        warnings.append(
            f"   Current: {len(lines):,} lines ({len(lines) - MAX_LINES:,} over limit)")
        warnings.append("   → Rotation REQUIRED")
    elif len(lines) > MAX_LINES * 0.8:
        warnings.append(f"⚠️  WARNING: Log approaching {MAX_LINES:,} lines")
        warnings.append(
            f"   Current: {len(lines):,} lines ({int((len(lines) / MAX_LINES) * 100)}% of limit)")
        warnings.append("   → Consider rotation soon")

    if size_mb > MAX_SIZE_MB:
        warnings.append(f"⚠️  CRITICAL: File size exceeds {MAX_SIZE_MB} MB")
        warnings.append(f"   Current: {size_mb:.2f} MB")
        warnings.append("   → Rotation REQUIRED")
    elif size_mb > MAX_SIZE_MB * 0.8:
        warnings.append(f"⚠️  WARNING: File size approaching {MAX_SIZE_MB} MB")
        warnings.append(
            f"   Current: {size_mb:.2f} MB ({int((size_mb / MAX_SIZE_MB) * 100)}% of limit)")
        warnings.append("   → Consider rotation soon")

    if warnings:
        print("🚨 Recommendations:")
        print("-" * 50)
        for warning in warnings:
            print(warning)
        print()
        print("💡 To rotate logs:")
        print("   python .parac/tools/hooks/rotate-logs.py")
    else:
        print("✅ Log size is within acceptable limits")
        print(
            f"   Lines: {len(lines):,} / {MAX_LINES:,} ({int((len(lines) / MAX_LINES) * 100)}%)")
        print(
            f"   Size: {size_mb:.2f} / {MAX_SIZE_MB} MB ({int((size_mb / MAX_SIZE_MB) * 100)}%)")

    print()

    # Archive statistics
    archive_dir = log_path.parent / "archives"
    if archive_dir.exists():
        archives = list(archive_dir.glob("*.log"))
        if archives:
            total_archive_size = sum(a.stat().st_size for a in archives)
            archive_mb = total_archive_size / (1024 * 1024)
            print(
                f"📦 Archives: {len(archives)} files ({archive_mb:.2f} MB total)")
        else:
            print("📦 Archives: None")
    else:
        print("📦 Archives: Directory not created yet")

    return len(lines), size_mb


if __name__ == "__main__":
    analyze_log_size()
