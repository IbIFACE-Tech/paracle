"""Security Tests for Paracle Framework.

Tests security controls including:
- Authentication and authorization
- Rate limiting
- Input validation
- Tool sandboxing
- Repository thread safety
"""

from __future__ import annotations

import threading

import pytest

# =============================================================================
# Test Security Configuration
# =============================================================================


class TestSecurityConfig:
    """Tests for security configuration."""

    def test_default_jwt_secret_warning(self):
        """Default JWT secret should trigger a warning."""
        from paracle_api.security.config import SecurityConfig

        with pytest.warns(UserWarning, match="Using default JWT secret"):
            config = SecurityConfig()

    def test_jwt_secret_minimum_length(self):
        """JWT secret must be at least 32 characters."""
        from paracle_api.security.config import SecurityConfig
        from pydantic import SecretStr

        with pytest.raises(ValueError, match="at least 32 characters"):
            SecurityConfig(jwt_secret_key=SecretStr("short"))

    def test_cors_wildcard_warning(self):
        """CORS wildcard origin should trigger a warning."""
        from paracle_api.security.config import SecurityConfig
        from pydantic import SecretStr

        with pytest.warns(UserWarning, match="allows all origins"):
            SecurityConfig(
                jwt_secret_key=SecretStr("a" * 32),
                cors_allowed_origins=["*"],
            )

    def test_production_validation(self):
        """Production config should fail with default values."""
        from paracle_api.security.config import SecurityConfig
        from pydantic import SecretStr

        config = SecurityConfig(
            jwt_secret_key=SecretStr("CHANGE-ME-IN-PRODUCTION-USE-SECURE-RANDOM-KEY"),
        )

        issues = config.validate_production_config()
        assert len(issues) > 0
        assert any("secret key" in issue.lower() for issue in issues)


# =============================================================================
# Test Authentication
# =============================================================================


class TestAuthentication:
    """Tests for JWT authentication."""

    def test_password_hashing(self):
        """Password hashing should work correctly."""
        from paracle_api.security.auth import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_token_creation(self):
        """JWT tokens should be created correctly."""
        from paracle_api.security.auth import create_access_token, decode_token
        from paracle_api.security.config import SecurityConfig
        from pydantic import SecretStr

        config = SecurityConfig(
            jwt_secret_key=SecretStr("a" * 64),
        )

        token = create_access_token(
            data={"sub": "testuser", "scopes": ["read"]},
            config=config,
        )

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        token_data = decode_token(token, config)
        assert token_data.sub == "testuser"
        assert "read" in token_data.scopes

    def test_user_creation_and_authentication(self):
        """User creation and authentication should work."""
        from paracle_api.security.auth import _users_db, authenticate_user, create_user

        # Clear existing users
        _users_db.clear()

        # Create user
        user = create_user(
            username="testuser",
            password="secure_password_123",
            email="test@example.com",
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"

        # Authenticate
        authenticated = authenticate_user("testuser", "secure_password_123")
        assert authenticated is not None
        assert authenticated.username == "testuser"

        # Wrong password should fail
        failed = authenticate_user("testuser", "wrong_password")
        assert failed is None


# =============================================================================
# Test Rate Limiting
# =============================================================================


class TestRateLimiting:
    """Tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_requests(self):
        """Rate limiter should allow requests under limit."""
        from paracle_api.security.rate_limit import RateLimiter

        limiter = RateLimiter(requests_per_window=10, window_seconds=60)

        for _ in range(5):
            allowed, _ = await limiter.is_allowed("test_client")
            assert allowed

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excess(self):
        """Rate limiter should block requests over limit."""
        from paracle_api.security.rate_limit import RateLimiter

        limiter = RateLimiter(requests_per_window=5, window_seconds=60)

        # Use up the limit
        for _ in range(5):
            allowed, _ = await limiter.is_allowed("test_client")
            assert allowed

        # Next request should be blocked
        allowed, headers = await limiter.is_allowed("test_client")
        assert not allowed
        assert "Retry-After" in headers

    @pytest.mark.asyncio
    async def test_rate_limit_per_client(self):
        """Rate limits should be per-client."""
        from paracle_api.security.rate_limit import RateLimiter

        limiter = RateLimiter(requests_per_window=3, window_seconds=60)

        # Exhaust client1's limit
        for _ in range(3):
            await limiter.is_allowed("client1")

        # client2 should still be allowed
        allowed, _ = await limiter.is_allowed("client2")
        assert allowed


# =============================================================================
# Test Filesystem Tool Security
# =============================================================================


class TestFilesystemSecurity:
    """Tests for filesystem tool sandboxing."""

    def test_filesystem_requires_allowed_paths(self):
        """Filesystem tools should require allowed_paths."""
        from paracle_tools.builtin.filesystem import (
            DeleteFileTool,
            ReadFileTool,
            WriteFileTool,
        )

        with pytest.raises(ValueError, match="allowed_paths is required"):
            ReadFileTool(allowed_paths=None)

        with pytest.raises(ValueError, match="allowed_paths is required"):
            ReadFileTool(allowed_paths=[])

        with pytest.raises(ValueError, match="allowed_paths is required"):
            WriteFileTool(allowed_paths=None)

        with pytest.raises(ValueError, match="allowed_paths is required"):
            DeleteFileTool(allowed_paths=[])

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, tmp_path):
        """Path traversal attempts should be blocked."""
        from paracle_tools.builtin.base import PermissionError
        from paracle_tools.builtin.filesystem import ReadFileTool

        # Create allowed directory
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()

        tool = ReadFileTool(allowed_paths=[str(allowed_dir)])

        # Attempt path traversal
        with pytest.raises(PermissionError):
            await tool._execute(path=str(tmp_path / "allowed" / ".." / "secret.txt"))

    @pytest.mark.asyncio
    async def test_sandboxed_access_works(self, tmp_path):
        """Access within sandbox should work."""
        from paracle_tools.builtin.filesystem import ReadFileTool

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        tool = ReadFileTool(allowed_paths=[str(tmp_path)])

        result = await tool._execute(path=str(test_file))
        assert result["content"] == "test content"


# =============================================================================
# Test Shell Tool Security
# =============================================================================


class TestShellSecurity:
    """Tests for shell command execution security."""

    def test_shell_requires_allowlist(self):
        """Shell tool should require command allowlist."""
        from paracle_tools.builtin.shell import RunCommandTool

        with pytest.raises(ValueError, match="allowed_commands is required"):
            RunCommandTool(allowed_commands=None)

        with pytest.raises(ValueError, match="allowed_commands is required"):
            RunCommandTool(allowed_commands=[])

    @pytest.mark.asyncio
    async def test_blocked_command_rejected(self):
        """Commands not in allowlist should be rejected."""
        from paracle_tools.builtin.base import PermissionError
        from paracle_tools.builtin.shell import RunCommandTool

        tool = RunCommandTool(allowed_commands=["ls", "cat"])

        with pytest.raises(PermissionError, match="not in allowed commands"):
            await tool._execute(command="rm -rf /")

    @pytest.mark.asyncio
    async def test_allowed_command_works(self):
        """Commands in allowlist should execute."""
        from paracle_tools.builtin.shell import RunCommandTool

        tool = RunCommandTool(allowed_commands=["echo"])

        result = await tool._execute(command="echo hello")
        assert result["success"]
        assert "hello" in result["stdout"]

    def test_timeout_capped(self):
        """Timeout should be capped at 5 minutes."""
        from paracle_tools.builtin.shell import RunCommandTool

        tool = RunCommandTool(
            allowed_commands=["echo"],
            timeout=600.0,  # Request 10 minutes
        )

        assert tool.timeout == 300.0  # Should be capped at 5 minutes

    def test_no_shell_parameter(self):
        """shell=True parameter should not be available."""
        from paracle_tools.builtin.shell import RunCommandTool

        tool = RunCommandTool(allowed_commands=["echo"])

        # The parameters should not include 'shell'
        assert "shell" not in tool.parameters.get("properties", {})


# =============================================================================
# Test Repository Thread Safety
# =============================================================================


class TestRepositoryThreadSafety:
    """Tests for repository thread safety."""

    def test_concurrent_access(self):
        """Repository should handle concurrent access safely."""
        from paracle_store.repository import InMemoryRepository
        from pydantic import BaseModel

        class TestEntity(BaseModel):
            id: str
            value: int

        repo = InMemoryRepository(
            entity_type="TestEntity",
            id_getter=lambda e: e.id,
        )

        errors = []
        results = []

        def worker(worker_id: int):
            try:
                for i in range(100):
                    entity = TestEntity(id=f"w{worker_id}_e{i}", value=i)
                    repo.add(entity)
                    repo.get(entity.id)
                results.append(worker_id)
            except Exception as e:
                errors.append((worker_id, e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert repo.count() == 1000  # 10 workers * 100 entities


# =============================================================================
# Test Input Validation
# =============================================================================


class TestInputValidation:
    """Tests for input validation limits."""

    def test_security_config_limits(self):
        """Security config should have sensible limits."""
        from paracle_api.security.config import SecurityConfig
        from pydantic import SecretStr

        config = SecurityConfig(jwt_secret_key=SecretStr("a" * 64))

        assert config.max_request_size_bytes > 0
        assert config.max_json_depth > 0
        assert config.max_string_length > 0

    def test_token_expiration_limits(self):
        """Token expiration should have limits."""
        from paracle_api.security.config import SecurityConfig
        from pydantic import SecretStr

        # Should reject very long token expiration
        with pytest.raises(Exception):
            SecurityConfig(
                jwt_secret_key=SecretStr("a" * 64),
                access_token_expire_minutes=10000,  # > 24 hours
            )


# =============================================================================
# Test Security Headers
# =============================================================================


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    @pytest.mark.asyncio
    async def test_headers_added(self):
        """Security headers should be added to responses."""
        from fastapi import FastAPI
        from paracle_api.security.config import SecurityConfig
        from paracle_api.security.headers import SecurityHeadersMiddleware
        from pydantic import SecretStr
        from starlette.testclient import TestClient

        app = FastAPI()
        config = SecurityConfig(jwt_secret_key=SecretStr("a" * 64))
        app.add_middleware(SecurityHeadersMiddleware, config=config)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
