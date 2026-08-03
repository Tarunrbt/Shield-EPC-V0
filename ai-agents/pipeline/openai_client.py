"""
Shared OpenAI-compatible client factory.

Honors OPENAI_BASE_URL so any Stage (2 or 3) can be pointed at a local
or alternate OpenAI-compatible endpoint (e.g. Ollama), falling back to
a provider-specific default endpoint when unset.
"""

import os
from openai import OpenAI


def create_client(api_key: str, default_base_url: str = ""):
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip() or default_base_url

    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)

    return OpenAI(api_key=api_key)
