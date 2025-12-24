# Open Questions

This document tracks unresolved questions and decisions pending.

## Architecture

### Q1: Agent Inheritance Depth Limit

**Status:** Open
**Priority:** High
**Context:** Need to decide max inheritance depth for agents
**Options:**

- No limit (flexible but risky)
- 5 levels (balanced)
- 3 levels (restrictive but safe)

**Discussion:**

- Deep inheritance can be hard to debug
- Most use cases need 2-3 levels
- Can always increase later

**Decision Needed By:** End of Phase 1

---

### Q2: Event Store Implementation

**Status:** Open
**Priority:** Medium
**Context:** Which event store to use for audit trail
**Options:**

- NDJSON files (simple, no dependencies)
- SQLite (queryable, integrated)
- Redis Streams (fast, requires infra)
- EventStoreDB (powerful, overkill for v0.0.1)

**Discussion:**

- NDJSON is simplest for v0.0.1
- Can migrate later
- SQLite good for queries

**Decision Needed By:** End of Phase 1

---

### Q3: API Versioning Strategy

**Status:** Open
**Priority:** Low
**Context:** How to version the API
**Options:**

- URL versioning (/v1/agents)
- Header versioning (Accept: application/vnd.paracle.v1+json)
- No versioning for v0.0.1

**Discussion:**

- URL versioning is common and simple
- v0.0.1 might not need versioning yet
- Defer to Phase 3?

**Decision Needed By:** End of Phase 2

---

## Features

### Q4: Tool Calling Interface

**Status:** Open
**Priority:** High
**Context:** How should agents call tools?
**Options:**

- MCP only
- Internal + MCP
- Plugin system

**Discussion:**

- MCP is standard
- Internal tools for core features
- Hybrid approach best

**Decision Needed By:** End of Phase 2

---

### Q5: Memory Management Strategy

**Status:** Open
**Priority:** Medium
**Context:** How to manage agent memory/context
**Options:**

- Simple in-memory (session-based)
- Persistent (SQLite/Redis)
- Vector store (for semantic search)

**Discussion:**

- Start simple with in-memory
- Add persistence in Phase 2
- Vector store can wait

**Decision Needed By:** End of Phase 2

---

## Operations

### Q6: Deployment Strategy

**Status:** Open
**Priority:** Low
**Context:** Recommended deployment approach
**Options:**

- Docker Compose (simple)
- Kubernetes (scalable)
- Serverless (cost-effective)

**Discussion:**

- Docker Compose for v0.0.1
- Document all options
- Users choose based on needs

**Decision Needed By:** Phase 4

---

### Q7: Observability Stack

**Status:** Open
**Priority:** Medium
**Context:** Which observability tools to use
**Options:**

- Prometheus + Grafana (standard)
- OpenTelemetry (modern)
- Simple logging + metrics endpoint

**Discussion:**

- Simple logging for v0.0.1
- OpenTelemetry for future
- Don't over-engineer

**Decision Needed By:** Phase 4

---

## Community

### Q8: Contribution Guidelines

**Status:** Open
**Priority:** Low
**Context:** How to structure contribution process
**Options:**

- Full CONTRIBUTING.md from start
- Minimal guidelines, evolve
- Wait for first external contributor

**Discussion:**

- Basic guidelines for Phase 0
- Evolve based on feedback

**Decision Needed By:** End of Phase 1

---

### Q9: Documentation Hosting

**Status:** Open
**Priority:** Low
**Context:** Where to host documentation
**Options:**

- GitHub Pages (free, simple)
- Read the Docs (professional)
- Custom domain + hosting

**Discussion:**

- GitHub Pages for v0.0.1
- Can upgrade later

**Decision Needed By:** Phase 5

---

## Process

Add new questions in this format:

```markdown
### Q#: Question Title

**Status:** Open | In Discussion | Decided
**Priority:** High | Medium | Low
**Context:** Background and why this matters
**Options:**

- Option 1
- Option 2

**Discussion:**
Key points and trade-offs

**Decision Needed By:** Timeline
```

---

## Resolved Questions

Questions will be moved here once decided, with reference to decision document.
