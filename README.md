# Relay CX

Relay CX is a small telecom support app for local demos and internal review work. It gives a customer-facing experience, a support workflow, and a simple way to check account and service cases without needing a heavy setup.

The project is built around a straightforward flow: a person asks about an account, billing, or service issue, the app gathers the relevant details, and the workflow helps review the case and decide the next step.

This repo is meant to be easy to run locally, quick to explore, and simple to understand.

## What is in this project

- Customer and support views for looking at account and service issues
- Review flows for checking case details and next steps
- Synthetic telecom data for local testing and demos
- A small API and frontend stacked together for a complete local app
- Simple project tooling for running the service and validating the repo

## Typical workflow

1. A user signs in as a customer or reviewer.
2. The app loads account, billing, or service context.
3. The flow checks the relevant information and business rules.
4. The case is reviewed, confirmed, or passed along for the next step.
5. The results can be inspected in the app and through the repo checks.

## Demo users

The project includes a few built-in demo accounts for local testing:

- Alex Morgan — `alex.morgan` / `ReviewerPass-1001`
- Jordan Lee — `jordan.lee` / `ReviewerPass-1002`
- Support agent — `support.agent` / `ReviewerPass-3001`

These are synthetic demo credentials intended only for local development.

## Quick start

### Prerequisites

- Python 3.11+
- Bun 1.3.14+
- Internet access for installing dependencies

### Install and run locally

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

Then open:

- Frontend: http://localhost:3000
- API docs: http://127.0.0.1:8080/docs

The development launcher starts the app stack for local use. Press Ctrl+C to stop it.

## Environment configuration

The root `.env` file is ignored by Git and stores local settings. The example file is already included at [.env.example](.env.example).

Common values include:

- `PUBLIC_ORIGIN` — the browser origin used by the app
- `DATABASE_PATH` — local SQLite database path
- `ENTERPRISE_API_BASE_URL` — telecom mock service base URL

## Project structure

```text
apps/
  web/                 Frontend app for the customer and review flows
  api/
    src/relay_api/
      domain/          Core models and business data
      application/     Workflow logic and case handling
      infrastructure/  Data adapters and persistence logic
      http/            API endpoints and transport layer
      evaluation/      Scenario and acceptance checks
      core/            Configuration and app setup
services/mock-telecom/  Synthetic telecom service used for local testing
resources/challenge/    Challenge assets, fixtures, and starter material
tests/                 Acceptance, contract, and integration tests
tools/                 Local dev, validation, and release utilities
deployment/            Docker and deployment assets
docs/                  Architecture and project documentation
evidence/current/      Generated verification output for this build
```

## Validation and checks

Run the checks from the repo root:

```powershell
.venv\Scripts\python.exe -m pytest -q --junitxml=evidence/current/pytest.xml
bun run typecheck
bun run test:web
bun run build
.venv\Scripts\python.exe tools/compliance_audit.py
```

You can also use the repo tools for deeper review and release packaging if needed.

## Docker and local deployment

Start the full stack with Docker:

```bash
docker compose up --build
```

This starts the frontend, API, and synthetic telecom service together. Data is stored in the `cx-data` volume. Use `docker compose down` when you are finished.

For deployment guidance, see [deployment/README.md](deployment/README.md).

## Documentation

The repo includes more detailed project guidance here:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/HANDOVER.md](docs/HANDOVER.md)
- [docs/CHANGES.md](docs/CHANGES.md)
- [docs/FINAL_COMPLIANCE_AUDIT.md](docs/FINAL_COMPLIANCE_AUDIT.md)
- [docs/relay-ui-guide.pdf](docs/relay-ui-guide.pdf)

## Notes

- This project uses synthetic telecom and authentication data for local development and evaluation.
- It is intended for a controlled local challenge environment and is not a full public-facing service.
- Local verification helps check the app behaves as expected in this repo setup.

## Summary

Relay CX is a simple telecom support demo that brings together a web app, API, review flows, and local test data in one project. It is meant to be understandable, easy to run, and useful for local validation and review work.
