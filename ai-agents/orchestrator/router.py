"""
Routing logic for the Hermes orchestrator.

Decides which script and environment variables apply for a given
provider choice, using the registry in providers.py. Validates that
required environment variables are set before a stage runs, so
failures are reported clearly instead of surfacing as a provider SDK
traceback.
"""

import os

from providers import VALIDATION_PROVIDERS, REPORT_PROVIDERS, PREPROCESS_SCRIPT, PREPROCESS_REQUIRED_ENV


class RoutingError(Exception):
    """Raised when a provider choice or its environment is invalid."""


def _check_env(required_env):
    missing = [var for var in required_env if not os.environ.get(var)]
    return missing


def resolve_preprocess():
    """Returns (script_path, missing_env_vars) for Stage 1."""
    missing = _check_env(PREPROCESS_REQUIRED_ENV)
    return PREPROCESS_SCRIPT, missing


def resolve_validation_provider(provider_name):
    """Returns (script_path, missing_env_vars) for the given Stage 2 provider."""
    provider_name = (provider_name or "").strip().lower()
    if provider_name not in VALIDATION_PROVIDERS:
        raise RoutingError(
            f"VALIDATION_PROVIDER must be one of {list(VALIDATION_PROVIDERS.keys())} "
            f"(got: '{provider_name or '<unset>'}')."
        )
    entry = VALIDATION_PROVIDERS[provider_name]
    missing = _check_env(entry["required_env"])
    return entry["script"], missing


def resolve_report_provider(provider_name):
    """Returns (script_path, missing_env_vars) for the given Stage 3 provider."""
    provider_name = (provider_name or "").strip().lower()
    if provider_name not in REPORT_PROVIDERS:
        raise RoutingError(
            f"REPORT_PROVIDER must be one of {list(REPORT_PROVIDERS.keys())} "
            f"(got: '{provider_name or '<unset>'}')."
        )
    entry = REPORT_PROVIDERS[provider_name]
    missing = _check_env(entry["required_env"])
    return entry["script"], missing
