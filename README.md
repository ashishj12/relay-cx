# Relay CX

Relay CX is a customer-support app for telecom accounts. A customer can check a bill, understand their plan, investigate a connection problem, and approve a support case from the same conversation.

It was built for the **Enterprise AI Customer Experience Resolution System** challenge. Gemini and Google ADK handle the live AI workflow; the backend controls account access, service calls, and actions. The telecom services and customer accounts are supplied test data.

## Demo video

**[Watch the Relay CX demo on Google Drive](https://drive.google.com/file/d/18qgT4OUle0U0e10KPms8YS1P_VFmqvDr/view?usp=drive_link)**

## Start here

- [Run the app with Docker](#run-the-app-with-docker)
- [Sign in and try it](#sign-in-and-try-it)
- [Use real Gemini replies](#use-real-gemini-replies)
- [Run without Docker](#run-without-docker)
- [Configuration](#configuration)
- [Tests and verification](#tests-and-verification)
- [Deployment and current limits](#deployment-and-current-limits)

## Run the app with Docker

Install Docker with Compose and make sure Docker is running. Open a terminal in the project folder, then run:

```bash
docker compose up --build
```

Once the services have started, open **http://127.0.0.1:3000**.

A fresh checkout uses **Reviewer mode**, which works without a Gemini key. If you already have a `.env` file, its settings still apply. Set `APP_MODE=REVIEWER` there if you want to try the app without using Gemini.

Docker starts the website, API, and sample telecom service together. You do not need to install Python or Bun separately for this option.

To stop the app, press `Ctrl+C`, then run:

```bash
docker compose down
```

This keeps the saved data. The `cx-data` volume holds application state; `enterprise-data` holds sample-service identities and case receipts. Removing these volumes removes that data.

## Sign in and try it

Use a supplied account from the sign-in page:

| Account                               | Username        | Password            |
| ------------------------------------- | --------------- | ------------------- |
| Alex Morgan — home internet           | `alex.morgan`   | `ReviewerPass-1001` |
| Jordan Lee — mobile                   | `jordan.lee`    | `ReviewerPass-1002` |
| Support staff — review and operations | `support.agent` | `ReviewerPass-3001` |

These are public test credentials for synthetic accounts.

For a first walkthrough, sign in as Jordan and try:

1. **“What's my data plan and last month's bill?”** Check the plan, billing period, and line items in the answer.
2. **“My internet keeps dropping.”** Answer the follow-up question if Relay asks which service you mean.
3. **“Create a support case for my mobile connection.”** Read the summary before confirming. A completed request should show a case number.
4. **“Show me the bill for ACC-2001.”** Jordan should be refused access to Alex's account.
5. Select **Request human support** to save a handoff reference.

The support account can run the eight challenge scenarios and inspect operational results. Customer accounts cannot access those staff-only functions.

Relay can open a sample support case, but it cannot change a plan, add roaming, or update account preferences. A human-review request saves the conversation for inspection; this demo does not contact live staff or arrange a callback.

## Use real Gemini replies

There are two ways to review the app:

| Mode       | What happens                                                                                                                                                                     | What you need                                         |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| `REVIEWER` | AI interpretation and fact selection are deterministic. The app still calls the local telecom services and applies the same access, validation, confirmation, and tracing rules. | No Gemini key                                         |
| `LIVE_AI`  | Gemini runs through Google ADK to interpret the request, use an authorized tool, and return an answer based on verified records.                                                 | A valid key, an available model, and sufficient quota |

To enable live mode:

1. If you do not already have `.env`, copy `.env.example` to `.env`. Keep any existing file and its settings.
2. Set these values in `.env`:

   ```dotenv
   APP_MODE=LIVE_AI
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=your_available_model_id
   ```

3. Recreate the API container so it receives the new settings:

   ```bash
   docker compose up -d --force-recreate api
   ```

For a local development session, stop the launcher and start it again instead. The workspace should show **Live AI** after sign-in.

Live AI still uses the challenge's synthetic telecom services. Enabling Gemini does not connect the app to a real telecom provider. Factual replies are limited to validated statements from those services.

If a model call fails, Relay explains the failure and saves a review reference. It does not silently replace the reply with a Reviewer answer. An **Assistant unavailable** status is a failed live request, not proof of successful AI execution. Human-review requests remain available without the model.

The separate `DEGRADED` configuration is an explicit offline option. It does not count as live Gemini inference.

## Run without Docker

For local development, install **Python 3.11 or later** and **Bun 1.3.14**. The recorded verification used Python 3.12 and Bun 1.3.14. Internet access is needed to install dependencies.

Run the commands for your operating system from the project folder.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
bun install --frozen-lockfile
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.venv\Scripts\python.exe tools/dev.py
```

### macOS or Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
bun install --frozen-lockfile
[ -f .env ] || cp .env.example .env
.venv/bin/python tools/dev.py
```

Open **http://127.0.0.1:3000**. The launcher starts all three services; `Ctrl+C` stops them.

In Reviewer mode, the local API documentation is at **http://127.0.0.1:8080/docs**. That port is available with this development setup; Docker keeps the API private.

## Configuration

`.env.example` lists the available settings. Copy it once, then edit `.env`. Keep real keys out of version control and screenshots. The API uses the Gemini key; the browser does not receive it. Existing process environment variables take precedence over the local file.

### Settings most people need

| Setting           | Purpose                                                                                            |
| ----------------- | -------------------------------------------------------------------------------------------------- |
| `APP_MODE`        | `REVIEWER` for offline review, `LIVE_AI` for Gemini, or explicitly selected `DEGRADED`.            |
| `GEMINI_API_KEY`  | Server-side key. Required only for live mode.                                                      |
| `GEMINI_MODEL`    | A model available to your key. The example value does not guarantee access.                        |
| `PUBLIC_ORIGIN`   | Browser address, including the port. Local default: `http://127.0.0.1:3000`.                       |
| `COOKIE_SECURE`   | Leave `false` for local HTTP. Use `true` behind HTTPS.                                             |
| `AI_TIMEOUT`      | Timeout per model stage; default and maximum are 40 seconds. This is not a total request deadline. |
| `REQUEST_TIMEOUT` | Timeout for a telecom-service request; default is 2 seconds.                                       |
| `MAX_RETRIES`     | Safe-read retries; default is 1. Case creation is not blindly retried.                             |

### Local service and storage settings

| Setting                                                                     | Purpose                                                                                |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `APP_HOST`, `APP_PORT`                                                      | Local API address and port; defaults are `127.0.0.1` and `8080`.                       |
| `MOCK_HOST`, `MOCK_PORT`                                                    | Local sample-service address and port; defaults are `127.0.0.1` and `8090`.            |
| `ENTERPRISE_API_BASE_URL`                                                   | Address of the sample telecom service. Compose supplies its private container address. |
| `DATABASE_PATH`                                                             | Application database path. Compose stores it in `cx-data`.                             |
| `MOCK_DATABASE_PATH`                                                        | Sample-service database path. Compose stores it in `enterprise-data`.                  |
| `STRUCTURED_LOG_PATH`                                                       | Optional local structured-event log path.                                              |
| `MOCK_ALLOW_FAILURES`                                                       | Allows controlled service failures during review.                                      |
| `MOCK_AUTH_MODE`, `MOCK_BILLING_MODE`, `MOCK_LEGACY_MODE`, `MOCK_CASE_MODE` | Optional failure settings for isolated service tests.                                  |

`GOOGLE_CLOUD_PROJECT`, `GCP_REGION`, `RELAY_API_IMAGE`, and `RELAY_WEB_IMAGE` are for the optional cloud setup. You do not need to fill them in to run locally. Setting them does not create cloud resources or change the Gemini client to Vertex AI.

If sign-in fails, check the sample credentials and use one browser address consistently. `localhost` and `127.0.0.1` have separate cookies. A Gemini **401/403** points to authentication or access; **429** means the provider rejected the request for rate or quota limits. Changing the UI cannot fix provider quota.

## How the project fits together

The frontend sends a customer's message to the API. In live mode, ADK agents interpret it and request the appropriate account, billing, or service check. The backend verifies access, validates service responses, and records the outcome. Creating a case requires a separate customer confirmation and a verified backend receipt.

The stack is **Next.js, TypeScript, and Bun** for the frontend; **FastAPI, Pydantic, Google ADK, and SQLite** for the backend.

```text
apps/web/               Website and customer/staff screens
apps/api/src/relay_api/ API, agents, workflows, adapters, and storage
services/mock-telecom/  Runnable synthetic telecom services
resources/challenge/   Supplied contracts, fixtures, and starter material
tests/                 Acceptance, integration, and contract tests
tools/                 Development, evaluation, and release commands
deployment/            Container and Google Cloud configuration
docs/                  Architecture, security, and handover guides
evidence/current/      Recorded test and workflow results
```

The supplied starter solution is retained for reference. It is not the application entry point.

## Tests and verification

After installing the development dependencies, run:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe tools/evaluate.py --mode REVIEWER
bun run test:web
bun run typecheck
bun run build
```

On macOS/Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

To record genuine Gemini execution, configure live access first, then run:

```powershell
.venv\Scripts\python.exe tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json
```

This makes real provider calls and consumes quota. A provider failure is recorded as a failed live verification.

The recorded clean-release results are **166 backend tests passed**, **8 Reviewer scenarios passed with 160 checks**, and **13 frontend tests passed**. TypeScript and the production build also passed. These are recorded results, not tests rerun by opening this README. The latest recorded live Gemini attempt failed with HTTP 429; successful current live inference remains unverified.

See the [verification summary](evidence/current/verification-summary.json), [requirement evidence matrix](docs/REQUIREMENT_EVIDENCE_MATRIX.md), and [repair report](docs/REMEDIATION.md) for the supporting detail. The checklist is not an independent challenge score.

To produce a source ZIP after your own checks:

```powershell
.venv\Scripts\python.exe tools/package_release.py
```

The ZIP, checksum, and file manifest are written under `release/`. Local environment files, databases, and installed dependencies are excluded.

## Deployment and current limits

The [deployment guide](deployment/README.md) describes the single-VM Google Cloud setup, persistent storage, HTTPS, secrets, backups, and rollback. Optional Cloud Logging and Cloud Trace export is included, but actual cloud delivery and deployment have not been verified.

Run one API process. The current account locks and SQLite setup do not establish safe operation across multiple API replicas. Sign-in and telecom services are synthetic, and no live human-support queue is connected. Connecting real customers requires real identity and enterprise integrations, protected storage and transport, and further operational and security review.

## Further reading

- [Reviewer guide](docs/REVIEWER_GUIDE.md) — customer and staff walkthroughs.
- [Architecture](docs/ARCHITECTURE.md) — components and request flow.
- [Gemini integration](docs/GEMINI_INVOCATIONS.md) — model calls, tools, and reply validation.
- [Gemini CX mapping](docs/GEMINI_CX_MAPPING.md) — how the implementation relates to the challenge architecture.
- [Security](docs/SECURITY.md) — enforced controls and their limits.
- [Handover](docs/HANDOVER.md) — maintenance, diagnosis, and extension.
- [Customer retest](docs/CUSTOMER_RETEST.md) — observed behaviour after the repairs.
