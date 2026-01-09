#!/usr/bin/env python3
"""
Paracle Governance Validator

Validates the consistency and syntax of all .parac/ files.
Run this before commits to ensure governance integrity.
"""

import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("⚠️  PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


PARAC_ROOT = Path(__file__).parent.parent
REQUIRED_FILES = [
    "project.yaml",
    "roadmap/roadmap.yaml",
    "roadmap/decisions.md",
    "roadmap/constraints.yaml",
    "policies/policy-pack.yaml",
    "policies/security.yaml",
    "policies/approvals.yaml",
    "agents/manifest.yaml",
    "memory/index.yaml",
    "memory/context/current_state.yaml",
    "memory/context/open_questions.md",
    "memory/knowledge/domain.md",
    "memory/knowledge/architecture.md",
    "memory/knowledge/glossary.md",
    "GOVERNANCE.md",
]

REQUIRED_AGENT_SPECS = [
    "agents/specs/architect.md",
    "agents/specs/coder.md",
    "agents/specs/reviewer.md",
    "agents/specs/tester.md",
    "agents/specs/pm.md",
    "agents/specs/documenter.md",
]


def validate_yaml_file(filepath: Path) -> tuple[bool, str]:
    """Validate YAML syntax."""
    try:
        with open(filepath, encoding="utf-8") as f:
            yaml.safe_load(f)
        return True, "OK"
    except yaml.YAMLError as e:
        return False, f"YAML Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def validate_required_files() -> list[str]:
    """Check all required files exist."""
    errors = []
    for file in REQUIRED_FILES:
        filepath = PARAC_ROOT / file
        if not filepath.exists():
            errors.append(f"Missing required file: {file}")

    for file in REQUIRED_AGENT_SPECS:
        filepath = PARAC_ROOT / file
        if not filepath.exists():
            errors.append(f"Missing agent spec: {file}")

    return errors


def validate_yaml_files() -> list[str]:
    """Validate all YAML files."""
    errors = []
    yaml_files = list(PARAC_ROOT.rglob("*.yaml")) + list(PARAC_ROOT.rglob("*.yml"))

    for filepath in yaml_files:
        valid, message = validate_yaml_file(filepath)
        if not valid:
            rel_path = filepath.relative_to(PARAC_ROOT)
            errors.append(f"{rel_path}: {message}")

    return errors


def validate_roadmap_consistency() -> list[str]:
    """Validate roadmap.yaml consistency."""
    errors = []
    roadmap_path = PARAC_ROOT / "roadmap" / "roadmap.yaml"
    state_path = PARAC_ROOT / "memory" / "context" / "current_state.yaml"

    try:
        with open(roadmap_path, encoding="utf-8") as f:
            roadmap = yaml.safe_load(f)
        with open(state_path, encoding="utf-8") as f:
            state = yaml.safe_load(f)

        # Check phase consistency
        roadmap_phase = roadmap.get("current_phase", "unknown")
        state_phase = state.get("current_phase", {}).get("id", "unknown")

        if roadmap_phase != state_phase:
            errors.append(
                f"Phase mismatch: roadmap.yaml says '{roadmap_phase}', "
                f"current_state.yaml says '{state_phase}'"
            )

        # Check version consistency
        roadmap_version = str(roadmap.get("version", "unknown"))
        state_version = str(state.get("project", {}).get("version", "unknown"))

        if roadmap_version != state_version:
            errors.append(
                f"Version mismatch: roadmap.yaml says '{roadmap_version}', "
                f"current_state.yaml says '{state_version}'"
            )

    except Exception as e:
        errors.append(f"Error validating roadmap consistency: {e}")

    return errors


def validate_open_questions() -> list[str]:
    """Validate open questions have owners and deadlines."""
    errors = []
    questions_path = PARAC_ROOT / "memory" / "context" / "open_questions.md"

    try:
        with open(questions_path, encoding="utf-8") as f:
            content = f.read()

        # Check for questions without owners
        if "**Owner:** TBD" in content or "**Owner:**\n" in content:
            errors.append("open_questions.md has questions without owners")

        # Check for questions without deadlines
        if "**Deadline:** TBD" in content or "**Deadline:**\n" in content:
            errors.append("open_questions.md has questions without deadlines")

    except Exception as e:
        errors.append(f"Error validating open questions: {e}")

    return errors


def validate_metrics() -> list[str]:
    """Validate metrics are present and reasonable."""
    errors = []
    roadmap_path = PARAC_ROOT / "roadmap" / "roadmap.yaml"

    try:
        with open(roadmap_path, encoding="utf-8") as f:
            roadmap = yaml.safe_load(f)

        metrics = roadmap.get("metrics", {})

        required_metrics = ["test_coverage", "documentation_coverage"]
        for metric in required_metrics:
            if metric not in metrics:
                errors.append(f"Missing required metric: {metric}")

    except Exception as e:
        errors.append(f"Error validating metrics: {e}")

    return errors


def main():
    """Run all validations."""
    print("=" * 60)
    print("Paracle Governance Validator")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    all_errors = []

    # Check required files
    print("📁 Checking required files...")
    errors = validate_required_files()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ All required files present")
    print()

    # Validate YAML syntax
    print("📄 Validating YAML syntax...")
    errors = validate_yaml_files()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ All YAML files valid")
    print()

    # Check roadmap consistency
    print("🗺️  Checking roadmap consistency...")
    errors = validate_roadmap_consistency()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ Roadmap and state consistent")
    print()

    # Check open questions
    print("❓ Checking open questions...")
    errors = validate_open_questions()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ⚠️  {e}")
    else:
        print("  ✅ All questions have owners and deadlines")
    print()

    # Check metrics
    print("📊 Checking metrics...")
    errors = validate_metrics()
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ All required metrics present")
    print()

    # Summary
    print("=" * 60)
    if all_errors:
        print(f"❌ Validation FAILED with {len(all_errors)} error(s)")
        sys.exit(1)
    else:
        print("✅ Validation PASSED - .parac/ is consistent")
        sys.exit(0)


if __name__ == "__main__":
    main()
