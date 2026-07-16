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
