"""Optional, advisory-only LLM layer.

On DGX Spark this targets the shared Desktop **vLLM** OpenAI-compatible server
(``http://127.0.0.1:8000/v1``), the same endpoint used by Article Buddy, Book
Buddy, Grey Swan, and ScreenLens. The LLM may write narratives and
recommendations; it NEVER makes a severity or verdict decision. If no provider
is configured (``DRIFTLAB_LLM_PROVIDER=none``) or the endpoint is unreachable,
every function returns ``None`` and the platform works fully without it — that
invariant is tested.

IMPORTANT:
- Always construct ``ChatOpenAI`` with ``streaming=False``.
- Prefer chat-completions only (``use_responses_api=False`` when the installed
  langchain-openai supports the kwarg) — vLLM does not implement ``/v1/responses``.
"""

from __future__ import annotations

import inspect
from typing import Any, Optional

from .config import get_settings


def is_enabled() -> bool:
    return get_settings().resolved_llm_provider() != "none"


def _apply_use_responses_api(kwargs: dict[str, Any], enabled: bool) -> None:
    """Set use_responses_api only when ChatOpenAI supports the kwarg."""
    try:
        from langchain_openai import ChatOpenAI

        sig = inspect.signature(ChatOpenAI.__init__)
        if "use_responses_api" in sig.parameters:
            kwargs["use_responses_api"] = enabled
    except (TypeError, ValueError, ImportError):
        pass


def _client():
    from langchain_openai import ChatOpenAI

    s = get_settings()
    kwargs: dict[str, Any] = {
        "model": s.resolved_vllm_model(),
        "base_url": s.resolved_vllm_base_url(),
        "api_key": s.resolved_vllm_api_key(),
        "streaming": False,
        "temperature": 0.0,
        "request_timeout": s.resolved_vllm_timeout_s(),
    }
    # vLLM: chat-completions only (no Responses API).
    _apply_use_responses_api(kwargs, False)
    return ChatOpenAI(**kwargs)


def executive_narrative(ledger: dict) -> Optional[str]:
    """Generate a short human narrative for a cycle. Returns None if LLM off."""
    if not is_enabled():
        return None
    try:
        client = _client()
        prompt = (
            "Summarize this agent compliance cycle in 2-3 sentences for a "
            "compliance officer. Facts only, no recommendations beyond noting "
            f"the score and confirmed drifts.\n{ledger}"
        )
        resp = client.invoke(prompt)
        return resp.content
    except Exception:
        # Advisory only — never fail a compliance run on LLM issues.
        return None


def analyst_decomposition(claim: str, rationale: str) -> Optional[str]:
    """Optional DeepAgents-style advisory decomposition of a confirmed drift.

    Advisory only; cannot alter a finding or verdict. Returns None if disabled
    or on any error.
    """
    if not is_enabled():
        return None
    try:
        client = _client()
        resp = client.invoke(
            "As an advisory analyst (read-only), suggest 2 decomposition angles "
            f"to further investigate this confirmed drift. Claim: {claim}. "
            f"Evidence: {rationale}."
        )
        return resp.content
    except Exception:
        return None
