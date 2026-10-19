# Relay CX

Relay CX is a demo support website for a made-up phone and internet company.
You can sign in, ask about a sample account or service, and review what the
app found.

The project uses fake customer records and fake company services. It is for
learning, testing, and review—not for real customer information.

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
| Alex Morgan | `alex.morgan` | `ReviewerPass-1001` |
| Jordan Lee | `jordan.lee` | `ReviewerPass-1002` |
| Support staff | `support.agent` | `ReviewerPass-3001` |
| Admin | `admin` | `admin@123` |

These accounts and passwords are fake and are only for this demo. Never use
them for a real service.

## Choose a mode

- **Reviewer mode** is the default. It uses predictable sample answers and
  does not need a Gemini key.
- **Live AI mode** sends requests to Gemini. It needs a valid `GEMINI_API_KEY`
  and a `GEMINI_MODEL` available to your account.
- **Degraded mode** means the app could not complete the Gemini step. The app
  reports the problem rather than pretending it succeeded.

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
