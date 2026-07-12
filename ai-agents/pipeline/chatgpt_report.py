"""
ChatGPT orchestration / report generation stage — STUB, not yet implemented.

Status as of 11 Jul 2026: defines the expected CLI contract and output
shape. Does NOT yet call the OpenAI API. Running it produces a placeholder
Markdown + JSON report, not a real generated report.

Expected role in the pipeline (per SESSION_RESUME.md):
- reasoning
- orchestration
- report generation
- final recommendations

Reads OPENAI_API_KEY from the environment (set by the workflow from
GitHub Secrets) — this stub does not use it yet.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser(description="ChatGPT report generation stage (stub)")
    parser.add_argument("--input", required=True, help="Path to stage 2 (Claude) output JSON")
    parser.add_argument("--output-md", required=True, help="Path to write Markdown report")
    parser.add_argument("--output-json", required=True, help="Path to write JSON report")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("::warning::OPENAI_API_KEY not set in environment — stub will still run but real implementation would fail here.", file=sys.stderr)

    if not os.path.exists(args.input):
        print(f"::error::Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        stage2 = json.load(f)

    timestamp = datetime.now(timezone.utc).isoformat()

    # STUB OUTPUT — not a real ChatGPT call, and no real recommendations
    # are generated. This exists only so the workflow has a complete,
    # runnable path end to end while the real integrations are built.
    report_json = {
        "stage": "chatgpt_report",
        "status": "STUB — not a real API call, no real recommendations generated",
        "generated_at": timestamp,
        "input_from": stage2.get("stage"),
        "recommendations": [],
        "note": "Replace this stub with a real OpenAI API call before treating any output here as a real recommendation.",
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    md_content = f"""# Verification Report (STUB)

**Generated**: {timestamp}
**Status**: STUB — this report was produced by placeholder pipeline scripts, not real Gemini/Claude/OpenAI API calls. Do not treat any content below as a real verification result.

## Pipeline Stage Status

| Stage | Status |
|---|---|
| Gemini preprocessing | STUB |
| Claude validation | STUB |
| ChatGPT report generation | STUB |

## Next Steps

Replace all three scripts in `ai-agents/pipeline/` with real API integrations before this report is trustworthy. See `docs/AI_AGENT_STANDARDS.md` for the standards this pipeline is meant to enforce once implemented.
"""

    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[STUB] Wrote placeholder outputs to {args.output_md} and {args.output_json}")


if __name__ == "__main__":
    main()
