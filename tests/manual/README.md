# Manual Test Scripts

This directory contains manual test scripts for development and debugging.

## Test Files

- **check_costs_db.py** - Cost tracking database verification
- **quick_test.py** - Quick smoke tests
- **test_cost_tracking.py** - Cost management testing
- **test_github_agents_workflow.py** - GitHub agents workflow testing
- **test_mcp_tools.py** - MCP tools integration testing
- **test_real_workflow.py** - Real workflow execution testing

## Usage

These are not automated tests. Run them manually for development:

```bash
# Example
python tests/manual/quick_test.py
```

## Note

For automated unit/integration tests, see 	ests/unit/ and 	ests/integration/.
