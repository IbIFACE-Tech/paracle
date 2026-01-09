"""Authentication Router for Paracle API.

Provides endpoints for user authentication and token management.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from paracle_api.security.auth import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    create_user,
    get_current_active_user,
    get_user,
)
from paracle_api.security.config import SecurityConfig, get_security_config

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# =============================================================================
# Request/Response Models
# =============================================================================


class UserCreateRequest(BaseModel):
    """Request to create a new user."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)


class UserResponse(BaseModel):
    """User information response."""

    username: str
    email: str | None
    full_name: str | None
    scopes: list[str]


class PasswordChangeRequest(BaseModel):
    """Request to change password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/token", response_model=Token, operation_id="loginForAccessToken")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    config: Annotated[SecurityConfig, Depends(get_security_config)],
) -> Token:
    """Get access token using username and password.

    OAuth2 compatible token endpoint.

    Args:
        form_data: OAuth2 form with username and password
        config: Security configuration

    Returns:
        Access token

    Raises:
        HTTPException: 401 if authentication fails
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        config=config,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=config.access_token_expire_minutes * 60,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    operation_id="registerUser",
)
async def register_user(
    request: UserCreateRequest,
    config: Annotated[SecurityConfig, Depends(get_security_config)],
) -> UserResponse:
    """Register a new user.

    Note: In production, this endpoint should be restricted
    or require admin approval.

    Args:
        request: User registration data
        config: Security configuration

    Returns:
        Created user information

    Raises:
        HTTPException: 400 if username already exists
    """
    # Check if registration is allowed (development only by default)
    if config.is_production():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User registration is disabled in production",
        )

    # Check if user already exists
    if get_user(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create user with default scopes
    user = create_user(
        username=request.username,
        password=request.password,
        email=request.email,
        full_name=request.full_name,
        scopes=["agents:read"],  # Default minimal scopes
    )

    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        scopes=user.scopes,
    )


@router.get("/me", response_model=UserResponse, operation_id="getCurrentUser")
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Get current user information.

    Args:
        current_user: Authenticated user

    Returns:
        User information
    """
    return UserResponse(
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        scopes=current_user.scopes,
    )


@router.post("/verify", operation_id="verifyToken")
async def verify_token(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Verify that a token is valid.

    Args:
        current_user: Authenticated user

    Returns:
        Verification status
    """
    return {
        "status": "valid",
        "username": current_user.username,
    }


@router.post("/logout", operation_id="logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    """Logout user (client should discard token).

    Note: With JWT, true logout requires token blocklisting
    which is not implemented in this version.

    Args:
        current_user: Authenticated user

    Returns:
        Logout confirmation
    """
    # In a production system, you would add the token to a blocklist
    # For now, we just return success and the client should discard the token
    return {
        "status": "logged_out",
        "message": "Please discard your access token",
    }
