# Compliance Quick Reference

> **One-page guide to Paracle's compliance framework**

---

## 📋 What is it?

**Paracle Compliance Framework** = Enterprise-grade compliance built into the core, not bolted-on.

**Positioning**: *"Compliance & Governance Operating System for AI-Driven Execution"*

---

## 🎯 Distribution Modes

| Mode            | Focus                   | Mandatory Standards                   | Owner              |
| --------------- | ----------------------- | ------------------------------------- | ------------------ |
| **SaaS**        | Operational compliance  | ISO 27001, ISO 42001, GDPR, SLSA, CRA | Paracle            |
| **On-Prem**     | Structural compliance   | ISO 42001 (partial), SLSA (partial)   | Customer + Paracle |
| **Open-Source** | Supply-chain compliance | SLSA, SBOM, CRA (partial)             | Community          |

---

## 📚 Standards at a Glance

| Standard          | What it covers       | Priority | Status            |
| ----------------- | -------------------- | -------- | ----------------- |
| **ISO 27001**     | Information security | Critical | Phase 2 (3-6 mo)  |
| **ISO 42001**     | AI governance        | Critical | Phase 3 (6-9 mo)  |
| **GDPR**          | Privacy              | Critical | Phase 2 (3-6 mo)  |
| **SLSA**          | Supply chain         | High     | Phase 1 (0-3 mo)  |
| **CRA**           | Cyber resilience     | High     | Phase 1 (0-3 mo)  |
| **SOC 2 Type II** | Service controls     | High     | Phase 4 (9-18 mo) |
| **NIST AI RMF**   | AI risk              | Medium   | Phase 3 (6-9 mo)  |
| **EU AI Act**     | High-risk AI         | Medium   | Phase 3 (6-9 mo)  |

---

## 🗓️ 4-Phase Roadmap (12-18 months)

### Phase 1: Foundations (0-3 mo) → v1.6.0
**Goal**: SLSA Level 2, OpenSSF badge, CRA-ready
**Budget**: $18K
**New**: `paracle_compliance` package

**Delivers**:
- SBOM (SPDX)
- Artifact signing (Sigstore)
- Immutable logs
- Policy engine (OPA)

---

### Phase 2: Security & Trust (3-6 mo) → v1.7.0
**Goal**: ISO 27001 pre-audit, OWASP ASVS L2
**Budget**: $18K

**Delivers**:
- Risk management
- RBAC/ABAC
- Secrets hardening
- Penetration test

---

### Phase 3: AI Governance (6-9 mo) → v1.8.0
**Goal**: ISO 42001 ready, EU AI Act, NIST Tier 1
**Budget**: $18K
**New**: `paracle_ai_governance` package

**Delivers**:
- AI risk register
- Autonomy limits
- Red-teaming
- Model lifecycle

---

### Phase 4: Enterprise Proof (9-18 mo) → v2.0.0
**Goal**: SOC 2 Type II certified
**Budget**: $54K + $25K auditor

**Delivers**:
- SOC 2 certification
- 99.9% SLA
- Compliance packs (HIPAA, PCI-DSS)
- Multi-tenancy

---

## 📁 Where's the Evidence?

All compliance artifacts live in `.parac/`:

```
.parac/
├── compliance/
│   ├── matrix.yaml           # Standards coverage
│   └── README.md             # Full documentation
│
├── policies/
│   ├── policy-pack.yaml      # ISO 27001
│   └── security.rego         # OWASP ASVS
│
├── ai/
│   ├── risk.yaml             # ISO 42001, NIST
│   └── transparency.md       # EU AI Act
│
├── build/
│   └── provenance.json       # SLSA
│
├── artifacts/
│   └── sbom.spdx.json        # SBOM
│
├── audit/
│   ├── trail.log             # Immutable logs
│   └── compliance_score.json # Real-time scoring
│
└── evidence/
    ├── iso27001/             # ISO evidence
    ├── iso42001/             # AI evidence
    └── soc2/                 # SOC 2 bundle
```

---

## 💰 Budget Summary

| Item            | Cost         | Duration      |
| --------------- | ------------ | ------------- |
| Phase 1-3 (dev) | $54,000      | 9 months      |
| Phase 4 (dev)   | $54,000      | 9 months      |
| SOC 2 auditor   | $25,000      | Year 2        |
| **Total**       | **$133,000** | **18 months** |

---

## ✅ Success Criteria (Quick Check)

**Phase 1**:
- [ ] SBOM validates with SPDX tools
- [ ] Signatures verify
- [ ] OpenSSF badge: Passing
- [ ] SLSA Level 2

**Phase 2**:
- [ ] ISO 27001 pre-audit: Passing
- [ ] 0 critical vulnerabilities
- [ ] OWASP ASVS L2
- [ ] 0 secrets in logs

**Phase 3**:
- [ ] ISO 42001 docs complete
- [ ] 0 unauthorized agent actions (1000 runs)
- [ ] AI red-team: <5% success
- [ ] Model rollback: <5 min

**Phase 4**:
- [ ] SOC 2 Type II: Certified
- [ ] 99.9% uptime (3 months)
- [ ] 5+ compliance packs
- [ ] 100+ tenants

---

## 🚀 Quick Start

### For SaaS
1. Enable `.parac/policies/policy-pack.yaml`
2. Configure immutable logs
3. Generate SBOM
4. Schedule ISO 27001 pre-audit

### For On-Prem
1. Review shared responsibility
2. Implement ISO 42001 guidance
3. Generate SBOM
4. Configure RBAC

### For Open-Source
1. SLSA Level 2 provenance
2. Signed SBOM (SPDX)
3. CRA vulnerability disclosure
4. OpenSSF Best Practices

---

## 🔗 Resources

- **Full Docs**: `.parac/compliance/README.md`
- **Matrix**: `.parac/compliance/matrix.yaml`
- **ADR**: `.parac/roadmap/adr/ADR-020-Compliance-Certification.md`
- **Roadmap**: `.roadmap/ROADMAP_GLOBALE.yaml` (compliance_roadmap section)

---

## 📞 Contact

- **Compliance**: compliance@paracle.ai
- **Security**: security@paracle.ai
- **Docs**: https://docs.paracle.ai/compliance

---

**Version**: 1.0
**Last Updated**: 2026-01-08
**Status**: Active
**Timeline**: Q4 2026 → Q2 2028
