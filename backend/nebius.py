"""
Nebius Token Factory provider factory for the AERO-ASTRA LLM fallback chain.

Reads three env vars:
    NEBIUS_API_KEY   — Token Factory API key
    NEBIUS_BASE_URL  — OpenAI-compatible base URL from the Token Factory docs
    <model_env>      — env var whose value is the exact model slug (e.g.
                       NEBIUS_MODEL_SHERLOCK or NEBIUS_MODEL_ATHENA)

When NEBIUS_ONLY=1 the factory raises loudly if any of those vars are missing,
instead of returning None and allowing a silent fallback to another provider.
This ensures demo and video runs use Token Factory exclusively.
"""
from __future__ import annotations

import logging
import os

from openai import OpenAI

from backend.llm_client import LLMProvider

log = logging.getLogger(__name__)


def nebius_only() -> bool:
    """Return True when the process is running in Nebius-only (demo) mode."""
    return os.environ.get("NEBIUS_ONLY", "0") == "1"


def nebius_provider(model_env: str, timeout_s: int = 120) -> LLMProvider | None:
    """
    Build a Token Factory LLMProvider.

    Args:
        model_env:  Name of the environment variable that holds the model slug,
                    e.g. ``"NEBIUS_MODEL_SHERLOCK"`` or ``"NEBIUS_MODEL_ATHENA"``.
        timeout_s:  Per-request wall-clock timeout in seconds.

    Returns:
        A configured LLMProvider, or None when the required env vars are missing
        and NEBIUS_ONLY is not set (allowing local/cloud fallback in dev mode).

    Raises:
        RuntimeError: When NEBIUS_ONLY=1 and any required env var is absent.
    """
    key   = os.environ.get("NEBIUS_API_KEY")
    base  = os.environ.get("NEBIUS_BASE_URL")
    model = os.environ.get(model_env)

    missing = [
        name
        for name, val in (
            ("NEBIUS_API_KEY",  key),
            ("NEBIUS_BASE_URL", base),
            (model_env,         model),
        )
        if not val
    ]

    if missing:
        if nebius_only():
            raise RuntimeError(
                f"NEBIUS_ONLY=1 but these env vars are missing: {missing}. "
                "Set them in .env before running in demo/video mode."
            )
        log.warning("Nebius provider disabled — missing env vars: %s", missing)
        return None

    log.info("Nebius Token Factory provider ready | model_env=%s model=%s", model_env, model)
    return LLMProvider(
        name=f"Nebius Token Factory ({model})",
        client=OpenAI(base_url=base, api_key=key),
        model=model,          # type: ignore[arg-type]  # checked non-None above
        timeout_s=timeout_s,
    )
