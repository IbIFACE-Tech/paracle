#!/bin/bash
# Version bump script for Paracle

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current version
CURRENT_VERSION=$(grep -E '^version = ' pyproject.toml | cut -d'"' -f2)
echo -e "${YELLOW}Current version: ${CURRENT_VERSION}${NC}"

# Parse version
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Determine new version
BUMP_TYPE="${1:-patch}"

case "$BUMP_TYPE" in
  major)
    NEW_MAJOR=$((MAJOR + 1))
    NEW_VERSION="${NEW_MAJOR}.0.0"
    ;;
  minor)
    NEW_MINOR=$((MINOR + 1))
    NEW_VERSION="${MAJOR}.${NEW_MINOR}.0"
    ;;
  patch)
    NEW_PATCH=$((PATCH + 1))
    NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"
    ;;
  *)
    echo -e "${RED}Error: Unknown bump type '$BUMP_TYPE'. Use: major, minor, or patch${NC}"
    exit 1
    ;;
esac

echo -e "${GREEN}New version: ${NEW_VERSION}${NC}"

# Confirm
read -p "Proceed with version bump? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted${NC}"
    exit 1
fi

# Update pyproject.toml
echo "Updating pyproject.toml..."
sed -i.bak "s/^version = \"${CURRENT_VERSION}\"/version = \"${NEW_VERSION}\"/" pyproject.toml
rm pyproject.toml.bak

# Update __version__ in main package
echo "Updating package __version__..."
if [ -f "packages/paracle_core/__init__.py" ]; then
    sed -i.bak "s/__version__ = \"${CURRENT_VERSION}\"/__version__ = \"${NEW_VERSION}\"/" packages/paracle_core/__init__.py
    rm packages/paracle_core/__init__.py.bak
fi

# Git operations
echo "Creating git commit and tag..."
git add pyproject.toml packages/paracle_core/__init__.py
git commit -m "chore: bump version to ${NEW_VERSION}"
git tag -a "v${NEW_VERSION}" -m "Release version ${NEW_VERSION}"

echo -e "${GREEN}✅ Version bumped to ${NEW_VERSION}${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review the changes: git show"
echo "  2. Push to GitHub: git push origin develop && git push origin v${NEW_VERSION}"
echo "  3. GitHub Actions will automatically build and publish"
echo ""
echo -e "${YELLOW}Or manually trigger workflow:${NC}"
echo "  gh workflow run release.yml --ref v${NEW_VERSION}"
