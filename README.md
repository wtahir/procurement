# Procura

Procura is a portfolio-grade, AridOS-inspired procurement orchestration system.

It demonstrates a multi-agent procurement workflow with a shared state model,
heterogeneous mocked suppliers, explicit human approval gates, and a strict
"LLM at the intelligence boundary" architecture.

## Current Status

This repository currently includes:

- Phase 0 scaffold: Python project, FastAPI entrypoint, local tooling.
- Phase 1 contracts: core procurement state, RFQ/quote/supplier models, adapter base interfaces.
- A deterministic (LLM-free) demo pipeline that runs the full five-stage flow:
  intake → sourcing → decision → approval gate → fulfilment.
- A built-in dashboard UI served by the API for creating requests, comparing
  supplier bids, and approving or rejecting orders.
- Basic tests for the shared state, audit trail, and the orders API.

## Run Locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
make test
```

## API & Dashboard

```bash
. .venv/bin/activate
uvicorn apps.api.main:app --reload
```

- Dashboard: `http://localhost:8000/`
- Health endpoint: `GET /health/live`
- API docs: `http://localhost:8000/docs`

The demo pipeline is fully deterministic and requires no API keys, so it runs
out of the box locally and on a clean deployment.

## Deploy to Render

The repository ships a [`render.yaml`](render.yaml) Blueprint that provisions a
single Python web service:

1. Push this repo to GitHub.
2. In Render, create a new **Blueprint** and point it at the repo.
3. Render builds with `pip install -e .` and starts
   `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`.
4. Health checks hit `/health/live`; the dashboard is served at `/`.

No database, Redis, or external credentials are required for the demo.

