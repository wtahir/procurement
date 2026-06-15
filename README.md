# Procura

Production-style, agentic procurement orchestration demo with a deterministic,
human-in-the-loop workflow and a built-in operations dashboard.

The system simulates how procurement teams intake material requests, source
suppliers across heterogeneous channels, compare bids, pass explicit approval
gates, and execute fulfilment tracking with auditability.

## Why This Project

Most procurement demos stop at a single API call. Procura models the full
workflow with explicit state transitions and practical decision logic:

- Multi-stage orchestration: intake -> sourcing -> decision -> approval -> fulfilment
- Shared typed state model for every stage and actor
- Mocked multi-channel supplier landscape (REST, SOAP, EDI, SFTP, GraphQL, mainframe)
- Deterministic, reproducible execution path for local and hosted demos
- Human approval gate before fulfilment to reflect real governance controls
- Built-in dashboard for request creation, bid analysis, and approval actions

## Architecture Snapshot

```text
Request Intake -> Supplier Sourcing -> Bid Decision -> Human Approval -> Fulfilment
       |                |                  |               |               |
   Feasibility      Candidate list      Winner pick     Approve/Reject    Tracking
   + budget         + RFQ dispatch      + rationale     + audit trail     + status
```

## Requirements

- Python 3.12+
- pip

Dependency management is based on standard requirements files:

- `requirements.txt`: runtime dependencies
- `requirements-dev.txt`: runtime + testing/lint/type-check tooling

## Quick Start (Local)

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
make test
```

Start the API and dashboard:

```bash
. .venv/bin/activate
uvicorn apps.api.main:app --reload
```

- Dashboard: http://localhost:8000/
- API docs: http://localhost:8000/docs
- Health: GET /health/live

## Dashboard (Professional Demo UI)

The built-in UI is designed for stakeholder walkthroughs, not just developer
inspection. It includes:

- Structured request intake form with material, quantity, and region inputs
- Live order list with pipeline status badges
- Bid comparison table with recommended supplier highlighting
- Approval control panel for accept/reject decisions
- Audit timeline showing which agent performed each action

## Render Deployment (Blueprint)

This repository includes a Render Blueprint in `render.yaml` for one web service.

### Deployment Flow

1. Push the repository to GitHub.
2. In Render, click New -> Blueprint.
3. Select this repository.
4. Render applies `render.yaml` and provisions the service.

### Render Build and Start Commands

- Build: `chmod +x render_build.sh && ./render_build.sh`
- Start: `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`

The build script performs:

1. `python -m pip install --upgrade pip`
2. `pip install -r requirements.txt`

### Environment and Health Checks

Configured in `render.yaml`:

- `PYTHON_VERSION=3.12.6`
- `APP_ENV=production`
- `healthCheckPath=/health/live`

### Operational Notes

- Free tier services sleep when idle. First request after inactivity may be slow.
- This demo has no external data stores, so deployment is straightforward.
- No external secrets are required for baseline functionality.

## Development Commands

- Install dependencies: `make install`
- Run tests: `make test`
- Lint: `make lint`
- Auto-fix lint issues: `make format`
- Run API: `make run-api`

## Project Layout (High-Level)

```text
apps/
  api/                 # FastAPI app, routes, dashboard static files
  suppliers/           # Mock supplier backends by channel
packages/
  agents/              # Pipeline orchestration and stage logic
  adapters/            # Supplier adapter interfaces and implementations
  core/                # Shared enums, models, audit structures
  tools/               # Pricing, matching, budget and credit helpers
tests/
  unit/ integration/ e2e/
render.yaml            # Render Blueprint definition
render_build.sh        # Render build script
requirements.txt       # Runtime dependencies
requirements-dev.txt   # Runtime + developer dependencies
```

## CI

GitHub Actions creates a virtual environment, installs from
`requirements-dev.txt`, and executes `pytest`.

