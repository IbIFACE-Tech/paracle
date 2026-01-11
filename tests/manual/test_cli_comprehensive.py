#!/usr/bin/env python
"""Comprehensive CLI testing script for Paracle.

This script tests all major CLI commands as documented in the QA agent spec.
"""

from typing import Any

from click.testing import CliRunner
from paracle_cli.main import cli


def run_cli_test(runner: CliRunner, command: str, description: str) -> dict[str, Any]:
    """Run a single CLI test.

    Args:
        runner: CliRunner instance
        command: Command string (without 'paracle' prefix)
        description: Test description

    Returns:
        Test result dictionary
    """
    result = runner.invoke(cli, command.split())

    return {
        'command': f'paracle {command}',
        'description': description,
        'exit_code': result.exit_code,
        'passed': result.exit_code == 0,
        'output': result.output,
        'output_preview': result.output[:150] if result.output else '',
    }


def main():
    """Run comprehensive CLI tests."""
    runner = CliRunner()

    # Test categories based on QA spec
    tests = [
        # Basic commands
        ('--version', 'Version check'),
        ('--help', 'Help command'),
        ('hello', 'Hello/installation verification'),

        # Agent commands
        ('agents list', 'List all agents'),
        ('agents show coder', 'Show specific agent'),

        # Tool commands
        ('tools list', 'List all tools'),

        # Status & health
        ('status', 'Show project status'),
        ('doctor', 'System health check'),

        # Configuration
        ('config show', 'Show configuration'),

        # Governance
        ('governance list', 'List governance policies'),
        ('compliance status', 'Show compliance status'),

        # Workflow commands
        ('workflow list', 'List workflows'),

        # Validation
        ('validate structure', 'Validate .parac structure'),

        # Sync
        ('sync --roadmap', 'Sync roadmap with state'),

        # Logs
        ('logs show', 'Show logs'),

        # Cache
        ('cache stats', 'Show cache statistics'),

        # Cost tracking
        ('cost summary', 'Show cost summary'),

        # Providers
        ('providers list', 'List LLM providers'),

        # Session management
        ('session list', 'List sessions'),

        # Board/Kanban
        ('board list', 'List Kanban boards'),
    ]

    print('\n' + '='*80)
    print(' Paracle CLI Comprehensive Test Suite')
    print('='*80 + '\n')

    results = []
    for cmd, desc in tests:
        print(f'Testing: {cmd}...', end=' ')
        result = run_cli_test(runner, cmd, desc)
        results.append(result)

        if result['passed']:
            print('[PASS]')
        else:
            print(f'[FAIL] (exit code: {result["exit_code"]})')

    # Summary
    print('\n' + '='*80)
    print(' Test Summary')
    print('='*80 + '\n')

    passed = sum(1 for r in results if r['passed'])
    failed = sum(1 for r in results if not r['passed'])
    total = len(results)

    print(f'[PASS] Passed: {passed}/{total}')
    print(f'[FAIL] Failed: {failed}/{total}')
    print(f'Success rate: {(passed/total)*100:.1f}%\n')

    # Detailed results
    print('\n' + '-'*80)
    print(' Detailed Results')
    print('-'*80 + '\n')

    for r in results:
        status = '[PASS]' if r['passed'] else f'[FAIL] (exit {r["exit_code"]})'
        print(f'{status:<20} {r["command"]:<35} ({r["description"]})')
        if r['output_preview']:
            print(f'                     Output: {r["output_preview"]}')
        print()

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    exit(main())
