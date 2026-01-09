#!/usr/bin/env python3
"""
Automatic .parac Maintenance Tool

Synchronizes .parac/ workspace state with actual project changes.
Run this tool:
- Manually: python .parac/tools/auto-maintain.py
- Via Git hook: .git/hooks/pre-commit (see setup instructions below)
- Via GitHub Actions: .github/workflows/maintain-parac.yml

Usage:
    python .parac/tools/auto-maintain.py [--dry-run] [--verbose]

Options:
    --dry-run    Show what would be updated without making changes
    --verbose    Show detailed output
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


class ParacMaintainer:
    """Maintains .parac/ workspace state automatically."""

    def __init__(self, repo_root: Path, dry_run: bool = False, verbose: bool = False):
        self.repo_root = repo_root
        self.parac_dir = repo_root / ".parac"
        self.dry_run = dry_run
        self.verbose = verbose
        self.changes: list[str] = []

    def log(self, message: str, level: str = "info") -> None:
        """Log message if verbose mode enabled."""
        if self.verbose or level == "change":
            prefix = "🔄" if level == "change" else "ℹ️"
            print(f"{prefix} {message}")

    def get_git_changes(self) -> dict[str, set[str]]:
        """Get changed files from git (staged + unstaged)."""
        try:
            # Get staged files
            staged = subprocess.check_output(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.repo_root,
                text=True,
            ).splitlines()

            # Get unstaged files
            unstaged = subprocess.check_output(
                ["git", "diff", "--name-only"], cwd=self.repo_root, text=True
            ).splitlines()

            # Get untracked files
            untracked = subprocess.check_output(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=self.repo_root,
                text=True,
            ).splitlines()

            all_changes = set(staged + unstaged + untracked)

            return {
                "templates": {f for f in all_changes if f.startswith("templates/")},
                "packages": {f for f in all_changes if f.startswith("packages/")},
                "docs": {f for f in all_changes if f.startswith("docs/")},
                "examples": {f for f in all_changes if f.startswith("examples/")},
                "tests": {f for f in all_changes if f.startswith("tests/")},
                "roadmap": {f for f in all_changes if ".roadmap/" in f},
                "all": all_changes,
            }
        except subprocess.CalledProcessError:
            self.log("Not a git repository or git not available", "warning")
            return {}

    def update_current_state(self, changes: dict[str, set[str]]) -> None:
        """Update .parac/memory/context/current_state.yaml based on changes."""
        state_file = self.parac_dir / "memory" / "context" / "current_state.yaml"

        if not state_file.exists():
            self.log(f"State file not found: {state_file}", "warning")
            return

        with open(state_file, encoding="utf-8") as f:
            state = yaml.safe_load(f)

        # Update snapshot date
        state["snapshot_date"] = datetime.now().strftime("%Y-%m-%d")

        # Detect new deliverables
        new_deliverables = []

        if changes.get("templates"):
            template_count = len(changes["templates"])
            self.log(f"Detected {template_count} template changes", "change")
            new_deliverables.append(
                {
                    "area": "templates",
                    "count": template_count,
                    "files": list(changes["templates"])[:5],  # Sample
                }
            )

        if changes.get("packages"):
            package_count = len(changes["packages"])
            self.log(f"Detected {package_count} package changes", "change")
            new_deliverables.append(
                {
                    "area": "packages",
                    "count": package_count,
                    "files": list(changes["packages"])[:5],
                }
            )

        # Add to state metadata
        if new_deliverables and "recent_changes" not in state:
            state["recent_changes"] = new_deliverables

        if not self.dry_run:
            with open(state_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(state, f, allow_unicode=True, sort_keys=False)
            self.changes.append(f"Updated {state_file.relative_to(self.repo_root)}")
        else:
            self.log(f"Would update {state_file.relative_to(self.repo_root)}", "change")

    def update_changelog(self, changes: dict[str, set[str]]) -> None:
        """Update .parac/changelog.md with recent changes."""
        changelog_file = self.parac_dir / "changelog.md"

        if not changelog_file.exists():
            self.log(f"Changelog not found: {changelog_file}", "warning")
            return

        with open(changelog_file, encoding="utf-8") as f:
            content = f.read()

        today = datetime.now().strftime("%Y-%m-%d")

        # Check if we already have an entry for today
        if today in content:
            self.log(f"Changelog already updated today ({today})", "info")
            return

        # Prepare changelog entry based on changes
        entry_lines = []

        if changes.get("packages"):
            entry_lines.append("- Package updates")
        if changes.get("templates"):
            entry_lines.append("- Template updates")
        if changes.get("docs"):
            entry_lines.append("- Documentation updates")
        if changes.get("examples"):
            entry_lines.append("- Example updates")

        if not entry_lines:
            return

        # Insert after "## [Unreleased]" section
        unreleased_marker = "## [Unreleased]"
        if unreleased_marker in content:
            parts = content.split(unreleased_marker, 1)
            new_entry = f"\n\n### Changed ({today})\n\n" + "\n".join(entry_lines) + "\n"

            # Find where to insert (after ### Added section if it exists)
            after_unreleased = parts[1]
            if "### Added" in after_unreleased:
                # Insert after ### Added section
                added_parts = after_unreleased.split("\n\n", 1)
                new_content = (
                    parts[0]
                    + unreleased_marker
                    + added_parts[0]
                    + new_entry
                    + (added_parts[1] if len(added_parts) > 1 else "")
                )
            else:
                new_content = (
                    parts[0] + unreleased_marker + new_entry + after_unreleased
                )

            if not self.dry_run:
                with open(changelog_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.changes.append(
                    f"Updated {changelog_file.relative_to(self.repo_root)}"
                )
            else:
                self.log(f"Would add changelog entry for {today}", "change")

    def check_roadmap_alignment(self) -> None:
        """Check if roadmap needs updates based on completed work."""
        roadmap_file = self.parac_dir / "roadmap" / "roadmap.yaml"

        if not roadmap_file.exists():
            return

        with open(roadmap_file, encoding="utf-8") as f:
            roadmap = yaml.safe_load(f)

        current_phase = roadmap.get("current_phase", "phase_0")
        self.log(f"Current phase: {current_phase}", "info")

        # Could add logic here to suggest phase transitions
        # based on deliverable completion

    def run(self) -> bool:
        """Run the maintenance process."""
        self.log("Starting .parac maintenance...", "info")

        # Get git changes
        changes = self.get_git_changes()

        if not changes.get("all"):
            self.log("No changes detected", "info")
            return True

        self.log(f"Detected {len(changes['all'])} changed files", "info")

        # Update state
        self.update_current_state(changes)

        # Update changelog
        self.update_changelog(changes)

        # Check roadmap
        self.check_roadmap_alignment()

        # Summary
        if self.changes:
            print("\n✅ Changes applied:")
            for change in self.changes:
                print(f"   - {change}")
        elif self.dry_run:
            print("\n✅ Dry run completed (no changes made)")
        else:
            print("\n✅ No .parac updates needed")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Automatically maintain .parac/ workspace state"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    # Find repository root
    try:
        repo_root = Path(
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            ).strip()
        )
    except subprocess.CalledProcessError:
        print("❌ Error: Not in a git repository", file=sys.stderr)
        return 1

    # Run maintainer
    maintainer = ParacMaintainer(repo_root, dry_run=args.dry_run, verbose=args.verbose)

    try:
        success = maintainer.run()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
