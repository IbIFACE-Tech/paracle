"""Paracle API - REST API.

This package provides the FastAPI-based REST API for Paracle:
- Health and status endpoints
- Agent CRUD operations
- Workflow CRUD and execution
- Tool management
- IDE integration
- Governance logging endpoints

Security Features:
- JWT Authentication with OAuth2
- Rate Limiting
- Security Headers (HSTS, CSP, X-Frame-Options)
- RFC 7807 Problem Details error responses
"""

from paracle_api.errors import (
    ProblemDetails,
    create_problem_details,
    inheritance_error_to_problem,
    internal_error_to_problem,
    not_found_error_to_problem,
    orchestration_error_to_problem,
    provider_error_to_problem,
    validation_error_to_problem,
)
from paracle_api.main import app, create_app

__version__ = "1.0.1"

__all__ = [
    # Application
    "app",
    "create_app",
    # RFC 7807 Problem Details
    "ProblemDetails",
    "create_problem_details",
    "provider_error_to_problem",
    "orchestration_error_to_problem",
    "inheritance_error_to_problem",
    "validation_error_to_problem",
    "not_found_error_to_problem",
    "internal_error_to_problem",
]
