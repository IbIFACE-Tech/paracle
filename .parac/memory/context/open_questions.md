# Open Questions

This document tracks unresolved questions and decisions pending.

## Summary

| ID  | Question                      | Owner      | Priority | Deadline    | Status       |
| --- | ----------------------------- | ---------- | -------- | ----------- | ------------ |
| Q1  | Agent Inheritance Depth Limit | Architect  | High     | Phase 1 End | Open         |
| Q2  | Event Store Implementation    | Architect  | Medium   | Phase 1 End | Open         |
| Q3  | API Versioning Strategy       | Architect  | Low      | Phase 2 End | Open         |
| Q4  | Tool Calling Interface        | Architect  | High     | Phase 2 End | **Resolved** |
| Q5  | Memory Management Strategy    | Architect  | Medium   | Phase 2 End | Open         |
| Q6  | Deployment Strategy           | PM         | Low      | Phase 4 End | Open         |
| Q7  | Observability Stack           | Architect  | Medium   | Phase 4 End | Open         |
| Q8  | Contribution Guidelines       | PM         | Low      | Phase 1 End | Open         |
| Q9  | Documentation Hosting         | Documenter | Low      | Phase 5 End | Open         |
| Q10 | API Middlewares Stack         | Architect  | High     | Phase 3 End | **Resolved** |
| Q11 | ISO 42001 Compliance Strategy | Architect  | High     | Phase 4 End | **Resolved** |

---

## Architecture

### Q1: Agent Inheritance Depth Limit

**Status:** Open
**Priority:** High
**Owner:** Architect Agent
**Deadline:** End of Phase 1 (Week 4)
**Context:** Need to decide max inheritance depth for agents
**Options:**

- No limit (flexible but risky)
- 5 levels (balanced)
- 3 levels (restrictive but safe)

**Discussion:**

- Deep inheritance can be hard to debug
- Most use cases need 2-3 levels
- Can always increase later
- ISO 42001 may require explainability (shallow = easier)

**Recommendation:** 5 levels with warning at 3+

**Decision Needed By:** End of Phase 1

---

### Q2: Event Store Implementation

**Status:** Open
**Priority:** Medium
**Owner:** Architect Agent
**Deadline:** End of Phase 1 (Week 4)
**Context:** Which event store to use for audit trail
**Options:**

- NDJSON files (simple, no dependencies)
- SQLite (queryable, integrated)
- Redis Streams (fast, requires infra)
- EventStoreDB (powerful, overkill for v0.0.1)

**Discussion:**

- NDJSON is simplest for v0.0.1
- Can migrate later with adapter pattern
- SQLite good for queries
- ISO 42001 requires audit trail - must be reliable

**Recommendation:** SQLite for v0.0.1, abstract behind EventStore interface

**Decision Needed By:** End of Phase 1

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
