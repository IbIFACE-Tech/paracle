# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Centralized Version Management** (`paracle_core.version`)
  - Single source of truth for version number
  - All modules import from `paracle_core.version`
  - Version metadata: major, minor, patch components
  - Release information: date, name, codename
  - Feature flags based on version
  - Utility functions: `get_version()`, `get_version_info()`, `format_version()`
- **Migration Guide** (`content/docs/migration-guide.md`)
  - 600+ lines comprehensive upgrade documentation
  - Version compatibility matrix
  - Breaking changes documentation
  - Automated migration scripts
  - Common issues and solutions
  - Rollback procedures
- **Health Check Command** (`paracle doctor`)
  - 7 comprehensive health checks
  - Validates Python environment, installation, workspace, config
  - Checks optional dependencies (Docker, SSH, AI providers)
  - System resource monitoring
  - Auto-fix suggestions with `--fix` flag
  - Verbose mode with `--verbose` flag
- **Watch Mode for IDE Sync** (`paracle ide sync --watch`)
  - Real-time file watching for `.parac/` changes
  - Auto-sync IDE configs on agent/workflow/policy updates
  - Debounced syncs (2s cooldown)
  - Watches agents, workflows, memory, roadmap, policies
  - Graceful shutdown with Ctrl+C
- **Developer Experience Metrics** (`content/docs/dx-metrics.md`)
  - 500+ lines DX measurement framework
  - 7 core metrics with baselines
  - Time to First Value: 3-4 min target
  - API Surface: 45 symbols
  - Error Clarity: 7.5/10 current score
  - Measurement methods and improvement targets
  - ICE prioritization framework
- **MCP Diagnostics Tool** (`mcp_diagnose`) for agents
  - Automatic detection of MCP server and UV issues
  - Self-healing capabilities with `auto_fix=True`
  - Actions: check, fix, stop_processes, reinstall
  - Cross-platform support (Windows, Linux, macOS)
- MCP server wrapper scripts for production deployments
  - `scripts/mcp-server.ps1` (PowerShell - Windows)
  - `scripts/mcp-server.sh` (Bash - Linux/macOS)
  - Auto-detection of virtual environment paths
- Process management scripts
  - `scripts/stop-mcp-processes.ps1` (PowerShell)
  - `scripts/stop-mcp-processes.sh` (Bash)
  - `scripts/clean-install-mcp.ps1` (Clean reinstall utility)
- Comprehensive troubleshooting documentation
  - `scripts/README-MCP-FIX.md` - Quick reference guide
  - `content/docs/tools/mcp-diagnostics-tool.md` - Agent usage guide

### Changed

- Updated `.vscode/mcp.json` to use `uv run --no-sync`
  - Prevents rebuilds on every MCP server start
  - Eliminates file lock issues on `paracle.exe`
  - Works across all platforms without hardcoded paths
- **Version Management Centralized**
  - All files now import from `paracle_core.version`
  - CLI dynamically reads version
  - `hello` command uses `format_version()`
  - Eliminates version drift across files

### Fixed

- MCP server startup failures caused by `uv run` rebuilds
- File lock issues on `paracle.exe` (Windows)
- Process conflicts during UV operations

### Documentation

- Added migration guide to README
- Added DX metrics to README
- Updated version references across all documentation

---

## [1.0.3] - 2026-01-10

### Added

- **Business Metrics CLI Commands** (`paracle metrics`)
  - `paracle metrics summary` - Comprehensive metrics with health score
  - `paracle metrics cost` - Cost breakdown and budget status
  - `paracle metrics usage` - Token and request usage patterns
  - `paracle metrics performance` - Latency and throughput metrics
  - `paracle metrics quality` - Success rate and error metrics
- Business metrics API client methods in `api_client.py`
- Rich console output with color-coded health indicators
- Health score calculation (0-100 scale)

### Changed

- Updated project version to 1.0.3 in `pyproject.toml`
- Updated CLI version to 1.0.3 in `main.py`

### Documentation

- Created comprehensive CLI implementation for business metrics
- Added 400+ lines of CLI command code
- Integration with existing `BusinessMetrics` class

---

## [1.0.2] - 2026-01-10

### Added

- Documentation of dogfooding separation (`.parac/DOGFOODING_SEPARATION.md`)
- Quick reference guide for file placement (`WHERE_TO_PUT_FILES.md`)
- Updated README files for `.parac/tools/hooks/` and `scripts/` with clear separation
- VS Code support in IDE setup (`paracle ide setup --ide vscode`)
- Documentation structure consolidation to `content/` directory
- All user-facing docs now in `content/docs/`
- All examples now in `content/examples/`
- All templates now in `content/templates/`

### Changed

- Updated project version to 1.0.2 in `pyproject.toml`
- Updated CLI version display to 1.0.2
- Consolidated documentation paths in governance files
- Updated `.parac/STRUCTURE.md` to reflect definitive structure
- Updated `.parac/GOVERNANCE.md` with new file placement rules
- Updated `.github/copilot-instructions.md` with new paths

### Fixed

- **CRITICAL**: Fixed `ModuleNotFoundError: No module named 'docker.errors'` when running CLI
  - Made Docker imports optional in `paracle_sandbox` package
  - Added graceful fallback when Docker is not installed
  - Users now get clear error message to install Docker when needed: `pip install docker psutil`
  - Fixed in files:
    - `packages/paracle_sandbox/__init__.py`
    - `packages/paracle_sandbox/manager.py`
    - `packages/paracle_sandbox/monitor.py`
- Fixed IDE setup failing with "Unsupported IDE: vscode"
  - Added VS Code configuration to `IDEConfigGenerator.SUPPORTED_IDES`
  - VS Code now uses GitHub Copilot template
- Fixed linting errors in sandbox manager and monitor modules
- Fixed type hints compatibility (replaced `Type | None` with `Optional[Type]`)

### Documentation

- Moved all documentation from root `docs/` to `content/docs/`
- Removed empty root directories (`docs/`, `examples/`, `templates/`)
- All documentation paths now consistent across the project

---

## [1.0.1] - 2026-01-09

### Added

- Performance benchmarking guide and examples
- Agent groups and A2A protocol documentation
- Agent CLI enhancements (inspect, validate, test commands)
- Remote SSH support verification and quick reference
- Sandbox implementation with Docker support
- Workflow-Kanban integration
- 12 new meta capabilities (polyglot, browser, cloud, database, etc.)
- Enhanced IDE integration and tooling

### Changed

- Phase 10 completion increased to 98%
- Enhanced security improvements and compliance updates

- Improved CI/CD pipelines with benchmark workflow

### Fixed

- Various security vulnerabilities (2 low-severity identified by Dependabot)
- Code style and linting issues across multiple packages
- Test coverage improvements (88% overall coverage)

---

## [1.0.0] - 2026-01-08

### Added

- Complete Phase 10 features
- Production-ready release
- 5-layer governance system
- Security audit complete (95/100 score)
- ISO 27001/42001 compliance

- SOC2 compliance preparation
- GitHub Actions CI/CD workflows
- Comprehensive test suite (613+ tests)

### Security

- Achieved 95/100 security score
- OWASP Top 10 compliance
- Secret detection and management
- Dependency vulnerability scanning
- Bandit security scanning
- Safety checks for known vulnerabilities

---

## [0.1.0] - 2026-01-06

### Added

- Initial beta release
- Core framework functionality

- Basic agent execution
- Tool integration
- MCP server support
- CLI commands
- API server

### Changed

- Project structure finalized
- Documentation improvements

---

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
- **Documentation** for documentation-only changes

---

## Versioning Guide

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New functionality in a backwards compatible manner
- **PATCH** version (0.0.X): Backwards compatible bug fixes

---

[Unreleased]: https://github.com/IbIFACE-Tech/paracle-lite/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/IbIFACE-Tech/paracle-lite/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/IbIFACE-Tech/paracle-lite/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/IbIFACE-Tech/paracle-lite/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/IbIFACE-Tech/paracle-lite/releases/tag/v0.1.0
