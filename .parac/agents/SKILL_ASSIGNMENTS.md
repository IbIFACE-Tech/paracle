# Agent Skill Assignments

This document maps skills to agents based on their roles and responsibilities.

## Overview

Each agent has been assigned relevant skills from the `.parac/agents/skills/` directory to enhance their capabilities and provide specialized expertise.

## Assignments

### 🔧 Architect Agent

**Role**: System architecture design, module structure, and technical decision making.

**Skills**:

- `framework-architecture` - System design and architectural patterns
- `api-development` - API design and RESTful patterns
- `performance-optimization` - Performance profiling and optimization
- `security-hardening` - Security architecture and best practices
- `paracle-development` - Framework-specific development patterns

**Rationale**: Architects need deep understanding of system design, API patterns, and non-functional requirements (performance, security).

---

### 💻 Coder Agent

**Role**: Implementation of features, writing production-quality code.

**Skills**:

- `paracle-development` - Framework-specific implementation patterns
- `api-development` - FastAPI endpoints and schemas
- `tool-integration` - Custom tool development
- `provider-integration` - LLM provider integration
- `testing-qa` - Unit testing and test-driven development

**Rationale**: Coders focus on implementation, requiring expertise in framework patterns, API development, tool integration, and testing.

---

### 📚 Documenter Agent

**Role**: Technical documentation, API references, user guides.

**Skills**:

- `technical-documentation` - README, tutorials, API docs
- `paracle-development` - Framework knowledge for documentation
- `api-development` - API documentation patterns

**Rationale**: Documenters need writing expertise, framework understanding, and API knowledge to create comprehensive documentation.

---

### 📋 PM Agent

**Role**: Project coordination, roadmap management, progress tracking.

**Skills**:

- `workflow-orchestration` - Workflow and task coordination
- `agent-configuration` - Agent spec management
- `paracle-development` - Framework understanding for planning
- `cicd-devops` - CI/CD pipelines and deployment

**Rationale**: PMs coordinate workflows, manage configurations, and oversee deployment processes.

---

### 👀 Reviewer Agent

**Role**: Code review, quality assurance, standards enforcement.

**Skills**:

- `security-hardening` - Security review and vulnerability detection
- `performance-optimization` - Performance analysis and bottleneck identification
- `testing-qa` - Test coverage and quality validation
- `paracle-development` - Framework standards enforcement

**Rationale**: Reviewers ensure code quality, security, performance, and adherence to framework standards.

---

### 🧪 Tester Agent

**Role**: Test design, implementation, and quality validation.

**Skills**:

- `testing-qa` - Test strategies, pytest, coverage
- `security-hardening` - Security testing and validation
- `performance-optimization` - Performance testing and benchmarking
- `paracle-development` - Framework-specific testing patterns

**Rationale**: Testers focus on quality validation across functional, security, and performance dimensions.

---

### 🚀 Release Manager Agent

**Role**: Git workflows, versioning, releases, and deployment automation.

**Skills**:

- `cicd-devops` - CI/CD pipelines and deployment automation
- `git-management` - Conventional commits, branching strategy, git operations
- `release-automation` - Semantic versioning, packaging, publishing (PyPI/Docker)
- `workflow-orchestration` - Coordinating release process across teams
- `paracle-development` - Framework knowledge for version management

**Rationale**: Release Managers need expertise in git workflows, semantic versioning, CI/CD pipelines, and deployment automation to orchestrate the entire release lifecycle from commit to production.

---

### 🔒 Security Agent

**Role**: Security auditing, vulnerability detection, and compliance enforcement.

**Skills**:

- `security-hardening` - Security best practices, authentication, authorization
- `testing-qa` - Security testing and validation
- `paracle-development` - Framework security patterns
- `performance-optimization` - Security performance analysis (DoS prevention)

**Rationale**: Security agents need deep security expertise, testing capabilities for penetration testing, framework knowledge to identify vulnerabilities, and performance understanding to prevent security-related performance issues.

---

### 🎯 QA Agent (Senior QA Architect)

**Role**: Quality assurance architecture, test strategy design, quality metrics tracking, and comprehensive quality validation.

**Skills**:

- `testing-qa` - Primary expertise in test strategies, frameworks, and quality validation
- `security-hardening` - Security testing and compliance validation
- `performance-optimization` - Performance testing and benchmarking
- `paracle-development` - Framework-specific testing patterns and standards
- `api-development` - API testing strategies and contract testing
- `cicd-devops` - Test automation in CI/CD pipelines
- `workflow-orchestration` - Test workflow coordination and quality gates

**Rationale**: Senior QA Architects need comprehensive expertise across all quality dimensions - functional testing, security validation, performance benchmarking, and process automation. They orchestrate quality across the entire SDLC, establish quality gates, mentor teams on testing practices, and ensure delivery of high-quality software. This role bridges testing implementation (Tester Agent) with quality strategy and architecture.

---

## Skill Distribution Matrix

| Skill                    | Architect | Coder | Documenter | PM  | Reviewer | Tester | ReleaseManager | Security | QA  |
| ------------------------ | --------- | ----- | ---------- | --- | -------- | ------ | -------------- | -------- | --- |
| framework-architecture   | ✅         |       |            |     |          |        |                |          |     |
| api-development          | ✅         | ✅     | ✅          |     |          |        |                |          | ✅   |
| performance-optimization | ✅         |       |            |     | ✅        | ✅      |                | ✅        | ✅   |
| security-hardening       | ✅         |       |            |     | ✅        | ✅      |                | ✅        | ✅   |
| paracle-development      | ✅         | ✅     | ✅          | ✅   | ✅        | ✅      | ✅              | ✅        | ✅   |
| tool-integration         |           | ✅     |            |     |          |        |                |          |     |
| provider-integration     |           | ✅     |            |     |          |        |                |          |     |
| testing-qa               |           | ✅     |            |     | ✅        | ✅      |                | ✅        | ✅   |
| technical-documentation  |           |       | ✅          |     |          |        |                |          |     |
| workflow-orchestration   |           |       |            | ✅   |          |        | ✅              |          | ✅   |
| agent-configuration      |           |       |            | ✅   |          |        |                |          |     |
| cicd-devops              |           |       |            | ✅   |          |        | ✅              |          | ✅   |
| git-management           |           |       |            |     |          |        | ✅              |          |     |
| release-automation       |           |       |            |     |          |        | ✅              |          |     |

## Skill Coverage

- **Most Shared**: `paracle-development` (9 agents) - Core framework knowledge
- **Quality Focus**: `testing-qa` (5 agents), `security-hardening` (5 agents), `performance-optimization` (5 agents) - Comprehensive quality coverage
- **DevOps Focus**: `cicd-devops`, `git-management`, `release-automation` specialized for Release Manager
- **QA Leadership**: QA Agent has the broadest skill set (7 skills) for comprehensive quality architecture
- **Specialized**: `technical-documentation`, `tool-integration`, `provider-integration`, `framework-architecture` assigned to specific agents

## Notes

- All agents have `paracle-development` as it provides core framework understanding
- Quality-related skills (`testing-qa`, `security-hardening`, `performance-optimization`) are shared across Architect, Reviewer, Tester, Security, and QA agents
- QA Agent has the broadest skill set (7 skills) encompassing quality architecture, testing, security, performance, API testing, CI/CD, and workflow orchestration
- Security agent is the primary owner of security-hardening skill with deepest expertise
- Tester Agent focuses on test implementation while QA Agent provides strategic oversight and quality architecture
- Specialized skills are assigned to agents with direct responsibilities in those areas
- Skills can be discovered, activated, and executed following the progressive disclosure pattern

## Next Steps

1. **Validation**: Test that agents correctly load and use their assigned skills
2. **Extension**: Add new skills as framework capabilities expand
3. **Refinement**: Adjust skill assignments based on agent effectiveness
4. **Documentation**: Keep this mapping synchronized with agent and skill changes
