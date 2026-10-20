# Relay CX

A bill that looks wrong. A connection that keeps dropping. A support request that needs someone to check the account before taking action.

Relay brings these tasks into one customer-support conversation. It checks the signed-in customer's records, explains what it finds, and asks for approval before opening a support case.

Built for Topcoder's **Enterprise AI Customer Experience Resolution System** challenge, Relay uses Gemini and Google ADK for live AI. The customer accounts and telecom services are synthetic so the project can be tried locally.

## Watch the demo

[**Play the demo video on Google Drive →**](https://drive.google.com/file/d/18qgT4OUle0U0e10KPms8YS1P_VFmqvDr/view?usp=drive_link)

## Start in mock mode

For a first review, use **mock mode**. Its actual configuration name is `REVIEWER`; `APP_MODE=MOCK` is not a supported value. This mode needs no Gemini key or GCP credits. It replaces the AI steps with fixed rules while still running the local service calls, access checks, case actions, and traces.

**1. Prepare the environment file.** Extract the submission and open a terminal in the folder containing `compose.yaml`. Create `.env` from the example if it does not exist.

Windows PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

macOS/Linux:

```bash
[ -f .env ] || cp .env.example .env
```

**2. Set mock mode.** Open `.env` and check these values. Existing Gemini credentials can stay in the file; Reviewer mode does not use them.

```dotenv
APP_MODE=REVIEWER
PUBLIC_ORIGIN=http://127.0.0.1:3000
COOKIE_SECURE=false
```

**3. Start the app.** Start Docker Desktop, then run:

```bash
docker compose --env-file .env up --build -d
docker compose ps
```

Wait for the API and enterprise services to report healthy, then open **http://127.0.0.1:3000**. After sign-in, the workspace should show **Reviewer mode**. If startup fails, check `docker compose logs --tail=80 api web enterprise`.

Docker runs the website, API, and sample telecom service together. Python and Bun are only needed if you use the development setup below.

To stop the app, run `docker compose down`. Saved data stays in the Docker volumes unless you remove them. Use the same browser address throughout the review; `localhost` and `127.0.0.1` have separate sign-in cookies.

## Take a quick look around

Sign in with one of these public demo accounts:

| Account              | Username        | Password            |
| -------------------- | --------------- | ------------------- |
| Alex — home internet | `alex.morgan`   | `ReviewerPass-1001` |
| Jordan — mobile      | `jordan.lee`    | `ReviewerPass-1002` |
| Support staff        | `support.agent` | `ReviewerPass-3001` |

Start with Jordan's account and follow this short walkthrough:

| Try this                                          | What to check                                                                                                               |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| “What's my data plan and last month's bill?”      | The answer identifies Jordan's plan and the available bill period. Use **View sources & execution** to inspect the records. |
| “My internet keeps dropping.”                     | If Relay asks which service you mean, answer “mobile”. It should check that service.                                        |
| “Create a support case for my mobile connection.” | A summary appears before creation. Confirm it and check that a case number is returned.                                     |
| “Show me the bill for ACC-2001.”                  | Access is denied because this is Alex's account.                                                                            |
| Select **Request human support**.                 | A saved review reference appears, with an explanation of what happens next.                                                 |

The human-review button does not contact live staff or schedule a callback. Plan changes, roaming additions, and account-preference changes are outside this demo's scope.

### Run the eight challenge scenarios

1. Stay in Reviewer mode, sign out, and sign in as `support.agent`.
2. Open **Evaluation** and select **Run all eight scenarios**.
3. Check the results for all eight scenarios. Expand each result to inspect the checks, responses, and execution trace.
4. Open **Operations** to inspect recorded requests, handoffs, and metrics.

The suite covers plan inquiries, clarification, billing, confirmed actions, unauthorized access, legacy XML, service failure, and provider failure. Scenario execution requires the support account and Reviewer mode. Passing this suite does not establish successful live Gemini inference.

## Switch to live AI

Reviewer mode uses fixed rules for the AI steps while still calling the local telecom services. **Live AI mode** uses real Gemini calls through Google ADK.

If `.env` does not exist, copy [`.env.example`](.env.example) to `.env`. Keep an existing file rather than replacing it. Set:

```dotenv
APP_MODE=LIVE_AI
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=your_available_model_id
```

After the mock-mode walkthrough, update those three values in the same `.env` file. Keep the local `PUBLIC_ORIGIN` and `COOKIE_SECURE` settings above, then recreate the API:

```bash
docker compose --env-file .env up -d --force-recreate api
```

Sign out, refresh the page, and sign in as a customer again. The workspace should show **Live AI**. Ask a plan or billing question and inspect **View sources & execution**. A Live AI badge alone is not proof that a model request succeeded.

For development without Docker, stop and restart the launcher instead. To return to mock mode, set `APP_MODE=REVIEWER`, run the same API recreation command, and sign in again.

Your key needs access to the selected model and available quota. Keep it in `.env`, out of commits and screenshots. A failed live call is reported as a failure; a Reviewer response is not substituted. Live AI still uses the supplied telecom data, not a real carrier's systems.

A provider **401/403** indicates a credentials or access issue; **429** indicates a rate or quota limit. Resolve that provider issue before treating the live review as passed. The separate `DEGRADED` mode is an explicit offline option and does not count as live AI.

## Work on the code

The frontend uses **Next.js, TypeScript, and Bun**. The backend uses **FastAPI, Pydantic, Google ADK, and SQLite**.

```text
apps/web/               Website and customer/staff screens
apps/api/src/relay_api/ API, agents, workflows, and adapters
services/mock-telecom/  Sample telecom services
resources/challenge/   Supplied contracts and test data
tests/                 Automated checks
tools/                 Development and evaluation commands
deployment/            Containers and cloud setup
docs/                  Technical guides
evidence/current/      Saved verification results
```

<details>
<summary><strong>Local setup without Docker</strong></summary>

Install Python 3.12 and Bun 1.3.14, then run the commands for your system from the project folder. These commands preserve an existing `.env` file.

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
bun install --frozen-lockfile
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.venv\Scripts\python.exe tools/dev.py
```

**macOS or Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
bun install --frozen-lockfile
[ -f .env ] || cp .env.example .env
.venv/bin/python tools/dev.py
```

Open **http://127.0.0.1:3000**. The launcher starts all three services; `Ctrl+C` stops them. In Reviewer mode, API documentation is available at **http://127.0.0.1:8080/docs**. Docker keeps that API port private.

</details>

The remaining settings are in [`.env.example`](.env.example). For local HTTP, keep `COOKIE_SECURE=false`. For a deployed HTTPS address, set `PUBLIC_ORIGIN` to that address and use `COOKIE_SECURE=true`. Cloud settings can stay blank for local use.

## Check your changes

After installing the development dependencies, run:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe tools/evaluate.py --mode REVIEWER
bun run test:web
bun run typecheck
bun run build
```

On macOS/Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

To check real Gemini execution, configure live access first, then run:

```powershell
.venv\Scripts\python.exe tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json
```

This uses provider quota and saves a new live result to `evidence/current/live-gemini-evidence.json`. Reviewer evaluation saves its results to `evidence/current/http-scenarios.json`. Check the command's exit status and recorded result; do not count a provider error as a pass.

For submission review, compare the [saved verification summary](evidence/current/verification-summary.json) with the [requirement evidence matrix](docs/REQUIREMENT_EVIDENCE_MATRIX.md), then rerun the checks you need. Saved reports describe previous executions. The recorded live verification was blocked by HTTP 429, so successful live inference remains unverified.

## Deploying beyond your machine

The [deployment guide](deployment/README.md) covers the Google Cloud reference setup, secrets, HTTPS, storage, and backups. Cloud deployment has not been verified.

Run one API process with the current SQLite design. Real customer use would also need real identity and telecom integrations, a connected support team, and further security and operational testing.

For the implementation details, see the [architecture](docs/ARCHITECTURE.md), [Gemini integration](docs/GEMINI_INVOCATIONS.md), and [security guide](docs/SECURITY.md).
