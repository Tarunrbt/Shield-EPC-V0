"""
Groq validation stage (free-tier fallback).

Calls the Groq API (OpenAI-compatible endpoint) to perform the checks
required by this repo's canonical standards (docs/AI_AGENT_STANDARDS.md):
human-in-the-loop gate respected, no bypass of frozen architecture, valid
Stage 1 envelope.
Reads GROQ_API_KEY from the environment (set by the workflow from
GitHub Secrets) — same pattern as GEMINI_API_KEY, CLAUDE_API_KEY, and
DEEPSEEK_API_KEY.
"""

import argparse
import json
import os
import sys

from openai import OpenAI
from openai_client import create_client

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

SYSTEM_PROMPT = (
    "You are Stage 2 (Groq) in an HSE automation pipeline. "
    "You receive Stage 1 output and must verify three checks against this "
    "repo's canonical standards (docs/AI_AGENT_STANDARDS.md): "
    "1) human_in_the_loop_respected — whether the workflow preserves human "
    "sign-off before any action is taken, "
    "2) architecture_bypass_detected — whether Stage 1 output shows any "
    "sign of bypassing the frozen architecture/ADR constraints, "
    "3) envelope_schema_valid — whether the Stage 1 JSON envelope matches "
    "the expected schema fields. "
    'Respond with ONLY a JSON object: {"human_in_the_loop_respected": true|false, '
    '"architecture_bypass_detected": true|false, "envelope_schema_valid": true|false, '
    '"notes": "short explanation"}. No markdown, no prose outside the JSON.'
)


def main():
    parser = argparse.ArgumentParser(description="Groq validation stage")
    parser.add_argument("--input", required=True, help="Path to stage 1 (Gemini) output JSON")
    parser.add_argument("--output", required=True, help="Path to write validated JSON output")
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("::error::GROQ_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"::error::Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        stage1 = json.load(f)

    client = create_client(api_key, default_base_url="https://api.groq.com/openai/v1")

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Stage 1 output:\n{json.dumps(stage1, ensure_ascii=False)}",
            },
        ],
        max_tokens=512,
    )

    raw = (response.choices[0].message.content or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        groq_checks = json.loads(raw)
    except json.JSONDecodeError:
        print(f"::error::Groq did not return valid JSON: {raw}", file=sys.stderr)
        sys.exit(1)

    checks = {
        "human_in_the_loop_respected": groq_checks.get("human_in_the_loop_respected"),
        "architecture_bypass_detected": groq_checks.get("architecture_bypass_detected"),
        "envelope_schema_valid": groq_checks.get("envelope_schema_valid"),
    }

    checks_passed = (
        checks["human_in_the_loop_respected"] is True
        and checks["architecture_bypass_detected"] is False
        and checks["envelope_schema_valid"] is True
    )

    result = {
        "stage": "groq_validate",
        "status": "pass" if checks_passed else "fail",
        "input_from": stage1.get("stage"),
        "checks": checks,
        "checks_passed": checks_passed,
        "note": groq_checks.get("notes", ""),
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[STAGE2] Wrote {args.output} — status: {result['status']}")


if __name__ == "__main__":
    main()
