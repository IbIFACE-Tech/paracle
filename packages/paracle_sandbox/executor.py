"""Sandbox executor for agent execution integration."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from paracle_sandbox.config import SandboxConfig
from paracle_sandbox.exceptions import SandboxExecutionError
from paracle_sandbox.manager import SandboxManager
from paracle_sandbox.monitor import SandboxMonitor

logger = logging.getLogger(__name__)


class SandboxExecutor:
    """High-level executor for running agents in sandboxes.

    Provides simplified interface for agent execution with automatic
    monitoring, rollback on failure, and resource management.

    Example:
        ```python
        executor = SandboxExecutor()

        result = await executor.execute_agent(
            agent_code="print('Hello from sandbox')",
            config=SandboxConfig(cpu_cores=1.0, memory_mb=512)
        )
        ```
    """

    def __init__(self, manager: SandboxManager | None = None):
        """Initialize sandbox executor.

        Args:
            manager: SandboxManager instance (creates default if None)
        """
        self.manager = manager or SandboxManager()

    async def execute_agent(
        self,
        agent_code: str | Path,
        config: SandboxConfig | None = None,
        inputs: dict[str, Any] | None = None,
        monitor: bool = True,
        rollback_on_error: bool = True,
    ) -> dict[str, Any]:
        """Execute agent code in sandbox.

        Args:
            agent_code: Python code or path to script
            config: Sandbox configuration (uses defaults if None)
            inputs: Input data for agent
            monitor: Enable resource monitoring
            rollback_on_error: Clean up sandbox on failure

        Returns:
            Dict with keys:
                success: bool
                result: execution result
                stats: resource usage stats
                error: error message (if failed)

        Raises:
            SandboxExecutionError: If execution fails critically
        """
        config = config or SandboxConfig()
        inputs = inputs or {}

        sandbox = None
        monitor_task = None

        try:
            # Create sandbox
            sandbox = await self.manager.create(config)
            logger.info(
                f"Created sandbox {sandbox.sandbox_id} for agent execution")

            # Start monitoring if enabled
            if monitor:
                sandbox_monitor = SandboxMonitor(sandbox)
                monitor_task = asyncio.create_task(sandbox_monitor.start())

            # Prepare agent code
            if isinstance(agent_code, Path):
                code_path = agent_code
                if not code_path.exists():
                    raise SandboxExecutionError(
                        f"Agent code file not found: {code_path}",
                        sandbox.sandbox_id,
                    )
                agent_code = code_path.read_text()

            # Write code to sandbox working directory
            code_filename = "agent_code.py"
            write_cmd = [
                "sh",
                "-c",
                f'cat > {config.working_dir}/{code_filename} << "EOF"\n{agent_code}\nEOF',
            ]
            await sandbox.execute(write_cmd)

            # Write inputs as JSON
            if inputs:
                import json

                inputs_json = json.dumps(inputs, indent=2)
                inputs_filename = "inputs.json"
                write_inputs_cmd = [
                    "sh",
                    "-c",
                    f'cat > {config.working_dir}/{inputs_filename} << "EOF"\n{inputs_json}\nEOF',
                ]
                await sandbox.execute(write_inputs_cmd)

            # Execute agent code
            exec_cmd = [
                "python3",
                f"{config.working_dir}/{code_filename}",
            ]
            result = await sandbox.execute(exec_cmd, timeout=config.timeout_seconds)

            # Get resource stats
            stats = await sandbox.get_stats()
            if monitor and monitor_task:
                # Stop monitoring
                await monitor_task
                # Get monitoring history
                stats["monitoring"] = {
                    "averages": sandbox_monitor.get_averages(),
                    "peaks": sandbox_monitor.get_peaks(),
                    "history_samples": len(sandbox_monitor.get_history()),
                }

            # Check if execution was successful
            success = result["exit_code"] == 0 and not result["timed_out"]

            response = {
                "success": success,
                "result": {
                    "exit_code": result["exit_code"],
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "timed_out": result["timed_out"],
                },
                "stats": stats,
                "sandbox_id": sandbox.sandbox_id,
            }

            if not success:
                response["error"] = (
                    result["stderr"]
                    if result["stderr"]
                    else f"Execution failed with exit code {result['exit_code']}"
                )
                logger.warning(
                    f"Agent execution failed in {sandbox.sandbox_id}: {response['error']}"
                )

            return response

        except Exception as e:
            logger.error(f"Agent execution error: {e}")

            error_response = {
                "success": False,
                "error": str(e),
                "sandbox_id": sandbox.sandbox_id if sandbox else None,
            }

            if rollback_on_error:
                # Clean up sandbox on error
                if sandbox:
                    await self.manager.destroy(sandbox.sandbox_id)
                    logger.info(f"Rolled back sandbox {sandbox.sandbox_id}")

            return error_response

        finally:
            # Clean up monitor task
            if monitor_task and not monitor_task.done():
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

            # Destroy sandbox
            if sandbox:
                await self.manager.destroy(sandbox.sandbox_id)

    async def execute_batch(
        self,
        jobs: list[dict[str, Any]],
        config: SandboxConfig | None = None,
        max_concurrent: int | None = None,
    ) -> list[dict[str, Any]]:
        """Execute multiple agent jobs in parallel sandboxes.

        Args:
            jobs: List of job dicts with keys: agent_code, inputs
            config: Default sandbox configuration
            max_concurrent: Max concurrent sandboxes (uses manager limit if None)

        Returns:
            List of execution results

        Example:
            ```python
            jobs = [
                {"agent_code": "print('Job 1')", "inputs": {"id": 1}},
                {"agent_code": "print('Job 2')", "inputs": {"id": 2}},
            ]
            results = await executor.execute_batch(jobs)
            ```
        """
        config = config or SandboxConfig()
        max_concurrent = max_concurrent or self.manager.max_concurrent

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(job: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await self.execute_agent(
                    agent_code=job["agent_code"],
                    config=config,
                    inputs=job.get("inputs"),
                    monitor=job.get("monitor", True),
                    rollback_on_error=job.get("rollback_on_error", True),
                )

        # Execute all jobs
        tasks = [execute_with_semaphore(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error dicts
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "success": False,
                        "error": str(result),
                        "job_index": i,
                    }
                )
            else:
                processed_results.append(result)

        return processed_results

    async def health_check(self) -> dict[str, Any]:
        """Check if sandbox execution is available.

        Tests Docker availability and basic sandbox functionality.

        Returns:
            Dict with keys:
            - available: bool
            - docker_available: bool
            - test_passed: bool
            - error: str (if not available)
        """
        try:
            import docker

            # Check Docker connection
            try:
                client = docker.from_env()
                client.ping()
                docker_available = True
                client.close()
            except Exception as e:
                return {
                    "available": False,
                    "docker_available": False,
                    "error": f"Docker not available: {e}",
                }

            # Test basic sandbox creation
            test_config = SandboxConfig(
                cpu_cores=0.5,
                memory_mb=256,
                timeout_seconds=30,
            )

            test_result = await self.execute_agent(
                agent_code="print('Sandbox test OK')",
                config=test_config,
                monitor=False,
            )

            test_passed = test_result.get("success", False)

            return {
                "available": test_passed,
                "docker_available": docker_available,
                "test_passed": test_passed,
                "error": test_result.get("error") if not test_passed else None,
            }

        except ImportError:
            return {
                "available": False,
                "docker_available": False,
                "error": "Docker SDK not installed (pip install docker)",
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Health check failed: {e}",
            }
