# Relay CX

Relay CX is a telecom customer-support workspace for account questions, billing checks, service diagnostics, and confirmed support cases. Google ADK agents use Gemini to understand requests and write replies from authorized enterprise results. Deterministic backend code controls identity, ownership and every consequential action.

This is the challenge's productionized proof of concept. All customer data and enterprise systems are synthetic. It can be reviewed locally without a paid AI account; live mode uses the configured Gemini service.

## What the app does

- Looks up sample account, bill, and service information.
- Uses Gemini to help understand questions when live AI is enabled.
- Requires the customer to confirm before creating a sample support case.
- Saves a record of what happened so it can be reviewed.

## Run it with Docker

This is the quickest way to try the app. Install Docker, open a terminal in
the project folder, and run:

```bash
docker compose up --build
```

When it starts, open **http://127.0.0.1:3000** in your browser.

To stop the app, press `Ctrl+C` in the terminal. You can also run:

```bash
docker compose down
```

## Run it for development

You will need Python 3.11 or newer and Bun 1.3.14 or newer. From the project
folder, run the commands for your computer.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
bun install --frozen-lockfile
Copy-Item .env.example .env
.venv\Scripts\python.exe tools/dev.py
```

### macOS or Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
bun install --frozen-lockfile
cp .env.example .env
.venv/bin/python tools/dev.py
```

Open the website at **http://127.0.0.1:3000**. The API's interactive
documentation is at **http://127.0.0.1:8080/docs**. Press `Ctrl+C` in the
terminal to stop the development app.

## Sign in

Use one of these sample accounts:

| User | Username | Password |
|---|---|---|
| Alex Morgan — home internet | `alex.morgan` | `ReviewerPass-1001` |
| Jordan Lee — mobile | `jordan.lee` | `ReviewerPass-1002` |
| Support staff | `support.agent` | `ReviewerPass-3001` |
| Staff alias (same support role) | `admin` | `admin@123` |

These accounts and passwords are fake and are only for this demo. Never use
them for a real service.

## Choose a mode

- **Reviewer mode** is the default. Only AI interpretation and fact ordering are deterministic. It still calls the real local HTTP services, enforces ownership and confirmation, validates XML, and records actual events. No Gemini key is needed.
- **Live AI mode** uses real Gemini through ADK for routing, tool use and the customer-facing reply. Set `APP_MODE=LIVE_AI`, `GEMINI_API_KEY` and an available `GEMINI_MODEL` in ignored `.env`, then recreate the API container. Provider failures stop the answer and save the request for review; they never substitute a reviewer answer.
- **Degraded status** appears when a live model stage fails. The response explains the failure. An explicitly configured `APP_MODE=DEGRADED` instead selects the documented deterministic offline path. Neither counts as successful live inference.

Keep `.env` on your computer. Do not commit it or share a real API key.

## Run the checks

After installing the development dependencies, run these from the project
folder:

```powershell
.venv\Scripts\python.exe -m pytest -q
bun run typecheck
bun run test:web
bun run build
.venv\Scripts\python.exe tools/evaluate.py --mode REVIEWER
```

These checks test the app and its sample workflows. Passing them does not
prove the app is ready for real customers.

## Where to go next

- [Try the app step by step](docs/REVIEWER_GUIDE.md)
- [Understand how the app works](docs/ARCHITECTURE.md)
- [Learn about its safety limits](docs/SECURITY.md)
- [Run and deploy the project](deployment/README.md)
- [Read about Gemini](docs/GEMINI_INVOCATIONS.md)
- [See the saved check results](docs/FINAL_COMPLIANCE_AUDIT.md)

## Important limits

The app uses fake sign-in, fake company services, and a local SQLite database.
It is designed to run with one backend process. The Google Cloud setup is a
reference only; it has not been deployed. Before using real customer data, the
project needs real company sign-in, protected connections, secure data
handling, monitoring, and more testing.


## Environment settings

Copy `.env.example` to `.env`. Keep the key on the API server; the browser never receives it. Existing process environment variables take precedence over `.env`.

| Setting | Purpose / default |
|---|---|
| `APP_MODE` | `REVIEWER`, `LIVE_AI`, or explicitly configured `DEGRADED` |
| `GEMINI_MODEL`, `GEMINI_API_KEY` | Model identifier and server-only key; live mode requires both and available quota |
| `AI_TIMEOUT` | Seconds per ADK stage, capped at 40; `15` is a shorter local option, not a whole-request deadline |
| `REQUEST_TIMEOUT`, `MAX_RETRIES` | Enterprise timeout (2 seconds) and safe-read retries (1; capped at 2) |
| `PUBLIC_ORIGIN` | Exact browser origin; local default `http://127.0.0.1:3000`; localhost aliases are supported |
| `COOKIE_SECURE` | `false` for local HTTP; `true` for HTTPS |
| `APP_HOST`, `APP_PORT` | Local API bind address and port, `127.0.0.1:8080` |
| `MOCK_HOST`, `MOCK_PORT` | Synthetic service bind address and port, `127.0.0.1:8090` |
| `ENTERPRISE_API_BASE_URL` | Local service URL; Compose sets the private service address |
| `DATABASE_PATH`, `STRUCTURED_LOG_PATH` | Local SQLite and JSON-lines log paths; Compose stores API state in its volume |
| `MOCK_ALLOW_FAILURES` | Enables reviewer failure injection; the live gateway never sends reviewer overrides |
| `MOCK_AUTH_MODE`, `MOCK_BILLING_MODE`, `MOCK_LEGACY_MODE`, `MOCK_CASE_MODE` | Optional dependency failure controls for isolated testing; see the supplied failure configuration |
| `GOOGLE_CLOUD_PROJECT` | Optional deployment identifier; it does not deploy resources or switch the model client to Vertex AI |
| `RELAY_API_IMAGE`, `RELAY_WEB_IMAGE` | Immutable image references used by the Google Cloud Compose overlay |

`APP_MODE=LIVE_AI` and `GEMINI_MODEL=gemini-3.6-flash` are examples, not a guarantee of access. A 429 response means the provider rejected that request for quota/rate limits. Authentication failures and 429 responses are not retried in the same turn. Other selected transient provider errors have bounded retries within the stage deadline.

## Reviewing a release

Run `python tools/evaluate.py --mode REVIEWER` for all eight mandatory scenarios. To collect genuine Gemini evidence, run `python tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json`. For low request quotas, `LIVE_EVALUATION_PAUSE=60` paces evaluation turns; this does not affect normal app response times or turn a failed result into a pass.

The source, scenario checks, evidence and limitations are linked in [the requirement matrix](docs/REQUIREMENT_EVIDENCE_MATRIX.md) and [client review](docs/CLIENT_REVIEW.md). [The handover guide](docs/HANDOVER.md) explains extension and diagnosis. [Deployment instructions](deployment/README.md) cover the single-VM reference, health checks, backups, TLS, secrets, cost and rollback. A cloud deployment has not been performed. The demo video remains excluded from this work.

## Customer and safety repairs

Human-review requests work independently of Gemini and return a saved reference. The demo does not assign live staff or promise callbacks. Sign-in can expire, but a fresh sign-in restores your conversation and unfinished case. Cases and duplicate protection are backed by durable account-level records; an uncertain write is checked against the existing enterprise receipt before any further action.

Live factual replies are intentionally extractive: Gemini chooses from verified account statements rather than freely inventing prose. Strict-live failures never substitute Reviewer responses. Account and bill questions can include both the current plan and the actual available billing period. Plan changes, roaming additions and travel bookings are explicitly unsupported.

See [the repair report](docs/REMEDIATION.md), [the original customer walkthrough](docs/RAHUL_CUSTOMER_REVIEW.md), [the customer retest](docs/CUSTOMER_RETEST.md) and [optional cloud setup](deployment/README.md). Cloud settings can stay blank until you have credits; they do not affect local Reviewer startup.
