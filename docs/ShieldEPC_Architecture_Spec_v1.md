# Shield EPC — AI-Powered HSE Platform
## System Architecture Specification v1.0

**Author**: Claude (Principal AI Systems Architect, acting) — for Tarun Kumar Saxena
**Status**: Draft for review — treat as ADR-000 (foundational architecture record) for the Shield EPC platform
**Scope**: Enterprise multi-tenant AI-HSE platform for EPC, Oil & Gas, Construction, Infrastructure, Manufacturing, Industrial

---

## 1. Architectural Philosophy

The single hardest constraint here is not the multi-agent design — it's that this system operates in a domain where a wrong answer can contribute to a fatality. Every architectural decision below is subordinate to three non-negotiables:

1. **The system must be able to say "I don't know" and mean it.** Silent failure (confident hallucination) is the primary risk to design against — more than latency, more than cost.
2. **Every output must be reconstructible.** A safety officer, auditor, or regulator must be able to ask "why did the system say this?" a year later and get a complete answer.
3. **AI recommends, humans decide.** The architecture must make it structurally difficult (not just policy-difficult) for an AI output to become an action without a human gate.

Given this, I'm rejecting the Fugu-style black-box orchestration pattern we discussed for exactly this reason — opaque routing is incompatible with requirement #2. Every agent call in this architecture is logged, versioned, and attributable.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  Web (React/Next.js) │ Mobile (offline-first PWA/React Native)   │
└───────────────────────────┬───────────────────────────────────────┘
                              │ HTTPS/TLS 1.3, JWT + mTLS (service-to-service)
┌───────────────────────────▼───────────────────────────────────────┐
│                      API GATEWAY (Kong / AWS API GW)              │
│   • Auth (OAuth2/OIDC)  • Rate limiting  • Tenant routing         │
│   • Request/response schema validation                            │
└───────────────────────────┬───────────────────────────────────────┘
                              │
┌───────────────────────────▼───────────────────────────────────────┐
│                   ORCHESTRATOR AGENT (Core)                       │
│  • Intent classification → agent routing                          │
│  • Human-in-the-loop gate enforcement                              │
│  • Response envelope assembly (see Section 5)                     │
│  • Escalation logic (low confidence → human queue)                 │
└──┬────────┬────────┬────────┬────────┬────────┬────────┬─────────┘
   │        │        │        │        │        │        │
┌──▼──┐ ┌──▼──┐ ┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼────┐ ┌─▼──────┐
│Risk │ │Comp-│ │Incident│ │Doc   │ │PTW/  │ │Training│ │Verifier│
│Asmt │ │lian-│ │Investi-│ │Gener-│ │JSA   │ │& Comp- │ │/Review │
│Agent│ │ce   │ │gation  │ │ator  │ │Agent │ │etency  │ │Agent   │
│     │ │Agent│ │Agent   │ │Agent │ │      │ │Agent   │ │        │
└──┬──┘ └──┬──┘ └───┬───┘ └──┬───┘ └──┬───┘ └──┬────┘ └─┬──────┘
   │       │        │        │        │        │         │
┌──▼───────▼────────▼────────▼────────▼────────▼─────────▼───────┐
│              KNOWLEDGE & GROUNDING LAYER                          │
│  • Vector DB (regulatory corpus, tenant SOPs, past incidents)     │
│  • Standards Knowledge Graph (ISO 45001/14001/9001, OSHA, BOCW,   │
│    Factory Act, state-specific rules) — versioned, dated          │
│  • Tenant-specific document store (project SOPs, permits, JSAs)   │
└──────────────────────────────┬────────────────────────────────────┘
                                 │
┌───────────────────────────────▼────────────────────────────────────┐
│                       DATA LAYER (multi-tenant)                     │
│  Postgres (tenant-partitioned, row-level security)                  │
│  Object storage (S3-compatible) — documents, photos, evidence       │
│  Audit log store (append-only, immutable — see Section 7)           │
│  Time-series DB — sensor/IoT feeds (optional module)                │
└───────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Roster and Single-Responsibility Definitions

Each agent is a bounded context. No agent calls another agent directly — all coordination goes through the Orchestrator. This mirrors the bounded-context discipline you already established in ADR-009 for ShieldGate, and it's the right call here for the same reason: it keeps failure domains isolated and audit trails linear.

| Agent | Responsibility | Explicitly NOT allowed to do |
|---|---|---|
| **Risk Assessment Agent** | Compute/estimate risk ratings (likelihood × severity) for a described task or hazard, using tenant risk matrix | Approve work; override human risk sign-off |
| **Compliance Agent** | Map a described activity/document against applicable standards (ISO 45001/14001/9001, OSHA, BOCW, Factory Act, state rules); flag gaps | Declare something "compliant" — only "no gap found against checked clauses as of [date]" |
| **Incident Investigation Agent** | Structure incident data into RCA formats (5-Why, Fishbone, Bowtie); surface pattern-matches to historical incidents | Assign blame/fault to individuals; conclude root cause without human validation |
| **Document Generator Agent** | Draft PTW, JSA, Method Statements, toolbox talk content from structured input | Auto-issue/approve any permit; publish without human sign-off |
| **PTW/JSA Agent** | Task-specific hazard identification and control-measure suggestion using tenant hazard library | Skip control measures because "task is routine" — always requires explicit control mapping |
| **Training & Competency Agent** | Track certification expiry, match worker competency to task requirements | Certify competency itself |
| **Verifier/Reviewer Agent** | Cross-checks other agents' outputs against source documents before they reach the response envelope; catches contradictions, unsupported claims, missing citations | Generate new content — verification only |

**Design note**: the Verifier is not decorative. It's the agent that actually enforces the Zero Hallucination Policy structurally — see Section 6.

---

## 4. Orchestrator Agent Design

The orchestrator does four things, in this order, for every request:

1. **Classify intent** → route to the correct specialist agent(s). Multi-agent requests (e.g., "review this JSA for compliance and suggest controls") get decomposed into a task graph, not a single free-form prompt.
2. **Enforce grounding requirements** before any agent runs — if a request requires standards lookup and the Knowledge Graph has no matching, dated clause, the agent is blocked from answering and must return `insufficient_information`.
3. **Enforce human-in-the-loop gates** — defined per action type in a policy table (Section 8), not left to agent discretion.
4. **Assemble the response envelope** (Section 5) — this is mandatory, not optional formatting. No raw agent output reaches the client layer un-enveloped.

Routing should be a deterministic rules engine + LLM classifier hybrid, not a learned black-box router. Given the Fugu discussion, I'd explicitly avoid "the model decides everything" — for this domain you want the routing logic itself to be auditable code, with the LLM only handling the ambiguous edge of intent classification.

---

## 5. Mandatory Output Envelope

Every AI-generated response, regardless of which agent produced it, is wrapped before reaching a user:

```json
{
  "response_id": "uuid",
  "tenant_id": "uuid",
  "agent": "compliance_agent",
  "agent_version": "1.4.2",
  "model_version": "claude-sonnet-4-6-2026xxxx",
  "timestamp": "ISO8601",
  "content": {
    "answer": "...",
    "confidence_score": 0.0,
    "confidence_basis": "explanation of what drove this score, not just a number"
  },
  "source_of_reasoning": [
    {"type": "standard_clause", "ref": "ISO 45001:2018 §8.1.2", "retrieved_date": "..."},
    {"type": "tenant_document", "ref": "doc_id", "excerpt_ref": "..."}
  ],
  "missing_information": ["e.g., work-at-height permit not provided for task described"],
  "assumptions_made": ["e.g., assumed standard 8hr shift; not stated in input"],
  "applicable_standards": ["ISO 45001:2018", "BOCW Act 1996", "Factory Act 1948 §21"],
  "human_review_required": true,
  "human_review_reason": "risk_rating_high | compliance_gap_flagged | low_confidence | statutory_requirement",
  "audit_trail_id": "uuid — links to immutable audit log entry",
  "schema_version": "1.0"
}
```

This is not cosmetic. `confidence_score` without `confidence_basis` is exactly the kind of number that gets misused ("the AI was 92% confident") without anyone knowing what it measured. Make the basis mandatory.

---

### 5.1 Agent-Specific Content Extensions

The `content` block above shows the core fields present on every envelope, regardless of agent. Some agents attach additional, agent-specific fields to `content`. These extensions are optional and are only populated by the agent that produces them.

Currently, the Incident Investigation Agent attaches:

- five_whys
- fishbone_causes
- bowtie
- investigator_signoff

`investigator_signoff` uses conditional validation:

- `status="pending"` → `investigator_id` may be `null`; `signed_at` must be `null`.
- `status="signed"` or `status="rejected"` → `investigator_id` is required; `signed_at` is required and must be timezone-aware.

These fields are optional extensions and are not present in envelopes produced by other agents.

## 6. Zero Hallucination Policy — Implementation, Not Slogan

"Zero hallucination" as a stated principle is unenforceable at the model level — no LLM has a hard guarantee against this. What's enforceable is the **system-level architecture around the model**:

1. **Retrieval-grounded generation only.** Every Compliance and Risk Assessment agent response must cite a retrieved clause with a document ID and retrieval date. If retrieval returns nothing relevant, the agent returns `insufficient_information`, not a best-effort guess.
2. **Verifier Agent as a second pass.** Before the envelope is assembled, the Verifier Agent checks: does every factual claim in `content.answer` trace to something in `source_of_reasoning`? Unsupported claims get stripped and logged, not silently passed through.
3. **Standards Knowledge Graph is versioned and dated.** Regulations change. Every clause reference includes the version/date of the standard it was retrieved from, so a 2024 OSHA clause isn't silently applied against a 2026 update.
4. **No agent may fill a gap with a plausible-sounding default.** This has to be a prompt-level and eval-level constraint, tested explicitly — this is the failure mode red-teaming should target hardest, since it's the one that looks like a complete answer.

Practically: budget real red-team time here before launch. The failure mode you're defending against isn't "the AI is obviously wrong" — it's "the AI is wrong in a way that sounds exactly as confident as when it's right." That's the only failure mode that matters in this domain.

---

## 7. Auditability

Append-only audit log, separate store from operational DB (so it can't be edited by application-layer bugs or bad actors with app-DB access):

- Every agent invocation: input, output, model version, timestamp, tenant, user
- Every human review action: reviewer ID, decision, timestamp, any edits made to AI output before acceptance
- Every document generated: full version history, not just latest
- Retention policy driven by regulatory requirement (OSHA/Factory Act records retention — jurisdiction-dependent, needs legal confirmation per tenant geography)

Recommend: hash-chain the audit log entries (each entry includes hash of previous entry) so tampering is detectable even by an insider with DB access. This is a standard pattern (similar to how certificate transparency logs work) and isn't expensive to implement.

---

## 8. Human-in-the-Loop Gate Policy (starting table — needs your domain judgment to finalize)

| Action | Gate |
|---|---|
| Risk rating ≥ High | Mandatory human sign-off before task proceeds |
| Any compliance gap flagged | Mandatory human review before document finalized |
| PTW/JSA generation | Always requires human approval before issuance (never auto-issue) |
| Incident RCA | AI drafts structure only; conclusions require human investigator sign-off |
| Confidence score < threshold (tenant-configurable, suggest starting at 0.75) | Routed to human review queue automatically |
| Any output where `missing_information` is non-empty | Cannot be finalized without human addressing the gap |

This table should itself be a versioned, tenant-configurable policy object — not hardcoded — because different tenants (a nuclear site vs. a warehouse) will legitimately want different thresholds.

### 8.1 Canonical Flow: AI-Flagged Observation → Field Action

This resolves ARCHITECTURE_REVIEW.md finding F2 (dashboard audit, 11 Jul 2026), where an AI hazard flag had a single-tap action that read as direct dispatch. Confirmed intended behavior: **no AI output ever reaches field action without two independent human decision points in between.** This is now the canonical pattern for any agent output that could lead to a physical action (not just the Hazard/Risk Assessment path — Compliance and Incident agents that surface field-actionable findings follow the same shape).

```
[1] AI creates observation
     Domain agent (e.g., Hazard/Risk Assessment) generates a finding with
     full envelope (confidence, source, basis, missing_information).
     Status: AI FLAGGED
     Audit log: agent_id, model_version, timestamp, full envelope
        │
        ▼
[2] Assign for Review  (human decision point #1 — any authorized user)
     A human explicitly routes the observation to a supervisor. This is
     not automatic and not the same action as approval — assigning for
     review is "this deserves a look," not "this is correct."
     Status: PENDING SUPERVISOR REVIEW
     Audit log: user_id, timestamp, action=assign_for_review
        │
        ▼
[3] Supervisor Approval  (human decision point #2 — role-gated: supervisor only)
     Supervisor reviews the AI's stated basis/sources, and either approves
     or rejects. Rejection ends the flow here (logged, does not proceed).
     This step must be performed by a distinct, role-verified user —
     the same person who did step 2 approving their own assignment
     defeats the purpose of a second gate.
     Status: SUPERVISOR APPROVED  (or: REJECTED — terminal)
     Audit log: supervisor_user_id, timestamp, action=approve/reject, reason (if rejected)
        │
        ▼
[4] Auditor Assignment  (human action — supervisor or designated dispatcher)
     Only after approval does a specific auditor/field resource get named
     and assigned. This is the first point where a real person is
     committed to go do something.
     Status: AUDITOR ASSIGNED
     Audit log: assigned_auditor_id, assigned_by, timestamp
        │
        ▼
[5] Field Action
     Auditor performs the inspection/action and logs the outcome.
     Status: FIELD ACTION COMPLETE (or: FIELD ACTION — FINDING CONFIRMED /
     FIELD ACTION — FALSE POSITIVE, feeding back into agent evaluation data)
     Audit log: auditor_id, timestamp, outcome, evidence (photos/notes)
```

**Design rule this establishes**: any UI control that could be read as triggering step 5 directly from step 1 is a defect, not a shortcut. Every intermediate status must be visibly distinct in the UI (not just logged invisibly in the backend) so a supervisor always knows which of the five states an observation is in.

**Feedback loop**: step 5's outcome (finding confirmed vs. false positive) should be fed back to the originating agent's evaluation dataset — this is how confidence calibration (the open threshold question in ROADMAP.md) gets real data over time instead of staying a guess.

---

## 9. Multi-Tenancy

- **Isolation model**: Postgres row-level security with `tenant_id` on every table, not separate schemas-per-tenant (given your ShieldGate v2.1 schema work already resolved this pattern for auth/SUPER_ADMIN scoping — reuse that design here rather than re-deriving it).
- **Knowledge layer**: shared regulatory corpus (standards don't change per tenant) + tenant-private document store (SOPs, JSAs, incident history) — strict separation, never mixed in a single retrieval call.
- **Cross-tenant leakage** is the single most damaging failure mode for an enterprise HSE platform (client A's incident data appearing in client B's risk assessment). This needs its own test suite, not just reliance on RLS policies being correct.

---

## 10. Offline-First Mobile

Field use (site walkdowns, permit issuance at remote locations) is the core mobile use case, and connectivity can't be assumed.

- Local-first data model (SQLite/WatermelonDB on device) with sync-on-reconnect
- AI agent calls that require live model inference **cannot** run offline — design the mobile UX to clearly distinguish "offline-capable" actions (form filling, photo capture, checklist completion against cached hazard library) from "requires connectivity" actions (live compliance check, risk agent query)
- Conflict resolution strategy needed for concurrent edits (e.g., two safety officers editing the same JSA) — last-write-wins is not acceptable for safety documents; needs explicit merge/flag-for-review on conflict

---

## 11. Security

- OIDC/OAuth2 for user auth, mTLS for service-to-service
- Secrets management via Vault/AWS Secrets Manager — never in agent prompts or logs
- PII/sensitive data (worker health records, if in scope) needs field-level encryption, separate from general document store
- Model API calls: no tenant data in prompts should be logged by the underlying LLM provider beyond what's contractually agreed (check Claude API's data retention terms for enterprise/zero-retention options if handling sensitive incident data)

---

## 12. Suggested Phased Build Order

Given this is a large surface area, I'd sequence it rather than build all seven agents simultaneously:

**Phase 1 (MVP core)**: Orchestrator + response envelope + audit log + Document Generator Agent + Verifier Agent. This alone, even with one working agent, proves out the hardest architectural pieces (grounding, envelope, audit trail, human gate).

**Phase 2**: Compliance Agent + Standards Knowledge Graph (start with ISO 45001 + BOCW, since those map to your immediate EPC/construction client base; expand jurisdiction coverage after).

**Phase 3**: Risk Assessment Agent + PTW/JSA Agent (these two are tightly coupled — build together).

**Phase 4**: Incident Investigation Agent + Training/Competency Agent.

**Phase 5**: Offline mobile layer, multi-tenant hardening, penetration testing, red-team pass on hallucination guardrails before any pilot client goes live.

---

## Open Questions for You to Resolve (need your domain call, not mine)

1. Which jurisdictions' regulatory corpus ships in v1 — India-only (BOCW, Factory Act) or India + Gulf (given your relocation plans and target market)?
2. Confidence threshold for auto-escalation (I suggested 0.75 as a starting point — needs calibration against real agent outputs, not a guess)
3. Data residency requirements — if targeting Gulf clients, may need region-specific hosting
4. Should the Verifier Agent use a different model/provider than the generating agents, as a genuine independent check rather than the same model checking itself? (This is worth seriously considering — self-verification has known blind spots)

I'd treat this document as ADR-000 and iterate the same way you've been running the ShieldGate chain — freeze sections as they're validated, keep contentious ones (like the Gulf jurisdiction question) open until you decide.
