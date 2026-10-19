# Run Relay CX

For local development, the easiest option is Docker Compose. From the project
folder, run:

```bash
docker compose up --build
```

Open `http://127.0.0.1:3000` in your browser. To stop the app, press
`Ctrl+C`, or run:

```bash
docker compose down
```

For the longer setup, backup, and recovery instructions, see the
[deployment guide](../deployment/README.md).

## Before using it outside a demo

Relay CX uses fake customer records and a local database. The Google Cloud
configuration is a starting point only; it has not been deployed. Do not use
this demo to handle real customer information.

A real service would need, at minimum:

- real sign-in and permission checks;
- private, protected connections to company systems;
- secure storage, backups, and a plan for deleting old customer data;
- monitoring and a recovery plan;
- shared storage and safe case handling before running more than one backend.
