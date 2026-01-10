"""JWT Authentication for Paracle API.

Provides secure authentication using JWT tokens with proper
security practices following OWASP guidelines.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from paracle_core.compat import UTC, datetime, timedelta
from pydantic import BaseModel, Field

# Optional dependencies - checked at runtime when actually used
try:
    from jose import JWTError, jwt

    JWT_AVAILABLE = True
except ImportError:
    JWTError = Exception  # type: ignore[misc,assignment]
    jwt = None  # type: ignore[assignment]
    JWT_AVAILABLE = False

try:
    from passlib.context import CryptContext

    PASSLIB_AVAILABLE = True
except ImportError:
    CryptContext = None  # type: ignore[misc,assignment]
    PASSLIB_AVAILABLE = False

if TYPE_CHECKING:
    from jose import jwt
    from passlib.context import CryptContext

from paracle_api.security.config import SecurityConfig, get_security_config


def _check_auth_dependencies() -> None:
    """Check that authentication dependencies are available.

    Raises:
        ImportError: If required dependencies are missing.
    """
    if not JWT_AVAILABLE:
        raise ImportError(
            "python-jose is required for authentication. "
            "Install with: pip install python-jose[cryptography]"
        )
    if not PASSLIB_AVAILABLE:
        raise ImportError(
            "passlib is required for password hashing. "
            "Install with: pip install passlib[bcrypt]"
        )


# Password hashing context - created lazily
_pwd_context: "CryptContext | None" = None


def _get_pwd_context() -> "CryptContext":
    """Get password context, creating it if needed."""
    global _pwd_context
    if _pwd_context is None:
        _check_auth_dependencies()
        _pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    return _pwd_context

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# =============================================================================
# Models
# =============================================================================


class Token(BaseModel):
    """OAuth2 token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    sub: str | None = Field(default=None, description="Subject (username)")
    exp: datetime | None = Field(default=None, description="Expiration time")
    scopes: list[str] = Field(default_factory=list, description="Token scopes")


class User(BaseModel):
    """User model for authentication."""

    username: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    disabled: bool = Field(default=False)
    scopes: list[str] = Field(default_factory=list)


class UserInDB(User):
    """User model with hashed password (for database storage)."""

    hashed_password: str


# =============================================================================
# Password Utilities
# =============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Argon2 hashed password

    Returns:
        True if password matches
    """
    return _get_pwd_context().verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2id.

    Argon2id is the recommended password hashing algorithm
    (winner of Password Hashing Competition 2015).

    Args:
        password: Plain text password

    Returns:
        Argon2 hashed password
    """
    return _get_pwd_context().hash(password)


# =============================================================================
# Token Management
# =============================================================================


def create_access_token(
    data: dict[str, Any],
    config: SecurityConfig | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token (must include 'sub' for subject)
        config: Security configuration (uses default if not provided)
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT token string
    """
    _check_auth_dependencies()
    if config is None:
        config = get_security_config()

    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=config.access_token_expire_minutes
        )

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "access",
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        config.jwt_secret_key.get_secret_value(),
        algorithm=config.jwt_algorithm,
    )

    return encoded_jwt


def decode_token(
    token: str,
    config: SecurityConfig | None = None,
) -> TokenData:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string
        config: Security configuration

    Returns:
        TokenData with decoded claims

    Raises:
        JWTError: If token is invalid
    """
    _check_auth_dependencies()
    if config is None:
        config = get_security_config()

    payload = jwt.decode(
        token,
        config.jwt_secret_key.get_secret_value(),
        algorithms=[config.jwt_algorithm],
    )

    return TokenData(
        sub=payload.get("sub"),
        exp=datetime.fromtimestamp(payload.get("exp", 0), tz=UTC),
        scopes=payload.get("scopes", []),
    )


# =============================================================================
# User Management (In-Memory for Development)
# =============================================================================


# In-memory user store (replace with database in production)
_users_db: dict[str, UserInDB] = {}


def get_user(username: str) -> UserInDB | None:
    """Get user by username.

    Args:
        username: Username to look up

    Returns:
        UserInDB if found, None otherwise
    """
    return _users_db.get(username)


def create_user(
    username: str,
    password: str,
    email: str | None = None,
    full_name: str | None = None,
    scopes: list[str] | None = None,
) -> UserInDB:
    """Create a new user.

    Args:
        username: Username
        password: Plain text password (will be hashed)
        email: Optional email
        full_name: Optional full name
        scopes: Optional permission scopes

    Returns:
        Created UserInDB
    """
    user = UserInDB(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        scopes=scopes or [],
    )
    _users_db[username] = user
    return user


def authenticate_user(username: str, password: str) -> UserInDB | None:
    """Authenticate a user with username and password.

    Args:
        username: Username
        password: Plain text password

    Returns:
        UserInDB if authentication successful, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# =============================================================================
# FastAPI Dependencies
# =============================================================================


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
    config: Annotated[SecurityConfig, Depends(get_security_config)] = None,
) -> User:
    """Get the current authenticated user.

    Supports both JWT tokens and API keys.

    Args:
        token: JWT token from Authorization header
        api_key: API key from X-API-Key header
        config: Security configuration

    Returns:
        Authenticated User

    Raises:
        HTTPException: 401 if not authenticated
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try API key authentication first
    if api_key:
        if config and config.api_keys:
            for valid_key in config.api_keys:
                if api_key == valid_key.get_secret_value():
                    # API key authenticated - return service user
                    return User(
                        username="api-service",
                        scopes=["api:full"],
                    )
        raise credentials_exception

    # Try JWT authentication
    if not token:
        raise credentials_exception

    try:
        token_data = decode_token(token, config)
        if token_data.sub is None:
            raise credentials_exception

        # Check expiration
        if token_data.exp and token_data.exp < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = get_user(token_data.sub)
        if user is None:
            raise credentials_exception

        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        return User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            scopes=user.scopes,
        )

    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user and verify they are active.

    Args:
        current_user: User from get_current_user

    Returns:
        Active User

    Raises:
        HTTPException: 403 if user is disabled
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_scopes(*required_scopes: str):
    """Create a dependency that requires specific scopes.

    Args:
        *required_scopes: Scopes that the user must have

    Returns:
        FastAPI dependency function

    Example:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_scopes("admin:read"))
        ):
            ...
    """

    async def scope_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        for scope in required_scopes:
            if (
                scope not in current_user.scopes
                and "api:full" not in current_user.scopes
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scope: {scope}",
                )
        return current_user

    return scope_checker


# =============================================================================
# Optional Authentication (for endpoints that work with or without auth)
# =============================================================================


async def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
    config: Annotated[SecurityConfig, Depends(get_security_config)] = None,
) -> User | None:
    """Get the current user if authenticated, None otherwise.

    Useful for endpoints that behave differently for authenticated vs anonymous users.

    Args:
        token: JWT token from Authorization header
        api_key: API key from X-API-Key header
        config: Security configuration

    Returns:
        User if authenticated, None otherwise
    """
    if not token and not api_key:
        return None

    try:
        return await get_current_user(token, api_key, config)
    except HTTPException:
        return None


# =============================================================================
# Initialize Default Admin User (Development Only)
# =============================================================================


def init_default_users() -> None:
    """Initialize default users for development.

    WARNING: Do NOT use in production!
    """
    import os

    if os.getenv("PARACLE_ENV", "development") == "production":
        return

    # Create default admin user if not exists
    if "admin" not in _users_db:
        create_user(
            username="admin",
            password="admin",  # CHANGE IN PRODUCTION
            email="admin@paracle.local",
            full_name="Admin User",
            scopes=["admin:read", "admin:write", "agents:read", "agents:write"],
        )
