# Shield EPC — UI Audit Report
## Target: Shield EPC Dashboard (Operational Command view)
**Audit type**: Design-vs-Architecture compliance check
**Reference spec**: ShieldEPC_Architecture_v1.md (ADR-000)
**Auditor**: Claude, acting as Verifier/Reviewer function
**Date**: 11 Jul 2026
**Audit scope note**: This is a UI/UX audit against internal architecture principles — not a claim of compliance against ISO 45001/OSHA/BOCW etc. Regulatory compliance of the underlying HSE processes is out of scope for this pass.

---

## Summary

4 findings. 0 Critical. 3 High. 1 Medium. All four repeat findings from a prior review of an earlier draft of this same file — this submission is the **original unfixed version**, not the corrected one delivered afterward. Recommend confirming which file is the current working copy before this goes further, since re-submitting the pre-fix version risks it becoming the baseline by accident.

**Status update (11 Jul 2026)**: superseded by `ARCHITECTURE_REVIEW.md`'s dashboard entry, now the authoritative record for this review — all 4 findings, including F2, are marked Resolved there with the confirmed canonical flow (full spec §8.1). The "Fix status" notes below are preserved as a historical snapshot of what was known at the time of this original audit; where one says "not a confirmed fix" (F2), that has since been confirmed — see `ARCHITECTURE_REVIEW.md` for current status, not this line.

| ID | Finding | Severity | Spec ref |
|---|---|---|---|
| F1 | Bare confidence score, no basis | High | Architecture §5 (Response Envelope) |
| F2 | One-tap "Deploy Auditor" bypasses human gate | High | Architecture §8 (Gate Policy) |
| F3 | "Compliance Score" presents blanket verdict | High | Architecture §3 (Compliance Agent constraint) |
| F4 | Unsourced status claims (Equipment/Staff tiles) | Medium | Architecture §5 (Response Envelope) |

---

## F1 — Confidence score without basis

**Location**: AI Pulse card, "Potential Hot Work Hazard"
**Observed**: `CONFIDENCE: 92%` rendered as an isolated badge, no supporting detail.
**Requirement violated**: Architecture §5 mandates `confidence_score` always ship with `confidence_basis`, plus `source_of_reasoning` and `missing_information`. None of these are surfaced here — the badge is decorative, not the envelope.
**Risk**: A supervisor reading "92%" has no way to know what that number measures. This is the exact failure mode Zero Hallucination Policy (§6) exists to prevent — not the model being wrong, but a confident-looking number with nothing behind it.
**Confidence in this finding**: High — this is a direct, checkable comparison against a written spec section, not a judgment call.
**Human review required**: Yes — design owner should confirm before this ships.
**Fix status**: Already resolved in the corrected file delivered previously (expandable "Why is this flagged?" disclosure with Source / Basis / Missing information).

---

## F2 — "Deploy Auditor" as a one-tap action

**Location**: AI Pulse card, hazard alert action row
**Observed**: A single primary-styled button, same visual weight as "View Site Map," with no intermediate confirmation step.
**Requirement violated**: Architecture §8 gate table — any risk-flagged item requires mandatory human sign-off before action; the diagram/agent design assumes AI *recommends*, humans *decide*. A button that appears to directly dispatch a resource collapses that gate into a single tap.
**Risk**: Under the "AI recommends, humans decide" principle (§1), this is the specific pattern that principle exists to prevent — not because dispatching an auditor is dangerous per se, but because the interface doesn't distinguish "the system suggests this" from "this is now happening."
**Confidence in this finding**: Medium — depends on unconfirmed backend behavior. If this button actually opens an assignment/review flow rather than dispatching directly, the finding is cosmetic (mislabeling) rather than architectural. This needs a definitive answer, not an assumption.
**Missing information**: What does this button actually trigger server-side? Not knowable from the HTML alone.
**Human review required**: Yes — needs your confirmation of intended behavior before it can be marked resolved either way.
**Fix status**: Relabeled to "Assign for Review" in the corrected file, as a conservative default — flagged there as an assumption, not a confirmed fix.

---

## F3 — Compliance Score as blanket verdict

**Location**: KPI Summary Grid, third tile
**Observed**: `94.8%` labeled "Compliance Score," no clause count, no standard reference, no as-of date, not a link-through.
**Requirement violated**: Architecture §3, Compliance Agent row — explicit constraint that the agent may never declare "compliant," only "no gap found against checked clauses as of [date]." An unscoped aggregate percentage on the primary dashboard does exactly what the constraint prohibits, at the most visible surface in the product.
**Risk**: This is the finding I'd weight highest of the four if forced to rank, despite matching severity with F1/F2 — a blanket compliance number is the kind of artifact that gets screenshotted into a client report or cited in an incident review months later, divorced from whatever scope it actually had. Once that happens, the scoping caveat is gone and the number reads as a certification it never was.
**Confidence in this finding**: High.
**Human review required**: Yes.
**Fix status**: Relabeled to "Checked Clauses Passing" with clause count, standards list, and as-of date in the corrected file; made link-through to clause-level view.

---

## F4 — Unsourced status tiles

**Location**: AI Pulse card, "Equipment Integrity" / "Staff Readiness" sub-tiles
**Observed**: "Optimal" and "Certified" presented as settled facts, no source tag.
**Requirement violated**: Architecture §5 — applies to all AI-originated content, not just the primary card. These two tiles get no attribution while the hazard alert above them does, creating an inconsistent trust surface within the same card.
**Risk**: Lower than F1–F3 because the content itself is lower-stakes (uptime/certification status vs. an active hazard flag), but the inconsistency is itself the problem — it trains users to treat some AI outputs as needing scrutiny and others as ambient truth, based on visual position rather than actual reliability.
**Confidence in this finding**: High.
**Human review required**: No — straightforward fix, doesn't need a judgment call.
**Fix status**: Source tags (`SCADA FEED`, `TRAINING AGENT`) added in the corrected file.

---

## Process note

Worth naming directly: this audit is me doing exactly the job I argued the Verifier Agent needs to do in the platform itself — checking output against a source spec, flagging what's confirmed vs. assumed, refusing to mark F2 fully resolved because the underlying behavior is still unknown to me. If this audit report is useful to you in this format, it's a reasonable template for what the actual Verifier/Audit Agent should produce at runtime — structured findings, severity, spec reference, explicit "missing information," rather than a pass/fail verdict.

**Open item carried forward from the architecture discussion**: this reinforces the earlier open question about whether the Verifier/Audit function should run on a different model than the generating agent. I flagged F2 as unresolved specifically because I don't have runtime access to confirm actual button behavior — a real Verifier Agent in production would have the same limitation unless it's wired to check against the actual API contract, not just the rendered markup.
