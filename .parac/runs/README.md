# Execution Runs

This directory stores execution history for agents and workflows, including inputs, outputs, artifacts, and traces.

## Structure

```
runs/
├── agents/              # Agent execution runs
│   └── {run_id}/
│       ├── metadata.yaml       # Run metadata (agent, timestamp, status)
│       ├── input.json          # Input prompt and context
│       ├── output.json         # Agent response
│       ├── artifacts/          # Generated files (code, docs, etc.)
│       ├── trace.json          # Execution trace (OpenTelemetry)
│       └── logs.txt            # Execution logs
│
└── workflows/           # Workflow execution runs
    └── {run_id}/
        ├── metadata.yaml       # Workflow metadata
        ├── steps/              # Per-step outputs
        │   └── {step_id}/
        │       ├── input.json
        │       ├── output.json
        │       └── artifacts/
        ├── artifacts/          # Final workflow artifacts
        ├── trace.json          # Full workflow trace
        └── logs.txt            # Workflow logs
```

## Run ID Format

Run IDs use ULID format for sortable, globally unique identifiers:
- Format: `01HN7X8K9M2PQRSTUVWXYZ3456`
- Sortable by timestamp
- URL-safe
- Collision-resistant

## Metadata Schema

### Agent Run Metadata

```yaml
# .parac/runs/agents/{run_id}/metadata.yaml
run_id: "01HN7X8K9M2PQRSTUVWXYZ3456"
agent_id: "coder"
agent_name: "Coder Agent"
started_at: "2026-01-06T10:30:00Z"
completed_at: "2026-01-06T10:31:45Z"
duration_seconds: 105
status: "completed"  # pending, running, completed, failed
exit_code: 0

# Execution context
provider: "openai"
model: "gpt-4"
temperature: 0.7

# Resource usage
tokens_used: 2450
cost_usd: 0.0245
memory_mb: 128
cpu_seconds: 3.2

# Result summary
artifacts_count: 3
files_modified: 2
error_count: 0
```

### Workflow Run Metadata

```yaml
# .parac/runs/workflows/{run_id}/metadata.yaml
run_id: "01HN7X8K9M2PQRSTUVWXYZ3456"
workflow_id: "data_pipeline"
workflow_name: "Data Pipeline"
started_at: "2026-01-06T10:30:00Z"
completed_at: "2026-01-06T10:35:20Z"
duration_seconds: 320
status: "completed"

# Steps
steps_total: 5
steps_completed: 5
steps_failed: 0
steps_skipped: 0

# Agents involved
agents_used:
  - "extractor"
  - "transformer"
  - "loader"

# Resource usage (aggregated)
tokens_total: 8500
cost_total_usd: 0.085
artifacts_count: 12
```

## Storage Policy

### Retention
- **Lite Mode:** Keep last 10 runs per agent/workflow
- **Standard Mode:** Keep last 50 runs per agent/workflow
- **Full Mode:** Keep all runs (configurable max age)

### Cleanup
```bash
# Manual cleanup
paracle runs cleanup --older-than 30d

# Automatic cleanup (configured in project.yaml)
paracle_config:
  runs:
    retention_days: 30
    max_runs_per_agent: 100
```

### Size Management
- Artifacts > 10MB compressed automatically
- Traces sampled after 1000 runs (configurable)
- Old runs archived to `.parac/runs/.archive/`

## Querying Runs

```bash
# List recent runs
paracle runs list --limit 20

# Get specific run
paracle runs get {run_id}

# Search runs
paracle runs search --agent coder --status completed --since 7d

# Get run artifacts
paracle runs artifacts {run_id}

# Replay run (re-execute with same inputs)
paracle runs replay {run_id}
```

## Integration with Observability

Runs integrate with Phase 8 monitoring:
- **Traces:** OpenTelemetry traces stored in `trace.json`
- **Metrics:** Extracted to Prometheus/Grafana
- **Logs:** Structured logs in `logs.txt`
- **Dashboards:** Run history visualized

## Privacy & Security

- **PII Scrubbing:** Sensitive data masked in stored runs
- **API Keys:** Never stored in run artifacts
- **Encryption:** Runs encrypted at rest (configurable)
- **Access Control:** RBAC applied to run queries

## Use Cases

### Development & Debugging
- Reproduce issues by replaying failed runs
- Compare outputs across model versions
- Analyze token usage and costs

### Testing & Validation
- Regression testing with historical inputs
- Performance benchmarking
- Cost analysis

### Compliance & Audit
- Full execution history
- Traceability for governance
- Cost attribution per project/agent

---

**Implementation:**
- Phase 6 (DX): Basic run storage and replay
- Phase 8 (Performance): Full observability integration
- Phase 10 (Governance): Audit trail compliance
