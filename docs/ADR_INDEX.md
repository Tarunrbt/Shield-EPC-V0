# Shield EPC — Architecture Decision Register (ADR Index)

This is the canonical decision register for Shield EPC. It tracks the lifecycle
status of each architectural decision, so any reviewer (human or AI) can
immediately see what's proposal, what's verified against source, and what's
policy.

This document is split into two parts, added in separate commits:

1. **This file — the governance framework.** Status model, evidence model,
   promotion rules, review policy. No claims about the current state of the
   codebase live here — this part should stay stable even as the codebase
   changes.
2. **The Current Register** (added in a follow-up commit) — the actual table
   of architectural decisions and their status. This is a living document;
   every row is an independently reviewable claim with its own evidence.

Keeping these separate means a reviewer's confidence in the governance rules
does not depend on the register being current.

## Status Model

| Status | Meaning |
|---|---|
| Open | Decision has not been made yet — options are being weighed |
| Accepted | The architecture/spec has committed to this decision, but code+tests supporting it haven't been (fully) verified yet |
| Deferred | Deliberately postponed for a later phase, with a stated reason |
| Verification Pending | Referenced/assumed in docs or inferred from tests/commit messages/partial file views, but the actual source has not been directly opened and confirmed |
| Verified Stable | Code AND tests AND architecture spec all support this decision — confirmed by direct inspection, not inference |
| Frozen | Changing this requires a new ADR with explicit justification — the highest bar, reserved for decisions the project should not casually revisit |
| Superseded | Replaced by a newer ADR — kept here for history, not current guidance |

There is no separate "Planned" status — a decision the architecture has
committed to but not yet started is Accepted (if actively intended) or
Deferred (if intentionally postponed with a reason). These two together cover
what "Planned" would otherwise mean, without adding a redundant state.

## Promotion Rule

A decision may only be marked **Frozen** if it is currently **Verified
Stable** — i.e., directly confirmed by source code and passing tests, not
merely "Accepted" at the architecture-spec level. Frozen cannot be reached
directly from Open or Accepted. This prevents architectural intent from being
mistaken for architectural fact.

A decision may only be marked **Verified Stable** if someone has actually
opened and read the relevant source file(s) — not inferred from a commit
message, a test's behavior alone, or a partial/truncated file view.

## Core Philosophy

Absence of evidence is never evidence of absence. If a file hasn't been
opened, the correct status is "Verification Pending" — never a confident
negative claim like "X doesn't exist" or "X isn't implemented." This applies
to every row in the Current Register and to any future addition.

## Evidence Types

Each register row's evidence is tagged with one or more of:

| Tag | Meaning |
|---|---|
| Source | Source code directly inspected (file opened and read) |
| Test | Verified by automated tests actually passing |
| Spec | Stated in the architecture specification document only |
| Runtime | Observed by actually executing code (e.g. a manual verification script, or a test asserting the observed behavior) |
| Inferred | Known only via commit message, test names, or a partial/truncated file view — not directly read |

Inferred evidence alone can never justify promoting a row to Verified Stable or
Frozen — it only ever supports Verification Pending, pending a direct source
read.

## Verification Record

Any status change to Verified Stable or Frozen, and any decision affecting an
ADR row, should be accompanied by a Verification Record following
[docs/VERIFICATION_TEMPLATE.md](./VERIFICATION_TEMPLATE.md) — Short Record for
feature completions, Full Record for status/ADR changes. This document
defines *what* a status means; VERIFICATION_TEMPLATE.md defines *how* a
status change gets evidenced. Content is not duplicated between the two.

*(Note: `docs/VERIFICATION_TEMPLATE.md` is added in the commit immediately
following this one. If this link is broken, that commit hasn't landed yet.)*

## Review Policy

Every architectural recommendation — from any reviewer, human or AI — must
satisfy all five gates before it becomes a roadmap item:

1. **Verified against source** — not assumed, not inferred from a commit
   message or test name alone.
2. **Solves a demonstrated problem** — not a hypothetical or trend-driven
   addition.
3. **Appropriate for the current project phase** — matches the actual
   scale/complexity the project has reached, not a future one.
4. **Does not contradict an existing Frozen ADR** — if it does, it must be
   proposed as a new ADR explicitly superseding the old one, not a silent
   override.
5. **Has an explicit migration path** if it changes an Accepted or Verified
   Stable decision — changing settled decisions requires a stated transition
   plan, not just a new preference.

This policy applies equally to any AI tool or human contributor reviewing
this project — it is the common protocol for how architectural change gets
proposed and accepted here.

## Contributor Workflow (Maintenance Rules)

- When updating the Current Register, add new evidence to the existing row
  rather than deleting history — if a status downgrades (e.g. something
  thought Verified Stable turns out to be only partially confirmed), note
  why, don't silently overwrite.
- Never write a confident negative ("X doesn't exist," "Y isn't
  implemented") from an unopened file — use "Verification Pending" instead,
  per the Core Philosophy above.
- A claim's evidence tag must match what was actually done: Source-only
  evidence does not justify writing "Runtime" or "Test" on the same row.
- This file should be one of the first things a new session opens when
  asked "what's the state of Shield EPC's architecture" — read it before
  re-deriving conclusions already settled here.
