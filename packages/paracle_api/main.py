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
from fastapi.openapi.utils import get_openapi
from paracle_core.logging import create_request_logging_middleware, get_logger
from paracle_domain.inheritance import InheritanceError
from paracle_orchestration.exceptions import OrchestrationError
from paracle_profiling import ProfilerMiddleware
from paracle_providers.exceptions import LLMProviderError

from paracle_api.errors import (
    inheritance_error_to_problem,
    internal_error_to_problem,
    orchestration_error_to_problem,
    provider_error_to_problem,
    validation_error_to_problem,
)
from paracle_api.middleware.cache import ResponseCacheMiddleware
from paracle_api.routers import (
    agent_crud_router,
    agents_router,
    approvals_router,
    health_router,
    ide_router,
    kanban_router,
    logs_router,
    observability_router,
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
        description="""User-driven multi-agent framework API with enterprise security.

        Build autonomous AI agent systems with:
        - Multi-agent orchestration and workflows
        - LLM provider abstraction (12+ providers)
        - Human-in-the-loop approvals (ISO 42001)
        - Comprehensive security (JWT, rate limiting, CORS)
        - Real-time execution tracking and observability
        """,
        version="1.0.0",
        contact={
            "name": "Paracle Support",
            "url": "https://github.com/IbIFACE-Tech/paracle-lite",
            "email": "support@paracle.ai",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        terms_of_service="https://github.com/IbIFACE-Tech/paracle-lite/blob/main/LICENSE",
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
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
    )

    # 3. Request logging middleware with correlation IDs
    app.add_middleware(create_request_logging_middleware())

    # 4. Performance profiling middleware (Phase 8)
    app.add_middleware(ProfilerMiddleware, slow_threshold=1.0)

    # 5. Response caching middleware (Phase 8 - Multi-level caching)
    app.add_middleware(
        ResponseCacheMiddleware,
        default_ttl=60,  # 1 minute default TTL
        cache_paths=["/api/agents", "/api/specs", "/api/workflows", "/api/tools"],
        exclude_paths=[
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth",
            "/api/executions",
        ],
    )

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
        problem = provider_error_to_problem(request, exc, config.is_production())
        return problem.to_response()

    @app.exception_handler(OrchestrationError)
    async def orchestration_exception_handler(
        request: Request, exc: OrchestrationError
    ):
        """Handle orchestration errors with Problem Details."""
        logger.error(f"Orchestration error: {exc}", exc_info=True)
        problem = orchestration_error_to_problem(request, exc, config.is_production())
        return problem.to_response()

    @app.exception_handler(InheritanceError)
    async def inheritance_exception_handler(request: Request, exc: InheritanceError):
        """Handle inheritance errors with Problem Details."""
        logger.error(f"Inheritance error: {exc}", exc_info=True)
        problem = inheritance_error_to_problem(request, exc, config.is_production())
        return problem.to_response()

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions with Problem Details."""
        logger.exception(f"Unhandled exception: {exc}")
        problem = internal_error_to_problem(request, exc, config.is_production())
        return problem.to_response()

    # =========================================================================
    # Register Routers
    # =========================================================================

    # =========================================================================
    # Register Routers with /v1 API Versioning
    # =========================================================================

    # Public endpoints (no auth required)
    app.include_router(health_router, prefix="/v1")

    # Protected endpoints
    app.include_router(parac_router, prefix="/v1")
    app.include_router(ide_router, prefix="/v1")
    app.include_router(agents_router, prefix="/v1")
    app.include_router(logs_router, prefix="/v1")

    # CRUD routers (protected)
    app.include_router(agent_crud_router, prefix="/v1")
    app.include_router(workflow_crud_router, prefix="/v1")
    # Phase 4: Workflow execution
    app.include_router(workflow_execution_router, prefix="/v1")
    app.include_router(tool_crud_router, prefix="/v1")
    # Human-in-the-Loop approvals (ISO 42001)
    app.include_router(approvals_router, prefix="/v1")
    # Phase 5: Artifact reviews
    app.include_router(reviews_router, prefix="/v1")

    # Kanban boards and tasks
    app.include_router(kanban_router, prefix="/v1")
    # Observability (metrics, traces, alerts)
    app.include_router(observability_router, prefix="/v1")

    # Auth router
    from paracle_api.routers.auth import router as auth_router

    app.include_router(auth_router, prefix="/v1")

    # =========================================================================
    # Custom OpenAPI Schema with Security Schemes
    # =========================================================================

    def custom_openapi():
        """Generate custom OpenAPI schema with security schemes and extensions."""
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            contact=app.contact,
            license_info=app.license_info,
            terms_of_service=app.terms_of_service,
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token obtained from /v1/auth/token endpoint",
            }
        }

        # Add global rate limit headers to all responses
        rate_limit_headers = {
            "X-RateLimit-Limit": {
                "description": "Maximum requests allowed per window",
                "schema": {"type": "integer"},
            },
            "X-RateLimit-Remaining": {
                "description": "Requests remaining in current window",
                "schema": {"type": "integer"},
            },
            "X-RateLimit-Reset": {
                "description": "Unix timestamp when rate limit resets",
                "schema": {"type": "integer"},
            },
        }

        # Add rate limit headers to all path responses
        for path_data in openapi_schema["paths"].values():
            for operation in path_data.values():
                if isinstance(operation, dict) and "responses" in operation:
                    for response_data in operation["responses"].values():
                        if isinstance(response_data, dict):
                            if "headers" not in response_data:
                                response_data["headers"] = {}
                            response_data["headers"].update(rate_limit_headers)

        # Add API version info to OpenAPI schema
        openapi_schema["info"]["x-api-version"] = "v1"
        openapi_schema["info"]["x-api-status"] = "stable"

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # =========================================================================
    # Root Endpoint
    # =========================================================================

    @app.get("/", tags=["root"], operation_id="getRoot")
    async def root() -> dict:
        """Root endpoint with API information and version details."""
        return {
            "message": "Welcome to Paracle API",
            "version": "1.0.0",
            "api_version": "v1",
            "status": "stable",
            "docs": "/docs" if not config.is_production() else "disabled",
            "security": "enabled",
            "features": [
                "multi-agent orchestration",
                "12+ LLM providers",
                "JWT authentication",
                "rate limiting",
                "real-time execution tracking",
            ],
        }

    return app


# Create the default application instance
app = create_app()
