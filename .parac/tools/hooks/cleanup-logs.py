#!/usr/bin/env python3
"""
Cleanup Old Log Archives

Removes log archives older than MAX_ARCHIVE_AGE_DAYS.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
MAX_ARCHIVE_AGE_DAYS = 365  # Keep archives for 1 year


def cleanup_old_archives():
    """Remove archives older than MAX_ARCHIVE_AGE_DAYS"""
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

    archive_dir = parac_dir / "memory" / "logs" / "archives"

    if not archive_dir.exists():
        print("✓ No archive directory found")
        return

    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=MAX_ARCHIVE_AGE_DAYS)

    # Find and delete old archives
    deleted_count = 0
    total_size = 0

    for archive in archive_dir.glob("*.log"):
        # Get file modification time
        mtime = datetime.fromtimestamp(archive.stat().st_mtime)

        if mtime < cutoff_date:
            size = archive.stat().st_size
            total_size += size
            archive.unlink()
            deleted_count += 1
            print(
                f"✓ Deleted: {archive.name} (age: {(datetime.now() - mtime).days} days)")

    # Print summary
    if deleted_count > 0:
        size_mb = total_size / (1024 * 1024)
        print()
        print("✓ Cleanup complete")
        print(f"  Deleted: {deleted_count} archive(s)")
        print(f"  Space freed: {size_mb:.2f} MB")
    else:
        print(f"✓ No archives older than {MAX_ARCHIVE_AGE_DAYS} days")

    # Show remaining archives
    remaining = list(archive_dir.glob("*.log"))
    if remaining:
        print(f"  Remaining: {len(remaining)} archive(s)")


if __name__ == "__main__":
    cleanup_old_archives()
