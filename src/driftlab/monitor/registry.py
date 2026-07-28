"""Monitored-agent registry loader (agents.yaml)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AgentSpec:
    id: str
    name: str
    baseline: str
    trace: str
    priority: int = 4
    owner: str = ""
    # Optional recorded resource stream (DL-8 telemetry plane). When absent,
    # the runner falls back to the live sensor path under the data dir.
    resource: str | None = None


def _resolve_against_registry(value: str | None, base: Path) -> str | None:
    """Resolve a registry path relative to the registry file's directory.

    Absolute paths pass through unchanged. This honors the agents.yaml
    contract ("paths resolve relative to this file") regardless of the
    process working directory.
    """
    if value is None:
        return None
    p = Path(value)
    return str(p if p.is_absolute() else (base / p).resolve())


def load_registry(path: str | Path) -> list[AgentSpec]:
    registry_path = Path(path)
    data = yaml.safe_load(registry_path.read_text())
    base = registry_path.resolve().parent
    out = []
    for a in data.get("agents", []):
        out.append(AgentSpec(
            id=a["id"], name=a.get("name", a["id"]),
            baseline=_resolve_against_registry(a["baseline"], base),
            trace=_resolve_against_registry(a["trace"], base),
            priority=int(a.get("priority", 4)), owner=a.get("owner", ""),
            resource=_resolve_against_registry(a.get("resource"), base),
        ))
    return out