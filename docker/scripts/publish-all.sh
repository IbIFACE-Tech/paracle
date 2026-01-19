#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION=${1:-$(grep "^version" ../../pyproject.toml | cut -d'"' -f2)}
DOCKER_USERNAME=${2:-ibiface}
BUILD_CONTEXT="../.."
DOCKER_DIR=".."

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Publishing Paracle Docker Images${NC}"
echo -e "${BLUE}==========================================${NC}"
echo -e "Version: ${GREEN}$VERSION${NC}"
echo -e "Username: ${GREEN}$DOCKER_USERNAME${NC}"
echo -e "Build Context: ${GREEN}$BUILD_CONTEXT${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Check if logged in to Docker Hub
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    exit 1
fi

# Array of images: name => dockerfile
declare -A IMAGES=(
    ["paracle"]="Dockerfile.api"
    ["paracle-worker"]="Dockerfile.worker"
    ["paracle-mcp"]="Dockerfile.mcp"
    ["paracle-sandbox"]="Dockerfile.sandbox"
    ["paracle-dev"]="Dockerfile.dev"
)

# Track success/failure
TOTAL=${#IMAGES[@]}
SUCCESS=0
FAILED=0

# Build and push each image
for IMAGE_NAME in "${!IMAGES[@]}"; do
    DOCKERFILE="${IMAGES[$IMAGE_NAME]}"
    FULL_DOCKERFILE="$DOCKER_DIR/$DOCKERFILE"

    echo ""
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${YELLOW}Building: $IMAGE_NAME${NC}"
    echo -e "${BLUE}Dockerfile: $DOCKERFILE${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"

    # Build with version and latest tags
    if docker build \
        -f "$FULL_DOCKERFILE" \
        -t "$DOCKER_USERNAME/$IMAGE_NAME:$VERSION" \
        -t "$DOCKER_USERNAME/$IMAGE_NAME:latest" \
        "$BUILD_CONTEXT"; then

        echo -e "${GREEN}✅ Built: $IMAGE_NAME${NC}"

        # Push version tag
        echo -e "${YELLOW}Pushing: $DOCKER_USERNAME/$IMAGE_NAME:$VERSION${NC}"
        if docker push "$DOCKER_USERNAME/$IMAGE_NAME:$VERSION"; then
            echo -e "${GREEN}✅ Pushed version tag${NC}"
        else
            echo -e "${RED}❌ Failed to push version tag${NC}"
            ((FAILED++))
            continue
        fi

        # Push latest tag
        echo -e "${YELLOW}Pushing: $DOCKER_USERNAME/$IMAGE_NAME:latest${NC}"
        if docker push "$DOCKER_USERNAME/$IMAGE_NAME:latest"; then
            echo -e "${GREEN}✅ Pushed latest tag${NC}"
            ((SUCCESS++))
        else
            echo -e "${RED}❌ Failed to push latest tag${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${RED}❌ Failed to build: $IMAGE_NAME${NC}"
        ((FAILED++))
    fi
done

echo ""
echo -e "${BLUE}==========================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All images published successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Some images failed to publish${NC}"
    echo -e "Success: ${GREEN}$SUCCESS${NC} / $TOTAL"
    echo -e "Failed: ${RED}$FAILED${NC} / $TOTAL"
fi
echo -e "${BLUE}==========================================${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}Published images:${NC}"
    for IMAGE_NAME in "${!IMAGES[@]}"; do
        echo -e "  ✅ ${BLUE}$DOCKER_USERNAME/$IMAGE_NAME:$VERSION${NC}"
    done
    echo ""
    echo -e "${YELLOW}All images also tagged as 'latest'${NC}"
    echo ""
    echo -e "${GREEN}Verify on Docker Hub:${NC}"
    echo -e "  https://hub.docker.com/u/$DOCKER_USERNAME"
fi

exit $FAILED
