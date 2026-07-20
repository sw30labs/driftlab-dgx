# DriftLab DGX

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![DGX](https://img.shields.io/badge/NVIDIA-DGX%20Spark-76B900.svg)](https://www.nvidia.com/en-us/products/workstations/dgx-spark/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

**Author:** Nic Cravino  
**Target host:** NVIDIA DGX Spark (local-first; optional shared vLLM)

**Continuous, machine-readable compliance observer for running agentic systems.**

DriftLab watches a live agent's *actual decision traces* — tool calls, routing
choices, escalations, refusals — and diffs observed behavior against a
**certified OSCAL baseline**. When observed behavior deviates, DriftLab doesn't
just alert: it runs a **micro-experiment** that *proves* or *refutes* the
suspected drift with controlled evidence, then emits OSCAL + human-readable
artifacts suitable for SOC 2 / EU AI Act / ISO 42001 evidence.

It is **local-first, private, deterministic in its compliance path, and works
without any LLM**. On DGX Spark the optional advisory narrative layer targets
the same shared Desktop **vLLM** stack as Article Buddy / Book Buddy / Grey Swan.

---

## Why it exists

Current AI governance is design-time (canvases, policy docs, one-shot audits)
or static (graph diff at build time). Nobody continuously observes *what an
agent actually does at runtime* and proves behavioral drift against a
machine-readable compliance baseline. DriftLab is the missing "control monitor"
layer for the agentic economy.

---

## Design principles (non-negotiable)

1. **Deterministic compliance path.** The diff, anomaly, and scoring engines are
   pure deterministic Python (Pydantic + a small NetworkX path analysis). The LLM
   is *advisory only* — it may write narratives; it never decides a severity or
   verdict.
2. **Local-first / private.** Everything runs on your machine. No agent traces
   leave the host. The LLM (shared Desktop vLLM or any OpenAI-compatible endpoint
   you control) is optional.
3. **Provenance is load-bearing.** Every anomaly traces to source trace events +
   a baseline control. Every experiment verdict cites the probe evidence.
4. **Idempotent by construction.** Re-running a cycle on the same inputs yields
   byte-identical artifacts (content-derived UUIDs / hashing).
5. **Bounded autonomy for the proof engine.** The micro-experiment loop probes
   only a *replay* of the agent's trace held in memory. It never calls the live
   system or any network endpoint. Isolation is enforced and tested.

---

## Quick start (DGX)

```bash
cd ~/Desktop/driftlab-dgx
(umask 077; cp -n .env.example .env)
chmod 600 .env

./driftlab install
source .venv/bin/activate

./driftlab doctor
./driftlab demo
./driftlab check --agent loan-officer
./driftlab dashboard --port 8321    # http://127.0.0.1:8321
```

Expected demo output:

```
DriftLab demo — full estate cycle
  loan-officer: score 0/100       <- 5 drift families detected + proven
  support-triage: score 100/100   <- clean
```

See [QUICKSTART.md](QUICKSTART.md) and [docs/DGX_SPARK.md](docs/DGX_SPARK.md).

### Optional advisory LLM

```bash
~/Desktop/start-vllm.sh nemotron-super   # if nothing on :8000
# set DRIFTLAB_LLM_PROVIDER=vllm in .env and match VLLM_MODEL to catalog
./driftlab test-vllm
```

---

## CLI reference

| Command | Purpose |
|---|---|
| `./driftlab install` | Create `.venv`, install package + extras, run pytest |
| `./driftlab doctor` | Host + seed + optional vLLM health |
| `./driftlab test-vllm` | Catalog + tiny completion against local vLLM |
| `./driftlab agents` | Show the monitored estate + staleness priorities |
| `./driftlab check --agent NAME` | One compliance cycle, now (with experiments) |
| `./driftlab check --agent NAME --no-experiments` | Diff + anomalies only |
| `./driftlab monitor run [--force] [--no-email]` | Staleness-weighted estate cycle |
| `./driftlab monitor status` | Recent runs from the store |
| `./driftlab report <cycle_id>` | Print a cycle's markdown report |
| `./driftlab dashboard [--host --port]` | Estate UI (default **8321**, air-gapped) |
| `./driftlab demo` | Full E2E on the bundled seed estate |
| `./driftlab pytest` | Test suite (no live LLM) |

---

## Architecture

```
Agent runtime (LangGraph/LangChain/any)
   │  emits decision traces (tool calls, routing, escalations, refusals)
   │  + resource telemetry via driftlab.sensor (separate stream; ADR-001)
   ▼
[Trace Ingestor] ──► [Trace Normalizer] ──► canonical DecisionEvent model
[Resource Stream Loader] ──► ResourceRecord replay (DL-8 telemetry plane)
[OSCAL Baseline Loader] ──► [Baseline Compiler] ──► canonical Control model (DL-1..8)
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    [Behavioral Diff] (observed vs baseline)  [Anomaly Engine] (severity, waivers, score)
              │                               │
              ├──────────────► [Compliance Score + Anomaly Ledger]
              │
    [Drift Hypothesis Generator] ──► [Micro-Experiment Loop]
    (suspected drift → probe)         (LangGraph: design→execute→evaluate→reflect)
              │
              ├─► [OSCAL Evidence Emitter]  (assessment-plan / assessment-results)
              ├─► [HTML Dashboard]          (estate + per-agent, port 8321)
              └─► [Monitor / Scheduler]     (staleness-weighted; cron)
```

### Module layout

```
driftlab-dgx/
├── driftlab           thin DGX launcher
├── setup-venv.sh      Python 3.12 venv bootstrap
├── .env.example       DRIFTLAB_* + VLLM_* defaults
├── src/driftlab/
│   ├── domain/        canonical DecisionEvent + BaselinePolicy models
│   ├── identity.py    content-derived, deterministic ids + digests
│   ├── ingest/        normalizer (fail-closed), JSONL replay, LangGraph hook
│   ├── sensor/        resource-budget ledger + meter + telemetry stream (ADR-001)
│   ├── baseline/      OSCAL profile loader + fail-closed compiler (DL-1..8)
│   ├── diff/          behavioral diff engine (7 deterministic control checks)
│   ├── anomaly/       severity resolution, waivers, scoring, DL-5 escalation
│   ├── experiment/    hypothesis generator + sandboxed replay + loop (LangGraph)
│   ├── cycle.py       one full compliance cycle
│   ├── emit/          OSCAL 1.1.2-shaped plan/results + markdown report
│   ├── store/         SQLAlchemy + SQLite (local, idempotent upsert)
│   ├── monitor/       staleness-weighted policy + runner + SMTP notifier
│   ├── dashboard/     FastAPI + inline-CSS Jinja (air-gapped)
│   ├── llm.py         optional vLLM client (streaming=False), advisory-only
│   ├── doctor.py      host / seed / vLLM health
│   ├── cli.py         Typer + Rich CLI
│   └── seed/          baselines, agents.yaml, recorded traces
├── ops/               cron (+ optional macOS launchd) templates
├── tests/             unit, integration, determinism, sandbox-safety, LLM-optional
└── docs/              DGX_SPARK, RUNBOOK, CERTIFICATION-GUIDE, PITCH, ROADMAP
```

---

## The eight behavioral controls (DL-1..8)

| ID | Control | NIST 800-53 | What it checks |
|---|---|---|---|
| DL-1 | Decision Rights | AC-3 / CM-6 | Every tool call is on the node's certified allowlist |
| DL-2 | Routing Integrity | CM-6 | Every transition is on the certified route allowlist |
| DL-3 | Human Oversight | AC-6(1) / PM-12 | Conditions requiring human-in-the-loop actually route there |
| DL-4 | Fallback Protocol | SI-13 / CP-2 | Error/exception events trigger the certified recovery |
| DL-5 | Critical Sink | AC-6 / SC-2 | Findings reaching irreversible actions are escalated to CRITICAL |
| DL-6 | Autonomy Budget | AC-5 / PM-12 | Autonomous disposition rate stays under the certified ceiling |
| DL-7 | Required Steps | CM-6 | Mandatory process steps (e.g. intake→assess) are present |
| DL-8 | Resource Budget | SC-6 / CA-7 | Cumulative resource spend stays under certified ceilings |

All eight are evaluated **deterministically**; none depend on an LLM. DL-8
audits the sensor's recorded telemetry stream (see `docs/ADR-001-RESOURCE-BUDGET.md`).

---

## LLM backends

| Backend | Description | Config |
|---------|-------------|--------|
| **`none`** (default) | Full compliance path offline | `DRIFTLAB_LLM_PROVIDER=none` |
| **`vllm`** (optional) | Shared Desktop OpenAI-compatible server on `:8000` | `DRIFTLAB_VLLM_*` / `VLLM_*` |
| `omlx` | Legacy alias for `vllm` | still accepted |

Local models are served the same way as other Desktop DGX apps:
`~/Desktop/serve-local-llm.sh` or `~/Desktop/start-vllm.sh`.

---

## Testing

```bash
./driftlab pytest
# or
pytest tests/ -q
```

Targets: unit (normalizer fail-closed, baseline fail-closed), integration
(synthetic fixtures), **determinism** (byte-identical ledger on re-run),
**sandbox safety** (experiment loop with sockets booby-trapped), and
**LLM-optional** (full compliance run with no vLLM reachable).

---

## Configuration

Keys use prefix `DRIFTLAB_`. Unprefixed `LLM_PROVIDER` / `VLLM_*` are also
honored for Desktop-wide consistency (see `.env.example`).

| Variable | Default | Purpose |
|---|---|---|
| `DRIFTLAB_DATA_DIR` | `./.driftlab` | SQLite DB + artifacts root |
| `DRIFTLAB_REGISTRY` | bundled `seed/agents.yaml` | monitored agent registry |
| `DRIFTLAB_LLM_PROVIDER` | `none` | `none` disables the LLM entirely |
| `DRIFTLAB_VLLM_BASE_URL` | `http://127.0.0.1:8000/v1` | shared Desktop vLLM |
| `DRIFTLAB_VLLM_MODEL` | `local` | model id from `/v1/models` |
| `DRIFTLAB_VLLM_API_KEY` | `test` | non-empty key for OpenAI client |
| `DRIFTLAB_VLLM_TIMEOUT_S` | `600` | request timeout |
| `DRIFTLAB_EMAIL__ENABLED` | `false` | enable SMTP digest |

---

## Related docs

- [QUICKSTART.md](QUICKSTART.md) — shortest path on DGX
- [docs/DGX_SPARK.md](docs/DGX_SPARK.md) — host deployment notes
- [docs/RUNBOOK.md](docs/RUNBOOK.md) — day-to-day operations
- [docs/CERTIFICATION-GUIDE.md](docs/CERTIFICATION-GUIDE.md) — baseline certification
- [README-WIRING.md](README-WIRING.md) — attach to LangGraph apps
- [NOTES.md](NOTES.md) — deviations from the original build brief

---

## License

Apache-2.0. See `LICENSE`.
