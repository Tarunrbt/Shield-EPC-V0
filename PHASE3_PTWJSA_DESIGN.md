# Phase 3 PTW/JSA Agent Design

Status: APPROVED

Decision:
- PTWJSAAgent will be a NEW agent.
- DocumentGeneratorAgent will NOT be modified.
- Existing templates remain unchanged.
- PTWJSAAgent will call:
  1. Hazard Library
  2. DocumentGeneratorAgent
- Hazard data will remain structured fields.
- No appending extra text to DocumentGeneratorAgent output.
- Existing Phase 1 and Phase 2 code remains untouched.

Next implementation:
1. backend/app/agents/ptw_jsa.py
2. Unit tests
3. Regression tests
