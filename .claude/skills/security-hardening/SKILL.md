---
name: security-hardening
description: Implement authentication, authorization, input validation, and security best practices. Use when securing API endpoints and data.
license: Apache-2.0
compatibility: Python 3.10+, FastAPI, OAuth2
metadata:
  author: paracle-core-team
  version: "1.0.0"
  category: security
  level: advanced
  display_name: "Security Hardening"
  tags:
    - security
    - authentication
    - authorization
    - validation
  capabilities:
    - authentication_implementation
    - authorization_policies
    - input_validation
    - security_testing
allowed-tools: Read Write Bash(python:*)
---

# Security Hardening Skill

## When to use this skill

Use when:
- Implementing authentication
- Setting up authorization
- Validating user input
- Preventing security vulnerabilities
- Securing API endpoints

## Authentication

```python
# JWT-based authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# Use in endpoints
@app.get("/agents")
async def list_agents(user: User = Depends(get_current_user)):
    # User is authenticated
    return await fetch_user_agents(user.id)
```

## Authorization (RBAC)

```python
# Role-Based Access Control
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class Permission(str, Enum):
    CREATE_AGENT = "create:agent"
    READ_AGENT = "read:agent"
    UPDATE_AGENT = "update:agent"
    DELETE_AGENT = "delete:agent"

ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.CREATE_AGENT,
        Permission.READ_AGENT,
        Permission.UPDATE_AGENT,
        Permission.DELETE_AGENT,
    ],
    Role.USER: [
        Permission.CREATE_AGENT,
        Permission.READ_AGENT,
        Permission.UPDATE_AGENT,
    ],
    Role.VIEWER: [
        Permission.READ_AGENT,
    ],
}

def require_permission(permission: Permission):
    async def check_permission(user: User = Depends(get_current_user)):
        if permission not in ROLE_PERMISSIONS.get(user.role, []):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission}",
            )
        return user

    return check_permission

# Use in endpoints
@app.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    user: User = Depends(require_permission(Permission.DELETE_AGENT)),
):
    return await delete_agent_service(agent_id, user)
```

## Input Validation

```python
# Use Pydantic for validation
from pydantic import BaseModel, Field, validator

class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, regex="^[a-z0-9-]+$")
    model: str = Field(..., regex="^(gpt-4|claude-3).*$")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: str = Field(..., max_length=10000)

    @validator("name")
    def validate_name(cls, v):
        # Additional validation
        if v in ["admin", "root", "system"]:
            raise ValueError("Reserved name")
        return v

# SQL Injection Prevention
from sqlalchemy import select, text

# Bad: SQL injection vulnerable
query = f"SELECT * FROM agents WHERE name = '{user_input}'"  # DON'T DO THIS

# Good: Use parameterized queries
query = select(Agent).where(Agent.name == user_input)  # Safe

# Or with raw SQL (use params)
query = text("SELECT * FROM agents WHERE name = :name")
result = await session.execute(query, {"name": user_input})  # Safe
```

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/agents")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def create_agent(
    request: Request,
    data: CreateAgentRequest,
    user: User = Depends(get_current_user),
):
    return await create_agent_service(data, user)
```

## Secret Management

```python
# Don't hardcode secrets
# Bad
API_KEY = "sk-1234567890abcdef"  # DON'T DO THIS

# Good: Use environment variables
import os
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY not set")

# Better: Use secret management service
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://my-vault.vault.azure.net", credential=credential)
API_KEY = client.get_secret("openai-api-key").value
```

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com",  # Specific origins only
        # Don't use "*" in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

## Security Headers

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Error Handling

```python
# Don't leak sensitive info in errors
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log full error for debugging
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    # Return generic message to user
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},  # Don't expose stack trace
    )

# Validate error messages don't expose system info
class AgentNotFoundError(HTTPException):
    def __init__(self, agent_id: str):
        # Don't include internal IDs or paths
        super().__init__(
            status_code=404,
            detail="Agent not found",  # Generic message
        )
        # Log details server-side only
        logger.warning(f"Agent not found: {agent_id}")
```

## Security Testing

```python
# Test authentication
def test_requires_authentication():
    response = client.get("/agents")
    assert response.status_code == 401

# Test authorization
def test_viewer_cannot_delete():
    token = create_token_for_role(Role.VIEWER)
    response = client.delete(
        "/agents/123",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

# Test input validation
def test_rejects_invalid_agent_name():
    response = client.post(
        "/agents",
        json={"name": "invalid name!"},  # Spaces and ! not allowed
    )
    assert response.status_code == 422
```

## Best Practices

1. **Never trust user input** - Validate everything
2. **Use parameterized queries** - Prevent SQL injection
3. **Implement rate limiting** - Prevent abuse
4. **Store secrets securely** - Never in code
5. **Use HTTPS only** - Encrypt in transit
6. **Add security headers** - Prevent common attacks
7. **Log security events** - Monitor for attacks
8. **Keep dependencies updated** - Patch vulnerabilities

## Security Checklist

- [ ] Authentication implemented (JWT)
- [ ] Authorization rules defined (RBAC)
- [ ] Input validation with Pydantic
- [ ] SQL injection prevention
- [ ] Rate limiting on endpoints
- [ ] Secrets in environment/vault
- [ ] HTTPS enforced
- [ ] CORS configured properly
- [ ] Security headers added
- [ ] Error messages sanitized
- [ ] Security tests written

## Resources

- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Security Guide: `content/docs/technical/security-audit-report.md`
