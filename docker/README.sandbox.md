# Paracle Sandbox Docker Images

This directory contains Dockerfiles for Paracle sandbox execution environments.

## Images

### `paracle/sandbox:latest` (Dockerfile.sandbox)

Secure, minimal Python 3.10 environment for agent execution.

**Features**:
- Python 3.10 slim base
- Non-root user (`paracle:1000`)
- Common Python packages pre-installed
- Minimal attack surface
- Security-hardened

**Build**:
```bash
docker build -t paracle/sandbox:latest -f Dockerfile.sandbox .
```

**Usage**:
```python
from paracle_sandbox import SandboxConfig

config = SandboxConfig(base_image="paracle/sandbox:latest")
```

**Pre-installed Packages**:
- requests
- pydantic
- click
- rich
- jinja2
- pyyaml

### Custom Images

You can create custom sandbox images:

```dockerfile
FROM paracle/sandbox:latest

# Install additional packages
USER root
RUN pip install numpy pandas
USER paracle

# Add custom files
COPY --chown=paracle:paracle scripts/ /workspace/scripts/
```

Build and use:
```bash
docker build -t my-custom-sandbox:latest .
```

```python
config = SandboxConfig(base_image="my-custom-sandbox:latest")
```

## Security Considerations

### Non-Root User

All containers run as non-root user `paracle` (UID 1000):
- Prevents privilege escalation
- Limits system access
- Best practice for containers

### Minimal Dependencies

Only essential packages installed:
- Reduces attack surface
- Faster image builds
- Smaller image size

### Read-Only Root Filesystem

Sandbox enforces read-only root filesystem:
- Prevents system modifications
- Only `/workspace` and `/tmp` writable
- Enhanced security

### Capability Dropping

All Linux capabilities dropped by default:
- No raw socket access
- No system administration
- No kernel module loading

## Image Variants

### Development Image

For development with additional tools:

```dockerfile
FROM paracle/sandbox:latest

USER root
RUN apt-get update && apt-get install -y \
    vim \
    ipython3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    ipdb \
    pytest \
    black \
    ruff

USER paracle
```

### ML/Data Science Image

For machine learning workloads:

```dockerfile
FROM paracle/sandbox:latest

USER root
RUN pip install \
    numpy \
    pandas \
    scikit-learn \
    matplotlib \
    seaborn

USER paracle
```

### API/Web Image

For API testing agents:

```dockerfile
FROM paracle/sandbox:latest

USER root
RUN pip install \
    httpx \
    aiohttp \
    fastapi \
    websockets

USER paracle
```

## Building Images

### Local Build

```bash
# Base image
docker build -t paracle/sandbox:latest -f Dockerfile.sandbox .

# Custom variant
docker build -t paracle/sandbox:ml -f Dockerfile.sandbox.ml .
```

### Multi-Stage Build

For optimized images:

```dockerfile
# Build stage
FROM python:3.10 as builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Runtime stage
FROM python:3.10-slim
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
# ... rest of image
```

### Push to Registry

```bash
# Tag
docker tag paracle/sandbox:latest your-registry.com/paracle/sandbox:latest

# Push
docker push your-registry.com/paracle/sandbox:latest

# Use in config
config = SandboxConfig(base_image="your-registry.com/paracle/sandbox:latest")
```

## Testing Images

Test sandbox image works correctly:

```bash
# CLI test
paracle sandbox test

# Manual test
docker run --rm -it paracle/sandbox:latest python3 -c "print('Hello from sandbox')"
```

## Troubleshooting

### Image Not Found

```bash
# Pull from Docker Hub (when available)
docker pull paracle/sandbox:latest

# Or build locally
docker build -t paracle/sandbox:latest -f docker/Dockerfile.sandbox .
```

### Permission Issues

Ensure files are owned by `paracle:1000`:
```dockerfile
COPY --chown=paracle:paracle files/ /workspace/
```

### Package Not Available

Add to Dockerfile:
```dockerfile
USER root
RUN pip install your-package
USER paracle
```

## See Also

- [Sandbox Guide](../docs/sandbox-guide.md) - Complete usage guide
- [Docker Documentation](https://docs.docker.com/) - Docker reference
- [Security Policy](../.parac/policies/SECURITY.md) - Security best practices
