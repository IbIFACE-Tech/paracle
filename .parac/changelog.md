# Changelog

All notable changes to Paracle will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Skills in manifest.yaml (2026-01-07)

- **Structured skills assignment**: Skills now defined in `manifest.yaml` under each agent's `skills:` field
- **manifest.yaml priority**: SkillLoader reads from manifest.yaml first, falls back to SKILL_ASSIGNMENTS.md
- **Agent enrichment**: AgentDiscovery enriches agents with tools and skills from manifest
- **Validation methods**: Added `validate_agent_skills()` and `validate_all_agents()` to SkillLoader
- **IDE skill export**: `paracle ide sync` now exports skills to all IDE platforms automatically
- **Platform support**: Exports to .github/skills/, .cursor/skills/, .claude/skills/, .codex/skills/
- **CLI option**: Added `--with-skills/--no-skills` to `paracle ide sync` (default: enabled)

#### Agent Skills System (2025-12-24)

- **Dual format support**: YAML (lightweight) + SKILL.md (rich documentation)
- **Built-in skills**: question-answering, code-generation, data-analysis, text-summarization, api-integration
- **Framework development skills**: framework-architectur<https://agentskills.io/specification>anced)
- **Agent Skills standard compliance**: Full support for <https://agentskills.io/specification>
- **Skill loader**: Automatic detection and loading of both formats
- **Skill categories**: communication, analysis, creation, transformation, integration, memory
- **Skill levels**: basic, intermediate, advanced, expert

#### AI IDE Instructions (2025-12-24)

- **9 IDE-specific instruction files** for Paracle .parac configuration:
  - Cursor (.cursorrules) - Detailed rules with comprehensive skills section
  - Minimal (.paracle) - Quick reference format
  - Cline (.clinerules) - Condensed rules
  - Windsurf (.windsurfrules) - Medium-detail format
  - GitHub Copilot (.github-copilot.md) - Full guide
  - DeepSeek Coder (.deepseek-coder.md) - Technical focus
  - Google Gemini (.google-gemini.md) - Gemini-optimized
  - Mistral Codestral (.mistral-codestral.md) - Code-first approach
  - Kimi K2 (.kimi-k2.md) - Bilingual CN/EN
- **Skills integration**: All IDE instructions include agent skills documentation
- **Format comparison**: Each file explains when to use YAML vs SKILL.md

#### User Templates (2025-12-24)

- **Complete .parac-template** for end users with 15+ configuration files
- **Skills templates**: 5 built-in skills (3 SKILL.md, 2 YAML examples)
- **Configuration examples**: project.yaml, agent specs, workflows, policies

- **Documentation**: README files explaining each component

#### Roadmap Updates (2025-12-24)

- **Phase 1 Core Domain**: Extended with SkillSpec model, SkillLoader implementation
- **Agent Skills integration**: SKILL.md format parsing, dual format validation
- **Next steps documentation**: Comprehensive examples and format comparison

- Initial .parac workspace structure
- Phase 0 Foundation setup
- Core project configuration

## [0.0.1] - 2025-12-24

### Added

- Project inception
- Repository structure with .parac workspace
- Initial roadmap (17 weeks, 5 phases)
- Foundation phase deliverables
