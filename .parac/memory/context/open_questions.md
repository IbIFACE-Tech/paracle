# Open Questions

This document tracks unresolved questions and decisions pending.

## Summary

| ID  | Question                      | Owner      | Priority | Deadline    | Status       |
| --- | ----------------------------- | ---------- | -------- | ----------- | ------------ |
| Q1  | Agent Inheritance Depth Limit | Architect  | High     | Phase 1 End | **Resolved** |
| Q2  | Event Store Implementation    | Architect  | Medium   | Phase 1 End | **Resolved** |
| Q3  | API Versioning Strategy       | Architect  | Low      | Phase 2 End | Open         |
| Q4  | Tool Calling Interface        | Architect  | High     | Phase 2 End | **Resolved** |
| Q5  | Memory Management Strategy    | Architect  | Medium   | Phase 2 End | **Resolved** |
| Q6  | Deployment Strategy           | PM         | Low      | Phase 4 End | **Resolved** |
| Q7  | Observability Stack           | Architect  | Medium   | Phase 4 End | Open         |
| Q8  | Contribution Guidelines       | PM         | Low      | Phase 1 End | Open         |
| Q9  | Documentation Hosting         | Documenter | Low      | Phase 5 End | Open         |
| Q10 | API Middlewares Stack         | Architect  | High     | Phase 3 End | **Resolved** |
| Q11 | ISO 42001 Compliance Strategy | Architect  | High     | Phase 4 End | **Resolved** |
| Q12 | Kanban Task Management        | Architect  | High     | Phase 6 End | **Resolved** |
| Q13 | Complexity vs Accessibility   | PM         | High     | Phase 6 End | Open         |
| Q14 | Learning Curve Reduction      | PM         | High     | Phase 6 End | Open         |
| Q15 | Performance at Scale          | Architect  | Medium   | Phase 7 End | Open         |
| Q16 | Community & Ecosystem Growth  | PM         | Critical | Phase 7 End | Open         |
| Q17 | Remote Development SSH        | Architect  | High     | Phase 8 End | **Resolved** |

---

## Architecture

### Q1: Agent Inheritance Depth Limit

**Status:** ✅ **Resolved**
**Priority:** High
**Owner:** Architect Agent
**Deadline:** End of Phase 1 (Week 4)
**Resolved Date:** 2025-12-25
**Decision:** 5 levels max with warning at 3+

**Context:** Need to decide max inheritance depth for agents

**DECISION (2025-12-25):**
Implemented in `paracle_domain/inheritance.py`:
- Max depth: 5 levels (configurable via `MAX_INHERITANCE_DEPTH`)
- Warning at 3+ levels for maintainability
- Circular dependency detection with `CircularInheritanceError`
- `validate_inheritance_chain()` for batch validation

See: [inheritance.py](../../../packages/paracle_domain/inheritance.py)

---

### Q2: Event Store Implementation

**Status:** ✅ **Resolved**
**Priority:** Medium
**Owner:** Architect Agent
**Deadline:** End of Phase 1 (Week 4)
**Resolved Date:** 2025-12-25
**Decision:** In-memory EventBus with SQLite persistence option

**Context:** Which event store to use for audit trail

**DECISION (2025-12-25):**
Implemented hybrid approach in `paracle_events/`:

- `paracle_events/bus.py` - In-memory EventBus with pub/sub
- `paracle_events/persistent_store.py` - SQLite persistence layer
- Wildcard subscriptions (e.g., `agent.*`)
- Event history for replay/debugging
- 33 unit tests (100% passing)

See: [paracle_events](../../../packages/paracle_events/)

---

### Q3: API Versioning Strategy

**Status:** Open
**Priority:** Low
**Owner:** Architect Agent
**Deadline:** End of Phase 2 (Week 8)
**Context:** How to version the API
**Options:**

- URL versioning (/v1/agents)
- Header versioning (Accept: application/vnd.paracle.v1+json)
- No versioning for v0.0.1

**Discussion:**

- URL versioning is common and simple
- v0.0.1 might not need versioning yet
- Defer to Phase 3?

**Recommendation:** URL versioning (/v1/) from start for stability

**Decision Needed By:** End of Phase 2

---

### Q13: Complexity vs Accessibility

**Status:** Open
**Priority:** High
**Owner:** PM Agent
**Deadline:** End of Phase 6 (Week 24)
**Context:** Governance model is thorough but may feel heavy for small projects. Need to balance power with accessibility.

**Challenge:**
- Multiple config files (project.yaml, manifest.yaml, roadmap.yaml, etc.)
- Extensive .parac/ structure (10+ subdirectories)
- Steep learning curve for simple use cases

**Options:**
1. **Lite Mode** - Minimal .parac/ for prototyping (`paracle init --lite`)
2. **Progressive Disclosure** - Start simple, add governance as needed
3. **Templates** - Small/Medium/Enterprise project templates
4. **Wizard** - Interactive setup with questions

**Discussion:**
- Lite mode would reduce initial barrier
- Templates provide clear paths for different scales
- Progressive disclosure allows growth
- Risk: fragmentation of approach

**Recommendation:** Implement all three:
- Lite mode for quick starts
- 3 templates (Small/Medium/Enterprise)
- Progressive disclosure via CLI prompts

**Decision Needed By:** Phase 6 planning

**Related:** Strategic feedback document (memory/knowledge/strategic_feedback_jan2026.md)

---

### Q14: Learning Curve Reduction

**Status:** Open
**Priority:** High
**Owner:** PM Agent
**Deadline:** End of Phase 6 (Week 24)
**Context:** Many concepts to grasp (agents, workflows, tools, inheritance, MCP, governance)

**Challenges:**
- Documentation is comprehensive but dense
- No visual guides or interactive tutorials
- Multiple configuration files to understand
- Concepts not introduced progressively

**Options:**
1. **Interactive Tutorial** - `paracle tutorial` command with step-by-step
2. **Video Guides** - Screen recordings for common workflows
3. **Visual Builder** - GUI for agent/workflow configuration
4. **Simplified Examples** - Clear path from Hello World to production
5. **Concept Map** - Visual diagram of relationships

**Discussion:**
- Interactive tutorial has highest ROI (build once, use always)
- Videos require maintenance but very accessible
- Visual builder is expensive but differentiating
- Examples should show progression of complexity

**Recommendation:** Phase 6 priorities:
1. Interactive tutorial (high priority)
2. 10+ simplified examples (high priority)
3. 4-5 video guides (medium priority)
4. Visual builder (Phase 7)

**Decision Needed By:** Phase 6 planning

**Related:** Strategic feedback document

---

### Q15: Performance at Scale

**Status:** Open
**Priority:** Medium
**Owner:** Architect Agent
**Deadline:** End of Phase 7 (Week 28)
**Context:** Current focus on correctness over performance (appropriate for v0.0.1), but need plan for scale

**Current State:**
- Async/await throughout (good foundation)
- No caching strategy
- No connection pooling
- Limited benchmarking

**Roadmap Coverage:**
- ✅ PostgreSQL migration planned (Phase 6)
- ✅ pgvector planned (Phase 6)
- ⚠️ Missing: Response caching, connection pooling

**Options:**
1. **Response Caching** - Redis/Valkey for LLM response cache
2. **Connection Pooling** - Database and HTTP connection reuse
3. **Async Optimization** - Review and optimize async patterns
4. **Rate Limiting** - Smart rate limit management across providers
5. **Benchmarking Suite** - Establish performance baselines

**Discussion:**
- Phase 6-7 is right time (after core features stable)
- Response caching has biggest impact (LLM calls expensive)
- Connection pooling prevents resource exhaustion
- Benchmarking needed to measure improvements

**Recommendation:**
- Phase 7 focus on performance
- Add items to roadmap:
  - Response caching (Redis/Valkey)
  - Connection pooling
  - Benchmarking suite
  - Performance documentation

**Decision Needed By:** Phase 6 retrospective

**Related:** Strategic feedback document

---

### Q16: Community & Ecosystem Growth

**Status:** Open
**Priority:** Critical
**Owner:** PM Agent
**Deadline:** End of Phase 7 (Week 28)
**Context:** Framework is production-ready but community is nascent. Need strategy for growth.

**Current State:**
- v0.0.1 released
- Limited examples
- No community structure
- No plugin marketplace

**Options:**
1. **Example Gallery** - 20+ real-world examples categorized
2. **Plugin System** - Extensibility mechanism for community
3. **Community Templates** - Agent/workflow marketplace
4. **Developer Advocates** - Blog posts, tutorials, talks
5. **Discord Community** - Real-time support and feedback
6. **Monthly Webinars** - Feature demos and Q&A

**Discussion:**
- Example gallery has highest immediate impact
- Plugin system enables long-term ecosystem
- Community templates create network effects
- Need balance between building and marketing

**Recommendation:** Phased approach:
- **Phase 6** (Foundation):
  - 10+ example gallery
  - Basic plugin system
  - GitHub Discussions setup

- **Phase 7** (Growth):
  - Community templates marketplace
  - Discord community
  - Monthly webinars
  - Blog series

- **Phase 8** (Scale):
  - Conference talks
  - Developer advocates
  - Enterprise success stories

**Success Metrics:**
- GitHub stars: 1,000+ (6 months)
- Weekly active users: 500+ (6 months)
- Community contributions: 20+ PRs/month

**Decision Needed By:** Phase 6 planning

**Related:** Strategic feedback document

---

## Features

### Q4: Tool Calling Interface

**Status:** ✅ **Resolved**
**Priority:** High
**Owner:** Architect Agent
**Deadline:** End of Phase 2 (Week 8)
**Resolved Date:** 2026-01-04
**Decision:** ADR-004 - Hybrid Built-in + MCP Architecture

**Context:** How should agents call tools?
**Options:**

- MCP only
- Internal + MCP
- Plugin system

**Discussion:**

- MCP is emerging standard
- Internal tools needed for core features
- Hybrid approach best for flexibility
- Security considerations for tool permissions

**Recommendation:** Hybrid - Internal tools + MCP for external

**DECISION (2026-01-04):**
Implemented **Hybrid Built-in + MCP architecture** with 3 tiers:
- **Tier 1**: 9 built-in tools (filesystem, HTTP, shell) - zero dependencies
- **Tier 2**: MCP integration for external tools
- **Tier 3**: Custom tools via `Tool` protocol

Security: All tools require explicit configuration (no defaults), sandboxing via `allowed_paths`/`allowed_commands`, audit logging.

See: [ADR-004](../../roadmap/decisions.md#adr-004-tool-calling-interface---hybrid-built-in--mcp)

---

### Q5: Memory Management Strategy

**Status:** Open
**Priority:** Medium
**Owner:** Architect Agent
**Deadline:** End of Phase 2 (Week 8)
**Context:** How to manage agent memory/context
**Options:**

- Simple in-memory (session-based)
- Persistent (SQLite/Redis)
- Vector store (for semantic search)

**Discussion:**

- Start simple with in-memory
- Add persistence in Phase 2
- Vector store planned for v0.5.0 (Knowledge Engine)
- Must consider memory limits

**Recommendation:** In-memory for v0.0.1, SQLite persistence optional

**Decision Needed By:** End of Phase 2

---

## Operations

### Q6: Deployment Strategy

**Status:** Open
**Priority:** Low
**Owner:** PM Agent
**Deadline:** End of Phase 4 (Week 15)
**Context:** Recommended deployment approach
**Options:**

- Docker Compose (simple)
- Kubernetes (scalable)
- Serverless (cost-effective)

**Discussion:**

- Docker Compose for v0.0.1
- Document all options
- Users choose based on needs
- Multi-cloud support in v0.9.0

**Recommendation:** Docker Compose with documented alternatives

**Decision Needed By:** Phase 4

---

### Q7: Observability Stack

**Status:** Open
**Priority:** Medium
**Owner:** Architect Agent
**Deadline:** End of Phase 4 (Week 15)
**Context:** Which observability tools to use
**Options:**

- Prometheus + Grafana (standard)
- OpenTelemetry (modern)
- Simple logging + metrics endpoint

**Discussion:**

- Simple logging for v0.0.1
- OpenTelemetry for future (v0.3.0+)
- Don't over-engineer early
- ISO 42001 requires observability

**Recommendation:** Structured logging (JSON) + metrics endpoint, OpenTelemetry in Phase 4

**Decision Needed By:** Phase 4

---

### Q10: API Middlewares Stack

**Status:** ✅ **Resolved**
**Priority:** High
**Owner:** Architect Agent
**Deadline:** End of Phase 3 (Week 12)
**Resolved Date:** 2026-01-04
**Decision:** ADR-010 - Layered Middleware Stack

**Context:** Production-grade API requires proper middleware chain for observability, security, and compliance.

**DECISION (2026-01-04):**
Implemented **layered middleware stack** (order matters - first added = last executed):

1. **SecurityHeadersMiddleware** (Outermost)
   - OWASP security headers: HSTS, CSP, X-Frame-Options, X-XSS-Protection
   - Referrer-Policy, Permissions-Policy
   - Production HSTS enforcement

2. **CORSMiddleware**
   - Configurable origins via `SecurityConfig`
   - Credential support (environment-specific)
   - Rate limit headers exposed

3. **RequestLoggingMiddleware** (Innermost)
   - Correlation ID generation (X-Correlation-ID)
   - Request/response logging with timing
   - ISO 42001 audit trail
   - Error context capture

4. **Rate Limiting** (Dependency Injection, not middleware)
   - Per-client IP sliding window
   - Burst protection
   - Automatic blocking on abuse
   - Why DI: Selective application, per-endpoint limits, better testing

5. **Authentication** (Dependency Injection)
   - OAuth2 JWT tokens
   - Why DI: Selective protection, better FastAPI integration

**Configuration:** Centralized in `paracle_api.security.config.SecurityConfig`

See: [ADR-010](../../roadmap/decisions.md#adr-010-api-middlewares-stack)

**Required Middlewares:**

| Middleware     | Purpose                    | Priority | Phase |
| -------------- | -------------------------- | -------- | ----- |
| RequestID      | Correlation ID for tracing | Critical | 3     |
| Logging        | Structured JSON logging    | Critical | 3     |
| Timing         | Response time metrics      | High     | 3     |
| ErrorHandler   | Consistent error format    | Critical | 3     |
| Authentication | JWT/API Key validation     | High     | 3     |
| RateLimiting   | Abuse protection           | High     | 3     |
| AuditLog       | ISO 42001 audit trail      | Critical | 4     |

**Request Flow:**
```
Request → RequestID → Logging → Timing → Auth → RateLimit → Router
Response ← Logging ← Timing ← ErrorHandler ← Router
```

**Discussion:**

- RequestID essential for distributed tracing
- Logging must be structured (JSON) for observability
- Timing feeds into P95/P99 metrics
- Auth deferred to Phase 3 with full API
- AuditLog critical for ISO 42001 compliance
- All middlewares must be configurable

**Recommendation:** Implement core middlewares (RequestID, Logging, Timing, ErrorHandler) in Phase 3, add Auth/RateLimit/AuditLog progressively.

**Decision Needed By:** Phase 3 Start

---

### Q11: ISO 42001 Compliance Strategy

**Status:** ✅ **Resolved**
**Priority:** High
**Owner:** Architect Agent
**Deadline:** End of Phase 4 (Week 15)
**Resolved Date:** 2026-01-04
**Decision:** ADR-011 - Layered Compliance Architecture

**Context:** Paracle targets ISO/IEC 42001 compliance for AI governance. Need to plan compliance requirements.

**DECISION (2026-01-04):**
Implemented **layered compliance architecture** with progressive enhancement:

**Phase 1: Foundation (v0.0.1 - ✅ COMPLETE)**
- **~40% ISO 42001 Coverage**
- Immutable `AuditEvent` model with 10 categories
- Correlation ID request tracing
- JWT authentication with audit logging
- Tool execution audit trail
- File-based audit storage (NDJSON, `.parac/logs/audit.log`)
- Security: sandboxing, permissions, input validation

**Phase 2: Enhanced Governance (v0.5.0 - Q2 2026)**
- **~65% Coverage**
- Policy engine (`paracle_governance`) with approval workflows
- Risk assessment engine (`paracle_risk`)
- Data governance: classification, lineage, PII detection
- SQLite audit database with full-text search
- Retention policies (critical: 7 years, info: 30 days)

**Phase 3: Advanced Compliance (v0.7.0 - Q4 2026)**
- **~85% Coverage**
- Automated compliance testing
- AI explainability & decision tracking
- Bias detection & mitigation
- External audit support with evidence collection

**Phase 4: Enterprise Compliance (v0.9.0 - Q2 2027)**
- **~95% Coverage - Certifiable**
- Multi-tenant compliance
- Regulatory packs: GDPR, HIPAA, SOC 2
- ML-powered risk prediction
- Board-level reporting

**Current Capabilities (v0.0.1):**
- ✅ Audit trail for all API calls
- ✅ Agent execution logging
- ✅ Tool execution audit
- ✅ Authentication events audited

See: [ADR-011](../../roadmap/decisions.md#adr-011-iso-42001-compliance-strategy)

**ISO 42001 Key Requirements:**

| Requirement             | Description                 | Implementation              |
| ----------------------- | --------------------------- | --------------------------- |
| **4.1 Context**         | Organization context for AI | `.parac/policies/`          |
| **5.2 AI Policy**       | Documented AI policy        | `policy-pack.yaml`          |
| **6.1 Risk Assessment** | AI risk identification      | `paracle_risk/` (v0.7.0)    |
| **7.2 Competence**      | Human oversight             | Approval workflows          |
| **8.4 AI Development**  | Development lifecycle       | Event sourcing, audit trail |
| **9.1 Monitoring**      | Performance monitoring      | Observability stack         |
| **9.2 Internal Audit**  | Audit processes             | `paracle_audit/` (v0.7.0)   |
| **10.1 Nonconformity**  | Incident management         | Event replay, rollback      |

**Paracle Components for Compliance:**

```
v0.0.1 (Foundation):
├── Event sourcing (audit trail)
├── Policy enforcement
└── Structured logging

v0.5.0 (Knowledge):
├── Explainability hooks
└── Decision logging

v0.7.0 (Governance):
├── paracle_governance/ - Policy engine
├── paracle_risk/ - Risk assessment
├── paracle_audit/ - Audit trail & reports
└── Approval workflows
```

**Discussion:**

- Foundation (event sourcing, policies) already planned
- Governance package (v0.7.0) handles most requirements
- Need explainability for AI decisions
- Human-in-the-loop for critical decisions
- Audit trail must be immutable
- Consider certification timeline

**Key Decisions Needed:**

1. Audit log format and retention policy
2. Risk scoring methodology
3. Approval workflow design
4. Explainability level for AI decisions
5. Certification target date

**Recommendation:**
- Implement foundation in v0.0.1 (events, policies, logging)
- Full governance in v0.7.0 (Q1 2026)
- Target certification readiness in v1.0.0 (Q4 2026)

**Decision Needed By:** Phase 4 Start

---

## Community

### Q8: Contribution Guidelines

**Status:** Open
**Priority:** Low
**Owner:** PM Agent
**Deadline:** End of Phase 1 (Week 4)
**Context:** How to structure contribution process
**Options:**

- Full CONTRIBUTING.md from start
- Minimal guidelines, evolve
- Wait for first external contributor

**Discussion:**

- Basic guidelines already exist
- Evolve based on feedback
- Need DCO/CLA decision

**Recommendation:** Expand CONTRIBUTING.md with clear process

**Decision Needed By:** End of Phase 1

---

### Q9: Documentation Hosting

**Status:** Open
**Priority:** Low
**Owner:** Documenter Agent
**Deadline:** End of Phase 5 (Week 17)
**Context:** Where to host documentation
**Options:**

- GitHub Pages (free, simple)
- Read the Docs (professional)
- Custom domain + hosting

**Discussion:**

- GitHub Pages for v0.0.1
- Can upgrade later
- MkDocs Material theme planned

**Recommendation:** GitHub Pages with MkDocs

**Decision Needed By:** Phase 5

---

### Q12: Kanban Task Management

**Status:** ✅ **Resolved**
**Priority:** High
**Owner:** Architect Agent
**Deadline:** End of Phase 6 (Week 22)
**Resolved Date:** 2026-01-05
**Decision:** ADR-021 - Kanban Task Management System

**Context:** User requested Kanban-style task management with stages: To Do, In Progress, In Review, Done, Cancelled.

**DECISION (2026-01-05):**
Implemented **Kanban task management as core domain feature** (not Enterprise-only):

**TaskStatus Enum:**
```python
class TaskStatus(str, Enum):
    BACKLOG = "backlog"           # In backlog, not scheduled
    TODO = "todo"                 # Scheduled, ready to start
    IN_PROGRESS = "in_progress"   # Currently executing
    IN_REVIEW = "in_review"       # Awaiting human review
    BLOCKED = "blocked"           # Blocked by dependency/issue
    DONE = "done"                 # Successfully completed
    CANCELLED = "cancelled"       # Manually cancelled
```

**Implementation (Phase 6):**
- Task model with Kanban metadata (column_order, swimlane)
- CLI commands: `paracle task list/create/move/assign/view`
- CLI board: `paracle board show/stats`
- API endpoints: `/tasks`, `/board`
- Integration with workflow steps and approval system

See: [ADR-021](../../roadmap/decisions.md#adr-021-kanban-task-management-system)

---

## Decision Process

### Adding New Questions

```markdown
### Q#: Question Title

**Status:** Open | In Discussion | Decided
**Priority:** High | Medium | Low
**Owner:** [Agent Name]
**Deadline:** [Phase X End / Specific Date]
**Context:** Background and why this matters
**Options:**

- Option 1
- Option 2

**Discussion:**
Key points and trade-offs

**Recommendation:** [If any]

**Decision Needed By:** Timeline
```

### Decision Workflow

1. **Open**: Question identified, options listed
2. **In Discussion**: Active analysis, stakeholder input
3. **Decided**: Decision made, documented in decisions.md
4. **Implemented**: Changes made based on decision

---

## Resolved Questions

Questions will be moved here once decided, with reference to decision document.

### Template for Resolved

```markdown
### Q#: [Question Title] ✅

**Status:** Resolved
**Decision:** [What was decided]
**Date:** [When decided]
**ADR:** [Reference to decisions.md entry]
**Implemented:** [Yes/No/Partial]
```


---

## Resolved Questions (Post-v1.0.0)

### Q17: Remote Development SSH Support ✅

**Status:** Resolved
**Priority:** High
**Owner:** Architect Agent
**Deadline:** Phase 8 End
**Resolved Date:** 2026-01-08
**Decision:** Workaround available now (manual SSH tunneling), native support in Phase 8 (v1.3.0)

**Context:** Users want to run Paracle on remote servers while editing locally in their IDE.

**Implementation Plan:**
1. **Now (v1.0.0)**: Manual SSH tunneling workaround documented
2. **Phase 8 (v1.3.0)**: Native SSH transport with automatic tunnel management

**Components:**
- SSH Transport Layer (\paracle_transport\ package)
- WebSocket MCP Transport (replaces unreliable stdio over SSH)
- CLI Remote Commands (\paracle agents list --remote prod\)
- Remote Configuration (\.parac/config/remotes.yaml\)
- IDE Integration (auto-connect from settings)

**Documentation:**
- \docs/technical/remote-development-ssh-guide.md\ - Complete guide with examples
- \.parac/roadmap/adr/ADR-019-Remote-SSH-Support.md\ - Architecture decision record

**ADR:** ADR-019
**Timeline:** Phase 8 (8 weeks, Q2 2026)
**Implemented:** Partial (workaround documented, native support planned)

