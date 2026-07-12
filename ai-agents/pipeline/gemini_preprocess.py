"""
Gemini preprocessing stage — STUB, not yet implemented.

Status as of 11 Jul 2026: this script defines the expected CLI contract
(--input, --output) and output shape so the GitHub Actions workflow has
something real to call, but it does NOT yet call the Gemini API. Running
it will produce a placeholder JSON file, not a real preprocessing result.

Do not remove this docstring warning until the real API call is implemented
and has been run successfully at least once.

Expected role in the pipeline (per SESSION_RESUME.md):
- preprocessing
- data normalization
- context extraction

Reads GEMINI_API_KEY from the environment (set by the workflow from
GitHub Secrets) — this stub does not use it yet.
"""

import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Gemini preprocessing stage (stub)")
    parser.add_argument("--input", required=True, help="Path to input document")
    parser.add_argument("--output", required=True, help="Path to write normalized JSON output")
    args = parser.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        print("::warning::GEMINI_API_KEY not set in environment — stub will still run but real implementation would fail here.", file=sys.stderr)

    if not os.path.exists(args.input):
        print(f"::error::Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # STUB OUTPUT — not a real Gemini call. Replace this block with an
    # actual Gemini API request before relying on this pipeline for
    # anything real.
    result = {
        "stage": "gemini_preprocess",
        "status": "STUB — not a real API call",
        "input_path": args.input,
        "input_length_chars": len(raw_text),
        "normalized_context": None,
        "extracted_entities": [],
        "note": "Replace this stub with a real Gemini API call before this pipeline is used for anything that matters.",
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[STUB] Wrote placeholder output to {args.output}")


if __name__ == "__main__":
    main()
