# Shield EPC Verification and Evidence Framework

## 1. Purpose

This framework ensures that every change to the Shield EPC repository — from a routine fix to an architecture decision — is backed by verifiable, inspectable evidence rather than assumption or intent.

It formalizes the evidence-first discipline: negative claims are not accepted without a source check, and status changes are not accepted without reproducible evidence tied to a specific commit.

## 2. Scope

Applies to all code changes, ADR status transitions, domain model changes, and architecture-affecting decisions in Shield EPC. It does not replace code review; it defines the minimum evidence record required before a change or claim can be treated as verified.

## 3. Verification Principles

- **Evidence over intent.** An ADR or status is promoted based on verified evidence, not architectural intent alone.
- **No negative claims without inspection.** A statement that something "does not exist" or "is not implemented" must cite the source location inspected to confirm its absence.
- **Reproducibility.** Every verification is tied to a specific commit hash so it remains a valid historical statement even after the codebase or test suite changes.
- **Proportionality.** Evidence depth scales with risk and blast radius, not with change size. A one-line fix can require full verification if it touches a domain boundary; a large but mechanical refactor may not.

## 4. Verification Levels

| Level | When to use |
|-------|-----------|
| **Routine** | Minor, low-risk changes (typos, styling, isolated logic tweaks) with no architectural surface |
| **Short** | Feature completion or moderate changes where structural evidence matters but full architectural review is unwarranted |
| **Full** | ADR status changes to Verified Stable or Frozen, domain model changes, or anything hitting the Escalation Rule |

## 5. Escalation Rule

If a Routine or Short Verification surfaces an unexpected architectural finding, a negative-claim contradiction, an ADR impact, a domain model change, or a public API/database behavior change, the verification is immediately escalated to a Full Verification Record — regardless of how small the original change appeared.

**Evidence takes precedence over the original change's perceived size.**

## 6. Short Verification Record (Template)

```markdown
### Short Verification Record

**Feature / Change:**  
**Commit Hash:**  
**Date:**  

#### Source Inspection
- Files inspected:
- File:Line references:
- Expected vs Observed:

#### Targeted Tests
- Tests executed:
- Result:

#### Conclusion:
### Full Verification Record

**Feature / Change:**  
**Status Change:**  
**Date:**  

#### Evidence Baseline
- Repository:
- Commit Hash:
- Version Tag:
- Branch:

#### Verification Method

**1. Source Inspection**
- Files inspected:
- File:Line references:
- Expected implementation:
- Observed implementation:

**2. Negative Claim Verification**
- Claim being verified:
- Evidence inspected:
- Result:

**3. Targeted Tests**
- Tests executed:
- Result:

**4. Full Regression**
- Test Suite Snapshot:
  - Passed:
  - Failed:
  - Skipped:
- Commit Hash:
- Environment (OS, runtime/interpreter version, dependency lock file hash):

#### Impact Assessment
- ADR affected:
- Domain model affected:
- Public API affected:
- Database schema affected:
- Breaking changes:

#### Evidence Quality
- Direct evidence:
- Indirect evidence:
- Assumptions:
- Confidence Level: High / Medium / Low (governed by weakest link, not the average)

#### Verification Metadata
- Verified By:
- Review Date:
- Review Notes:

#### Evidence Summary
- Conclusion:
- Remaining work:
- Follow-up required:
