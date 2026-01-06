# Phase 6: Developer Experience & Accessibility - Detailed Specification

**Version:** 1.0
**Date:** 2026-01-06
**Status:** Planning
**Owner:** PM Agent
**Related:** ADR-017, Strategic Action Plan

---

## Executive Summary

**Goal:** Reduce learning curve by ~50% and make Paracle accessible to developers of all skill levels.

**Duration:** 4 weeks (Weeks 21-24)
**Priority:** CRITICAL - Drives adoption
**Budget:** ~$42K (14 developer-weeks @ $3K/week)
**Success:** Time to first agent < 2 min, tutorial completion >70%, 10+ examples

---

## Deliverables

### D6.1: Quick Start Mode (Lite Mode)

**Priority:** P0 (Highest - Blocker for others)
**Effort:** 2 weeks (1 developer)
**Owner:** Coder Agent

#### Description

Minimal configuration mode for rapid prototyping with 5 files instead of 30+.

#### Implementation

**New Command:**
```bash
paracle init --lite [project-name]
```

**Lite .parac/ Structure:**
```
.parac/
  project.yaml          # Basic config only (name, version, agents_dir)
  agents/
    specs/
      my-agent.md       # Single agent template
  memory/
    current_state.yaml  # Minimal state tracking (phase, status, progress)
```

**Comparison:**
| Feature             | Lite Mode | Full Mode |
| ------------------- | --------- | --------- |
| Files               | 5         | 30+       |
| Subdirectories      | 3         | 10+       |
| Governance          | No        | Yes       |
| Roadmap             | No        | Yes       |
| Policies            | No        | Yes       |
| Agent specs         | 1 default | Multiple  |
| Time to first agent | <2 min    | ~10 min   |

**Upgrade Path:**
```bash
paracle upgrade --full
# Generates missing governance files:
# - roadmap/roadmap.yaml
# - roadmap/decisions.md
# - policies/policy-pack.yaml
# - memory/context/open_questions.md
# - etc.
```

#### Acceptance Criteria

- ✅ `paracle init --lite` creates minimal structure
- ✅ Can execute agent immediately after init
- ✅ `paracle upgrade --full` adds governance files
- ✅ Documentation explains lite vs full mode
- ✅ 5+ unit tests for init/upgrade commands

#### Files to Create/Modify

**New:**
- `packages/paracle_cli/commands/init.py` - Init command with --lite flag
- `packages/paracle_cli/commands/upgrade.py` - Upgrade command
- `packages/paracle_core/templates/lite/` - Lite mode templates
- `tests/unit/cli/test_init_lite.py` - Unit tests

**Modified:**
- `packages/paracle_cli/main.py` - Register init/upgrade commands
- `docs/getting-started.md` - Add lite mode section
- `.parac/CONFIG_FILES.md` - Document lite mode

---

### D6.2: Interactive Tutorial

**Priority:** P0 (Highest)
**Effort:** 3 weeks (1 developer)
**Owner:** Coder Agent + Documenter Agent

#### Description

Built-in step-by-step tutorial via CLI with progress tracking and checkpoints.

#### Implementation

**Command:**
```bash
paracle tutorial
# Launches interactive tutorial:
# Step 1/6: Create your first agent
# Step 2/6: Add tools to agent
# Step 3/6: Test agent locally
# Step 4/6: Configure LLM provider
# Step 5/6: Run first workflow
# Step 6/6: Review and iterate

paracle tutorial resume
# Resumes from last checkpoint
```

**Tutorial Structure:**

**Step 1: Create First Agent (5 min)**
- Interactive prompts for agent name, description
- Creates `.parac/agents/specs/my-agent.md`
- Validates YAML frontmatter
- Shows result

**Step 2: Add Tools (5 min)**
- Lists available built-in tools
- User selects 2-3 tools (filesystem, http, shell)
- Updates agent spec with tools
- Explains tool permissions

**Step 3: Test Agent Locally (3 min)**
- Generates simple test prompt
- Executes agent with test prompt
- Shows execution logs
- Explains output

**Step 4: Configure LLM Provider (5 min)**
- Lists supported providers (OpenAI, Anthropic, etc.)
- Prompts for API key (with security warning)
- Creates `.env` file
- Tests provider connection

**Step 5: Run First Workflow (7 min)**
- Creates simple workflow (e.g., "analyze file")
- Shows workflow YAML
- Executes workflow
- Displays results

**Step 6: Review & Next Steps (5 min)**
- Recap of what was learned
- Pointers to:
  - Example gallery
  - Documentation
  - Community (Discord, templates)
- Badge: "Tutorial Complete! 🎓"

**Progress Tracking:**
```yaml
# Stored in .parac/memory/.tutorial_progress
version: 1
started: "2026-01-07T10:00:00Z"
last_step: 3
checkpoints:
  step_1: completed
  step_2: completed
  step_3: in_progress
  step_4: not_started
  step_5: not_started
  step_6: not_started
```

#### Acceptance Criteria

- ✅ 6 tutorial steps implemented
- ✅ Progress tracking with checkpoints
- ✅ Can resume from any checkpoint
- ✅ Interactive prompts with validation
- ✅ Help available at each step
- ✅ Tutorial completion rate >70% (tracked)
- ✅ Time to complete: <30 minutes
- ✅ 10+ unit tests for tutorial logic

#### Files to Create/Modify

**New:**
- `packages/paracle_cli/commands/tutorial.py` - Tutorial orchestrator
- `packages/paracle_cli/tutorial/steps/` - Step implementations
- `packages/paracle_cli/tutorial/progress.py` - Progress tracking
- `packages/paracle_core/templates/tutorial/` - Tutorial templates
- `tests/unit/cli/test_tutorial.py` - Unit tests

**Modified:**
- `packages/paracle_cli/main.py` - Register tutorial command
- `docs/getting-started.md` - Link to tutorial

---

### D6.3: Example Gallery

**Priority:** P1 (High)
**Effort:** 4 weeks (2 developers)
**Owner:** Multiple agents (Coder, Documenter, Tester)

#### Description

10+ real-world, production-ready examples categorized by use case.

#### Example Categories

**1. Business Automation (3 examples)**
- **Customer Support Agent** - Ticket classification, response generation
- **Invoice Processing** - Extract data, validate, categorize
- **Email Categorization** - Auto-label, prioritize, route

**2. Developer Tools (3 examples)**
- **Code Reviewer** - PR analysis, style check, suggestions
- **Test Generator** - Generate pytest tests from code
- **Documentation Writer** - Generate README, API docs

**3. Data Analysis (2 examples)**
- **Data Analyst Agent** - CSV analysis, insights, visualizations
- **Report Generator** - Aggregate data, create reports

**4. Research & Knowledge (2 examples)**
- **Research Assistant** - Literature review, summarization
- **Knowledge Base Builder** - Extract, organize, index content

#### Example Structure

Each example includes:

```
examples/gallery/<category>/<name>/
  README.md           # Overview, use case, prerequisites
  .parac/             # Full .parac/ structure
    agents/
      specs/
        <name>-agent.md
    workflows/
      <name>-workflow.yaml
  data/               # Sample data files
    input/
    expected_output/
  tests/              # Example-specific tests
    test_<name>.py
  requirements.txt    # Additional dependencies (if any)
```

**README.md Template:**
```markdown
# <Example Name>

## Overview
One-paragraph description of what this example does.

## Use Case
When to use this example, what problems it solves.

## Prerequisites
- API keys needed (OpenAI, etc.)
- Data format requirements
- Dependencies

## Quick Start
```bash
cd examples/gallery/<category>/<name>
cp .env.example .env
# Edit .env with your API keys
paracle agents run <agent-name> "sample prompt"
```

## Expected Output
What you should see when running the example.

## Customization
How to adapt this example for your use case.

## Learn More
- Related examples
- Documentation links
```

#### CLI Integration

```bash
paracle examples list
# Lists all examples with categories

paracle examples show <name>
# Shows example details (README)

paracle examples create <name> [project-dir]
# Copies example to project directory
```

#### Acceptance Criteria

- ✅ 10+ examples implemented
- ✅ Each example tested and documented
- ✅ Sample data included
- ✅ All examples execute successfully
- ✅ CLI commands for discovery/creation
- ✅ Examples categorized (4 categories)
- ✅ >50% of users try at least one example
- ✅ Documentation links to gallery

#### Files to Create/Modify

**New:**
- `examples/gallery/<category>/<name>/` - 10+ example directories
- `examples/gallery/README.md` - Gallery overview
- `packages/paracle_cli/commands/examples.py` - Examples CLI
- `tests/integration/examples/` - Example tests

**Modified:**
- `docs/getting-started.md` - Link to gallery
- `README.md` - Add gallery section

---

### D6.4: Project Templates

**Priority:** P1 (High)
**Effort:** 2 weeks (1 developer)
**Owner:** Architect Agent

#### Description

Three templates for different project scales (Small, Medium, Enterprise).

#### Templates

**1. Small Template - Prototyping**
- **Use Case:** Single developer, rapid prototyping
- **Mode:** Lite by default
- **Agents:** 1-2 agents
- **Persistence:** SQLite
- **Logging:** Basic (console only)
- **Governance:** Minimal

```bash
paracle init --template small my-project
```

**Structure:**
```
my-project/
  .parac/
    project.yaml (lite mode config)
    agents/specs/main-agent.md
    memory/current_state.yaml
  .env.example
  README.md
```

**2. Medium Template - Team Project**
- **Use Case:** Small team, staging environment
- **Mode:** Full governance
- **Agents:** 5-10 agents
- **Persistence:** SQLite → PostgreSQL option
- **Logging:** Comprehensive (file + structured)
- **Governance:** Full (.parac/ complete)
- **CI/CD:** GitHub Actions template

```bash
paracle init --template medium my-project
```

**Structure:**
```
my-project/
  .parac/ (full structure)
    roadmap/
    policies/
    agents/specs/ (5 agent templates)
    memory/
    workflows/
  .github/
    workflows/ci.yaml
  docker-compose.yaml
  .env.example
  README.md
```

**3. Enterprise Template - Production**
- **Use Case:** Multi-team, production environment
- **Mode:** Full governance + security
- **Agents:** 20+ agent templates
- **Persistence:** PostgreSQL + pgvector
- **Logging:** Audit trail (ISO 42001)
- **Governance:** Full + compliance
- **Security:** Secrets management, RBAC
- **Observability:** Metrics, tracing, alerts
- **Multi-environment:** dev/staging/prod

```bash
paracle init --template enterprise my-project
```

**Structure:**
```
my-project/
  .parac/ (full + security)
    policies/
      SECURITY.md (comprehensive)
      COMPLIANCE.md (ISO 42001)
    agents/specs/ (20+ templates by role)
  .github/
    workflows/
      ci.yaml
      security-scan.yaml
      deploy.yaml
  docker/
    Dockerfile.api
    Dockerfile.worker
    docker-compose.prod.yaml
  kubernetes/
    deployments/
    services/
  docs/
    architecture.md
    runbooks/
  scripts/
    setup-secrets.sh
  .env.dev
  .env.staging
  .env.prod.example
  README.md
```

#### Template Comparison

| Feature       | Small  | Medium    | Enterprise |
| ------------- | ------ | --------- | ---------- |
| Files         | 5      | 30+       | 50+        |
| Agents        | 1-2    | 5-10      | 20+        |
| Governance    | Lite   | Full      | Full + Sec |
| Persistence   | SQLite | SQLite/PG | PostgreSQL |
| CI/CD         | No     | Basic     | Full       |
| Security      | Basic  | Medium    | High       |
| Multi-env     | No     | No        | Yes        |
| Compliance    | No     | No        | ISO 42001  |
| Observability | Basic  | Medium    | Full       |

#### Upgrade Path

```bash
# Small → Medium
paracle template upgrade --to medium

# Medium → Enterprise
paracle template upgrade --to enterprise
```

#### Acceptance Criteria

- ✅ 3 templates implemented
- ✅ Each template tested
- ✅ Clear differentiation documented
- ✅ Upgrade path works
- ✅ Templates used in >60% of new projects
- ✅ Documentation per template

#### Files to Create/Modify

**New:**
- `packages/paracle_core/templates/small/` - Small template
- `packages/paracle_core/templates/medium/` - Medium template
- `packages/paracle_core/templates/enterprise/` - Enterprise template
- `packages/paracle_cli/commands/template.py` - Template CLI
- `docs/templates.md` - Template documentation

**Modified:**
- `packages/paracle_cli/commands/init.py` - Add --template flag
- `docs/getting-started.md` - Add templates section

---

### D6.5: Video Guides

**Priority:** P2 (Medium)
**Effort:** 3 weeks (1 video producer + 1 developer)
**Owner:** Documenter Agent + External Video Producer

#### Description

4-5 screen-recorded guides for visual learners.

#### Videos

**Video 1: Getting Started (5 minutes)**
- **Content:**
  - Installation (pip install paracle)
  - First agent creation (paracle init --lite)
  - Running first execution
  - Understanding output
- **Format:** Screen recording + voiceover
- **Tools:** OBS Studio, Audacity
- **Published:** YouTube + docs site

**Video 2: Agent Inheritance Explained (10 minutes)**
- **Content:**
  - Why inheritance? (Code reuse, composition)
  - Creating base agents (common settings)
  - Overriding behaviors (specialized agents)
  - Best practices (depth limit, clarity)
  - Live demo
- **Format:** Screen recording + slides + voiceover
- **Diagrams:** Inheritance tree visualization

**Video 3: Production Deployment (15 minutes)**
- **Content:**
  - Docker setup (Dockerfile, compose)
  - Environment configuration (.env, secrets)
  - API deployment (FastAPI, uvicorn)
  - Monitoring (logs, metrics)
  - Troubleshooting common issues
- **Format:** Live demo + terminal recording
- **Code samples:** GitHub repo

**Video 4: MCP Integration (10 minutes)**
- **Content:**
  - What is MCP? (Model Context Protocol)
  - Connecting MCP servers
  - Custom tool development
  - Testing MCP tools
  - Use cases
- **Format:** Screen recording + diagrams
- **Resources:** MCP documentation links

**Video 5: Best Practices (8 minutes)** (Optional)
- **Content:**
  - Project structure
  - Governance tips
  - Testing strategies
  - Cost optimization
  - Community resources
- **Format:** Presentation + examples

#### Production Process

1. **Script Writing** (1 week)
   - Outline content
   - Write narration scripts
   - Create diagrams/slides

2. **Recording** (1 week)
   - Screen recordings
   - Voiceover recording
   - Multiple takes

3. **Editing** (1 week)
   - Video editing
   - Audio cleanup
   - Add captions
   - Export (1080p MP4)

4. **Publishing**
   - Upload to YouTube
   - Embed in docs
   - Create thumbnails
   - SEO optimization

#### Success Metrics

- ✅ 4-5 videos published
- ✅ YouTube channel created
- ✅ Embedded in docs site
- ✅ >1,000 views per video (6 months)
- ✅ Positive user feedback ("helpful", "clear")

#### Acceptance Criteria

- ✅ Scripts reviewed and approved
- ✅ Videos recorded and edited
- ✅ Published on YouTube
- ✅ Embedded in documentation
- ✅ Captions/subtitles added
- ✅ Thumbnails created

#### Deliverables

**New:**
- `docs/videos.md` - Video gallery page
- Videos published to YouTube channel
- Video transcripts in docs

**Modified:**
- `docs/getting-started.md` - Link to videos
- `docs/index.md` - Add video section

---

### D6.6: Legacy Deliverables (From Old Phase 6)

**Priority:** P2 (Lower priority - deferred if needed)
**Effort:** 2 weeks (1 developer)
**Owner:** Coder Agent

#### execution_chains

Follow-up execution with feedback loop (retry mechanism).

#### agent_profiles

Agent configuration profiles for model variants (e.g., fast-agent, accurate-agent).

**Note:** These can be deferred to Phase 9 if Phase 6 runs over time. Focus on D6.1-D6.5 first.

---

## Timeline

### Week 21 (Target: 2026-01-07 to 2026-01-13)
- **D6.1:** Lite mode prototype (50% complete)
- **D6.2:** Tutorial design + step 1-2 implementation
- **D6.3:** Example 1-2 (Customer Support, Code Reviewer)
- **D6.4:** Template design + Small template
- **D6.5:** Script writing for Videos 1-2

### Week 22 (2026-01-14 to 2026-01-20)
- **D6.1:** Lite mode complete + tests
- **D6.2:** Tutorial steps 3-4 implementation
- **D6.3:** Examples 3-5 (Invoice, Test Gen, Data Analyst)
- **D6.4:** Medium + Enterprise templates
- **D6.5:** Record Videos 1-2

### Week 23 (2026-01-21 to 2026-01-27)
- **D6.2:** Tutorial steps 5-6 + polish
- **D6.3:** Examples 6-8 (Email, Docs, Report Gen)
- **D6.4:** Template upgrade path
- **D6.5:** Script + record Videos 3-4

### Week 24 (2026-01-28 to 2026-02-03)
- **D6.2:** Tutorial testing + docs
- **D6.3:** Examples 9-10 + gallery docs
- **D6.4:** Template testing + docs
- **D6.5:** Edit + publish all videos

**Phase 6 Complete:** 2026-02-03

---

## Resource Requirements

| Role             | Weeks  | Cost        |
| ---------------- | ------ | ----------- |
| Coder Agent      | 10     | $30,000     |
| Documenter Agent | 2      | $6,000      |
| Architect Agent  | 2      | $6,000      |
| Video Producer   | 3      | $5,000      |
| **Total**        | **17** | **$47,000** |

**Note:** Actual cost ~$42K assuming overlapping work and part-time contributors.

---

## Success Metrics

| Metric                   | Target        | Measurement                    |
| ------------------------ | ------------- | ------------------------------ |
| Time to First Agent      | < 2 minutes   | Tutorial analytics             |
| Tutorial Completion Rate | >70%          | Progress tracking logs         |
| Example Gallery Size     | 10+ examples  | Count in examples/gallery/     |
| Example Usage            | >50% try 1+   | CLI analytics                  |
| Template Adoption        | >60% use      | Init command analytics         |
| Video Views              | >1K per video | YouTube analytics (6 months)   |
| User Feedback            | "Easy"        | Survey, Discord, GitHub issues |

---

## Risks & Mitigations

### High Risks

1. **Resource Constraints** - Only 1-2 developers available
   - **Mitigation:** Prioritize D6.1-D6.3 (highest impact), defer D6.6

2. **Video Production Quality** - No in-house expertise
   - **Mitigation:** Contract experienced video producer or use screen recording tools

3. **Tutorial Complexity** - May be too long or too short
   - **Mitigation:** User testing with 5+ beta users, iterate based on feedback

### Medium Risks

4. **Example Maintenance** - 10+ examples to keep updated
   - **Mitigation:** Automated testing for examples, community contributions

5. **Template Divergence** - Templates may fall out of sync with framework
   - **Mitigation:** Template validation tests, update templates with each release

---

## Testing Strategy

### Unit Tests
- ✅ Lite mode init/upgrade commands
- ✅ Tutorial step logic
- ✅ Example CLI commands
- ✅ Template generation

### Integration Tests
- ✅ Full tutorial flow (end-to-end)
- ✅ Example execution (each example)
- ✅ Template initialization (each template)
- ✅ Upgrade paths (lite → full, small → medium → enterprise)

### User Testing
- ✅ 5+ beta testers for tutorial
- ✅ Feedback collection (survey)
- ✅ Iterate based on feedback

---

## Documentation

### New Documents
- [ ] `docs/lite-mode.md` - Lite mode guide
- [ ] `docs/tutorial.md` - Tutorial reference
- [ ] `docs/examples.md` - Example gallery index
- [ ] `docs/templates.md` - Template comparison guide
- [ ] `docs/videos.md` - Video gallery

### Updated Documents
- [ ] `docs/getting-started.md` - Add tutorial, lite mode, examples
- [ ] `docs/index.md` - Add Phase 6 features
- [ ] `README.md` - Update with Phase 6 highlights

---

## Phase 6 Retrospective (To be completed after Phase 6)

**Questions:**
1. Did we achieve the success metrics?
2. What worked well?
3. What didn't work?
4. Lessons learned?
5. Adjustments for Phase 7?

**Next Steps:**
- Conduct retrospective meeting
- Update `.parac/memory/summaries/phase_6_retrospective.md`
- Plan Phase 7 based on learnings

---

**Status:** Planning
**Next:** Begin D6.1 prototype (lite mode)
**Owner:** PM Agent
**Last Updated:** 2026-01-06
