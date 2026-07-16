"""
Gemini preprocessing stage.

Reads an input document, sends it to the Gemini API for normalization /
section extraction, and writes the structured result to --output as JSON.

Requires GEMINI_API_KEY to be set in the environment (passed in via the
GitHub Actions workflow from repo Secrets).

Role in the pipeline (per SESSION_RESUME.md):
- Gemini preprocessing
- Data normalization
- Raw text extraction
"""

import argparse
import json
import logging
import os
import sys
import time

from google import genai
from google.genai import types
from google.genai.errors import APIError

try:
    import httpx
except ImportError:
    # httpx may not be directly imported if via google.genai; define a fallback
    httpx = None

from config import (
    GEMINI_MODEL,
    GEMINI_MAX_RETRIES,
    GEMINI_RETRY_INITIAL_DELAY_SECONDS,
    GEMINI_RETRY_MAX_DELAY_SECONDS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Explicit timeout to prevent indefinite hangs. The 4m 44s failure suggests
# requests can stall; this hard limit ensures the workflow fails fast and
# audibly rather than timing out silently.
GEMINI_REQUEST_TIMEOUT_SECONDS = 300

SYSTEM_INSTRUCTION = (
    "You are a document preprocessing agent. Normalize the given document "
    "into structured sections for downstream review by other AI agents "
    "(Claude for validation/architecture review, ChatGPT for orchestration "
    "and report generation)."
)

# Enforced output shape — the model is constrained to return exactly this,
# so no fence-stripping or "hope it's valid JSON" parsing is needed.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["heading", "content"],
            },
        },
        "key_points": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["title", "summary", "sections", "key_points"],
}

REQUIRED_OUTPUT_KEYS = {"title", "summary", "sections", "key_points"}


def build_client(api_key: str) -> "genai.Client":
    """
    Client-level retry uses the SDK's own HttpRetryOptions rather than a
    hand-rolled loop — it retries on the documented transient codes
    (408/429/5xx) and is Google's recommended approach.
    
    NOTE: HttpRetryOptions does NOT handle connection-level errors like
    RemoteProtocolError (server disconnect). Those must be caught at the
    call site in call_gemini().
    """
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=GEMINI_MAX_RETRIES,
                initial_delay=GEMINI_RETRY_INITIAL_DELAY_SECONDS,
                max_delay=GEMINI_RETRY_MAX_DELAY_SECONDS,
                http_status_codes=[408, 429, 500, 502, 503, 504],
            )
        ),
    )


def validate_input(raw_text: str) -> None:
    """
    Generic input validation.

    NOTE: this stage's real input (per the workflow) is a document like
    docs/AI_AGENT_STANDARDS.md — free-form text/markdown, not structured
    JSON. Do not add fields like incident_id/description/site_context
    here unless the pipeline's actual input contract changes to require
    them; that assumption would break the current workflow.
    """
    if not raw_text.strip():
        raise ValueError("Input file is empty.")


def validate_output(parsed: dict) -> dict:
    """
    Validate Gemini response against the required schema.
    """
    missing = REQUIRED_OUTPUT_KEYS - parsed.keys()
    if missing:
        raise ValueError(f"Gemini output is missing schema keys: {missing}")
    if not isinstance(parsed.get("summary"), str):
        raise TypeError("'summary' must be a string.")
    if not isinstance(parsed.get("sections"), list):
        raise TypeError("'sections' must be a list.")
    if not isinstance(parsed.get("key_points"), list):
        raise TypeError("'key_points' must be a list.")
    return parsed


def call_gemini(client: "genai.Client", raw_text: str) -> dict:
    """
    Call Gemini API with structured error handling.
    
    Retries are handled by the client-level HttpRetryOptions for transient
    HTTP errors (5xx, 429, 408). This function catches additional failure
    modes:
    - APIError: all non-retryable HTTP errors and exhausted retries
    - httpx.RemoteProtocolError: server disconnect before response
    - Other exceptions: logging for observability
    
    Args:
        client: Initialized Gemini client with retry configuration.
        raw_text: Preprocessed input document to normalize.
        
    Returns:
        Validated dict with keys: title, summary, sections, key_points.
        
    Raises:
        SystemExit with code 1 on any failure (logs details first).
    """
    payload_size_bytes = len(raw_text.encode("utf-8"))
    logger.info(
        f"Calling Gemini API: model={GEMINI_MODEL}, "
        f"payload_size_bytes={payload_size_bytes}, "
        f"timeout={GEMINI_REQUEST_TIMEOUT_SECONDS}s"
    )
    
    start_time = time.time()
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=raw_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
            ),
            request_options={"timeout": GEMINI_REQUEST_TIMEOUT_SECONDS},
        )
    except APIError as e:
        # Client-level retry already exhausted transient codes by the time
        # this is raised. 400/401/403 land here immediately (fatal, not
        # transient) and 429/5xx land here only after retries are spent.
        elapsed_seconds = time.time() - start_time
        logger.error(
            f"Gemini API call failed (code={e.code}): {e.message} "
            f"[elapsed={elapsed_seconds:.1f}s, payload_bytes={payload_size_bytes}]"
        )
        sys.exit(1)
    except Exception as e:
        # Catch connection-level errors (httpx.RemoteProtocolError, etc.)
        # that are NOT mapped to APIError by the SDK.
        elapsed_seconds = time.time() - start_time
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(
            f"Gemini API call raised {error_type}: {error_msg} "
            f"[elapsed={elapsed_seconds:.1f}s, payload_bytes={payload_size_bytes}]"
        )
        logger.info(
            "Network errors (RemoteProtocolError, ConnectionError) may be "
            "transient. Consider re-running the workflow."
        )
        sys.exit(1)

    elapsed_seconds = time.time() - start_time
    logger.info(f"Gemini API call succeeded in {elapsed_seconds:.1f}s")

    try:
        parsed = json.loads(response.text)
    except json.JSONDecodeError as e:
        logger.error(f"Gemini response failed JSON parsing: {e}")
        logger.debug(f"Response text (first 500 chars): {response.text[:500]}")
        sys.exit(1)

    try:
        return validate_output(parsed)
    except (ValueError, TypeError) as e:
        logger.error(f"Gemini output failed schema validation: {e}")
        logger.debug(f"Parsed response: {json.dumps(parsed, indent=2)[:500]}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Gemini preprocessing stage")
    parser.add_argument("--input", required=True, help="Path to input document")
    parser.add_argument("--output", required=True, help="Path to write normalized JSON output")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not set in environment")
        sys.exit(1)

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        raw_text = f.read()

    try:
        validate_input(raw_text)
    except ValueError as e:
        logger.error(f"Input validation failed: {e}")
        sys.exit(1)

    client = build_client(api_key)
    normalized = call_gemini(client, raw_text)

    result = {
        "source_file": args.input,
        "status": "ok",
        "model": GEMINI_MODEL,
        "raw_text_length": len(raw_text),
        **normalized,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Wrote Gemini preprocessing output to {args.output}")


if __name__ == "__main__":
    main()
