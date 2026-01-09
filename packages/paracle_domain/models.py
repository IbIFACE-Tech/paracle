"""Domain models for Paracle.

Core domain entities following DDD principles.
All models are pure Python with Pydantic validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{uuid4().hex[:12]}"


class EntityStatus(str, Enum):
    """Common status for entities."""

    PENDING = "pending"
    ACTIVE = "active"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ARCHIVED = "archived"


# =============================================================================
# Agent Models
# =============================================================================


class AgentSpec(BaseModel):
    """Specification of an agent.

    AgentSpec defines the configuration for an agent, including:
    - LLM provider and model settings
    - System prompt and behavior
    - Inheritance from parent agents
    - Tool configuration
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "code-reviewer",
                "description": "Reviews code for best practices",
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.3,
                "parent": "base-agent",
            }
        }
    )

    name: str = Field(..., description="Unique name of the agent")
    description: str | None = Field(None, description="Agent description")
    provider: str = Field(
        ..., description="LLM provider (openai, anthropic, google, ollama)"
    )
    model: str = Field(..., description="Model name (e.g., gpt-4, claude-3)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    system_prompt: str | None = Field(None, description="System prompt")
    parent: str | None = Field(None, description="Parent agent name for inheritance")
    tools: list[str] = Field(default_factory=list, description="List of tool names")
    skills: list[str] = Field(
        default_factory=list,
        description="List of skill IDs (from .parac/agents/skills/)",
    )
    config: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata (tags, labels, etc.)"
    )

    def has_parent(self) -> bool:
        """Check if agent has a parent."""
        return self.parent is not None


class AgentStatus(BaseModel):
    """Runtime status of an agent."""

    phase: EntityStatus = Field(default=EntityStatus.PENDING)
    message: str | None = None
    error: str | None = None
    last_run: datetime | None = None
    run_count: int = Field(default=0, ge=0)
    last_updated: datetime = Field(default_factory=utc_now)


class Agent(BaseModel):
    """Agent instance.

    An Agent is a runtime instance created from an AgentSpec.
    It tracks execution status and maintains state.
    """

    id: str = Field(default_factory=lambda: generate_id("agent"))
    spec: AgentSpec
    resolved_spec: AgentSpec | None = Field(
        None, description="Spec after inheritance resolution"
    )
    status: AgentStatus = Field(default_factory=AgentStatus)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    def get_effective_spec(self) -> AgentSpec:
        """Get the effective spec (resolved or original)."""
        return self.resolved_spec if self.resolved_spec else self.spec

    def update_status(
        self,
        phase: EntityStatus | None = None,
        message: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update agent status."""
        if phase:
            self.status.phase = phase
        if message:
            self.status.message = message
        if error:
            self.status.error = error
        self.status.last_updated = utc_now()
        self.updated_at = utc_now()


# =============================================================================
# Workflow Models
# =============================================================================


class WorkflowStep(BaseModel):
    """A step in a workflow."""

    id: str = Field(..., description="Step identifier")
    name: str = Field(..., description="Step name")
    agent: str = Field(..., description="Agent name to execute")
    prompt: str | None = Field(None, description="Prompt template")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input mappings")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output mappings")
    depends_on: list[str] = Field(default_factory=list, description="Step dependencies")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Step configuration"
    )
    # Human-in-the-Loop approval (ISO 42001)
    requires_approval: bool = Field(
        default=False, description="Require human approval after step execution"
    )
    approval_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Approval configuration (approvers, timeout, priority)",
    )


class WorkflowSpec(BaseModel):
    """Specification of a workflow."""

    name: str = Field(..., description="Workflow name")
    description: str | None = Field(None, description="Workflow description")
    steps: list[WorkflowStep] = Field(..., description="Workflow steps")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Workflow inputs")
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="Workflow outputs"
    )
    config: dict[str, Any] = Field(
        default_factory=dict, description="Workflow configuration"
    )


class WorkflowStatus(BaseModel):
    """Status of workflow execution."""

    phase: EntityStatus = Field(default=EntityStatus.PENDING)
    current_step: str | None = None
    completed_steps: list[str] = Field(default_factory=list)
    failed_steps: list[str] = Field(default_factory=list)
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    results: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class Workflow(BaseModel):
    """Workflow instance."""

    id: str = Field(default_factory=lambda: generate_id("workflow"))
    spec: WorkflowSpec
    status: WorkflowStatus = Field(default_factory=WorkflowStatus)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    def start(self) -> None:
        """Mark workflow as started."""
        self.status.phase = EntityStatus.RUNNING
        self.status.started_at = utc_now()
        self.updated_at = utc_now()

    def complete(self, results: dict[str, Any] | None = None) -> None:
        """Mark workflow as completed."""
        self.status.phase = EntityStatus.SUCCEEDED
        self.status.progress = 100.0
        self.status.completed_at = utc_now()
        if results:
            self.status.results = results
        self.updated_at = utc_now()

    def fail(self, error: str) -> None:
        """Mark workflow as failed."""
        self.status.phase = EntityStatus.FAILED
        self.status.error = error
        self.status.completed_at = utc_now()
        self.updated_at = utc_now()


# =============================================================================
# Tool Models
# =============================================================================


class ToolSpec(BaseModel):
    """Specification of a tool."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for parameters"
    )
    returns: dict[str, Any] = Field(
        default_factory=dict, description="Return type schema"
    )
    is_mcp: bool = Field(default=False, description="Is MCP tool")
    mcp_server: str | None = Field(None, description="MCP server URI")


class Tool(BaseModel):
    """Tool instance."""

    id: str = Field(default_factory=lambda: generate_id("tool"))
    spec: ToolSpec
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()


# =============================================================================
# Human-in-the-Loop Approval Models (ISO 42001 Compliance)
# =============================================================================


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalPriority(str, Enum):
    """Priority level for approval requests."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalConfig(BaseModel):
    """Configuration for step approval requirements.

    Defines when and how human approval is needed for a workflow step.
    Supports ISO 42001 requirements for human oversight of AI decisions.
    """

    required: bool = Field(
        default=False, description="Whether approval is required for this step"
    )
    approvers: list[str] = Field(
        default_factory=list,
        description="List of user/role IDs who can approve (empty = any)",
    )
    timeout_seconds: int = Field(
        default=3600, ge=60, description="Approval timeout (default 1 hour)"
    )
    priority: ApprovalPriority = Field(
        default=ApprovalPriority.MEDIUM, description="Priority for approval queue"
    )
    auto_reject_on_timeout: bool = Field(
        default=False, description="Auto-reject if timeout expires"
    )
    reason_required: bool = Field(
        default=False, description="Require reason for approval/rejection"
    )
    notify_channels: list[str] = Field(
        default_factory=list,
        description="Notification channels (email, slack, webhook)",
    )


class ApprovalRequest(BaseModel):
    """Request for human approval of a workflow step.

    Created when a workflow reaches a step that requires approval.
    The workflow pauses until approval is granted or denied.

    Example:
        >>> request = ApprovalRequest(
        ...     workflow_id="wf_123",
        ...     execution_id="exec_456",
        ...     step_id="review",
        ...     step_name="Code Review",
        ...     context={
        ...         "code": "def hello(): pass",
        ...         "analysis": "No issues found"
        ...     },
        ... )
    """

    id: str = Field(default_factory=lambda: generate_id("approval"))
    workflow_id: str = Field(..., description="Workflow requesting approval")
    execution_id: str = Field(..., description="Execution ID within workflow")
    step_id: str = Field(..., description="Step ID requiring approval")
    step_name: str = Field(..., description="Human-readable step name")
    agent_name: str = Field(..., description="Agent that produced the output")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Context for approval decision (step output, inputs)",
    )
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    priority: ApprovalPriority = Field(default=ApprovalPriority.MEDIUM)
    config: ApprovalConfig = Field(default_factory=ApprovalConfig)
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = Field(None, description="When approval expires")
    decided_at: datetime | None = Field(None, description="When decision was made")
    decided_by: str | None = Field(None, description="Who approved/rejected")
    decision_reason: str | None = Field(None, description="Reason for decision")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def approve(self, approver: str, reason: str | None = None) -> None:
        """Approve the request."""
        self.status = ApprovalStatus.APPROVED
        self.decided_at = utc_now()
        self.decided_by = approver
        self.decision_reason = reason

    def reject(self, approver: str, reason: str | None = None) -> None:
        """Reject the request."""
        self.status = ApprovalStatus.REJECTED
        self.decided_at = utc_now()
        self.decided_by = approver
        self.decision_reason = reason

    def expire(self) -> None:
        """Mark as expired due to timeout."""
        self.status = ApprovalStatus.EXPIRED
        self.decided_at = utc_now()

    def cancel(self) -> None:
        """Cancel the approval request (workflow cancelled)."""
        self.status = ApprovalStatus.CANCELLED
        self.decided_at = utc_now()

    @property
    def is_pending(self) -> bool:
        """Check if still awaiting decision."""
        return self.status == ApprovalStatus.PENDING

    @property
    def is_decided(self) -> bool:
        """Check if decision has been made."""
        return self.status in {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.EXPIRED,
            ApprovalStatus.CANCELLED,
        }

    @property
    def is_approved(self) -> bool:
        """Check if approved."""
        return self.status == ApprovalStatus.APPROVED


# =============================================================================
# Retry Models
# =============================================================================


class BackoffStrategy(str, Enum):
    """Backoff strategy for retries."""

    CONSTANT = "constant"  # Same delay between retries
    LINEAR = "linear"  # Linearly increasing delay
    EXPONENTIAL = "exponential"  # Exponentially increasing delay
    FIBONACCI = "fibonacci"  # Fibonacci sequence delay


class ErrorCategory(str, Enum):
    """Error categories for conditional retry."""

    TRANSIENT = "transient"  # Temporary errors (network, rate limit)
    TIMEOUT = "timeout"  # Timeout errors
    VALIDATION = "validation"  # Validation errors (retry with different input)
    RESOURCE = "resource"  # Resource errors (out of memory, quota)
    PERMANENT = "permanent"  # Permanent errors (don't retry)
    UNKNOWN = "unknown"  # Unknown errors (retry with caution)


class RetryCondition(BaseModel):
    """Condition for when to retry.

    Attributes:
        error_types: List of error types that should trigger retry
        error_categories: List of error categories that should trigger retry
        status_codes: List of HTTP status codes that should trigger retry
        error_messages: List of error message patterns (regex) that
            should trigger retry
    """

    error_types: list[str] = Field(default_factory=list)
    error_categories: list[ErrorCategory] = Field(default_factory=list)
    status_codes: list[int] = Field(default_factory=list)
    error_messages: list[str] = Field(default_factory=list)


class RetryPolicy(BaseModel):
    """Retry policy for workflow steps.

    Defines how a workflow step should be retried on failure,
    including max attempts, backoff strategy, and retry conditions.

    Example:
        ```python
        policy = RetryPolicy(
            max_attempts=3,
            backoff_strategy=BackoffStrategy.EXPONENTIAL,
            initial_delay=1.0,
            max_delay=60.0,
            retry_condition=RetryCondition(
                error_categories=[
                    ErrorCategory.TRANSIENT,
                    ErrorCategory.TIMEOUT
                ]
            ),
        )
        ```

    Attributes:
        enabled: Whether retry is enabled
        max_attempts: Maximum number of retry attempts
        backoff_strategy: Strategy for calculating delay between retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for exponential backoff
        retry_condition: Conditions that must be met to retry
        accumulate_context: Whether to accumulate context across attempts
        timeout_per_attempt: Optional timeout for each attempt
    """

    enabled: bool = True
    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    initial_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    max_delay: float = Field(default=60.0, ge=1.0, le=3600.0)
    backoff_factor: float = Field(default=2.0, ge=1.0, le=10.0)
    retry_condition: RetryCondition = Field(default_factory=RetryCondition)
    accumulate_context: bool = True
    timeout_per_attempt: float | None = None

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number.

        Args:
            attempt: Attempt number (1-based)

        Returns:
            Delay in seconds
        """
        if self.backoff_strategy == BackoffStrategy.CONSTANT:
            delay = self.initial_delay

        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.initial_delay * attempt

        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))

        elif self.backoff_strategy == BackoffStrategy.FIBONACCI:
            # Generate Fibonacci number for attempt
            if attempt <= 2:
                fib = 1
            else:
                a, b = 1, 1
                for _ in range(attempt - 2):
                    a, b = b, a + b
                fib = b
            delay = self.initial_delay * fib

        else:
            delay = self.initial_delay

        # Cap at max_delay
        return min(delay, self.max_delay)

    def should_retry(
        self,
        attempt: int,
        error: Exception,
        error_category: ErrorCategory = ErrorCategory.UNKNOWN,
    ) -> bool:
        """Determine if we should retry based on attempt count and error.

        Args:
            attempt: Current attempt number (1-based)
            error: The exception that occurred
            error_category: Category of the error

        Returns:
            True if should retry, False otherwise
        """
        # Check if retry is enabled
        if not self.enabled:
            return False

        # Check if we've exceeded max attempts
        if attempt >= self.max_attempts:
            return False

        # Check retry conditions
        condition = self.retry_condition

        # If no conditions specified, retry all errors
        if (
            not condition.error_types
            and not condition.error_categories
            and not condition.status_codes
            and not condition.error_messages
        ):
            return True

        # Check error type
        error_type_name = type(error).__name__
        if condition.error_types and error_type_name in condition.error_types:
            return True

        # Check error category
        if condition.error_categories and error_category in condition.error_categories:
            return True

        # Check status code (if error has one)
        if condition.status_codes and hasattr(error, "status_code"):
            if error.status_code in condition.status_codes:
                return True

        # Check error message patterns
        if condition.error_messages:
            error_message = str(error).lower()
            for pattern in condition.error_messages:
                if pattern.lower() in error_message:
                    return True

        return False


class RetryAttempt(BaseModel):
    """Record of a retry attempt.

    Attributes:
        attempt_number: Attempt number (1-based)
        started_at: When attempt started
        ended_at: When attempt ended
        error: Error message if attempt failed
        error_type: Type of error that occurred
        error_category: Category of error
        delay_before: Delay before this attempt (seconds)
        context: Context accumulated for this attempt
    """

    attempt_number: int
    started_at: datetime
    ended_at: datetime | None = None
    error: str | None = None
    error_type: str | None = None
    error_category: ErrorCategory = ErrorCategory.UNKNOWN
    delay_before: float = 0.0
    context: dict[str, Any] = Field(default_factory=dict)


class RetryContext(BaseModel):
    """Context for retry execution.

    Tracks all retry attempts and accumulated context across attempts.

    Attributes:
        step_name: Name of the step being retried
        workflow_id: ID of the workflow
        execution_id: ID of the execution
        policy: Retry policy being used
        attempts: List of all retry attempts
        accumulated_context: Context accumulated across attempts
        total_retries: Total number of retries performed
        succeeded: Whether the step eventually succeeded
    """

    step_name: str
    workflow_id: str
    execution_id: str
    policy: RetryPolicy
    attempts: list[RetryAttempt] = Field(default_factory=list)
    accumulated_context: dict[str, Any] = Field(default_factory=dict)
    total_retries: int = 0
    succeeded: bool = False

    def add_attempt(
        self,
        attempt_number: int,
        started_at: datetime,
        error: Exception | None = None,
        error_category: ErrorCategory = ErrorCategory.UNKNOWN,
        delay_before: float = 0.0,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Add a retry attempt to the context.

        Args:
            attempt_number: Attempt number (1-based)
            started_at: When attempt started
            error: Error that occurred (None if successful)
            error_category: Category of error
            delay_before: Delay before this attempt
            context: Context for this attempt
        """
        attempt = RetryAttempt(
            attempt_number=attempt_number,
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
            error=str(error) if error else None,
            error_type=type(error).__name__ if error else None,
            error_category=error_category,
            delay_before=delay_before,
            context=context or {},
        )
        self.attempts.append(attempt)
        # First attempt is not a retry
        self.total_retries = len(self.attempts) - 1

        # Accumulate context if enabled
        if self.policy.accumulate_context and context:
            self.accumulated_context.update(context)

        # Mark as succeeded if no error
        if error is None:
            self.succeeded = True
