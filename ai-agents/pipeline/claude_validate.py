"""
Claude validation stage — STUB, not yet implemented.

Status as of 11 Jul 2026: defines the expected CLI contract and output
shape. Does NOT yet call the Claude API. Running it produces a placeholder
JSON file with hardcoded flags, not a real validation result.

Expected role in the pipeline (per SESSION_RESUME.md):
- validation
- policy checking
- architecture review
- consistency review

This is meant to encode the same checks this repo's canonical standards
require of any change (docs/AI_AGENT_STANDARDS.md) — e.g. does the input
respect the human-in-the-loop gate, does it avoid bypassing frozen
architecture — but as a stub it does not actually perform those checks.

Reads CLAUDE_API_KEY from the environment (set by the workflow from
GitHub Secrets) — this stub does not use it yet.
"""

import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Claude validation stage (stub)")
    parser.add_argument("--input", required=True, help="Path to stage 1 (Gemini) output JSON")
    parser.add_argument("--output", required=True, help="Path to write validated JSON output")
    args = parser.parse_args()

    if not os.environ.get("CLAUDE_API_KEY"):
        print("::warning::CLAUDE_API_KEY not set in environment — stub will still run but real implementation would fail here.", file=sys.stderr)

    if not os.path.exists(args.input):
        print(f"::error::Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        stage1 = json.load(f)

    # STUB OUTPUT — not a real Claude call, and NOT a real policy/
    # architecture check. Do not treat "checks_passed: true" below as a
    # real verification result — replace this block with an actual Claude
    # API call implementing real checks before relying on it.
    result = {
        "stage": "claude_validate",
        "status": "STUB — not a real API call, checks below are not real",
        "input_from": stage1.get("stage"),
        "checks": {
            "human_in_the_loop_respected": None,
            "architecture_bypass_detected": None,
            "envelope_schema_valid": None,
        },
        "checks_passed": None,
        "note": "Replace this stub with a real Claude API call implementing real validation before trusting any 'checks_passed' value.",
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[STUB] Wrote placeholder output to {args.output}")


if __name__ == "__main__":
    main()
