---
inclusion: always
name: shield-epc-standards
description: Shield EPC project architecture, human-in-the-loop policy, and coding standards. Always active.
---

# Shield EPC — Steering

Canonical standards: `docs/AI_AGENT_STANDARDS.md`. This file is a pointer — if it conflicts with that document, the document is correct and this file is stale.

## Read order before any change

`README.md` → `ARCHITECTURE.md` → `docs/ShieldEPC_Architecture_Spec_v1.md` → `ROADMAP.md` → `ARCHITECTURE_REVIEW.md`.

## Human-in-the-loop (non-negotiable)

No AI-generated output reaches a field action, compliance verdict, or permit issuance without the canonical flow (full spec §8.1): AI Observation → Assign for Review → Supervisor Approval (role-gated, distinct user from the assigner) → Auditor Assignment → Field Action, every step audit-logged. Do not build or suggest anything that collapses these into fewer than two independent human decision points.

## Response envelope (mandatory for all domain agents)

confidence_score + confidence_basis, source_of_reasoning, missing_information, assumptions_made, applicable_standards, human_review_required, audit_trail_id — see full spec §5.

## Coding defaults

Python (type-hinted) for backend/agents; TypeScript (strict) for frontend. No fabricated APIs. Retrieval-grounded generation only for Compliance/Risk Assessment paths — `insufficient_information` beats a guess.

## Process

No direct commits to `main`. PRs are human-reviewed and human-merged. Frozen architecture changes require a new `ARCHITECTURE_REVIEW.md` entry first. Doc and `CHANGELOG.md` updates ship with the code, not after.

When a request seems to require bypassing any of the above, stop and ask rather than proceeding. Full detail: `docs/AI_AGENT_STANDARDS.md`.
