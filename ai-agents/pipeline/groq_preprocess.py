"""
Groq preprocessing stage.

Reads an input document, sends it to Groq API for normalization /
section extraction, and writes the structured result to --output as JSON.

Output schema is identical to gemini_preprocess.py so downstream stages
(validation, report generation) work without modification.

Requires GROQ_API_KEY to be set in the environment (passed via workflow).

Role in the pipeline:
- Groq preprocessing (alternative to Gemini, avoids 503 timeouts)
- Data normalization
- Raw text extraction
"""

import argparse
import json
import logging
import os
import sys
import time

from groq import Groq

from config import (
    GROQ_MODEL,
    GROQ_MAX_RETRIES,
    GROQ_INITIAL_DELAY_SECONDS,
    GROQ_MAX_DELAY_SECONDS,
    GROQ_MAX_TOKENS,
    GROQ_JSON_MODE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are a document preprocessing agent. Normalize the given document "
    "into structured sections for downstream review by other AI agents "
    "(Claude for validation/architecture review, ChatGPT for orchestration "
    "and report generation).\n\n"
    "IMPORTANT: Return ONLY a valid JSON object. Do not include markdown "
    "code fences, explanations, or preamble. The JSON object MUST have exactly "
    "these keys:\n"
    "- title (string): Document title\n"
    "- summary (string): Executive summary\n"
    "- sections (array): List of {heading, content} objects\n"
    "- key_points (array): List of important points (strings)\n\n"
    "Example output format:\n"
    '{"title": "...", "summary": "...", "sections": [...], "key_points": [...]}'
)

# Schema for output validation (identical to gemini_preprocess.py)
REQUIRED_OUTPUT_KEYS = {"title", "summary", "sections", "key_points"}


def validate_input(raw_text: str) -> None:
    """Generic input validation."""
    if not raw_text.strip():
        raise ValueError("Input file is empty.")


def validate_output(parsed: dict) -> dict:
    """
    Validate Groq response against the required schema.
    Identical to gemini_preprocess.py for downstream compatibility.
    """
    missing = REQUIRED_OUTPUT_KEYS - parsed.keys()
    if missing:
        raise ValueError(f"Groq output is missing schema keys: {missing}")
    
    if not isinstance(parsed.get("title"), str):
        raise TypeError("'title' must be a string.")
    if not isinstance(parsed.get("summary"), str):
        raise TypeError("'summary' must be a string.")
    if not isinstance(parsed.get("sections"), list):
        raise TypeError("'sections' must be a list.")
    if not isinstance(parsed.get("key_points"), list):
        raise TypeError("'key_points' must be a list.")
    
    # Validate sections structure
    for i, section in enumerate(parsed.get("sections", [])):
        if not isinstance(section, dict):
            raise TypeError(f"Section {i} must be an object.")
        if "heading" not in section or "content" not in section:
            raise ValueError(f"Section {i} missing 'heading' or 'content'.")
    
    return parsed


def call_groq_with_retry(client: Groq, raw_text: str) -> dict:
    """
    Call Groq API with exponential backoff retry logic.
    
    Groq SDK does not provide built-in retry options, so retry is implemented
    at the function level — standard pattern for handling rate limits (429)
    and transient errors (5xx).
    
    Args:
        client: Initialized Groq client.
        raw_text: Input document to normalize.
        
    Returns:
        Validated dict with keys: title, summary, sections, key_points.
        
    Raises:
        SystemExit with code 1 on any failure (logs details first).
    """
    payload_size_bytes = len(raw_text.encode("utf-8"))
    logger.info(
        f"Calling Groq API: model={GROQ_MODEL}, "
        f"payload_size_bytes={payload_size_bytes}, "
        f"max_retries={GROQ_MAX_RETRIES}"
    )
    
    delay = GROQ_INITIAL_DELAY_SECONDS
    start_time = time.time()
    
    for attempt in range(GROQ_MAX_RETRIES):
        try:
            # Build request with optional JSON mode
            request_kwargs = {
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_INSTRUCTION,
                    },
                    {
                        "role": "user",
                        "content": raw_text,
                    },
                ],
                "temperature": 0.1,  # Low temperature for deterministic output
                "max_tokens": GROQ_MAX_TOKENS,
            }
            
            # Add response_format only if explicitly enabled via config
            if GROQ_JSON_MODE:
                request_kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**request_kwargs)
            
            elapsed_seconds = time.time() - start_time
            logger.info(f"Groq API call succeeded in {elapsed_seconds:.1f}s (attempt {attempt + 1})")
            
            # Validate response structure before accessing content
            choice = response.choices[0]
            if not choice.message or not choice.message.content:
                logger.error("Groq returned an empty response.")
                sys.exit(1)
            
            response_text = choice.message.content.strip()
            
            # Defensive parsing: strip markdown code fences if present
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("\n", 1)[0]
            response_text = response_text.strip()
            
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Groq response failed JSON parsing: {e}")
                logger.debug(
                    "Response preview: %r",
                    response_text[:200],
                )
                sys.exit(1)
            
            try:
                return validate_output(parsed)
            except (ValueError, TypeError) as e:
                logger.error(f"Groq output failed schema validation: {e}")
                logger.debug(
                    "Response length: %d bytes",
                    len(response_text.encode("utf-8")),
                )
                sys.exit(1)
        
        except Exception as e:
            elapsed_seconds = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Classify as retryable: rate limit, server errors
            is_retryable = any(code in error_msg for code in ["429", "500", "502", "503", "504"]) or "rate" in error_msg.lower()
            
            if attempt < GROQ_MAX_RETRIES - 1 and is_retryable:
                logger.warning(
                    f"Groq API error (attempt {attempt + 1}/{GROQ_MAX_RETRIES}): {error_type} — {error_msg[:100]} "
                    f"[elapsed={elapsed_seconds:.1f}s]. Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
                delay = min(delay * 2, GROQ_MAX_DELAY_SECONDS)
            else:
                logger.exception(
                    f"Groq API call failed ({error_type}) "
                    f"[elapsed={elapsed_seconds:.1f}s, payload_bytes={payload_size_bytes}]"
                )
                sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Groq preprocessing stage")
    parser.add_argument("--input", required=True, help="Path to input document")
    parser.add_argument("--output", required=True, help="Path to write normalized JSON output")
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not set in environment")
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

    client = Groq(api_key=api_key)
    normalized = call_groq_with_retry(client, raw_text)

    result = {
        "source_file": args.input,
        "status": "ok",
        "model": GROQ_MODEL,
        "raw_text_length": len(raw_text),
        **normalized,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Wrote Groq preprocessing output to {args.output}")


if __name__ == "__main__":
    main()
