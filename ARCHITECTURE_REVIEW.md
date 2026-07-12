# Shield EPC — Architecture Review Log

**Status**: Active
**Last updated**: 11 Jul 2026
**Purpose**: This file is the record of every point where something built, drafted, or proposed was checked against `ARCHITECTURE.md` and the full spec (`docs/ShieldEPC_Architecture_Spec_v1.md`). It exists so "does this match the architecture?" has a documented answer, not a remembered one — anyone should be able to reconstruct why a decision was made without asking the person who made it.

If you're about to review a design, a diagram, a UI, a PR, or an agent's output against the architecture, the result goes here. `ARCHITECTURE.md` says what the system should be; this file is the evidence that it still is.

---

## When to log a review here

Log an entry when:
- A UI, diagram, or document is checked against `ARCHITECTURE.md` or the full spec
- A proposed change would alter a frozen architectural decision (agent boundaries, gate policy, envelope schema, etc.)
- A red-team or audit pass produces findings
- An open question from a prior review gets resolved

Don't log routine implementation work here — this is for review-and-verify moments, not a general work log. `CHANGELOG.md` covers what shipped; this file covers what was checked and what it was checked against.

---

## Entry Template

Copy this block for each new entry. Keep entries in reverse-chronological order (newest at top, immediately below this section).

```markdown
## [YYYY-MM-DD] — <Short title of what was reviewed>

**Reviewed**: <what was reviewed — file, diagram, PR, proposal>
**Reviewed against**: <ARCHITECTURE.md section(s) or spec section(s)>
**Reviewer**: <who/what did the review>
**Outcome**: <N findings — X Critical / X High / X Medium / X Low>

### Findings

| ID | Finding | Severity | Spec ref | Status |
|---|---|---|---|---|
| F1 | <short description> | Critical/High/Medium/Low | <§ reference> | Open/Resolved/Accepted-with-reason |

### Detail per finding (for Critical/High only — Medium/Low can stay in the table)

**F1 — <title>**
- Observed: <what was actually seen>
- Requirement violated: <specific principle or spec line>
- Risk: <what happens if this ships unfixed>
- Confidence in this finding: <High/Medium/Low, and why — is this a direct spec comparison or a judgment call?>
- Missing information: <anything the reviewer couldn't confirm — don't guess and mark it resolved>
- Resolution: <what was done, or "open, owner: <name>, target: <date/phase>">

### Open questions carried forward

- <question> — blocks: <what this blocks, e.g. "Phase 2 exit criteria">
```

---

## Severity Definitions

Consistent severity across entries so findings are comparable over time:

- **Critical** — violates a Core Principle (Architecture "Core Principles" section) in a way that could reach a real user/decision before being caught. Blocks release regardless of what else is ready.
- **High** — violates a specific, frozen spec requirement (envelope schema, agent boundary, gate policy). Should be fixed before the affected phase's exit criteria are considered met.
- **Medium** — inconsistent with architecture intent but not a direct violation of a written requirement (e.g., a UI pattern that's confusing but not unsafe). Fix before broader rollout, not necessarily before phase exit.
- **Low** — cosmetic, or a clarity issue that doesn't affect correctness or safety (e.g., placeholder data, wording).

## Status Definitions

- **Open** — not yet addressed
- **Resolved** — fixed and the fix has been checked against the original finding
- **Accepted-with-reason** — deliberately not fixed, with a named decision-maker and stated reason (e.g., "acceptable for internal demo, must resolve before pilot" — accepted by T. Saxena, 11 Jul 2026). Never leave a finding silently dropped — if it's not being fixed, that has to be a decision, not an omission.

---

## Log Entries

## [2026-07-11] — Dashboard mockup, first pass (Operational Command view)

**Reviewed**: `frontend/dashboard_mockup_v1.html` (initial version, pre-fix)
**Reviewed against**: `ARCHITECTURE.md` — Core Principles (human-in-the-loop, explainable decisions); `docs/ShieldEPC_Architecture_Spec_v1.md` §5 (Response Envelope), §8 (Gate Policy), §3 (Compliance Agent constraints)
**Reviewer**: Claude, acting as Verifier/Reviewer function
**Outcome**: 4 findings — 0 Critical / 3 High / 1 Medium / 0 Low. **Update (11 Jul 2026): all 4 findings now Resolved.**

### Findings

| ID | Finding | Severity | Spec ref | Status |
|---|---|---|---|---|
| F1 | Bare confidence score, no basis, source, or missing-info disclosure | High | §5 | Resolved |
| F2 | One-tap "Deploy Auditor" action bypasses human-in-the-loop gate | High | §8, §8.1 | Resolved |
| F3 | "Compliance Score" presented as unscoped blanket verdict | High | §3 | Resolved |
| F4 | Unsourced status claims on Equipment Integrity / Staff Readiness tiles | Medium | §5 | Resolved |

### Detail per finding

**F1 — Bare confidence score**
- Observed: `CONFIDENCE: 92%` rendered as an isolated badge with no supporting detail.
- Requirement violated: §5 mandates `confidence_score` ship with `confidence_basis`, `source_of_reasoning`, and `missing_information`.
- Risk: A confident-looking number with nothing behind it — the exact failure mode the Zero Hallucination Policy targets.
- Confidence in this finding: High — direct comparison against a written spec section.
- Resolution: Added expandable "Why is this flagged?" disclosure showing Source, Basis for confidence, and Missing information.

**F2 — One-tap "Deploy Auditor"**
- Observed: A single primary-styled button, same visual weight as a passive action ("View Site Map"), with no confirmation step.
- Requirement violated: §8 gate table — risk-flagged items require mandatory human sign-off before action.
- Risk: Collapses the "AI recommends, humans decide" principle into a single tap if the button actually dispatches a resource server-side.
- Confidence in this finding: High (updated from Medium — backend behavior now confirmed, see below).
- Resolution (11 Jul 2026, confirmed by T. Saxena): Intended behavior is **not** direct dispatch. Architecture updated with a new canonical flow (§8.1 in the full spec): AI creates observation → Assign for Review (human #1) → Supervisor Approval (human #2, role-gated) → Auditor Assignment → Field Action, every step audit-logged with its own status. This is now the standard pattern for any agent output that could lead to a physical action, not just this card. Dashboard updated to implement the full five-state flow with a visible status badge and inline audit trail (see `frontend/dashboard_mockup_v1.html`, Hazard card). `ARCHITECTURE.md` updated to reference this flow under the human-in-the-loop principle.

**F3 — Compliance Score as blanket verdict**
- Observed: `94.8%` labeled "Compliance Score," no clause count, standard reference, or as-of date; not a link-through.
- Requirement violated: §3 — Compliance Agent may never declare "compliant," only "no gap found against checked clauses as of [date]."
- Risk: Highest-weighted finding of the pass — an unscoped number at the most visible dashboard surface is the kind of artifact that gets cited months later, divorced from its original scope.
- Confidence in this finding: High.
- Resolution: Relabeled to "Checked Clauses Passing" with clause count, standards list, and as-of date; made link-through to clause-level view.

**F4 — Unsourced status tiles**
- Observed: "Optimal" / "Certified" presented as settled fact, no source tag, inconsistent with the hazard card above it in the same component.
- Requirement violated: §5 applies to all AI-originated content, not just primary alerts.
- Risk: Lower stakes than F1–F3, but the inconsistency itself trains users to trust some AI outputs more than others based on visual position rather than actual reliability.
- Confidence in this finding: High.
- Resolution: Added source tags (`SCADA FEED`, `TRAINING AGENT`).

### Open questions carried forward

- Whether the Verifier Agent should run on a model/provider independent from the generating agent — blocks: Phase 1 exit criteria (per `ROADMAP.md` open questions).
- New from this resolution: role-gating for Supervisor Approval (§8.1 step 3) must be enforced at the Auth layer, not just the UI. Added as a Phase 1 exit criterion in `ROADMAP.md` (11 Jul 2026) — no longer open here, tracked there.
