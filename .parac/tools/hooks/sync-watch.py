#!/usr/bin/env python3
"""Watch .parac/agents/specs/ for changes and auto-regenerate manifest.

Usage:
    python .parac/hooks/sync-watch.py
    python .parac/hooks/sync-watch.py --interval=2  # Check every 2 seconds
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. Using polling mode.")
    print("Install with: pip install watchdog")


def find_parac_root() -> Optional[Path]:
    """Find .parac/ directory."""
    current = Path.cwd()
    while current != current.parent:
        parac_dir = current / ".parac"
        if parac_dir.is_dir():
            return parac_dir
        current = current.parent
    return None


def regenerate_manifest() -> bool:
    """Regenerate manifest using paracle CLI."""
    try:
        print("🔄 Regenerating manifest...")
        result = subprocess.run(
            ["paracle", "parac", "sync", "--manifest", "--no-git", "--no-metrics"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ Manifest regenerated")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to regenerate manifest: {e}")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("❌ 'paracle' command not found. Is it installed?")
        return False


class AgentSpecHandler(FileSystemEventHandler):
    """Handle file system events for agent specs."""

    def __init__(self):
        self.last_modified = 0
        self.debounce_seconds = 1

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification."""
        if event.is_directory:
            return

        # Only process .md files
        if not event.src_path.endswith(".md"):
            return

        # Debounce: avoid multiple triggers for same file
        now = time.time()
        if now - self.last_modified < self.debounce_seconds:
            return

        self.last_modified = now
        print(f"📝 Detected change: {Path(event.src_path).name}")
        regenerate_manifest()

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation."""
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"➕ New agent spec: {Path(event.src_path).name}")
            regenerate_manifest()

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion."""
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"➖ Deleted agent spec: {Path(event.src_path).name}")
            regenerate_manifest()


def watch_with_watchdog(specs_dir: Path) -> None:
    """Watch directory using watchdog library."""
    event_handler = AgentSpecHandler()
    observer = Observer()
    observer.schedule(event_handler, str(specs_dir), recursive=False)
    observer.start()

    print(f"👀 Watching {specs_dir} for changes...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n👋 Stopping watcher...")

    observer.join()


def watch_with_polling(specs_dir: Path, interval: float) -> None:
    """Watch directory using simple polling."""
    print(f"👀 Watching {specs_dir} for changes (polling mode)...")
    print(f"Checking every {interval} seconds")
    print("Press Ctrl+C to stop")

    # Track file modification times
    file_mtimes: dict[Path, float] = {}

    def get_md_files() -> set[Path]:
        return set(specs_dir.glob("*.md"))

    # Initialize
    files = get_md_files()
    for f in files:
        file_mtimes[f] = f.stat().st_mtime

    try:
        while True:
            time.sleep(interval)

            current_files = get_md_files()

            # Check for new files
            new_files = current_files - set(file_mtimes.keys())
            if new_files:
                for f in new_files:
                    print(f"➕ New agent spec: {f.name}")
                    file_mtimes[f] = f.stat().st_mtime
                regenerate_manifest()

            # Check for deleted files
            deleted_files = set(file_mtimes.keys()) - current_files
            if deleted_files:
                for f in deleted_files:
                    print(f"➖ Deleted agent spec: {f.name}")
                    del file_mtimes[f]
                regenerate_manifest()

            # Check for modified files
            for f in current_files:
                mtime = f.stat().st_mtime
                if f in file_mtimes and mtime > file_mtimes[f]:
                    print(f"📝 Modified: {f.name}")
                    file_mtimes[f] = mtime
                    regenerate_manifest()
                    break

    except KeyboardInterrupt:
        print("\n👋 Stopping watcher...")


def main():
    parser = argparse.ArgumentParser(
        description="Watch .parac/agents/specs/ and auto-regenerate manifest"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds (default: 2.0)",
    )

    args = parser.parse_args()

    # Find .parac/ directory
    parac_root = find_parac_root()
    if parac_root is None:
        print("❌ Error: .parac/ directory not found")
        print("Run this script from within a PARACLE workspace")
        sys.exit(1)

    specs_dir = parac_root / "agents" / "specs"
    if not specs_dir.exists():
        print(f"❌ Error: {specs_dir} does not exist")
        sys.exit(1)

    # Use watchdog if available, otherwise fall back to polling
    if WATCHDOG_AVAILABLE:
        watch_with_watchdog(specs_dir)
    else:
        watch_with_polling(specs_dir, args.interval)


if __name__ == "__main__":
    main()
