# Publishing Paracle Docker Images to Docker Hub

> **Complete guide to build, tag, and publish all Paracle Docker images**

---

## 📋 Overview

Paracle has **5 Docker images**:

| Image | Dockerfile | Purpose | Size |
|-------|------------|---------|------|
| `paracle` | `Dockerfile.api` | Main API server | ~400MB |
| `paracle-worker` | `Dockerfile.worker` | Background worker | ~350MB |
| `paracle-mcp` | `Dockerfile.mcp` | MCP server | ~300MB |
| `paracle-sandbox` | `Dockerfile.sandbox` | Sandbox executor | ~500MB |
| `paracle-dev` | `Dockerfile.dev` | Development environment | ~600MB |

---

## 🚀 Quick Publish (All Images)

### Option 1: Using the Publish Script (Recommended)

```bash
# 1. Login to Docker Hub
docker login

# 2. Set version
export PARACLE_VERSION="1.0.3"
export DOCKER_USERNAME="ibiface"

# 3. Run publish script
./docker/scripts/publish-all.sh
```

### Option 2: Manual Publish (Step-by-Step)

```bash
# 1. Login
docker login

# 2. Set variables
VERSION="1.0.3"
USERNAME="ibiface"

# 3. Build and push all images
cd docker
./build-and-push-all.sh $VERSION $USERNAME
```

---

## 📝 Detailed Instructions

### Step 1: Prerequisites

```bash
# 1. Docker installed and running
docker --version
# Docker version 24.0.0 or higher

# 2. Docker Hub account
# Sign up at https://hub.docker.com

# 3. Login to Docker Hub
docker login
# Username: ibiface
# Password: [your-password]
```

### Step 2: Set Version

```bash
# Set version for all images
export PARACLE_VERSION="1.0.3"

# Or read from pyproject.toml
export PARACLE_VERSION=$(grep "^version" ../pyproject.toml | cut -d'"' -f2)
echo "Publishing version: $PARACLE_VERSION"
```

### Step 3: Build Images

#### Build All Images

```bash
cd docker

# Build all images with version tag
docker build -f Dockerfile.api -t ibiface/paracle:$PARACLE_VERSION -t ibiface/paracle:latest ..
docker build -f Dockerfile.worker -t ibiface/paracle-worker:$PARACLE_VERSION -t ibiface/paracle-worker:latest ..
docker build -f Dockerfile.mcp -t ibiface/paracle-mcp:$PARACLE_VERSION -t ibiface/paracle-mcp:latest ..
docker build -f Dockerfile.sandbox -t ibiface/paracle-sandbox:$PARACLE_VERSION -t ibiface/paracle-sandbox:latest ..
docker build -f Dockerfile.dev -t ibiface/paracle-dev:$PARACLE_VERSION -t ibiface/paracle-dev:latest ..
```

#### Build Individual Image

```bash
# Example: Build only API server
docker build -f docker/Dockerfile.api \
  -t ibiface/paracle:1.0.3 \
  -t ibiface/paracle:latest \
  .
```

### Step 4: Test Images Locally

```bash
# Test API server
docker run --rm -p 8000:8000 ibiface/paracle:$PARACLE_VERSION
curl http://localhost:8000/health

# Test MCP server
docker run --rm -p 8080:8080 ibiface/paracle-mcp:$PARACLE_VERSION

# Test worker
docker run --rm ibiface/paracle-worker:$PARACLE_VERSION --help
```

### Step 5: Push Images to Docker Hub

#### Push All Images

```bash
# Push all tags for all images
docker push ibiface/paracle:$PARACLE_VERSION
docker push ibiface/paracle:latest

docker push ibiface/paracle-worker:$PARACLE_VERSION
docker push ibiface/paracle-worker:latest

docker push ibiface/paracle-mcp:$PARACLE_VERSION
docker push ibiface/paracle-mcp:latest

docker push ibiface/paracle-sandbox:$PARACLE_VERSION
docker push ibiface/paracle-sandbox:latest

docker push ibiface/paracle-dev:$PARACLE_VERSION
docker push ibiface/paracle-dev:latest
```

#### Push Individual Image

```bash
# Example: Push only API server
docker push ibiface/paracle:1.0.3
docker push ibiface/paracle:latest
```

---

## 🤖 Automated Scripts

### Create Build & Push Script

Create `docker/scripts/publish-all.sh`:

```bash
#!/bin/bash
set -e

# Configuration
VERSION=${1:-$(grep "^version" ../pyproject.toml | cut -d'"' -f2)}
DOCKER_USERNAME=${2:-ibiface}
BUILD_CONTEXT=".."

echo "=========================================="
echo "Publishing Paracle Docker Images"
echo "=========================================="
echo "Version: $VERSION"
echo "Username: $DOCKER_USERNAME"
echo "Build Context: $BUILD_CONTEXT"
echo "=========================================="

# Array of images
declare -A IMAGES=(
    ["paracle"]="Dockerfile.api"
    ["paracle-worker"]="Dockerfile.worker"
    ["paracle-mcp"]="Dockerfile.mcp"
    ["paracle-sandbox"]="Dockerfile.sandbox"
    ["paracle-dev"]="Dockerfile.dev"
)

# Build and push each image
for IMAGE_NAME in "${!IMAGES[@]}"; do
    DOCKERFILE="${IMAGES[$IMAGE_NAME]}"

    echo ""
    echo "----------------------------------------"
    echo "Building: $IMAGE_NAME"
    echo "Dockerfile: $DOCKERFILE"
    echo "----------------------------------------"

    # Build with version and latest tags
    docker build \
        -f "$DOCKERFILE" \
        -t "$DOCKER_USERNAME/$IMAGE_NAME:$VERSION" \
        -t "$DOCKER_USERNAME/$IMAGE_NAME:latest" \
        "$BUILD_CONTEXT"

    echo "✅ Built: $IMAGE_NAME"

    # Push version tag
    echo "Pushing: $DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
    docker push "$DOCKER_USERNAME/$IMAGE_NAME:$VERSION"

    # Push latest tag
    echo "Pushing: $DOCKER_USERNAME/$IMAGE_NAME:latest"
    docker push "$DOCKER_USERNAME/$IMAGE_NAME:latest"

    echo "✅ Pushed: $IMAGE_NAME (both $VERSION and latest)"
done

echo ""
echo "=========================================="
echo "✅ All images published successfully!"
echo "=========================================="
echo ""
echo "Published images:"
echo "  - $DOCKER_USERNAME/paracle:$VERSION"
echo "  - $DOCKER_USERNAME/paracle-worker:$VERSION"
echo "  - $DOCKER_USERNAME/paracle-mcp:$VERSION"
echo "  - $DOCKER_USERNAME/paracle-sandbox:$VERSION"
echo "  - $DOCKER_USERNAME/paracle-dev:$VERSION"
echo ""
echo "All images also tagged as 'latest'"
```

Make it executable:

```bash
chmod +x docker/scripts/publish-all.sh
```

---

## 🏷️ Tagging Strategy

### Version Tags

```bash
# Semantic version
ibiface/paracle:1.0.3

# Major.minor
ibiface/paracle:1.0

# Major only
ibiface/paracle:1

# Latest (always points to newest stable)
ibiface/paracle:latest
```

### Create All Tags

```bash
VERSION="1.0.3"

# Full version
docker tag ibiface/paracle:$VERSION ibiface/paracle:latest

# Major.minor
docker tag ibiface/paracle:$VERSION ibiface/paracle:1.0

# Major only
docker tag ibiface/paracle:$VERSION ibiface/paracle:1

# Push all tags
docker push ibiface/paracle:$VERSION
docker push ibiface/paracle:latest
docker push ibiface/paracle:1.0
docker push ibiface/paracle:1
```

---

## 🔄 CI/CD Integration (GitHub Actions)

Create `.github/workflows/docker-publish.yml`:

```yaml
name: Publish Docker Images

on:
  push:
    tags:
      - 'v*'  # Trigger on version tags (v1.0.3, etc.)
  workflow_dispatch:  # Manual trigger

env:
  DOCKER_USERNAME: ibiface

jobs:
  publish:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        image:
          - name: paracle
            dockerfile: Dockerfile.api
          - name: paracle-worker
            dockerfile: Dockerfile.worker
          - name: paracle-mcp
            dockerfile: Dockerfile.mcp
          - name: paracle-sandbox
            dockerfile: Dockerfile.sandbox
          - name: paracle-dev
            dockerfile: Dockerfile.dev

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ env.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract version from tag
        id: version
        run: |
          if [[ $GITHUB_REF == refs/tags/v* ]]; then
            VERSION=${GITHUB_REF#refs/tags/v}
          else
            VERSION=$(grep "^version" pyproject.toml | cut -d'"' -f2)
          fi
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/${{ matrix.image.dockerfile }}
          push: true
          tags: |
            ${{ env.DOCKER_USERNAME }}/${{ matrix.image.name }}:${{ steps.version.outputs.version }}
            ${{ env.DOCKER_USERNAME }}/${{ matrix.image.name }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Image digest
        run: echo "Published ${{ matrix.image.name }}:${{ steps.version.outputs.version }}"
```

**Setup**:
1. Go to GitHub repo → Settings → Secrets
2. Add `DOCKER_PASSWORD` secret
3. Push a version tag: `git tag v1.0.3 && git push origin v1.0.3`

---

## 🧪 Testing Published Images

### Test API Server

```bash
# Pull and run
docker pull ibiface/paracle:latest
docker run -d --name paracle-test -p 8000:8000 ibiface/paracle:latest

# Test
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Cleanup
docker stop paracle-test
docker rm paracle-test
```

### Test Full Stack

```bash
# Pull all images
docker pull ibiface/paracle:latest
docker pull ibiface/paracle-worker:latest
docker pull ibiface/paracle-mcp:latest

# Run with docker-compose
docker-compose -f docker/docker-compose.yaml up -d

# Test
curl http://localhost:8000/health

# Cleanup
docker-compose -f docker/docker-compose.yaml down
```

---

## 📊 Image Sizes

Check image sizes before publishing:

```bash
docker images | grep ibiface/paracle

# Expected output:
# ibiface/paracle           latest    abc123    400MB
# ibiface/paracle-worker    latest    def456    350MB
# ibiface/paracle-mcp       latest    ghi789    300MB
# ibiface/paracle-sandbox   latest    jkl012    500MB
# ibiface/paracle-dev       latest    mno345    600MB
```

---

## 🔐 Security

### Multi-Arch Builds (AMD64 + ARM64)

```bash
# Create buildx builder
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# Build and push multi-arch
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile.api \
  -t ibiface/paracle:1.0.3 \
  -t ibiface/paracle:latest \
  --push \
  .
```

### Security Scanning

```bash
# Scan images before publishing
docker scout cves ibiface/paracle:latest
docker scout recommendations ibiface/paracle:latest

# Or use Trivy
trivy image ibiface/paracle:latest
```

---

## 🎯 Quick Reference

### One-Command Publish (All Images)

```bash
# Login + Build + Push all in one command
docker login && \
VERSION=$(grep "^version" pyproject.toml | cut -d'"' -f2) && \
cd docker && \
for img in paracle paracle-worker paracle-mcp paracle-sandbox paracle-dev; do \
  dockerfile="Dockerfile.${img#paracle-}"; \
  [[ "$img" == "paracle" ]] && dockerfile="Dockerfile.api"; \
  docker build -f "$dockerfile" -t "ibiface/$img:$VERSION" -t "ibiface/$img:latest" .. && \
  docker push "ibiface/$img:$VERSION" && \
  docker push "ibiface/$img:latest"; \
done
```

### Verify Published Images

```bash
# Check on Docker Hub
curl -s "https://hub.docker.com/v2/repositories/ibiface/paracle/tags/" | jq

# Or visit:
# https://hub.docker.com/r/ibiface/paracle/tags
```

---

## 📝 Checklist Before Publishing

- [ ] Version updated in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] All tests passing
- [ ] Docker images build successfully
- [ ] Images tested locally
- [ ] Logged in to Docker Hub (`docker login`)
- [ ] Security scan passed
- [ ] README.md updated with new version
- [ ] Git tag created (`git tag v1.0.3`)

---

## 🐛 Troubleshooting

### "denied: requested access to the resource is denied"

**Solution**: Login to Docker Hub

```bash
docker login
# Enter username: ibiface
# Enter password: [your-password]
```

### Build fails with "no space left on device"

**Solution**: Clean up Docker

```bash
docker system prune -a --volumes
docker builder prune -a
```

### Image too large

**Solution**: Use multi-stage builds and .dockerignore

```dockerfile
# Already implemented in Paracle Dockerfiles
FROM python:3.11-slim AS builder
# ... build steps ...

FROM python:3.11-slim
COPY --from=builder /app /app
```

---

## 📚 Related Documentation

- [Docker README](README.md)
- [Docker Compose Guide](docker-compose.yaml)
- [Sandbox Setup](README.sandbox.md)
- [Deployment Guide](../content/docs/deployment.md)

---

**Last Updated**: 2026-01-11
**Version**: 1.0.3
