# Phase 3 Step 3 – Orchestrator Integration Design

Status: REVIEW

Goals:
- Preserve Phase 1 and Phase 2 behavior.
- Do not modify DocumentGeneratorAgent logic.
- Do not modify RiskAssessmentAgent logic.
- Do not modify PTWJSAAgent logic.
- Integrate new agents through Orchestrator only.

Integration Order:

1. Keep existing /generate endpoint working unchanged.

2. Register:
   - DocumentGeneratorAgent
   - RiskAssessmentAgent
   - PTWJSAAgent

3. Add routing rules only.

4. No existing request format should break.

5. Existing test_api.py and test_e2e.py must continue to pass without modification.

6. Add new integration tests after routing is complete.

Approval required before implementation.
