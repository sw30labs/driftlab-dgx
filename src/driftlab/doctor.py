"""Host / .env / seed / vLLM health checks for DriftLab on DGX Spark.

Author: Nic Cravino — driftlab-dgx
"""

from __future__ import annotations

import json
import platform
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_ROOT = Path(__file__).resolve().parent / "seed"

__all__ = ["cmd_doctor", "cmd_test_vllm"]


def _ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def _warn(msg: str) -> None:
    print(f"  ⚠ {msg}")


def _fail(msg: str) -> None:
    print(f"  ✗ {msg}")


def _probe_vllm(base_url: str, api_key: str, timeout: float = 3.0) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {api_key or 'local'}"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _tiny_completion(
    base_url: str, api_key: str, model: str, timeout: float = 60.0
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
            "max_tokens": 16,
            "temperature": 0,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key or 'local'}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "").strip()


def cmd_doctor() -> int:
    """Print host + seed + optional vLLM health. Exit 0 when healthy enough."""
    print("DriftLab doctor")
    print(f"  project: {PROJECT_ROOT}")
    print(f"  python : {sys.version.split()[0]} ({platform.machine()})")
    print(f"  platform: {platform.platform()}")

    errors = 0
    get_settings.cache_clear()
    settings = get_settings()
    provider = settings.resolved_llm_provider()

    pkg = PROJECT_ROOT / "src" / "driftlab"
    if pkg.is_dir():
        _ok("src/driftlab package")
    else:
        _fail("missing src/driftlab")
        errors += 1

    if SEED_ROOT.is_dir() and (SEED_ROOT / "agents.yaml").is_file():
        baselines = list((SEED_ROOT / "baselines").glob("*.json")) if (SEED_ROOT / "baselines").is_dir() else []
        traces = list((SEED_ROOT / "traces").glob("*.jsonl")) if (SEED_ROOT / "traces").is_dir() else []
        _ok(f"seed estate ({len(baselines)} baseline(s), {len(traces)} trace(s))")
    else:
        _fail("seed/ missing or incomplete (agents.yaml required)")
        errors += 1

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        _ok(".env present")
    else:
        _warn(".env missing — copy .env.example (optional; defaults work offline)")

    _ok(f"llm_provider={provider}")
    _ok(f"data_dir={settings.data_dir}")
    if provider != "none":
        _ok(f"vllm_base_url={settings.resolved_vllm_base_url()}")
        _ok(f"vllm_model={settings.resolved_vllm_model()}")

    if shutil.which("nvidia-smi"):
        _ok("nvidia-smi on PATH")
    else:
        _warn("nvidia-smi not on PATH (expected on DGX Spark; fine for offline-only)")

    base = settings.resolved_vllm_base_url()
    key = settings.resolved_vllm_api_key()
    model = settings.resolved_vllm_model()
    try:
        payload = _probe_vllm(base, key)
        models = sorted({m.get("id") for m in payload.get("data", []) if m.get("id")})
        _ok(f"vLLM reachable at {base} ({len(models)} model(s))")
        for mid in models[:8]:
            print(f"      - {mid}")
        if model and models and model not in models and model != "local":
            _warn(f"configured model {model!r} not in catalog")
    except Exception as exc:  # noqa: BLE001
        if provider == "vllm":
            _fail(f"vLLM not reachable at {base}: {exc}")
            errors += 1
        else:
            _warn(
                f"vLLM not reachable at {base} "
                f"(ok when llm_provider=none; start with ~/Desktop/start-vllm.sh)"
            )

    serve = Path.home() / "Desktop" / "serve-local-llm.sh"
    start = Path.home() / "Desktop" / "start-vllm.sh"
    if serve.is_file() or start.is_file():
        _ok("Desktop vLLM helper script(s) present")
    else:
        _warn("~/Desktop/serve-local-llm.sh / start-vllm.sh not found")

    try:
        import driftlab  # noqa: F401

        _ok(f"import driftlab (version {getattr(driftlab, '__version__', '?')})")
    except Exception as exc:  # noqa: BLE001
        _fail(f"cannot import driftlab: {exc}")
        errors += 1

    print()
    if errors:
        print(f"doctor: {errors} error(s)")
        return 1
    print("doctor: ok")
    print("  next: ./driftlab demo")
    print("        ./driftlab dashboard --port 8321")
    if provider == "none":
        print("  optional advisory LLM: set DRIFTLAB_LLM_PROVIDER=vllm and run test-vllm")
    return 0


def cmd_test_vllm(*, skip_invoke: bool = False) -> int:
    """Catalog (+ optional tiny completion) against local vLLM."""
    get_settings.cache_clear()
    settings = get_settings()
    base = settings.resolved_vllm_base_url()
    key = settings.resolved_vllm_api_key()
    model = settings.resolved_vllm_model()
    timeout = settings.resolved_vllm_timeout_s()

    print("DriftLab test-vllm")
    print(f"  base_url: {base}")
    print(f"  model   : {model}")

    try:
        payload = _probe_vllm(base, key)
    except Exception as exc:  # noqa: BLE001
        _fail(f"catalog probe failed: {exc}")
        print("  hint: ~/Desktop/start-vllm.sh nemotron-super")
        return 1

    models = sorted({m.get("id") for m in payload.get("data", []) if m.get("id")})
    _ok(f"catalog ({len(models)} model(s))")
    for mid in models:
        print(f"      - {mid}")

    if not models:
        _fail("empty model catalog")
        return 1

    if model == "local" or (model and model not in models):
        model = models[0]
        _warn(f"using first catalog model: {model}")

    if skip_invoke:
        print("test-vllm: ok (catalog only)")
        return 0

    try:
        text = _tiny_completion(base, key, model, timeout=min(timeout, 120.0))
        _ok(f"completion: {text!r}")
    except Exception as exc:  # noqa: BLE001
        _fail(f"chat completion failed: {exc}")
        return 1

    print("test-vllm: ok")
    return 0
