# Relay CX

Relay CX is a controlled telecom customer-resolution demo built around a FastAPI backend, a Next.js frontend, and synthetic enterprise integrations. The app models a support workflow where a customer can sign in, ask about billing or service issues, and have a governed AI-assisted resolution flow review account, service, and case data before an action is confirmed.

This repository is designed for local development, evaluation, and challenge-based review. It is intentionally bounded: synthetic authentication, mock enterprise services, and local SQLite storage are used instead of full production infrastructure.

## What this project includes

- Customer workflow for account and service review
- Support/reviewer access with scoped operational views
- AI-assisted resolution flow using Google ADK and Gemini
- Mock telecom enterprise adapters for billing, account, and service data
- Structured events, traces, and scenario-based verification
- Docker Compose + local runner for quick setup

## Core architecture

The repo is split into a few clear components:

- apps/web: Next.js customer/support UI
- apps/api: FastAPI service and workflow orchestration layer
- services/mock-telecom: synthetic telecom backend used by the app
- resources/challenge: challenge artifacts, scenario fixtures, and evaluation inputs
- tests: acceptance, contract, integration, and security checks
- tools: local dev and validation scripts
- docs: architecture, security, and Gemini mapping references

## Typical workflow

1. A customer or support user signs in.
2. The backend validates the session and account context.
3. The AI workflow reads only session-bound, authorized data.
4. The app proposes an action or next step.
5. A confirmation endpoint enforces an explicit approval step before a case write is executed.
6. Events and traces are stored for review and scenario validation.

## Demo users

The project includes synthetic demo accounts for local testing:

- Alex Morgan — `alex.morgan` / `ReviewerPass-1001`
- Jordan Lee — `jordan.lee` / `ReviewerPass-1002`
- Support agent — `support.agent` / `ReviewerPass-3001`

These credentials are intentionally fake and meant only for local challenge/demo usage.

## Prerequisites

- Python 3.11+
- Bun 1.3.14+
- Internet access for dependency installation
- Docker (optional, for Compose-based local stack)

## Local development quick start

From the repository root:

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
bun install --frozen-lockfile
Copy-Item .env.example .env
.venv\Scripts\python.exe tools/dev.py
```

macOS/Linux:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
bun install --frozen-lockfile
cp .env.example .env
.venv/bin/python tools/dev.py
```

The launcher starts the API and mock telecom services together with the web app. After startup, open:

- Web app: http://127.0.0.1:3000
- API docs: http://127.0.0.1:8080/docs

Press Ctrl+C in the launcher terminal to stop the stack.

## Environment configuration

The repository includes a local example file at [.env.example](.env.example). Copy it to `.env` for local settings. The file is intentionally excluded from source control.

Common variables include:

- `APP_MODE` — request mode, typically `REVIEWER`
- `PUBLIC_ORIGIN` — browser origin for the frontend
- `DATABASE_PATH` — path to the local SQLite database
- `ENTERPRISE_API_BASE_URL` — mock enterprise service URL
- `GEMINI_API_KEY` — API key for Gemini-backed workflow calls
- `COOKIE_SECURE` — set to `true` when serving behind HTTPS

## Docker Compose

To start the full stack with Docker:

```bash
docker compose up --build
```

This runs the frontend, the API, and the synthetic telecom service together. The app data is stored in the `cx-data` Docker volume. To stop the stack:

```bash
docker compose down
```

For operational guidance, see [deployment/README.md](deployment/README.md).

## Repository layout

```text
apps/
  api/                 FastAPI backend and workflow orchestration
    src/relay_api/     API application, domain logic, adapters, and agents
  web/                 Next.js frontend for customer and support flows
services/
  mock-telecom/        Synthetic telecom service used by the app
resources/
  challenge/           Scenario fixtures, supplied contracts, and challenge assets
tests/                Acceptance, contract, integration, and security tests
tools/                Local dev, validation, and release scripts
docs/                 Architecture and security documentation
deployment/          Docker and reference deployment guidance
evidence/current/    Generated verification and test artifacts
```

## Validation

Run the project checks from the repo root:

```powershell
.venv\Scripts\python.exe -m pytest -q --junitxml=evidence/current/pytest.xml
bun run typecheck
bun run test:web
bun run build
.venv\Scripts\python.exe tools/evaluate.py --mode REVIEWER
.venv\Scripts\python.exe tools/compliance_audit.py
```

These checks cover API behavior, frontend type safety, and repo-level verification. The repo also contains scenario and integration tests for security and workflow correctness.

## Documentation

This repository includes the main project references:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/GEMINI_CX_MAPPING.md](docs/GEMINI_CX_MAPPING.md)
- [docs/GEMINI_INVOCATIONS.md](docs/GEMINI_INVOCATIONS.md)
- [deployment/README.md](deployment/README.md)

## Important caveat

This project is a controlled challenge/demo environment, not a production public-facing telecom platform. It intentionally keeps trust boundaries narrow, uses synthetic credentials and mock enterprise fixtures, and requires additional production hardening before real-world deployment.

## Summary

Relay CX is a local, reviewable customer-resolution platform that combines a Next.js frontend, Google ADK/Gemini-backed workflow logic, and controlled enterprise adapters to model a realistic but safe telecom support scenario.

## Review and evidence

Start with [the independent reviewer guide](docs/REVIEWER_GUIDE.md), [requirement matrix](docs/REQUIREMENT_EVIDENCE_MATRIX.md), [handover](docs/HANDOVER.md) and [changes](docs/CHANGES.md). The original requirements are preserved under `docs/challenge/ORIGINAL_CHALLENGE.md`; supplied fixtures/contracts remain under `resources/challenge`.

`REVIEWER` replaces only AI interpretation and fact ordering; enterprise calls, authorization, confirmation and telemetry remain real. `LIVE_AI` uses native Google ADK and the configured Gemini model. `DEGRADED` is explicit deterministic fallback. The UI and workflow response identify the current mode. Only the API receives the ignored local key; active credentials must never be submitted.

After configuring `GEMINI_API_KEY` and `GEMINI_MODEL` locally, collect fresh live evidence:

```bash
python tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json
```

For low provider quotas set `LIVE_EVALUATION_PAUSE=65` in the shell. Fallback is not live success. Cloud resources have not been provisioned. The video remains excluded by the user's earlier instruction and is an outstanding challenge deliverable. Scores belong to the independent evaluator; no acceptance guarantee is claimed.

Release workflow: run all checks, `python tools/package_release.py`, `python tools/verify_clean_release.py`, then `python tools/compliance_audit.py` and package again. To verify Docker, start `docker compose -p relay-release up --build --wait` and run `python tools/verify_containers.py`. This checks both loopback names, role isolation and all eight scenarios. The source archive has a per-file SHA-256 manifest and excludes runtime state.

The release was live-verified with `gemini-3.8-flash` through native Google ADK; see `evidence/current/live-gemini-evidence.json`. Earlier quota/unavailable-model attempts remain separate evidence. Current local/runtime checks and exact source freshness are summarized in `evidence/current/verification-summary.json`.
