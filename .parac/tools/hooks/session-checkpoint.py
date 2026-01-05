#!/usr/bin/env python3
"""
Paracle Session Checkpoint

Creates a checkpoint of the current session state.
Use at the end of each work session to ensure .parac/ is updated.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("⚠️  PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


PARAC_ROOT = Path(__file__).parent.parent
STATE_FILE = PARAC_ROOT / "memory" / "context" / "current_state.yaml"
DECISIONS_FILE = PARAC_ROOT / "roadmap" / "decisions.md"
QUESTIONS_FILE = PARAC_ROOT / "memory" / "context" / "open_questions.md"


def load_state() -> dict:
    """Load current state."""
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_state(state: dict):
    """Save state file."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def update_progress(state: dict, progress: int) -> dict:
    """Update phase progress."""
    if "current_phase" in state:
        state["current_phase"]["progress"] = f"{progress}%"
    state["snapshot_date"] = datetime.now().strftime("%Y-%m-%d")
    return state


def add_completed_item(state: dict, item: str) -> dict:
    """Add item to completed list."""
    if "current_phase" not in state:
        state["current_phase"] = {}
    if "completed" not in state["current_phase"]:
        state["current_phase"]["completed"] = []

    if item not in state["current_phase"]["completed"]:
        state["current_phase"]["completed"].append(item)

    # Remove from in_progress if present
    if "in_progress" in state["current_phase"]:
        state["current_phase"]["in_progress"] = [
            i for i in state["current_phase"]["in_progress"] if i != item
        ]

    return state


def add_in_progress_item(state: dict, item: str) -> dict:
    """Add item to in_progress list."""
    if "current_phase" not in state:
        state["current_phase"] = {}
    if "in_progress" not in state["current_phase"]:
        state["current_phase"]["in_progress"] = []

    if item not in state["current_phase"]["in_progress"]:
        state["current_phase"]["in_progress"].append(item)

    # Remove from pending if present
    if "pending" in state["current_phase"]:
        state["current_phase"]["pending"] = [
            i for i in state["current_phase"]["pending"] if i != item
        ]

    return state


def add_decision(title: str, decision: str, rationale: str):
    """Add a decision to decisions.md."""
    timestamp = datetime.now().strftime("%Y-%m-%d")

    entry = f"""
### ADR-XXX: {title}

**Date:** {timestamp}
**Status:** Accepted

**Context:**
[Add context here]

**Decision:**
{decision}

**Rationale:**
{rationale}

**Consequences:**
- [Add consequences]

---
"""

    with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"✅ Decision added to decisions.md: {title}")


def generate_checkpoint_summary(state: dict) -> str:
    """Generate a checkpoint summary."""
    phase = state.get("current_phase", {})

    summary = f"""
## Session Checkpoint - {datetime.now().strftime("%Y-%m-%d %H:%M")}

### Current Phase
- **Phase:** {phase.get('id', 'unknown')} - {phase.get('name', 'unknown')}
- **Progress:** {phase.get('progress', 'unknown')}
- **Status:** {phase.get('status', 'unknown')}

### Completed This Session
{chr(10).join('- ' + item for item in phase.get('completed', [])[-5:]) or '- None'}

### In Progress
{chr(10).join('- ' + item for item in phase.get('in_progress', [])) or '- None'}

### Next Actions
{chr(10).join('- ' + item for item in state.get('next_actions', [])[:5]) or '- None'}

### Blockers
{chr(10).join('- ' + b.get('description', 'unknown') for b in state.get('blockers', [])) or '- None'}
"""
    return summary


def interactive_checkpoint():
    """Interactive checkpoint process."""
    print("=" * 60)
    print("Paracle Session Checkpoint")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    state = load_state()
    modified = False

    # Show current state
    phase = state.get("current_phase", {})
    print(f"📍 Current Phase: {phase.get('id', 'unknown')} ({phase.get('progress', '0%')})")
    print()

    # Ask about progress
    print("📊 Update progress? (Enter new percentage or press Enter to skip)")
    progress_input = input("   Progress [0-100]: ").strip()
    if progress_input.isdigit():
        progress = int(progress_input)
        if 0 <= progress <= 100:
            state = update_progress(state, progress)
            modified = True
            print(f"   ✅ Progress updated to {progress}%")
    print()

    # Ask about completed items
    print("✅ Add completed item? (Enter item name or press Enter to skip)")
    while True:
        item = input("   Completed item: ").strip()
        if not item:
            break
        state = add_completed_item(state, item)
        modified = True
        print(f"   ✅ Added: {item}")
    print()

    # Ask about in-progress items
    print("🔄 Add in-progress item? (Enter item name or press Enter to skip)")
    while True:
        item = input("   In-progress item: ").strip()
        if not item:
            break
        state = add_in_progress_item(state, item)
        modified = True
        print(f"   ✅ Added: {item}")
    print()

    # Ask about decisions
    print("📝 Add decision? (y/n)")
    if input("   ").strip().lower() == "y":
        title = input("   Decision title: ").strip()
        decision = input("   Decision: ").strip()
        rationale = input("   Rationale: ").strip()
        if title and decision:
            add_decision(title, decision, rationale)
            modified = True
    print()

    # Save if modified
    if modified:
        save_state(state)
        print("💾 State saved to current_state.yaml")
    else:
        print("ℹ️  No changes made")
    print()

    # Show summary
    print("📋 Checkpoint Summary:")
    print(generate_checkpoint_summary(state))


def main():
    parser = argparse.ArgumentParser(description="Paracle Session Checkpoint")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive checkpoint mode"
    )
    parser.add_argument(
        "--progress",
        type=int,
        help="Set phase progress (0-100)"
    )
    parser.add_argument(
        "--complete",
        type=str,
        help="Mark item as completed"
    )
    parser.add_argument(
        "--in-progress",
        type=str,
        help="Mark item as in-progress"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show checkpoint summary"
    )

    args = parser.parse_args()

    if args.interactive:
        interactive_checkpoint()
        return

    state = load_state()
    modified = False

    if args.progress is not None:
        state = update_progress(state, args.progress)
        modified = True
        print(f"✅ Progress updated to {args.progress}%")

    if args.complete:
        state = add_completed_item(state, args.complete)
        modified = True
        print(f"✅ Marked as completed: {args.complete}")

    if args.in_progress:
        state = add_in_progress_item(state, args.in_progress)
        modified = True
        print(f"✅ Marked as in-progress: {args.in_progress}")

    if modified:
        save_state(state)
        print("💾 State saved")

    if args.summary or not any([args.progress, args.complete, args.in_progress]):
        print(generate_checkpoint_summary(state))


if __name__ == "__main__":
    main()
