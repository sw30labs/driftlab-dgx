# Quickstart (DGX Spark)

```bash
cd ~/Desktop/driftlab-dgx
./driftlab install
source .venv/bin/activate
```

## First run (fully offline)

```bash
./driftlab doctor
./driftlab demo
./driftlab check --agent loan-officer
./driftlab dashboard --port 8321
```

Expected demo:

```
loan-officer: score low     <- drifts detected + proven
support-triage: score 100/100
```

## Optional advisory LLM (shared Desktop vLLM)

```bash
~/Desktop/start-vllm.sh nemotron-super   # or serve-local-llm.sh up nemotron-super
# Edit .env: DRIFTLAB_LLM_PROVIDER=vllm  and match VLLM_MODEL to catalog
./driftlab test-vllm
./driftlab check --agent loan-officer
```

## Useful commands

| What | Command |
|---|---|
| Activate venv | `source .venv/bin/activate` |
| Install / update | `./driftlab install` |
| Host + seed health | `./driftlab doctor` |
| Smoke-test vLLM | `./driftlab test-vllm` |
| Catalog only | `./driftlab test-vllm --skip-invoke` |
| Full seed demo | `./driftlab demo` |
| One agent cycle | `./driftlab check --agent loan-officer` |
| Estate monitor | `./driftlab monitor run --force` |
| Dashboard | `./driftlab dashboard --port 8321` |
| Tests | `./driftlab pytest` |

## Ports on this machine

| Service | Port |
|---|---|
| vLLM inference (optional) | **8000** |
| DriftLab dashboard | **8321** |

## Provider env (see `.env.example`)

```bash
DRIFTLAB_LLM_PROVIDER=none
DRIFTLAB_VLLM_BASE_URL=http://127.0.0.1:8000/v1
DRIFTLAB_VLLM_MODEL=Qwen/Qwen3.6-27B-FP8
DRIFTLAB_VLLM_API_KEY=test
DRIFTLAB_VLLM_TIMEOUT_S=600
```
