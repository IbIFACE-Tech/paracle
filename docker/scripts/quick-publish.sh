#!/bin/bash
# Quick publish script - one command to publish all images

set -e

# Get version from pyproject.toml or use argument
VERSION=${1:-$(grep "^version" ../../pyproject.toml | cut -d'"' -f2)}
USERNAME=${2:-ibiface}

echo "🐳 Publishing Paracle Docker Images v$VERSION to $USERNAME/*"
echo ""

# Login check
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker not running!"
    exit 1
fi

# One-liner: build + push all
cd .. && \
for img in api worker mcp sandbox dev; do
    name="paracle"
    [[ "$img" != "api" ]] && name="paracle-$img"
    dockerfile="Dockerfile.$img"
    echo "📦 Building $name..."
    docker build -f "$dockerfile" -t "$USERNAME/$name:$VERSION" -t "$USERNAME/$name:latest" .. && \
    echo "⬆️  Pushing $name:$VERSION..." && \
    docker push "$USERNAME/$name:$VERSION" && \
    docker push "$USERNAME/$name:latest" && \
    echo "✅ $name published!"
done

echo ""
echo "🎉 All images published successfully!"
echo ""
echo "Verify: https://hub.docker.com/u/$USERNAME"
