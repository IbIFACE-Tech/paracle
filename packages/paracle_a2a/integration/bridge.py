"""A2A-Paracle Bridge.

Maps between A2A protocol concepts and Paracle execution model.
"""

from typing import Any

from paracle_a2a.models import (
    Artifact,
    Message,
    Task,
    TaskState,
    TextPart,
    create_artifact,
    create_message,
    get_message_text,
)


class A2AParacleBridge:
    """Bridges A2A and Paracle execution models.

    Maps between:
    - A2A Task states <-> Paracle ExecutionStatus
    - A2A Messages <-> Paracle context/prompts
    - A2A Artifacts <-> Paracle outputs
    """

    # State mapping: A2A -> Paracle (SDK uses lowercase enum values)
    A2A_TO_PARACLE_STATUS = {
        TaskState.submitted: "PENDING",
        TaskState.working: "RUNNING",
        TaskState.input_required: "AWAITING_APPROVAL",
        TaskState.auth_required: "AWAITING_APPROVAL",
        TaskState.completed: "COMPLETED",
        TaskState.failed: "FAILED",
        TaskState.canceled: "CANCELLED",  # SDK uses 'canceled' (US spelling)
        TaskState.rejected: "FAILED",
    }

    # State mapping: Paracle -> A2A
    PARACLE_TO_A2A_STATUS = {
        "PENDING": TaskState.submitted,
        "RUNNING": TaskState.working,
        "AWAITING_APPROVAL": TaskState.input_required,
        "COMPLETED": TaskState.completed,
        "FAILED": TaskState.failed,
        "CANCELLED": TaskState.canceled,
    }

    @classmethod
    def a2a_state_to_paracle(cls, state: TaskState) -> str:
        """Convert A2A TaskState to Paracle status.

        Args:
            state: A2A task state

        Returns:
            Paracle execution status string
        """
        return cls.A2A_TO_PARACLE_STATUS.get(state, "PENDING")

    @classmethod
    def paracle_status_to_a2a(cls, status: str) -> TaskState:
        """Convert Paracle status to A2A TaskState.

        Args:
            status: Paracle execution status

        Returns:
            A2A TaskState
        """
        return cls.PARACLE_TO_A2A_STATUS.get(status.upper(), TaskState.submitted)

    @classmethod
    def messages_to_prompt(cls, messages: list[Message]) -> str:
        """Convert A2A messages to prompt string.

        Args:
            messages: List of A2A messages

        Returns:
            Formatted prompt string
        """
        parts = []
        for msg in messages:
            role = msg.role
            text = get_message_text(msg)
            if text:
                parts.append(f"[{role}]: {text}")
        return "\n\n".join(parts)

    @classmethod
    def prompt_to_message(
        cls,
        prompt: str,
        role: str = "user",
    ) -> Message:
        """Convert prompt string to A2A message.

        Args:
            prompt: Prompt string
            role: Message role

        Returns:
            A2A Message
        """
        return create_message(prompt, role=role)

    @classmethod
    def result_to_artifact(
        cls,
        result: Any,
        name: str = "output",
        artifact_type: str = "text",
    ) -> Artifact:
        """Convert execution result to A2A artifact.

        Args:
            result: Execution result
            name: Artifact name
            artifact_type: Artifact type

        Returns:
            A2A Artifact
        """
        from paracle_a2a.models import create_data_artifact

        if isinstance(result, str):
            return create_artifact(result, name=name)
        elif isinstance(result, dict):
            # Structured result
            return create_data_artifact(result, name=name)
        else:
            # Convert to string
            return create_artifact(str(result), name=name)

    @classmethod
    def artifact_to_result(cls, artifact: Artifact) -> Any:
        """Convert A2A artifact to result.

        Args:
            artifact: A2A Artifact

        Returns:
            Result value
        """
        from paracle_a2a.models import DataPart

        # Check for data parts
        for part in artifact.parts:
            if isinstance(part, DataPart):
                return part.data

        # Fall back to text
        texts = []
        for part in artifact.parts:
            if isinstance(part, TextPart):
                texts.append(part.text)
        return "\n".join(texts)

    @classmethod
    def task_to_execution_context(cls, task: Task) -> dict[str, Any]:
        """Convert A2A task to Paracle execution context dict.

        Args:
            task: A2A Task

        Returns:
            Dictionary suitable for ExecutionContext
        """
        # SDK Task doesn't have session_id, it's stored in metadata
        session_id = (task.metadata or {}).get("session_id")
        return {
            "a2a_task_id": task.id,
            "a2a_context_id": task.context_id,
            "a2a_session_id": session_id,
            "a2a_status": task.status.state.value,
            "metadata": task.metadata,
        }

    @classmethod
    def execution_result_to_task_update(
        cls,
        result: Any,
        success: bool = True,
        error: str | None = None,
    ) -> tuple[TaskState, str | None, dict[str, Any] | None]:
        """Convert execution result to task update params.

        Args:
            result: Execution result
            success: Whether execution succeeded
            error: Optional error message

        Returns:
            Tuple of (state, message, error_dict)
        """
        if success:
            return (TaskState.completed, "Execution completed", None)
        else:
            return (
                TaskState.failed,
                error or "Execution failed",
                {"error": error} if error else None,
            )
