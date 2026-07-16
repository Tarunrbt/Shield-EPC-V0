"""
Shared pipeline configuration. Values can be overridden via environment
variables so CI and local runs can point at different models without
code changes.

NOTE (11 Jul 2026): gemini-2.0-flash and gemini-2.0-flash-lite were shut
down by Google on 1 June 2026 — do not use them as a default. Current
GA options as of this date: gemini-3.5-flash (stable, cheaper) or
gemini-3.5-flash (newer, stronger on agentic/coding tasks). Re-check
https://ai.google.dev/gemini-api/docs/models before changing this.
"""

import os

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

# Retry tuning — used by the SDK's built-in HttpRetryOptions, not a
# hand-rolled retry loop.
GEMINI_MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "4"))
GEMINI_RETRY_INITIAL_DELAY_SECONDS = float(os.environ.get("GEMINI_RETRY_INITIAL_DELAY_SECONDS", "2"))
GEMINI_RETRY_MAX_DELAY_SECONDS = float(os.environ.get("GEMINI_RETRY_MAX_DELAY_SECONDS", "30"))

# Groq configuration
GROQ_MODEL = os.environ.get("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_MAX_RETRIES = int(os.environ.get("GROQ_MAX_RETRIES", "3"))
GROQ_INITIAL_DELAY_SECONDS = float(
    os.environ.get("GROQ_INITIAL_DELAY_SECONDS", "2")
)
GROQ_MAX_DELAY_SECONDS = float(
    os.environ.get("GROQ_MAX_DELAY_SECONDS", "10")
)
GROQ_MAX_TOKENS = int(
    os.environ.get("GROQ_MAX_TOKENS", "4000")
)
GROQ_JSON_MODE = (
    os.environ.get("GROQ_JSON_MODE", "false").lower() == "true"
)
