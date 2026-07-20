# NVIDIA DGX Spark deployment

**DriftLab DGX** targets DGX Spark for continuous, machine-readable compliance
observation of agentic systems. The **compliance path is fully offline**
(deterministic Python — no GPU required). An optional **advisory LLM** uses the
shared Desktop **vLLM** OpenAI-compatible server on loopback port **8000**.

## Architecture

- Application runs in `.venv` with **Python 3.12** (3.11 also supported).
- Default `DRIFTLAB_LLM_PROVIDER=none` — diff, anomaly, score, experiment
  verdicts never call a model.
- When enabled, provider `vllm` uses `langchain-openai.ChatOpenAI` against
  `VLLM_BASE_URL` / `DRIFTLAB_VLLM_BASE_URL` (default `http://127.0.0.1:8000/v1`),
  **chat-completions only** (Responses API disabled — vLLM does not implement
  `/v1/responses`).
- Legacy provider name `omlx` is accepted as an alias for `vllm`.
- Estate dashboard is FastAPI + Jinja on port **8321** (air-gapped; no CDN).
  It does **not** compete with vLLM on **8000**.
- Seed estate (loan-officer + support-triage baselines/traces) ships under
  `src/driftlab/seed/`.

## Sharing vLLM with other Desktop projects

Article Buddy, Book Buddy, DigitalTwin, ScreenLens, Grey Swan, and Ralph all
use the same loopback port. Only one Compose / `serve-local-llm` project can
own **:8000**. DriftLab only needs that port when advisory narratives are on.

```bash
~/Desktop/serve-local-llm.sh status
~/Desktop/serve-local-llm.sh up nemotron-super   # or qwen27 / coder-next
curl -s http://127.0.0.1:8000/v1/models | head
```

Set `DRIFTLAB_VLLM_MODEL` (or `VLLM_MODEL`) to an id returned by the catalog.
Weights and HF caches live under `$HOME/models/huggingface` when using the
shared Desktop helpers.

## Prerequisites

- NVIDIA DGX Spark / GB10 on ARM64 Linux (DGX OS) — GPU only needed if you run
  the shared vLLM server for advisory text
- Python 3.12 with `venv` / `ensurepip`
- Optional: shared vLLM helper `~/Desktop/serve-local-llm.sh` or
  `~/Desktop/start-vllm.sh`
- Outbound HTTPS for package indexes when installing

## One-time setup

```bash
cd ~/Desktop/driftlab-dgx
(umask 077; cp -n .env.example .env)
chmod 600 .env

./driftlab install
./driftlab doctor
```

## Validation

```bash
./driftlab pytest
./driftlab demo

# Optional advisory LLM path:
~/Desktop/start-vllm.sh nemotron-super   # if nothing on :8000
# set DRIFTLAB_LLM_PROVIDER=vllm in .env
./driftlab test-vllm
```

## Running

```bash
./driftlab demo
./driftlab check --agent loan-officer
./driftlab monitor run --force
./driftlab dashboard --port 8321    # http://127.0.0.1:8321
```

Or after `source .venv/bin/activate`:

```bash
driftlab demo
driftlab doctor
```

## Ports on this machine

| Service | Port |
|---|---|
| vLLM inference (shared, optional) | **8000** |
| DriftLab estate dashboard | **8321** |

## Provider env (see `.env.example`)

```bash
DRIFTLAB_LLM_PROVIDER=none
# For advisory narratives:
# DRIFTLAB_LLM_PROVIDER=vllm
DRIFTLAB_VLLM_BASE_URL=http://127.0.0.1:8000/v1
DRIFTLAB_VLLM_MODEL=Qwen/Qwen3.6-27B-FP8
DRIFTLAB_VLLM_API_KEY=test
DRIFTLAB_VLLM_TIMEOUT_S=600
```
