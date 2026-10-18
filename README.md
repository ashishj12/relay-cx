# Relay CX

Relay CX is a telecom support and operations workspace for customer service teams. It combines a customer-facing experience, AI-assisted decision support, and reviewer/operations tooling in one application.

The system is built around a simple premise: a customer asks about an account, billing, or service issue; the application verifies the facts, checks the right policies and system data, and can route the issue to a human reviewer or operations workflow when needed.

This repo is structured to be easy to run locally, verify with tests, and package for deployment.

## What the product does

- Helps a customer work through account and service questions
- Validates enterprise and telecom facts before acting on them
- Uses AI for reasoning in live mode while preserving deterministic behavior in reviewer mode
- Supports human review, approvals, and operational handoff
- Exposes protected reviewer and support workflows separate from customer access
- Provides synthetic telecom scenarios and evidence for local validation

## Stack

- Frontend: Next.js + TypeScript + Bun
- API: FastAPI + Pydantic + Uvicorn
- AI orchestration: Google ADK + Gemini
- Data: SQLite + synthetic telecom APIs
- Containerization: Docker Compose

## Typical workflow

1. A user signs in as a customer or support reviewer.
2. The app loads account, billing, or service context.
3. Business rules and enterprise facts are validated.
4. AI can provide guided reasoning when `APP_MODE=LIVE_AI` is enabled.
5. The system records actions, confirmation steps, and handoff details.
6. Reviewers and operations teams can inspect the outcomes in protected screens.

## Demo users

The project includes synthetic demo accounts for local testing:

- Alex Morgan — `alex.morgan` / `ReviewerPass-1001`
- Jordan Lee — `jordan.lee` / `ReviewerPass-1002`
- Support agent — `support.agent` / `ReviewerPass-3001`

These are public synthetic challenge credentials for local development only.

## Quick start

### Prerequisites

- Python 3.11+
- Bun 1.3.14+
- Internet access for dependency installation and AI verification

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

The dev launcher starts the app stack for local development. Press Ctrl+C to stop it.

## Environment configuration

The root `.env` file is ignored by Git and stores local environment values. The example file is already included at [.env.example](.env.example).

Key settings include:

- `APP_MODE` — `REVIEWER` or `LIVE_AI`
- `GEMINI_API_KEY` — required only when using live AI mode
- `GEMINI_MODEL` — the model to use for AI calls
- `PUBLIC_ORIGIN` — the public origin used by the app
- `DATABASE_PATH` — local SQLite database path
- `ENTERPRISE_API_BASE_URL` — telecom mock service base URL

For live AI usage, configure the following in `.env`:

```env
APP_MODE=LIVE_AI
GEMINI_MODEL=gemini-3.5-flash
GEMINI_API_KEY=your-key-here
```

When AI is unavailable, the app falls back to deterministic logic and verified enterprise facts rather than silently guessing.

## Project structure

```text
apps/
  web/                 Frontend app for customer, support, review, and operations flows
  api/
    src/relay_api/
      domain/          Domain models and validated business data
      application/     Workflow orchestration, confirmations, and handoff logic
      agents/          ADK router and session-scoped specialist tools
      ai/              AI provider integration and result validation
      infrastructure/  Enterprise data adapters and persistence logic
      http/            FastAPI endpoints and transport layer
      evaluation/      Scenario and acceptance checks
      core/            Configuration and app initialization
services/mock-telecom/  Synthetic telecom service used for local testing
resources/challenge/    Challenge source material, fixtures, and preserved starter assets
tests/                 Acceptance, contract, and integration tests
tools/                 Dev, evaluation, auditing, and release utilities
deployment/            Docker and cloud deployment assets
docs/                  Architecture, security, handoff, and compliance docs
evidence/current/      Generated verification output for this build
```

## Verification and quality checks

Run the project validation commands from the repo root:

```powershell
.venv\Scripts\python.exe -m pytest -q --junitxml=evidence/current/pytest.xml
.venv\Scripts\python.exe tools/evaluate.py --mode REVIEWER
.venv\Scripts\python.exe tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json
bun run typecheck
bun run test:web
bun run build
.venv\Scripts\python.exe tools/compliance_audit.py
.venv\Scripts\python.exe tools/package_release.py
```

Important notes:

- Live verification performs real provider calls and may fail due to quota or connectivity limits.
- Reviewer mode and non-AI checks work without a Gemini key.
- Release packaging writes a source ZIP and SHA-256 hash to `release/`.
- The packager scans for unexpected runtime or binary files and produces a manifest for auditability.

## Docker and deployment

Start the full stack with Docker:

```bash
docker compose up --build
```

This starts the frontend, API, and synthetic telecom service using the configured environment values. Data is persisted in the `cx-data` volume. Use `docker compose down` when finished; this preserves data unless you explicitly remove the volume.

For deployment guidance, see [deployment/README.md](deployment/README.md).

## Documentation

The repo includes more detailed project guidance here:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/HANDOVER.md](docs/HANDOVER.md)
- [docs/CHANGES.md](docs/CHANGES.md)
- [docs/FINAL_COMPLIANCE_AUDIT.md](docs/FINAL_COMPLIANCE_AUDIT.md)
- [docs/GEMINI_INVOCATIONS.md](docs/GEMINI_INVOCATIONS.md)
- [docs/relay-ui-guide.pdf](docs/relay-ui-guide.pdf)

## Important guardrails

- This project uses synthetic telecom and authentication data for local development and evaluation.
- The app is intended for a controlled challenge environment and not presented as a production-certified CSP platform.
- GCP deployment and formal production qualification are outside the scope of what this repo claims.
- Passing local verification does not guarantee the original challenge rubric threshold or production readiness certification.

## Summary

Relay CX is a production-style sample application for telecom service resolution with AI-assisted reasoning, auditable workflows, and reviewer operations. It is designed to be understandable, verifiable, and easy to run locally while still reflecting a realistic enterprise workflow.
