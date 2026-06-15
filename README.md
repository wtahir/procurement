# Procura

Procura is a portfolio-grade, AridOS-inspired procurement orchestration system.

It demonstrates a multi-agent procurement workflow with a shared state model,
heterogeneous mocked suppliers, explicit human approval gates, and a strict
"LLM at the intelligence boundary" architecture.

## Current Status

This repository currently includes:

- Phase 0 scaffold: Python project, FastAPI entrypoint, local tooling.
- Phase 1 contracts: core procurement state, RFQ/quote/supplier models, adapter base interfaces.
- Basic tests for the shared state and audit trail.

## Run Locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
make test
```

## API

```bash
. .venv/bin/activate
uvicorn apps.api.main:app --reload
```

Health endpoint: `GET /health/live`
