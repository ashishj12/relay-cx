# Relay CX deployment guide

This repo can run locally with Docker, and it also has a reference deployment pattern for Google Cloud.

This is meant to be easy to follow. The main idea is simple:

- local dev: run everything with Docker Compose
- cloud reference: run the same containers on a VM with a persistent disk
- keep secrets outside the repo
- expose only the web app publicly
- keep the API and mock telecom services private

## Local deployment

From the project root:

```bash
docker compose up --build
```

This starts:

- the Next.js web app on http://127.0.0.1:3000
- the FastAPI service
- the synthetic telecom mock service

The API keeps its data in the `cx-data` volume. When you are done:

```bash
docker compose down
```

If you need a local environment file, copy the example file first:

```bash
cp .env.example .env
```

## Google Cloud reference deployment

This is a deployment pattern for a single VM, not a live cloud service already running.

The recommended target is:

- Google Compute Engine VM
- Docker Compose
- ext4 persistent disk for SQLite data
- Secret Manager for the Gemini key
- HTTPS load balancer or private reverse proxy in front of the web app

### Basic flow

1. Build container images with Artifact Registry and Cloud Build.
2. Create a VM with Docker, Compose, and a service account.
3. Mount a persistent disk at `/srv/relay/data`.
4. Copy the release without `.env` values.
5. Point Compose at the built images and store runtime config outside the repo.
6. Keep the API and mock telecom private; only the web app should be public.
7. Set `PUBLIC_ORIGIN` to the exact HTTPS hostname and enable `COOKIE_SECURE=true`.
8. Set up backups, logging, health checks, and rollback steps.

### Important deployment notes

- Use one API process and one SQLite database.
- Store SQLite data on a real persistent disk, not on a shared or temporary filesystem.
- Keep secrets in Secret Manager, not inside Docker images or config files in the repo.
- Do not expose the internal mock services or the protected API directly.
- Only the frontend should be reachable from outside.

## Runtime settings

A few settings matter in production:

- `PUBLIC_ORIGIN`: exact browser origin used by the app
- `COOKIE_SECURE=true`: required for HTTPS
- `REQUEST_TIMEOUT=2`: timeout for enterprise network calls
- `MAX_RETRIES=1`: safe read-only retry limit
- `AI_TIMEOUT=40`: model call timeout

These are operational guardrails, not a full production platform design.

## Operational checklist

Before running this outside a demo or challenge environment, make sure you have:

- backup and restore process for SQLite
- monitoring and logs for failed AI or enterprise calls
- alerts for auth failures, tool failures, and uncertain actions
- budget and quota controls for Gemini usage
- a clear rollback plan before replacing containers

## Important caution

This repository is designed for local challenge/demo work and controlled evaluation. It is not a complete production customer-facing system. Production features such as full identity federation, mTLS, external enterprise integration, queueing, and distributed scaling still need engineering work.

For more detail, see:

- [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- [../docs/SECURITY.md](../docs/SECURITY.md)
- [../docs/GEMINI_CX_MAPPING.md](../docs/GEMINI_CX_MAPPING.md)
