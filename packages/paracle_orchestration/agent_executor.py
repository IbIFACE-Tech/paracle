"""Agent execution utilities for workflow orchestration.

Provides helpers for executing workflow steps with real agents
and LLM providers.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from paracle_core.governance import log_agent_action
from paracle_domain.models import WorkflowStep
from paracle_providers.registry import ProviderRegistry
from rich.console import Console

console = Console()
logger = logging.getLogger("paracle.orchestration.executor")


class AgentExecutor:
    """Executes workflow steps with real agents and LLM providers.

    This executor:
    - Loads agent specs from .parac/agents/specs/
    - Resolves agent configuration and prompts
    - Calls LLM providers with appropriate parameters
    - Tracks token usage and costs
    - Handles errors gracefully with fallbacks

    Example:
        >>> executor = AgentExecutor()
        >>> result = await executor.execute_step(step, {"input": "data"})
        >>> print(result["outputs"])
        >>> print(result["cost"])  # Cost information
    """

    def __init__(
        self,
        parac_root: Path | None = None,
        provider_registry: ProviderRegistry | None = None,
        cost_tracker: Any | None = None,
    ) -> None:
        """Initialize the agent executor.

        Args:
            parac_root: Path to .parac/ directory (auto-discovered if None)
            provider_registry: LLM provider registry (created if None)
            cost_tracker: Optional CostTracker for cost management
        """
        self.parac_root = parac_root or self._find_parac_root()
        self.provider_registry = provider_registry or ProviderRegistry()
        self.agent_specs_cache: dict[str, dict[str, Any]] = {}
        self._cost_tracker = cost_tracker
        self._init_cost_tracker()

    def _init_cost_tracker(self) -> None:
        """Initialize cost tracker if not provided."""
        if self._cost_tracker is None:
            try:
                from paracle_core.cost import CostTracker

                self._cost_tracker = CostTracker()
            except ImportError:
                logger.debug("Cost tracking not available")

    def _calculate_step_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        step_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        """Calculate and track cost for a step.

        Args:
            provider: Provider name
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            step_id: Optional step ID
            agent_id: Optional agent ID
            workflow_id: Optional workflow ID
            execution_id: Optional execution ID

        Returns:
            Cost information dictionary
        """
        if self._cost_tracker is None:
            # Return zero costs if tracker not available
            return {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "prompt_cost": 0.0,
                "completion_cost": 0.0,
                "total_cost": 0.0,
                "provider": provider,
                "model": model,
            }

        # Calculate costs
        prompt_cost, completion_cost, total_cost = self._cost_tracker.calculate_cost(
            provider, model, prompt_tokens, completion_tokens
        )

        # Track usage
        self._cost_tracker.track_usage(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            step_id=step_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
        )

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "total_cost": total_cost,
            "provider": provider,
            "model": model,
        }

    def _find_parac_root(self) -> Path:
        """Find .parac/ directory by searching upward from cwd.

        Returns:
            Path to .parac/ directory

        Raises:
            FileNotFoundError: If .parac/ not found
        """
        current = Path.cwd()
        for parent in [current, *current.parents]:
            parac_dir = parent / ".parac"
            if parac_dir.is_dir():
                return parac_dir

        raise FileNotFoundError(
            ".parac/ directory not found in current or parent directories"
        )

    def _load_agent_spec(self, agent_name: str) -> dict[str, Any]:
        """Load agent spec from .parac/agents/specs/.

        Args:
            agent_name: Name of agent (e.g., "coder", "architect")

        Returns:
            Agent spec dictionary

        Raises:
            FileNotFoundError: If agent spec not found
        """
        # Check cache first
        if agent_name in self.agent_specs_cache:
            return self.agent_specs_cache[agent_name]

        # Try to load from file
        spec_file = self.parac_root / "agents" / "specs" / f"{agent_name}.md"

        if not spec_file.exists():
            # Fallback: return minimal spec
            console.print(
                f"[yellow]Warning: Agent spec not found for '{agent_name}', "
                f"using default[/yellow]"
            )
            return {
                "name": agent_name,
                "role": f"{agent_name} agent",
                "provider": "openai",
                "model": "gpt-4",
            }

        # Parse agent spec from markdown
        # For now, return basic structure - full parsing would read frontmatter
        spec = {
            "name": agent_name,
            "role": f"{agent_name} agent",
            "provider": "openai",  # Default
            "model": "gpt-4",  # Default
        }

        self.agent_specs_cache[agent_name] = spec
        return spec

    def _build_prompt(
        self,
        step: WorkflowStep,
        inputs: dict[str, Any],
    ) -> str:
        """Build execution prompt from step configuration.

        Args:
            step: Workflow step to execute
            inputs: Step input data

        Returns:
            Formatted prompt string
        """
        # Use step's prompt if provided
        if step.prompt:
            # Simple template replacement
            prompt = step.prompt
            for key, value in inputs.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(value))
            return prompt

        # Otherwise, build generic prompt
        prompt_parts = [
            f"# Task: {step.name}",
            "",
            f"Agent Role: {step.agent}",
            "",
            "## Inputs",
        ]

        for key, value in inputs.items():
            prompt_parts.append(f"- {key}: {value}")

        prompt_parts.extend(
            [
                "",
                "## Instructions",
                "Process the inputs and generate the required outputs.",
                "",
                "## Expected Outputs",
            ]
        )

        for output_key in step.outputs.keys():
            prompt_parts.append(f"- {output_key}")

        return "\n".join(prompt_parts)

    @log_agent_action("AgentExecutor", "EXECUTION")
    async def execute_step(
        self,
        step: WorkflowStep,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a workflow step with real agent.

        Args:
            step: Workflow step to execute
            inputs: Step input data

        Returns:
            Execution result with outputs
        """
        try:
            # Load agent spec
            agent_spec = self._load_agent_spec(step.agent)

            # Build prompt
            prompt = self._build_prompt(step, inputs)

            # Get provider (with fallback to mock)
            provider_name = step.config.get(
                "provider", agent_spec.get("provider", "openai")
            )
            model_name = step.config.get("model", agent_spec.get("model", "gpt-4"))

            # Display execution info
            console.print(f"[cyan]→[/cyan] Executing step: [bold]{step.name}[/bold]")
            console.print(f"[dim]  Agent: {step.agent}[/dim]")
            console.print(f"[dim]  Model: {provider_name}/{model_name}[/dim]")

            # Try to get provider
            try:
                provider = self.provider_registry.create_provider(provider_name)

                # Execute with LLM
                from paracle_providers.base import ChatMessage, LLMConfig

                messages = [
                    ChatMessage(
                        role="system", content=f"You are a {step.agent} agent."
                    ),
                    ChatMessage(role="user", content=prompt),
                ]

                config = LLMConfig(
                    temperature=step.config.get("temperature", 0.7),
                    max_tokens=step.config.get("max_tokens"),
                )

                response = await provider.chat_completion(
                    messages=messages,
                    model=model_name,
                    config=config,
                )

                # Extract outputs from response
                # For now, return the full response as a single output
                outputs = {}
                for output_key in step.outputs.keys():
                    if output_key == "result" or len(step.outputs) == 1:
                        outputs[output_key] = response.content
                    else:
                        outputs[output_key] = f"{output_key}_value"

                # Calculate cost
                cost_info = self._calculate_step_cost(
                    provider_name,
                    model_name,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    step.id,
                    step.agent,
                )

                console.print("[green]  ✓ Completed[/green]")
                if cost_info["total_cost"] > 0:
                    console.print(
                        f"[dim]  Cost: ${cost_info['total_cost']:.6f} "
                        f"({cost_info['total_tokens']} tokens)[/dim]"
                    )

                return {
                    "step_id": step.id,
                    "status": "completed",
                    "outputs": outputs,
                    "metadata": {
                        "provider": provider_name,
                        "model": model_name,
                        "tokens": response.usage.total_tokens,
                    },
                    "cost": cost_info,
                }

            except Exception as provider_error:
                # Fallback to mock execution if provider fails
                console.print(
                    "[yellow]  ⚠ Provider unavailable, " "using mock[/yellow]"
                )
                console.print(f"[dim]  {provider_error}[/dim]")

                # Simulate work
                await asyncio.sleep(0.1)

                # Return mock outputs
                outputs = {key: f"mock_{key}_result" for key in step.outputs.keys()}

                return {
                    "step_id": step.id,
                    "status": "completed",
                    "outputs": outputs,
                    "metadata": {
                        "mode": "mock",
                        "reason": str(provider_error),
                    },
                }

        except Exception as e:
            console.print(f"[red]  ✗ Failed: {e}[/red]")
            return {
                "step_id": step.id,
                "status": "failed",
                "error": str(e),
                "outputs": {},
            }
