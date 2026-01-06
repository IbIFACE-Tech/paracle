"""Paracle API - FastAPI Application.

Main entry point for the Paracle REST API with comprehensive security.
Run with: uvicorn paracle_api.main:app --reload

Security Features:
- JWT Authentication with OAuth2
- Rate Limiting
- Security Headers (HSTS, CSP, X-Frame-Options, etc.)
- Secure CORS Configuration
- Input Validation
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from paracle_core.logging import create_request_logging_middleware, get_logger
from paracle_domain.inheritance import InheritanceError
from paracle_orchestration.exceptions import OrchestrationError
from paracle_providers.exceptions import LLMProviderError

from paracle_api.errors import (
    inheritance_error_to_problem,
    internal_error_to_problem,
    orchestration_error_to_problem,
    provider_error_to_problem,
    validation_error_to_problem,
)
from paracle_api.routers import (
    agent_crud_router,
    agents_router,
    approvals_router,
    health_router,
    ide_router,
    logs_router,
    parac_router,
    reviews_router,
    tool_crud_router,
    workflow_crud_router,
    workflow_execution_router,
)
from paracle_api.security.config import SecurityConfig, get_security_config
from paracle_api.security.headers import SecurityHeadersMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    config = get_security_config()

    # Validate production configuration
    if config.is_production():
        issues = config.validate_production_config()
        if issues:
            for issue in issues:
                logger.error(f"Security configuration issue: {issue}")
            raise RuntimeError(
                "Security configuration invalid for production. "
                f"Issues: {', '.join(issues)}"
            )

    # Initialize default users for development
    if not config.is_production():
        from paracle_api.security.auth import init_default_users
        init_default_users()
        logger.info("Development mode: initialized default users")

    logger.info("Paracle API started with security enabled")

    yield

    # Shutdown
    logger.info("Paracle API shutting down")


def create_app(config: SecurityConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config: Security configuration (uses default if not provided)

    Returns:
        Configured FastAPI application
    """
    if config is None:
        config = get_security_config()

    app = FastAPI(
        title="Paracle API",
        description="User-driven multi-agent framework API with enterprise security",
        version="0.0.1",
        docs_url="/docs" if not config.is_production() else None,
        redoc_url="/redoc" if not config.is_production() else None,
        openapi_url="/openapi.json" if not config.is_production() else None,
        lifespan=lifespan,
    )

    # =========================================================================
    # Security Middleware (order matters - first added = last executed)
    # =========================================================================

    # 1. Security Headers (outermost - runs last on response)
    app.add_middleware(SecurityHeadersMiddleware, config=config)

    # 2. CORS with secure configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allowed_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=config.cors_allowed_methods,
        allow_headers=config.cors_allowed_headers,
        expose_headers=["X-RateLimit-Limit",
                        "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

    # 3. Request logging middleware with correlation IDs
    app.add_middleware(create_request_logging_middleware())

    # =========================================================================
    # Global Exception Handlers (RFC 7807 Problem Details)
    # =========================================================================

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle Pydantic validation errors with Problem Details."""
        logger.warning(f"Validation error: {exc.errors()}")
        problem = validation_error_to_problem(request, exc.errors())
        return problem.to_response()

    @app.exception_handler(LLMProviderError)
    async def provider_exception_handler(request: Request, exc: LLMProviderError):
        """Handle LLM provider errors with Problem Details."""
        logger.error(f"Provider error: {exc}", exc_info=True)
        problem = provider_error_to_problem(
            request, exc, config.is_production())
        return problem.to_response()

    @app.exception_handler(OrchestrationError)
    async def orchestration_exception_handler(
        request: Request, exc: OrchestrationError
    ):
        """Handle orchestration errors with Problem Details."""
        logger.error(f"Orchestration error: {exc}", exc_info=True)
        problem = orchestration_error_to_problem(
            request, exc, config.is_production())
        return problem.to_response()

    @app.exception_handler(InheritanceError)
    async def inheritance_exception_handler(request: Request, exc: InheritanceError):
        """Handle inheritance errors with Problem Details."""
        logger.error(f"Inheritance error: {exc}", exc_info=True)
        problem = inheritance_error_to_problem(
            request, exc, config.is_production())
        return problem.to_response()

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions with Problem Details."""
        logger.exception(f"Unhandled exception: {exc}")
        problem = internal_error_to_problem(
            request, exc, config.is_production())
        return problem.to_response()

    # =========================================================================
    # Register Routers
    # =========================================================================

    # Public endpoints (no auth required)
    app.include_router(health_router)

    # Protected endpoints
    app.include_router(parac_router)
    app.include_router(ide_router)
    app.include_router(agents_router)
    app.include_router(logs_router)

    # CRUD routers (protected)
    app.include_router(agent_crud_router)
    app.include_router(workflow_crud_router)
    # Phase 4: Workflow execution
    app.include_router(workflow_execution_router)
    app.include_router(tool_crud_router)
    # Human-in-the-Loop approvals (ISO 42001)
    app.include_router(approvals_router)
    # Phase 5: Artifact reviews
    app.include_router(reviews_router)

    # Auth router
    from paracle_api.routers.auth import router as auth_router
    app.include_router(auth_router)

    # =========================================================================
    # Root Endpoint
    # =========================================================================

    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "message": "Welcome to Paracle API",
            "docs": "/docs" if not config.is_production() else "disabled",
            "version": "0.0.1",
            "security": "enabled",
        }

    return app


# Create the default application instance
app = create_app()
