# AGENTS.md — DriftLab DGX

Guidance for coding agents working in this repository.

## Product

Continuous compliance observer for agentic systems on **NVIDIA DGX Spark**.

- **Primary UX:** Typer CLI + thin `./driftlab` launcher
- **Dashboard:** FastAPI estate UI on port **8321** (air-gapped)
- **Default inference:** **none** — compliance path is pure deterministic Python
- **Optional advisory LLM:** shared Desktop vLLM on `127.0.0.1:8000`

## Commands

```bash
./driftlab install
./driftlab doctor
./driftlab demo
./driftlab check --agent loan-officer
./driftlab dashboard --port 8321
pytest tests/ -q
```

## Layout

| Path | Role |
|------|------|
| `driftlab` | Thin launcher (`install` / `doctor` / `demo` / …) |
| `src/driftlab/cli.py` | Typer multi-command entry |
| `src/driftlab/doctor.py` | Host / seed / vLLM health |
| `src/driftlab/llm.py` | Optional advisory client (**vllm**; `omlx` alias) |
| `src/driftlab/config.py` | `DRIFTLAB_*` + unprefixed `VLLM_*` resolution |
| `src/driftlab/seed/` | Bundled baselines + traces |
| `docs/DGX_SPARK.md` | Host deployment |
| `docs/RUNBOOK.md` | Operator runbook |

## Rules

- The compliance path (diff / anomaly / score / experiment verdict) must stay
  **LLM-free and deterministic**. Never let the model set severity or verdict.
- vLLM must use chat-completions only (`use_responses_api=False` when supported).
- Share port **8000** with other Desktop DGX projects; never hard-kill foreign
  containers. Dashboard stays on **8321**.
- Tests must not call live LLMs.
- Prefer Linux paths under `~/Desktop/driftlab-dgx` (not `/Users/spider/...`).
