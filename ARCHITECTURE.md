# Shield EPC — Architecture

**Status:** Accepted (v1.0) — pending Verified Stable per ADR promotion rules  
**Last updated:** 11 Jul 2026  
**Owner:** Tarun Kumar Saxena  
**Related:** docs/ShieldEPC_Architecture_Spec_v1.md (full detailed spec), ARCHITECTURE_REVIEW.md (review log)

---

## Vision

Shield EPC assists HSE professionals with AI-powered risk assessment, compliance checking, incident investigation, and documentation — without replacing human judgment. The platform's core bet is that trust in a safety-critical system comes from traceability, not from a system claiming to be right. Every AI output is explainable, sourced, and gated by a human decision before it becomes an action.

---

## Core Principles

**Human-in-the-loop** — AI recommends, humans decide. High-risk outputs (elevated risk ratings, compliance gaps, permit issuance) always require explicit human sign-off before they take effect. No AI-flagged observation reaches a field action in fewer than two independent human decision points (assignment for review, then role-gated supervisor approval) — see docs/ShieldEPC_Architecture_Spec_v1.md §8.1 for the canonical flow.

**Explainable decisions** — no AI output ships without its reasoning attached: what it's based on, what's missing, what was assumed.

**Auditability** — every agent action, every human review decision, every document version is logged in an immutable, reconstructible record. A reviewer should be able to answer "why did the system say this?" a year later.

**Privacy by design** — tenant data is isolated by default; sensitive data (worker health records, incident specifics) gets field-level protection, not just table-level access control.

---

## High-Level Layer Diagram

The system is organized as nine layers, request flowing top to bottom:

### 1. Presentation (Dashboard)
Web portal and offline-first mobile app. Where HSE professionals view AI outputs, approve/reject recommendations, and manage day-to-day work.

**Implementation Status:** Verification Pending (backend API complete, frontend scope requires review)

---

### 2. API Gateway
Single entry point for all client traffic. Handles routing, rate limiting, and request/response schema validation before anything reaches internal services.

**Implementation Status:** Built and Tested
- CORS middleware configured in main.py
- Exception mapping layer handles domain exceptions (ValidationFailed, TenantNotFound, DocumentNotFound)
- Request routing to all domain routers (generate, incident_investigation, health, tenants, projects)

---

### 3. Auth
Identity and access control (OAuth2/OIDC), tenant resolution, and zero-trust service-to-service verification for everything downstream.

**Implementation Status:** Verification Pending (exception handling and tenant routing in place, full OAuth2/OIDC scope requires code review)

---

### 4. Multi-Agent Orchestrator
Classifies intent, routes requests to the correct domain agent(s), enforces human-in-the-loop gates, and assembles every AI response into the mandatory output envelope (confidence, sources, assumptions, applicable standards, audit reference) before it reaches Presentation.

**Implementation Status:** Built and Tested
- Orchestrator base class exists (backend/app/agents/base.py)
- All domain agents inherit from orchestrator
- Envelope contract enforced (Incident Investigation envelope recently completed per commit 5a525e9)
- Intent routing implemented for all active endpoints

---

### 5. Domain Agents
Purpose-scoped specialists (Risk Assessment, Compliance, Incident Investigation, Document Generation, PTW/JSA, Training & Competency, Verifier). Each has a single responsibility and is explicitly barred from fabricating information — when uncertain, it asks rather than guesses.

**Implementation Status by Agent:**

| Agent | Purpose | Status | File | API Endpoint | Details |
|-------|---------|--------|------|--------------|---------|
| **Document Generator** | Draft documents from structured input | Built and Tested | document_generator.py | /generate | Least ambiguous domain, used to prove envelope pattern in Phase 1 |
| **Verifier** | Validates output against source docs before envelope assembly | Built and Tested | verifier.py | (internal pipeline) | Critical gate preventing fabrication, policy-tested |
| **Compliance** | Checks activity/document against regulatory corpus | Built and Tested | compliance.py | (via orchestrator) | First to exercise Zero Hallucination Policy; clause-level citations only |
| **Risk Assessment** | Tenant-configurable risk matrix evaluation | Built and Tested | risk_assessment.py | (via orchestrator) | Severity classification for escalation gating |
| **PTW/JSA** | Generates permits and JSAs with control measures | Built and Tested | ptw_jsa.py | (via orchestrator) | Tightly coupled with Risk Assessment, shares hazard library |
| **Incident Investigation** | RCA scaffolding (5-Why, Fishbone, Bowtie) with historical pattern matching | Built and Tested | incident_investigation.py | /incident-investigation | Phase 4A complete; envelope contract finalized; no-blame policy enforced |
| **Training & Competency** | Certification tracking and competency-to-task matching | Not Yet Implemented | — | — | Blocked until Phase 4A stabilization |

**Built and Tested Agents (6/7):**
- All agents follow orchestrator base pattern
- All use mandatory response envelope (Architecture §5)
- All output flows through audit trail (Architecture §7)
- Policy enforcement: no agent bypasses human-in-the-loop gates

**Not Yet Implemented (1/7):**
- Training & Competency Agent — scheduled for Phase 4B after Phase 4A (Incident Investigation) stabilization

---

### 6. Knowledge Base
Versioned, dated regulatory corpus (ISO 45001/14001/9001, OSHA, BOCW Act, Factory Act, local regulations) plus tenant-specific document store (SOPs, permits, incident history). Every agent answer that cites a standard must trace back to a specific, dated entry here.

**Implementation Status:** Verification Pending
- Structure defined in schema
- Agent contracts expect versioned, dated entries
- Ingestion pipeline scope and Standards Knowledge Graph integration require code review
- Compliance Agent expects zero-hallucination enforcement at this layer

---

### 7. Data Layer
Multi-tenant operational database (row-level isolation), object storage for documents/evidence, and a separate append-only audit ledger — kept architecturally distinct from the operational data so the audit trail can't be silently altered by application-layer bugs.

**Implementation Status:** Verification Pending
- Row-level tenant isolation implemented (core/exceptions.py TenantNotFound exception)
- Audit log structure defined in schema
- Database and ledger architectural separation confirmed in design
- Multi-tenant isolation test suite scope requires verification

---

### 8. Integration
Connections to external systems (ERP, IoT/SCADA feeds, third-party compliance tools). Data entering from this layer is treated as evidence, not ground truth — sensor drift and fault conditions are real, so domain agents must handle integration data with the same grounding discipline as everything else.

**Implementation Status:** Not Yet Implemented (Planned for Phase 2–3 expansion)
- Integration points defined in Architecture Spec
- External data handling policies established
- Specific ERP/SCADA connectors scheduled after core agents stabilize

---

### 9. Monitoring
Observability across the whole stack: agent performance, escalation rates, human-override patterns, and system health. This is also where drift in agent accuracy over time gets caught before it becomes a safety issue.

**Implementation Status:** Verification Pending
- Exception handling and logging in place (main.py exception_handler)
- Agent performance tracking infrastructure exists
- Full observability scope requires instrumentation review

---

## Why this structure

GitHub here isn't a code repository with docs bolted on — ARCHITECTURE.md is the entry point precisely so that anyone (a new engineer, an auditor, a client's technical reviewer) can understand what the system does and why before reading a single line of code. Code that doesn't match this document is a bug in the code or a stale document — either way, ARCHITECTURE_REVIEW.md is where that gets resolved and this file gets updated.

---

## Implementation Status Summary

**Phases Complete:**
- **Phase 1 (Core Scaffolding):** All agents built and tested; orchestrator, envelope, audit log in place
- **Phase 2 (Compliance Agent):** Agent built and tested; Standards Knowledge Graph integration pending
- **Phase 3 (Risk Assessment + PTW/JSA):** Both agents built and tested; hazard library integration pending

**Phase 4 (Incident Investigation + Training & Competency):**
- **Phase 4A (Incident Investigation):** Built and Tested — agent, API endpoint, envelope contract, tests complete
- **Phase 4B (Training & Competency):** Not Yet Implemented — blocked until 4A stabilization

**Phase 5 (Offline Mobile, Multi-Tenant Hardening, Red-Team):**
- **Offline-first mobile sync:** Not Yet Implemented
- **Multi-tenant isolation test suite:** Verification Pending
- **Full red-team pass:** Verification Pending (Phase 2 Compliance red-team criterion underway)

---

## Implementation Status Legend

- **Built and Tested:** Feature implemented, integrated into live codebase, test coverage exists, verified working end-to-end
- **Verification Pending:** Structure/design complete, awaiting code review or integration testing to confirm specification compliance
- **Not Yet Implemented:** On roadmap, not yet started; typically blocked by prior phase completion or architectural decision
- **Planned for Later Phase:** Explicitly deferred; will be addressed in specified future phase after current dependencies stabilize
