"""
ChatGPT orchestration / report generation stage.

Calls the OpenAI API to synthesize Stage 2 (Claude) validation output into
a final report: summary and recommendations, per this repo's canonical
standards (docs/AI_AGENT_STANDARDS.md).

Reads OPENAI_API_KEY from the environment (set by the workflow from
GitHub Secrets / Termux environment) — same pattern as GEMINI_API_KEY and
CLAUDE_API_KEY.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from openai import OpenAI

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

SYSTEM_PROMPT = (
    "You are Stage 3 (ChatGPT) in an HSE automation pipeline. "
    "You receive Stage 2 (Claude) validation output and must produce a "
    "short summary and a list of concrete recommendations, consistent "
    "with this repo's canonical standards (docs/AI_AGENT_STANDARDS.md). "
    'Respond with ONLY a JSON object: {"summary": "short overall summary", '
    '"recommendations": ["...", "..."]}. No markdown, no prose outside the JSON.'
)


def main():
    parser = argparse.ArgumentParser(description="ChatGPT report generation stage")
    parser.add_argument("--input", required=True, help="Path to stage 2 (Claude) output JSON")
    parser.add_argument("--output-md", required=True, help="Path to write Markdown report")
    parser.add_argument("--output-json", required=True, help="Path to write JSON report")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("::error::OPENAI_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"::error::Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        stage2 = json.load(f)

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Stage 2 output:\n{json.dumps(stage2, ensure_ascii=False)}",
            },
        ],
        max_tokens=768,
    )

    raw = (response.choices[0].message.content or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        chatgpt_output = json.loads(raw)
    except json.JSONDecodeError:
        print(f"::error::ChatGPT did not return valid JSON: {raw}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).isoformat()
    summary = chatgpt_output.get("summary", "")
    recommendations = chatgpt_output.get("recommendations", [])

    report_json = {
        "stage": "chatgpt_report",
        "status": "ok",
        "generated_at": timestamp,
        "input_from": stage2.get("stage"),
        "recommendations": recommendations,
        "note": summary,
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    checks = stage2.get("checks", {})

    md_lines = [
        "# Verification Report",
        "",
        f"**Generated**: {timestamp}",
        "",
        "## Pipeline Summary",
        "",
        "| Stage | Result |",
        "|---|---|",
        f"| Stage 2 — Claude validation | {stage2.get('status', 'unknown')} |",
        "| Stage 3 — ChatGPT report | ok |",
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

    print(f"[STAGE3] Wrote {args.output_md} and {args.output_json} — status: ok")


if __name__ == "__main__":
    main()
