#!/usr/bin/env python3
"""
Changelog generation script for Paracle project.

Generates changelog entries from conventional commit messages.

Usage:
    python scripts/generate_changelog.py [from_tag] [to_tag]
    python scripts/generate_changelog.py v0.0.1 HEAD
    python scripts/generate_changelog.py --version 0.1.0
"""

import argparse
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def run_git_command(cmd: list[str]) -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ['git'] + cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")
        raise


def get_commits(from_ref: str, to_ref: str) -> list[str]:
    """Get commit messages between two refs."""
    cmd = ['log', f'{from_ref}..{to_ref}', '--pretty=format:%s']
    output = run_git_command(cmd)
    return [line for line in output.split('\n') if line.strip()]


def parse_commit(commit_msg: str) -> tuple[str, str, str, bool]:
    """
    Parse conventional commit message.

    Returns: (type, scope, subject, is_breaking)
    """
    # Match: type(scope)!: subject or type!: subject
    match = re.match(
        r'^(\w+)(?:\(([^)]+)\))?(!?):\s*(.+)$',
        commit_msg
    )

    if not match:
        return ('other', '', commit_msg, False)

    type_, scope, breaking_marker, subject = match.groups()
    scope = scope or ''
    is_breaking = breaking_marker == '!' or 'BREAKING CHANGE' in commit_msg

    return (type_, scope, subject, is_breaking)


def group_commits(commits: list[str]) -> dict[str, list[tuple[str, str]]]:
    """
    Group commits by type.

    Returns: Dict[type, List[(scope, subject)]]
    """
    groups = defaultdict(list)
    breaking_changes = []

    for commit in commits:
        type_, scope, subject, is_breaking = parse_commit(commit)

        if is_breaking:
            breaking_changes.append((scope, subject))

        groups[type_].append((scope, subject))

    if breaking_changes:
        groups['breaking'] = breaking_changes

    return groups


def format_changelog_section(title: str, commits: list[tuple[str, str]]) -> str:
    """Format a changelog section."""
    if not commits:
        return ""

    lines = [f"\n### {title}\n"]

    for scope, subject in commits:
        if scope:
            lines.append(f"- **{scope}**: {subject}")
        else:
            lines.append(f"- {subject}")

    return "\n".join(lines)


def generate_changelog_entry(
    version: str,
    from_ref: str,
    to_ref: str,
    date: str = None
) -> str:
    """Generate changelog entry for a version."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Get commits
    commits = get_commits(from_ref, to_ref)

    if not commits:
        print(f"⚠️  No commits found between {from_ref} and {to_ref}")
        return ""

    print(f"📝 Processing {len(commits)} commits...")

    # Group commits
    groups = group_commits(commits)

    # Build changelog entry
    lines = [
        f"\n## [{version}] - {date}\n"
    ]

    # Type mapping to changelog sections
    section_map = {
        'feat': ('Added', 'feat'),
        'fix': ('Fixed', 'fix'),
        'perf': ('Performance', 'perf'),
        'docs': ('Documentation', 'docs'),
        'style': ('Style', 'style'),
        'refactor': ('Refactored', 'refactor'),
        'test': ('Tests', 'test'),
        'build': ('Build', 'build'),
        'ci': ('CI/CD', 'ci'),
        'chore': ('Chore', 'chore'),
        'breaking': ('Breaking Changes', 'breaking'),
    }

    # Add sections in order
    for section_title, type_key in section_map.values():
        if type_key in groups:
            section = format_changelog_section(section_title, groups[type_key])
            if section:
                lines.append(section)

    # Add other commits
    if 'other' in groups:
        section = format_changelog_section('Other', groups['other'])
        if section:
            lines.append(section)

    return "\n".join(lines) + "\n"


def get_latest_tag() -> str:
    """Get the latest git tag."""
    try:
        return run_git_command(['describe', '--tags', '--abbrev=0'])
    except:
        return None


def update_changelog_file(root: Path, new_entry: str, dry_run: bool = False) -> None:
    """Update CHANGELOG.md with new entry."""
    changelog_path = root / "CHANGELOG.md"

    if changelog_path.exists():
        content = changelog_path.read_text(encoding='utf-8')

        # Find insertion point (after ## [Unreleased] section)
        unreleased_match = re.search(
            r'## \[Unreleased\].*?\n(?=## \[|$)', content, re.DOTALL)

        if unreleased_match:
            # Insert after [Unreleased] section
            insert_pos = unreleased_match.end()
            updated = content[:insert_pos] + new_entry + content[insert_pos:]
        else:
            # No [Unreleased] section, insert after header
            header_match = re.search(r'# Changelog\n+', content)
            if header_match:
                insert_pos = header_match.end()
                updated = content[:insert_pos] + \
                    new_entry + content[insert_pos:]
            else:
                # Prepend to file
                updated = new_entry + "\n" + content
    else:
        # Create new changelog
        updated = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
{new_entry}
"""

    if dry_run:
        print(f"\n[DRY RUN] Would update {changelog_path}:")
        print("=" * 80)
        print(new_entry)
        print("=" * 80)
    else:
        changelog_path.write_text(updated, encoding='utf-8')
        print(f"✅ Updated {changelog_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate changelog from conventional commits"
    )
    parser.add_argument(
        'from_ref',
        nargs='?',
        help="Starting git ref (tag or commit). Default: latest tag"
    )
    parser.add_argument(
        'to_ref',
        nargs='?',
        default='HEAD',
        help="Ending git ref. Default: HEAD"
    )
    parser.add_argument(
        '--version',
        help="Version for changelog entry"
    )
    parser.add_argument(
        '--date',
        help="Date for changelog entry (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        '--stdout',
        action='store_true',
        help="Print changelog to stdout instead of updating file"
    )

    args = parser.parse_args()

    # Get project root
    root = Path(__file__).parent.parent.resolve()

    try:
        # Determine from_ref
        from_ref = args.from_ref
        if not from_ref:
            from_ref = get_latest_tag()
            if not from_ref:
                print("⚠️  No tags found. Using first commit.")
                from_ref = run_git_command(
                    ['rev-list', '--max-parents=0', 'HEAD'])

        # Determine version
        version = args.version
        if not version:
            # Try to extract from to_ref if it's a tag
            if args.to_ref.startswith('v'):
                version = args.to_ref[1:]  # Remove 'v' prefix
            else:
                version = "Unreleased"

        print(f"📦 Generating changelog for {version}")
        print(f"📍 From: {from_ref}")
        print(f"📍 To: {args.to_ref}")

        # Generate changelog entry
        entry = generate_changelog_entry(
            version,
            from_ref,
            args.to_ref,
            args.date
        )

        if not entry:
            print("⚠️  No changes to document")
            return 0

        if args.stdout:
            print("\n" + "=" * 80)
            print(entry)
            print("=" * 80)
        else:
            update_changelog_file(root, entry, args.dry_run)

            if not args.dry_run:
                print("\n✅ Changelog generated successfully")
                print("\nNext steps:")
                print("  1. Review CHANGELOG.md")
                print("  2. Edit if needed (add migration notes, etc.)")
                print("  3. Commit: git commit -am 'docs(changelog): update for vX.Y.Z'")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
