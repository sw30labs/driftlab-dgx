"""Configuration via environment / .env (prefix DRIFTLAB_).

The LLM path is optional. When ``llm_provider`` is ``none`` every compliance
feature works without any inference server reachable — this invariant is
enforced by the test suite.

On NVIDIA DGX Spark the advisory LLM defaults to the shared Desktop **vLLM**
OpenAI-compatible server on loopback port **8000** (same stack as Article Buddy,
Book Buddy, Grey Swan, ScreenLens). Provider values:

- ``none`` — no LLM (default; full deterministic compliance path)
- ``vllm`` — shared Desktop vLLM on :8000
- ``omlx`` — legacy alias for ``vllm`` (Mac-era name; still accepted)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Unprefixed Desktop conventions (shared with other *-dgx projects).
_VLLM_BASE_DEFAULT = "http://127.0.0.1:8000/v1"
_VLLM_KEY_DEFAULT = "test"
_VLLM_MODEL_DEFAULT = "local"
_VLLM_TIMEOUT_DEFAULT = 600.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DRIFTLAB_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    data_dir: Path = Path("./.driftlab")
    registry_path: Path | None = None

    # "none" | "vllm" | "omlx" (omlx → vllm). Override with DRIFTLAB_LLM_PROVIDER
    # or unprefixed LLM_PROVIDER when set.
    llm_provider: str = "none"
    vllm_base_url: str = _VLLM_BASE_DEFAULT
    vllm_api_key: str = _VLLM_KEY_DEFAULT
    vllm_model: str = _VLLM_MODEL_DEFAULT
    vllm_timeout_s: float = _VLLM_TIMEOUT_DEFAULT

    # Legacy OMLX field names (still read from DRIFTLAB_OMLX_* for old .env files).
    omlx_base_url: str | None = None
    omlx_api_key: str | None = None

    email__enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_to: str = ""
    email_from: str = ""

    @property
    def artifacts_dir(self) -> Path:
        return self.data_dir / "artifacts"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "driftlab.db"

    def resolved_llm_provider(self) -> str:
        """Normalize provider: none | vllm. Accepts omlx as vllm alias."""
        raw = (
            os.environ.get("LLM_PROVIDER")
            or os.environ.get("DRIFTLAB_LLM_PROVIDER")
            or self.llm_provider
            or "none"
        ).strip().lower()
        if raw in ("", "none", "off", "disabled", "false", "0"):
            return "none"
        if raw in ("omlx", "openai", "local"):
            return "vllm"
        if raw == "vllm":
            return "vllm"
        return raw

    def resolved_vllm_base_url(self) -> str:
        return (
            os.environ.get("VLLM_BASE_URL")
            or os.environ.get("DRIFTLAB_VLLM_BASE_URL")
            or self.omlx_base_url
            or self.vllm_base_url
            or _VLLM_BASE_DEFAULT
        ).rstrip("/")

    def resolved_vllm_api_key(self) -> str:
        return (
            os.environ.get("VLLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("DRIFTLAB_VLLM_API_KEY")
            or self.omlx_api_key
            or self.vllm_api_key
            or _VLLM_KEY_DEFAULT
        )

    def resolved_vllm_model(self) -> str:
        return (
            os.environ.get("VLLM_MODEL")
            or os.environ.get("LLM_MODEL")
            or os.environ.get("DRIFTLAB_VLLM_MODEL")
            or self.vllm_model
            or _VLLM_MODEL_DEFAULT
        )

    def resolved_vllm_timeout_s(self) -> float:
        raw = (
            os.environ.get("VLLM_TIMEOUT_S")
            or os.environ.get("DRIFTLAB_VLLM_TIMEOUT_S")
        )
        if raw:
            try:
                return float(raw)
            except ValueError:
                pass
        return float(self.vllm_timeout_s or _VLLM_TIMEOUT_DEFAULT)

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
