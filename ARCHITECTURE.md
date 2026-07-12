# Shield EPC — Architecture

**Status**: Frozen v1.0
**Last updated**: 11 Jul 2026
**Owner**: Tarun Kumar Saxena
**Related**: `docs/ShieldEPC_Architecture_Spec_v1.md` (full detailed spec), `ARCHITECTURE_REVIEW.md` (review log)

---

## Vision

Shield EPC assists HSE professionals with AI-powered risk assessment, compliance checking, incident investigation, and documentation — without replacing human judgment. The platform's core bet is that trust in a safety-critical system comes from traceability, not from a system claiming to be right. Every AI output is explainable, sourced, and gated by a human decision before it becomes an action.

---

## Core Principles

- **Human-in-the-loop** — AI recommends, humans decide. High-risk outputs (elevated risk ratings, compliance gaps, permit issuance) always require explicit human sign-off before they take effect. No AI-flagged observation reaches a field action in fewer than two independent human decision points (assignment for review, then role-gated supervisor approval) — see `docs/ShieldEPC_Architecture_Spec_v1.md` §8.1 for the canonical flow.
- **Explainable decisions** — no AI output ships without its reasoning attached: what it's based on, what's missing, what was assumed.
- **Auditability** — every agent action, every human review decision, every document version is logged in an immutable, reconstructible record. A reviewer should be able to answer "why did the system say this?" a year later.
- **Privacy by design** — tenant data is isolated by default; sensitive data (worker health records, incident specifics) gets field-level protection, not just table-level access control.

---

## High-Level Layer Diagram

The system is organized as nine layers, request flowing top to bottom:

1. **Presentation (Dashboard)** — Web portal and offline-first mobile app. Where HSE professionals view AI outputs, approve/reject recommendations, and manage day-to-day work.

2. **API Gateway** — Single entry point for all client traffic. Handles routing, rate limiting, and request/response schema validation before anything reaches internal services.

3. **Auth** — Identity and access control (OAuth2/OIDC), tenant resolution, and zero-trust service-to-service verification for everything downstream.

4. **Multi-Agent Orchestrator** — Classifies intent, routes requests to the correct domain agent(s), enforces human-in-the-loop gates, and assembles every AI response into the mandatory output envelope (confidence, sources, assumptions, applicable standards, audit reference) before it reaches Presentation.

5. **Domain Agents** — Purpose-scoped specialists (Risk Assessment, Compliance, Incident Investigation, Document Generation, PTW/JSA, Training & Competency, Verifier). Each has a single responsibility and is explicitly barred from fabricating information — when uncertain, it asks rather than guesses.

6. **Knowledge Base** — Versioned, dated regulatory corpus (ISO 45001/14001/9001, OSHA, BOCW Act, Factory Act, local regulations) plus tenant-specific document store (SOPs, permits, incident history). Every agent answer that cites a standard must trace back to a specific, dated entry here.

7. **Data Layer** — Multi-tenant operational database (row-level isolation), object storage for documents/evidence, and a separate append-only audit ledger — kept architecturally distinct from the operational data so the audit trail can't be silently altered by application-layer bugs.

8. **Integration** — Connections to external systems (ERP, IoT/SCADA feeds, third-party compliance tools). Data entering from this layer is treated as evidence, not ground truth — sensor drift and fault conditions are real, so domain agents must handle integration data with the same grounding discipline as everything else.

9. **Monitoring** — Observability across the whole stack: agent performance, escalation rates, human-override patterns, and system health. This is also where drift in agent accuracy over time gets caught before it becomes a safety issue.

---

## Why this structure

GitHub here isn't a code repository with docs bolted on — `ARCHITECTURE.md` is the entry point precisely so that anyone (a new engineer, an auditor, a client's technical reviewer) can understand what the system does and why before reading a single line of code. Code that doesn't match this document is a bug in the code or a stale document — either way, `ARCHITECTURE_REVIEW.md` is where that gets resolved and this file gets updated.
