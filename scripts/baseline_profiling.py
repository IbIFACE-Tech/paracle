"""Baseline Performance Profiling Script.

Runs comprehensive profiling across all key operations to establish
performance baselines for Phase 8 optimization.

Usage:
    python scripts/baseline_profiling.py
    python scripts/baseline_profiling.py --output baseline_report.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

try:
    from paracle_core.parac.agent_discovery import AgentDiscovery
    from paracle_orchestration.skill_loader import SkillLoader
    from paracle_orchestration.workflow_loader import WorkflowLoader
    from paracle_profiling import (
        PerformanceAnalyzer,
        Profiler,
        clear_profile_stats,
        get_profile_stats,
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root.")
    sys.exit(1)


def print_header(title: str) -> None:
    """Print section header."""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def run_agent_discovery_tests() -> None:
    """Profile agent discovery operations."""
    print_header("Agent Discovery Performance")

    try:
        discovery = AgentDiscovery(parac_root=Path.cwd() / ".parac")
    except Exception as e:
        print(f"  Warning: Could not initialize AgentDiscovery: {e}")
        return

    # List all agents
    print("Testing agent listing...")
    agents = []
    for i in range(5):
        agents = discovery.discover_agents()

    print(f"  Found {len(agents)} agents")

    # Get specific agents
    print("Testing agent retrieval (20x)...")
    agent_ids = [a.id for a in agents[:4]]  # Test first 4 agents
    for _ in range(5):
        for agent_id in agent_ids:
            agent = discovery.get_agent(agent_id)
            spec = discovery.get_agent_spec_content(agent_id)

    print("  Agent operations profiled")


def run_workflow_loader_tests() -> None:
    """Profile workflow loading operations."""
    print_header("Workflow Loading Performance")

    try:
        loader = WorkflowLoader()

        # List workflows
        print("Testing workflow listing (5x)...")
        for _ in range(5):
            workflows = loader.list_workflows()
        print(f"  Found {len(workflows)} workflows")

        # Load workflow specs
        print("Testing workflow loading (10x per workflow)...")
        for workflow_name in workflows[:3]:  # Test first 3
            for _ in range(10):
                try:
                    yaml_data = loader.load_workflow_yaml(workflow_name)
                    spec = loader.load_workflow_spec(workflow_name)
                except Exception as e:
                    print(f"  Warning: Could not load {workflow_name}: {e}")

        print("  Workflow operations profiled")
    except Exception as e:
        print(f"  Warning: Workflow profiling failed: {e}")


def run_skill_loader_tests() -> None:
    """Profile skill loading operations."""
    print_header("Skill Loading Performance")

    try:
        loader = SkillLoader()

        # Discover skills
        print("Testing skill discovery (5x)...")
        for _ in range(5):
            skills = loader.discover_skills()
        print(f"  Found {len(skills)} skills")

        # Load skills
        print("Testing skill loading (10x per skill)...")
        for skill_id in skills[:5]:  # Test first 5
            for _ in range(10):
                skill = loader.load_skill(skill_id)

        print("  Skill operations profiled")
    except Exception as e:
        print(f"  Warning: Skill profiling failed: {e}")


def generate_report() -> dict:
    """Generate performance report."""
    print_header("Performance Analysis")

    analyzer = PerformanceAnalyzer()

    # Get bottlenecks
    bottlenecks = analyzer.analyze_bottlenecks(top_n=20, min_calls=1)

    print(f"Found {len(bottlenecks)} profiled functions")
    print()

    # Print detailed report
    report_text = analyzer.generate_report(top_n=20, min_calls=1)
    print(report_text)

    # Check Phase 8 targets
    print()
    print_header("Phase 8 Target Validation")
    targets = analyzer.check_targets()

    print(
        f"P95 < 500ms:     {'✅ PASS' if targets['p95_under_500ms'] else '❌ FAIL'}")
    if not targets['p95_under_500ms'] and 'worst_p95' in targets:
        print(f"  Worst P95: {targets['worst_p95']:.3f}s")

    print(
        f"P99 < 1000ms:    {'✅ PASS' if targets['p99_under_1000ms'] else '❌ FAIL'}")
    if not targets['p99_under_1000ms'] and 'worst_p99' in targets:
        print(f"  Worst P99: {targets['worst_p99']:.3f}s")

    print(
        f"Average < 100ms: {'✅ PASS' if targets['avg_under_100ms'] else '❌ FAIL'}")
    if not targets['avg_under_100ms'] and 'worst_avg' in targets:
        print(f"  Worst Avg: {targets['worst_avg']:.3f}s")

    # Create JSON report
    all_stats = get_profile_stats()

    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_functions": len(all_stats),
            "total_bottlenecks": len(bottlenecks),
            "targets": targets,
        },
        "bottlenecks": [
            {
                "name": b.name,
                "avg_time": b.avg_time,
                "max_time": b.max_time,
                "p95_time": b.p95_time,
                "calls": b.calls,
                "total_time": b.total_time,
                "percentage": b.percentage_of_total,
                "severity": b.severity,
            }
            for b in bottlenecks
        ],
        "all_stats": {
            name: {
                "calls": stats["calls"],
                "avg_time": stats["avg_time"],
                "min_time": stats["min_time"],
                "max_time": stats["max_time"],
                "p95_time": stats["p95_time"],
                "p99_time": stats["p99_time"],
                "total_time": stats["total_time"],
            }
            for name, stats in all_stats.items()
        },
    }

    return report


def main():
    """Run baseline profiling."""
    parser = argparse.ArgumentParser(
        description="Baseline performance profiling for Phase 8"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="baseline_profile.json",
        help="Output file for JSON report (default: baseline_profile.json)",
    )
    args = parser.parse_args()

    print_header("Phase 8: Baseline Performance Profiling")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Enable profiler
    Profiler.enable()
    print("✅ Profiler enabled")

    # Clear any existing stats
    clear_profile_stats()
    print("✅ Stats cleared")

    # Run profiling tests
    try:
        run_agent_discovery_tests()
        run_workflow_loader_tests()
        run_skill_loader_tests()
    except KeyboardInterrupt:
        print("\n\nProfiling interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during profiling: {e}")
        import traceback
        traceback.print_exc()

    # Generate report
    report = generate_report()

    # Save to file
    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print()
    print_header("Baseline Profiling Complete")
    print(f"Report saved to: {output_path}")
    print(f"Total functions profiled: {report['summary']['total_functions']}")
    print(f"Bottlenecks identified: {report['summary']['total_bottlenecks']}")
    print()

    # Exit with failure if targets not met
    targets = report['summary']['targets']
    if not all([targets['p95_under_500ms'], targets['p99_under_1000ms'], targets['avg_under_100ms']]):
        print("⚠️  Some Phase 8 targets not met - optimization needed!")
        sys.exit(1)
    else:
        print("✅ All Phase 8 targets met!")
        sys.exit(0)


if __name__ == "__main__":
    main()
