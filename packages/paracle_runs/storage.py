"""Run storage implementation."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from paracle_core.parac.state import find_parac_root

from paracle_runs.models import AgentRunMetadata, RunQuery, WorkflowRunMetadata


class RunStorage:
    """Manages storage and retrieval of execution runs."""

    def __init__(self, runs_dir: Path | None = None):
        """Initialize run storage.

        Args:
            runs_dir: Directory for storing runs (defaults to .parac/runs/)
        """
        if runs_dir is None:
            parac_root = find_parac_root()
            runs_dir = parac_root / "runs"

        self.runs_dir = runs_dir
        self.agents_dir = runs_dir / "agents"
        self.workflows_dir = runs_dir / "workflows"

        # Ensure directories exist
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def save_agent_run(
        self,
        metadata: AgentRunMetadata,
        input_data: dict[str, Any],
        output_data: dict[str, Any] | None = None,
        artifacts: dict[str, Any] | None = None,
        logs: str | None = None,
        trace: dict[str, Any] | None = None,
    ) -> Path:
        """Save agent run data.

        Args:
            metadata: Run metadata
            input_data: Input prompt and context
            output_data: Agent response
            artifacts: Generated artifacts (code, docs, etc.)
            logs: Execution logs
            trace: OpenTelemetry trace

        Returns:
            Path to run directory
        """
        run_dir = self.agents_dir / metadata.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata as YAML
        metadata_path = run_dir / "metadata.yaml"
        with open(metadata_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(metadata.model_dump(mode="json"), f, sort_keys=False)

        # Save input as JSON
        input_path = run_dir / "input.json"
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(input_data, f, indent=2)

        # Save output if available
        if output_data:
            output_path = run_dir / "output.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)

        # Save artifacts if available
        if artifacts:
            artifacts_dir = run_dir / "artifacts"
            artifacts_dir.mkdir(exist_ok=True)
            artifacts_path = artifacts_dir / "artifacts.json"
            with open(artifacts_path, "w", encoding="utf-8") as f:
                json.dump(artifacts, f, indent=2)

        # Save logs if available
        if logs:
            logs_path = run_dir / "logs.txt"
            with open(logs_path, "w", encoding="utf-8") as f:
                f.write(logs)

        # Save trace if available
        if trace:
            trace_path = run_dir / "trace.json"
            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(trace, f, indent=2)

        return run_dir

    def save_workflow_run(
        self,
        metadata: WorkflowRunMetadata,
        inputs: dict[str, Any],
        outputs: dict[str, Any] | None = None,
        steps: dict[str, dict[str, Any]] | None = None,
        artifacts: dict[str, Any] | None = None,
        logs: str | None = None,
        trace: dict[str, Any] | None = None,
    ) -> Path:
        """Save workflow run data.

        Args:
            metadata: Run metadata
            inputs: Workflow inputs
            outputs: Workflow outputs
            steps: Per-step execution data
            artifacts: Generated artifacts
            logs: Execution logs
            trace: OpenTelemetry trace

        Returns:
            Path to run directory
        """
        run_dir = self.workflows_dir / metadata.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata as YAML
        metadata_path = run_dir / "metadata.yaml"
        with open(metadata_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(metadata.model_dump(mode="json"), f, sort_keys=False)

        # Save inputs as JSON
        inputs_path = run_dir / "inputs.json"
        with open(inputs_path, "w", encoding="utf-8") as f:
            json.dump(inputs, f, indent=2)

        # Save outputs if available
        if outputs:
            outputs_path = run_dir / "outputs.json"
            with open(outputs_path, "w", encoding="utf-8") as f:
                json.dump(outputs, f, indent=2)

        # Save step data if available
        if steps:
            steps_dir = run_dir / "steps"
            steps_dir.mkdir(exist_ok=True)
            for step_id, step_data in steps.items():
                step_path = steps_dir / f"{step_id}.json"
                with open(step_path, "w", encoding="utf-8") as f:
                    json.dump(step_data, f, indent=2)

        # Save artifacts if available
        if artifacts:
            artifacts_dir = run_dir / "artifacts"
            artifacts_dir.mkdir(exist_ok=True)
            artifacts_path = artifacts_dir / "artifacts.json"
            with open(artifacts_path, "w", encoding="utf-8") as f:
                json.dump(artifacts, f, indent=2)

        # Save logs if available
        if logs:
            logs_path = run_dir / "logs.txt"
            with open(logs_path, "w", encoding="utf-8") as f:
                f.write(logs)

        # Save trace if available
        if trace:
            trace_path = run_dir / "trace.json"
            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(trace, f, indent=2)

        return run_dir

    def load_agent_run(self, run_id: str) -> tuple[AgentRunMetadata, dict[str, Any]]:
        """Load agent run data.

        Args:
            run_id: Run ID

        Returns:
            Tuple of (metadata, run_data)

        Raises:
            FileNotFoundError: If run not found
        """
        run_dir = self.agents_dir / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Agent run not found: {run_id}")

        # Load metadata
        metadata_path = run_dir / "metadata.yaml"
        with open(metadata_path, encoding="utf-8") as f:
            metadata_dict = yaml.safe_load(f)
        metadata = AgentRunMetadata(**metadata_dict)

        # Load all available data
        run_data: dict[str, Any] = {}

        input_path = run_dir / "input.json"
        if input_path.exists():
            with open(input_path, encoding="utf-8") as f:
                run_data["input"] = json.load(f)

        output_path = run_dir / "output.json"
        if output_path.exists():
            with open(output_path, encoding="utf-8") as f:
                run_data["output"] = json.load(f)

        artifacts_path = run_dir / "artifacts" / "artifacts.json"
        if artifacts_path.exists():
            with open(artifacts_path, encoding="utf-8") as f:
                run_data["artifacts"] = json.load(f)

        logs_path = run_dir / "logs.txt"
        if logs_path.exists():
            with open(logs_path, encoding="utf-8") as f:
                run_data["logs"] = f.read()

        trace_path = run_dir / "trace.json"
        if trace_path.exists():
            with open(trace_path, encoding="utf-8") as f:
                run_data["trace"] = json.load(f)

        return metadata, run_data

    def load_workflow_run(
        self, run_id: str
    ) -> tuple[WorkflowRunMetadata, dict[str, Any]]:
        """Load workflow run data.

        Args:
            run_id: Run ID

        Returns:
            Tuple of (metadata, run_data)

        Raises:
            FileNotFoundError: If run not found
        """
        run_dir = self.workflows_dir / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Workflow run not found: {run_id}")

        # Load metadata
        metadata_path = run_dir / "metadata.yaml"
        with open(metadata_path, encoding="utf-8") as f:
            metadata_dict = yaml.safe_load(f)
        metadata = WorkflowRunMetadata(**metadata_dict)

        # Load all available data
        run_data: dict[str, Any] = {}

        inputs_path = run_dir / "inputs.json"
        if inputs_path.exists():
            with open(inputs_path, encoding="utf-8") as f:
                run_data["inputs"] = json.load(f)

        outputs_path = run_dir / "outputs.json"
        if outputs_path.exists():
            with open(outputs_path, encoding="utf-8") as f:
                run_data["outputs"] = json.load(f)

        # Load steps
        steps_dir = run_dir / "steps"
        if steps_dir.exists():
            steps = {}
            for step_file in steps_dir.glob("*.json"):
                step_id = step_file.stem
                with open(step_file, encoding="utf-8") as f:
                    steps[step_id] = json.load(f)
            run_data["steps"] = steps

        artifacts_path = run_dir / "artifacts" / "artifacts.json"
        if artifacts_path.exists():
            with open(artifacts_path, encoding="utf-8") as f:
                run_data["artifacts"] = json.load(f)

        logs_path = run_dir / "logs.txt"
        if logs_path.exists():
            with open(logs_path, encoding="utf-8") as f:
                run_data["logs"] = f.read()

        trace_path = run_dir / "trace.json"
        if trace_path.exists():
            with open(trace_path, encoding="utf-8") as f:
                run_data["trace"] = json.load(f)

        return metadata, run_data

    def list_agent_runs(self, query: RunQuery | None = None) -> list[AgentRunMetadata]:
        """List agent runs.

        Args:
            query: Query parameters for filtering

        Returns:
            List of agent run metadata
        """
        if query is None:
            query = RunQuery()

        runs = []
        for run_dir in sorted(self.agents_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue

            metadata_path = run_dir / "metadata.yaml"
            if not metadata_path.exists():
                continue

            try:
                with open(metadata_path, encoding="utf-8") as f:
                    metadata_dict = yaml.safe_load(f)
                metadata = AgentRunMetadata(**metadata_dict)

                # Apply filters
                if query.agent_id and metadata.agent_id != query.agent_id:
                    continue
                if query.status and metadata.status != query.status:
                    continue
                if query.since and metadata.started_at < query.since:
                    continue
                if query.until and metadata.started_at > query.until:
                    continue

                runs.append(metadata)

                if len(runs) >= query.limit:
                    break

            except Exception:
                # Skip invalid metadata files
                continue

        return runs

    def list_workflow_runs(
        self, query: RunQuery | None = None
    ) -> list[WorkflowRunMetadata]:
        """List workflow runs.

        Args:
            query: Query parameters for filtering

        Returns:
            List of workflow run metadata
        """
        if query is None:
            query = RunQuery()

        runs = []
        for run_dir in sorted(self.workflows_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue

            metadata_path = run_dir / "metadata.yaml"
            if not metadata_path.exists():
                continue

            try:
                with open(metadata_path, encoding="utf-8") as f:
                    metadata_dict = yaml.safe_load(f)
                metadata = WorkflowRunMetadata(**metadata_dict)

                # Apply filters
                if query.workflow_id and metadata.workflow_id != query.workflow_id:
                    continue
                if query.status and metadata.status != query.status:
                    continue
                if query.since and metadata.started_at < query.since:
                    continue
                if query.until and metadata.started_at > query.until:
                    continue

                runs.append(metadata)

                if len(runs) >= query.limit:
                    break

            except Exception:
                # Skip invalid metadata files
                continue

        return runs

    def delete_run(self, run_id: str, run_type: str = "agent") -> bool:
        """Delete a run.

        Args:
            run_id: Run ID
            run_type: 'agent' or 'workflow'

        Returns:
            True if deleted, False if not found
        """
        if run_type == "agent":
            run_dir = self.agents_dir / run_id
        else:
            run_dir = self.workflows_dir / run_id

        if not run_dir.exists():
            return False

        shutil.rmtree(run_dir)
        return True

    def cleanup_old_runs(
        self, max_age_days: int = 30, max_runs: int | None = None
    ) -> int:
        """Clean up old runs.

        Args:
            max_age_days: Delete runs older than this many days
            max_runs: Keep only this many recent runs per type

        Returns:
            Number of runs deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0

        # Clean up agent runs
        agent_runs = self.list_agent_runs(RunQuery(limit=10000))
        if max_runs and len(agent_runs) > max_runs:
            # Delete oldest runs beyond max_runs
            for metadata in agent_runs[max_runs:]:
                if self.delete_run(metadata.run_id, "agent"):
                    deleted_count += 1

        # Delete runs older than cutoff
        for metadata in agent_runs:
            if metadata.started_at < cutoff_date:
                if self.delete_run(metadata.run_id, "agent"):
                    deleted_count += 1

        # Clean up workflow runs
        workflow_runs = self.list_workflow_runs(RunQuery(limit=10000))
        if max_runs and len(workflow_runs) > max_runs:
            for metadata in workflow_runs[max_runs:]:
                if self.delete_run(metadata.run_id, "workflow"):
                    deleted_count += 1

        for metadata in workflow_runs:
            if metadata.started_at < cutoff_date:
                if self.delete_run(metadata.run_id, "workflow"):
                    deleted_count += 1

        return deleted_count


# Global instance
_run_storage: RunStorage | None = None


def get_run_storage() -> RunStorage:
    """Get global run storage instance."""
    global _run_storage
    if _run_storage is None:
        _run_storage = RunStorage()
    return _run_storage


def set_run_storage(storage: RunStorage) -> None:
    """Set global run storage instance (primarily for testing).

    Args:
        storage: RunStorage instance to use
    """
    global _run_storage
    _run_storage = storage
