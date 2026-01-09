.PHONY: help install install-dev test test-cov lint format clean build publish

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package
	uv sync

install-dev: ## Install package with dev dependencies
	uv sync --all-extras

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=packages --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	uv run pytest-watch

lint: ## Run linters
	uv run black --check packages/ tests/
	uv run isort --check-only packages/ tests/
	uv run ruff check packages/ tests/
	uv run mypy packages/

format: ## Format code
	uv run black packages/ tests/
	uv run isort packages/ tests/

security: ## Run security checks
	uv run bandit -r packages/ -ll
	uv run safety check

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

build: clean ## Build package
	uv build

publish-test: build ## Publish to TestPyPI (for testing)
	uv publish --publish-url https://test.pypi.org/legacy/

publish: build ## Publish to PyPI (requires authentication)
	@echo "⚠️  Publishing to PyPI. Make sure version is bumped!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	uv publish

release-check: ## Check if ready for release
	@echo "🔍 Running release checks..."
	@echo "\n1. Running tests..."
	uv run pytest -v
	@echo "\n2. Checking governance..."
	uv run paracle governance health
	@echo "\n3. Building package..."
	uv build
	@echo "\n4. Checking package..."
	uv run twine check dist/*
	@echo "\n✅ Release checks passed!"

release-patch: ## Create patch release (0.0.X) [Windows: powershell scripts/bump-version.ps1 patch]
	@echo "Creating patch release..."
	@scripts/bump-version.sh patch

release-minor: ## Create minor release (0.X.0) [Windows: powershell scripts/bump-version.ps1 minor]
	@echo "Creating minor release..."
	@scripts/bump-version.sh minor

release-major: ## Create major release (X.0.0) [Windows: powershell scripts/bump-version.ps1 major]
	@echo "Creating major release..."
	@scripts/bump-version.sh major

docs-serve: ## Serve documentation locally
	uv run mkdocs serve

docs-build: ## Build documentation
	uv run mkdocs build

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install

pre-commit-run: ## Run pre-commit on all files
	uv run pre-commit run --all-files

validate: ## Validate governance compliance
	uv run paracle validate --all

validate-ai: ## Validate AI instruction files
	uv run paracle validate ai-instructions

validate-governance: ## Validate .parac/ structure
	uv run paracle validate governance

validate-roadmap: ## Validate roadmap consistency
	uv run paracle validate roadmap

cli-hello: ## Run CLI hello command
	uv run paracle hello

all: install-dev lint test ## Run install, lint, and test
