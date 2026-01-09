"""RFC 7807 Problem Details for HTTP APIs.

Implements the Problem Details for HTTP APIs specification (RFC 7807/9457)
for standardized error responses across the Paracle API.

See: https://www.rfc-editor.org/rfc/rfc7807
"""

from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from paracle_core.logging import get_logger
from paracle_domain.inheritance import (
    CircularInheritanceError,
    InheritanceError,
    MaxDepthExceededError,
    ParentNotFoundError,
)
from paracle_orchestration.exceptions import (
    CircularDependencyError,
    ExecutionTimeoutError,
    InvalidWorkflowError,
    OrchestrationError,
    StepExecutionError,
    WorkflowNotFoundError,
)
from paracle_providers.exceptions import (
    LLMProviderError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderInvalidRequestError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class ProblemDetails(BaseModel):
    """RFC 7807 Problem Details response model.

    Attributes:
        type: URI reference identifying the problem type (default: about:blank)
        title: Short human-readable summary of the problem
        status: HTTP status code
        detail: Human-readable explanation specific to this occurrence
        instance: URI reference identifying the specific occurrence
        error_code: Paracle-specific error code (PARACLE-XXX-NNN)
        extensions: Additional problem-specific fields
    """

    type: str = Field(
        default="about:blank",
        description="URI reference identifying the problem type",
    )
    title: str = Field(description="Short human-readable summary")
    status: int = Field(description="HTTP status code")
    detail: str | None = Field(
        default=None,
        description="Explanation specific to this occurrence",
    )
    instance: str | None = Field(
        default=None,
        description="URI reference identifying the specific occurrence",
    )
    error_code: str | None = Field(
        default=None,
        description="Paracle error code (PARACLE-XXX-NNN)",
    )
    extensions: dict[str, Any] | None = Field(
        default=None,
        description="Additional problem-specific fields",
    )

    def to_response(self) -> JSONResponse:
        """Convert to FastAPI JSONResponse with proper content-type."""
        content = self.model_dump(exclude_none=True)
        # Move extensions to top level per RFC 7807
        if "extensions" in content and content["extensions"]:
            extensions = content.pop("extensions")
            content.update(extensions)
        return JSONResponse(
            status_code=self.status,
            content=content,
            media_type="application/problem+json",
        )


# =============================================================================
# Problem Details Factory Functions
# =============================================================================


def create_problem_details(
    request: Request,
    status_code: int,
    title: str,
    detail: str | None = None,
    error_code: str | None = None,
    extensions: dict[str, Any] | None = None,
    problem_type: str = "about:blank",
) -> ProblemDetails:
    """Create a ProblemDetails instance for an error response.

    Args:
        request: The FastAPI request object
        status_code: HTTP status code
        title: Short human-readable summary
        detail: Detailed explanation (optional)
        error_code: Paracle error code (optional)
        extensions: Additional fields (optional)
        problem_type: URI for problem type documentation

    Returns:
        ProblemDetails instance ready to be converted to response
    """
    return ProblemDetails(
        type=problem_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=str(request.url.path),
        error_code=error_code,
        extensions=extensions,
    )


# =============================================================================
# Exception to Problem Details Mapping
# =============================================================================


def provider_error_to_problem(
    request: Request,
    exc: LLMProviderError,
    is_production: bool = False,
) -> ProblemDetails:
    """Convert LLMProviderError to ProblemDetails."""
    status_code = status.HTTP_502_BAD_GATEWAY
    title = "LLM Provider Error"

    # Map specific provider errors to appropriate status codes
    if isinstance(exc, ProviderNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        title = "Provider Not Found"
    elif isinstance(exc, ProviderRateLimitError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        title = "Rate Limit Exceeded"
    elif isinstance(exc, ProviderTimeoutError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        title = "Provider Timeout"
    elif isinstance(exc, ProviderAuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
        title = "Provider Authentication Failed"
    elif isinstance(exc, ProviderInvalidRequestError):
        status_code = status.HTTP_400_BAD_REQUEST
        title = "Invalid Provider Request"
    elif isinstance(exc, ProviderConnectionError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        title = "Provider Unavailable"

    # Build extensions with context
    extensions: dict[str, Any] = {}
    if not is_production:
        if exc.provider:
            extensions["provider"] = exc.provider
        if exc.model:
            extensions["model"] = exc.model
        if isinstance(exc, ProviderRateLimitError) and exc.retry_after:
            extensions["retry_after"] = exc.retry_after
        if isinstance(exc, ProviderTimeoutError) and exc.timeout:
            extensions["timeout"] = exc.timeout

    return create_problem_details(
        request=request,
        status_code=status_code,
        title=title,
        detail=str(exc) if not is_production else None,
        error_code=exc.error_code,
        extensions=extensions if extensions else None,
    )


def orchestration_error_to_problem(
    request: Request,
    exc: OrchestrationError,
    is_production: bool = False,
) -> ProblemDetails:
    """Convert OrchestrationError to ProblemDetails."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    title = "Workflow Orchestration Error"

    # Map specific orchestration errors
    if isinstance(exc, CircularDependencyError):
        status_code = status.HTTP_400_BAD_REQUEST
        title = "Circular Dependency Detected"
    elif isinstance(exc, StepExecutionError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        title = "Workflow Step Failed"
    elif isinstance(exc, WorkflowNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        title = "Workflow Not Found"
    elif isinstance(exc, InvalidWorkflowError):
        status_code = status.HTTP_400_BAD_REQUEST
        title = "Invalid Workflow Definition"
    elif isinstance(exc, ExecutionTimeoutError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        title = "Workflow Execution Timeout"

    # Build extensions
    extensions: dict[str, Any] = {}
    if not is_production:
        if isinstance(exc, CircularDependencyError):
            extensions["cycle"] = exc.cycle
        elif isinstance(exc, StepExecutionError):
            extensions["step_id"] = exc.step_id
        elif isinstance(exc, WorkflowNotFoundError):
            extensions["workflow_id"] = exc.workflow_id
        elif isinstance(exc, InvalidWorkflowError):
            extensions["reason"] = exc.reason
        elif isinstance(exc, ExecutionTimeoutError):
            extensions["execution_id"] = exc.execution_id
            extensions["timeout_seconds"] = exc.timeout_seconds

    return create_problem_details(
        request=request,
        status_code=status_code,
        title=title,
        detail=str(exc) if not is_production else None,
        error_code=exc.error_code,
        extensions=extensions if extensions else None,
    )


def inheritance_error_to_problem(
    request: Request,
    exc: InheritanceError,
    is_production: bool = False,
) -> ProblemDetails:
    """Convert InheritanceError to ProblemDetails."""
    status_code = status.HTTP_400_BAD_REQUEST
    title = "Agent Inheritance Error"

    # Map specific inheritance errors
    if isinstance(exc, CircularInheritanceError):
        title = "Circular Inheritance Detected"
    elif isinstance(exc, MaxDepthExceededError):
        title = "Inheritance Depth Exceeded"
    elif isinstance(exc, ParentNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        title = "Parent Agent Not Found"

    # Build extensions
    extensions: dict[str, Any] = {}
    if not is_production:
        if isinstance(exc, CircularInheritanceError):
            extensions["chain"] = exc.chain
        elif isinstance(exc, MaxDepthExceededError):
            extensions["depth"] = exc.depth
            extensions["max_depth"] = exc.max_depth
            extensions["chain"] = exc.chain
        elif isinstance(exc, ParentNotFoundError):
            extensions["child"] = exc.child
            extensions["parent"] = exc.parent

    # Get error code if available
    error_code = getattr(exc, "error_code", None)

    return create_problem_details(
        request=request,
        status_code=status_code,
        title=title,
        detail=str(exc) if not is_production else None,
        error_code=error_code,
        extensions=extensions if extensions else None,
    )


def _serialize_validation_error(error: dict[str, Any]) -> dict[str, Any]:
    """Serialize a validation error dict to be JSON-serializable.

    Pydantic validation errors may contain non-serializable objects
    like ValueError instances in the 'ctx' field.
    """
    result = {}
    for key, value in error.items():
        if key == "ctx" and isinstance(value, dict):
            # Serialize context values to strings
            result[key] = {
                k: (
                    str(v)
                    if not isinstance(v, str | int | float | bool | type(None))
                    else v
                )
                for k, v in value.items()
            }
        elif isinstance(value, str | int | float | bool | type(None) | list | tuple):
            result[key] = value
        else:
            result[key] = str(value)
    return result


def validation_error_to_problem(
    request: Request,
    errors: list[Any],
) -> ProblemDetails:
    """Convert Pydantic validation errors to ProblemDetails."""
    # Serialize errors to ensure JSON compatibility
    serialized_errors = [
        _serialize_validation_error(e) if isinstance(e, dict) else str(e)
        for e in errors
    ]
    return create_problem_details(
        request=request,
        status_code=422,  # Using int instead of deprecated HTTP_422_UNPROCESSABLE_ENTITY
        title="Validation Error",
        detail="Request validation failed",
        error_code="PARACLE-API-001",
        extensions={"validation_errors": serialized_errors},
    )


def not_found_error_to_problem(
    request: Request,
    resource_type: str,
    resource_id: str,
) -> ProblemDetails:
    """Create ProblemDetails for resource not found errors."""
    detail = f"The requested {resource_type.lower()} '{resource_id}' was not found"
    extensions = {
        "resource_type": resource_type,
        "resource_id": resource_id,
    }
    return create_problem_details(
        request=request,
        status_code=status.HTTP_404_NOT_FOUND,
        title=f"{resource_type} Not Found",
        detail=detail,
        error_code="PARACLE-API-002",
        extensions=extensions,
    )


def internal_error_to_problem(
    request: Request,
    exc: Exception,
    is_production: bool = False,
) -> ProblemDetails:
    """Create ProblemDetails for unhandled internal errors."""
    detail = None if is_production else str(exc)
    extensions = None if is_production else {"exception_type": type(exc).__name__}

    return create_problem_details(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail=detail,
        error_code="PARACLE-API-000",
        extensions=extensions,
    )
