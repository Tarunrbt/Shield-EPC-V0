"""
Stage 3 report generation.

Synthesizes Stage 2 validation output into a final report: summary and
recommendations, per this repo's canonical standards
(docs/AI_AGENT_STANDARDS.md).

Provider-agnostic: REPORT_PROVIDER selects between Groq and OpenAI, both
accessed via the OpenAI-compatible chat completions API. No model IDs are
hardcoded — all model selection comes from GitHub Variables.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from openai import OpenAI
from openai_client import create_client

SYSTEM_PROMPT = (
    "You are Stage 3 in an HSE automation pipeline. "
    "You receive Stage 2 validation output and must produce a "
    "short summary and a list of concrete recommendations, consistent "
    "with this repo's canonical standards (docs/AI_AGENT_STANDARDS.md). "
    'Respond with ONLY a JSON object: {"summary": "short overall summary", '
    '"recommendations": ["...", "..."]}. No markdown, no prose outside the JSON.'
)


def main():
    parser = argparse.ArgumentParser(description="Stage 3 report generation")
    parser.add_argument("--input", required=True, help="Path to Stage 2 output JSON")
    parser.add_argument("--output-md", required=True, help="Path to write Markdown report")
    parser.add_argument("--output-json", required=True, help="Path to write JSON report")
    args = parser.parse_args()

    # --- Provider selection (validated here, after argparse, not at import time) ---
    report_provider = os.environ.get("REPORT_PROVIDER", "").strip().lower()

    if report_provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("::error::GROQ_API_KEY not set in environment.", file=sys.stderr)
            sys.exit(1)
        report_model = os.environ.get("GROQ_REPORT_MODEL")
        if not report_model:
            print("::error::GROQ_REPORT_MODEL not set in environment.", file=sys.stderr)
            sys.exit(1)
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        supports_json_mode = True  # Groq's OpenAI-compatible endpoint supports response_format

    elif report_provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("::error::OPENAI_API_KEY not set in environment.", file=sys.stderr)
            sys.exit(1)
        report_model = os.environ.get("OPENAI_MODEL")
        if not report_model:
            print("::error::OPENAI_MODEL not set in environment.", file=sys.stderr)
            sys.exit(1)
        client = create_client(api_key)
        supports_json_mode = True

    else:
        print(
            "::error::REPORT_PROVIDER must be 'groq' or 'openai' "
            f"(got: '{report_provider or '<unset>'}').",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"::error::Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        stage2 = json.load(f)

    completion_kwargs = dict(
        model=report_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Stage 2 output:\n{json.dumps(stage2, ensure_ascii=False)}",
            },
        ],
        max_tokens=768,
    )
    if supports_json_mode:
        completion_kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**completion_kwargs)

    raw = (response.choices[0].message.content or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        report_output = json.loads(raw)
    except json.JSONDecodeError:
        print(f"::error::{report_provider} did not return valid JSON: {raw}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).isoformat()
    summary = report_output.get("summary", "")
    recommendations = report_output.get("recommendations", [])

    report_json = {
        "stage": "stage3_report",
        "status": "ok",
        "generated_at": timestamp,
        "input_from": stage2.get("stage"),
        "recommendations": recommendations,
        "note": summary,
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    checks = stage2.get("checks", {})
    validation_provider = os.environ.get("VALIDATION_PROVIDER", "unknown").strip().lower() or "unknown"

    md_lines = [
        "# Verification Report",
        "",
        f"**Generated**: {timestamp}",
        "",
        "## Pipeline Summary",
        "",
        "| Stage | Result |",
        "|---|---|",
        f"| Stage 2 — {validation_provider.capitalize()} validation | {stage2.get('status', 'unknown')} |",
        f"| Stage 3 — {report_provider.capitalize()} report | ok |",
        "",
        "## Stage 2 Validation Checks",
        "",
        f"- human_in_the_loop_respected: {checks.get('human_in_the_loop_respected', 'unknown')}",
        f"- architecture_bypass_detected: {checks.get('architecture_bypass_detected', 'unknown')}",
        f"- envelope_schema_valid: {checks.get('envelope_schema_valid', 'unknown')}",
        "",
        "## Summary",
        "",
        summary or "_No summary returned._",
        "",
        "## Recommendations",
        "",
    ]
    if recommendations:
        for rec in recommendations:
            md_lines.append(f"- {rec}")
    else:
        md_lines.append("_No recommendations returned._")

    md_content = "\n".join(md_lines) + "\n"

    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[STAGE3] Wrote {args.output_md} and {args.output_json} — status: ok (provider: {report_provider})")


if __name__ == "__main__":
    main()
