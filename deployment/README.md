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

## Timeouts, retries and concurrency

Enterprise HTTP calls have a two-second socket timeout and one retry by default (at most two configured retries). Only GETs and explicitly read-only diagnostic/XML POSTs retry temporary transport errors, HTTP 429 and selected 5xx codes, with bounded backoff. Login and case creation do not retry automatically. Malformed/foreign data does not retry. AI has one SDK attempt per call, up to three LLM calls per stage, and a maximum 40-second wall-clock stage deadline. A normal inquiry has two stages. The BFF times out at 120 seconds; callers must inspect current action/session status after a disconnect rather than blindly resubmit.

The API serializes workflows with a process lock to protect local SQLite action state. This is a small, single-process PoC, not a throughput claim. Queue time and slow concurrent requests can exceed browser deadlines; use ingress rate/concurrency limits and a bounded queue before public load. Do not add API workers/replicas without shared transactional action claims. Structured events and independent WAL reads keep activity visible during a request.

## Health and incident response

`GET /health` (public gateway `/api/health`) is process liveness and mode, not a guarantee of model or enterprise availability. Staff `/api/ops/health` probes the enterprise endpoint. Staff metrics/traces identify provider failure, authorization denial, tool retries/failure and handoffs. A provider outage is DEGRADED; an enterprise failure is an explicit handoff. An uncertain case remains blocked until reconciled. Clear neither database nor action markers to bypass it.

Suggested alerts: any uncertain action, sustained tool or provider failure, unexpected auth/authorization spikes, missing request.finished, disk pressure, SQLite lock errors or failed backup verification. Filter simulated reviewer failures out of live alerts. This release exposes events/metrics but does not provision Cloud Monitoring policies or an exporter. Keep failure injection disabled outside reviewer environments.

## Backup, restore and rollback

Use `python tools/backup_database.py --database /path/to/relay.sqlite --output /secure/backup.sqlite` to create a consistent SQLite online backup and run integrity_check. The output must not exist. Restrict backups to the service operator, encrypt storage and apply retention; session bearer credentials/history are sensitive. The JSONL file is a mirror; SQLite contains authoritative events/state. A raw copy of a live WAL database is not a valid backup strategy.

Before release replacement: stop new ingress, drain active workflows, stop the API, take/verify a backup and record immutable image digests. Start the new version against a copy first, run health, login, reviewer scenarios and inspect uncertain actions. Schema changes require a versioned migration and rollback plan before shipping. Current schema additions are additive indexes only.

For restore: stop ingress and the API; preserve the current database and WAL/SHM files for investigation; verify backup integrity; restore into an empty data directory with service ownership; start one API process; run health/login/read checks before reopening ingress. Use `COOKIE_SECURE=true` and log in again if the synthetic identity service restarted. Restoring older state can lose action receipts; reconcile writes with the enterprise system before allowing new proposals. Roll back container digests only when the restored/current schema is compatible. Never delete volumes as a recovery shortcut.

Google references: [consistent disk snapshots](https://docs.cloud.google.com/compute/docs/disks/snapshots), [Secret Manager best practices](https://docs.cloud.google.com/secret-manager/docs/best-practices). Disk snapshots supplement, not replace, application-consistent backup/drain.

## Google Cloud release procedure and cost controls

Prepare a project with billing, Compute Engine, Artifact Registry, Cloud Build and Secret Manager enabled. Create a regional registry and a dedicated build identity with repository write permissions. Invoke `gcloud builds submit --config deployment/cloudbuild.yaml --substitutions=_REGION=REGION,_REPOSITORY=REPOSITORY,_TAG=IMMUTABLE_TAG`. This builds/pushes images; it does not deploy resources. Record the resolved digests and configure the VM Compose services to those digests with `image:` and no build step.

Give the runtime VM a separate service account with access only to its Gemini secret version and required image pulls/log writes. Mount an ext4 persistent disk and bind it at `/app/data`; a plain Docker named volume on an ephemeral boot disk is insufficient. Fetch secrets via the VM identity into a mode-0600 runtime environment file outside the release, never a build argument or checked-in file. Set an exact HTTPS PUBLIC_ORIGIN and secure cookies. Expose web only through a controlled TLS ingress; firewall API/enterprise, restrict SSH/admin access and use OS Login. Keep the synthetic service private and use only supplied/synthetic records. Configure backup retention and least-privilege log access before external use.

Install/configure the Google Ops Agent or an explicit event exporter for the sanitized JSONL sink, preserving correlation fields. Alert on observed metrics and retain logs under a documented policy. Set billing budgets and provider quotas, cap ingress request rates, monitor model latency/failure and storage growth, and retain only required event history. Billing budgets are notifications, not hard spending caps. Model token cost accounting is not implemented; bound call count/context and confirm current model pricing separately.

Cloud Run is a future alternative requiring Cloud SQL or another transactional shared store, cross-instance action claims, durable upstream idempotency, scoped OIDC and proper draining. Do not mount SQLite on Cloud Run or scale this Compose API horizontally. GCP deployment is prepared but has not been executed or load-tested in this release.

## Concrete VM override

`deployment/compose.gcp.yaml` selects prebuilt immutable images, disables reviewer failure injection, enforces LIVE_AI/secure cookies, binds `/srv/relay/data`, and allows 90 seconds to drain the API. Supply `RELAY_API_IMAGE` and `RELAY_WEB_IMAGE` as complete Artifact Registry digest references in `/etc/relay/runtime.env`, alongside key/model and the exact HTTPS `PUBLIC_ORIGIN`. Create/mount the persistent disk directory with owner UID/GID 10001 and mode 0700 before starting the API. The runtime environment file must be mode 0600 and outside the source/image.

```bash
docker compose --env-file /etc/relay/runtime.env -f compose.yaml -f deployment/compose.gcp.yaml config --quiet
docker compose --env-file /etc/relay/runtime.env -f compose.yaml -f deployment/compose.gcp.yaml up -d --no-build --pull always --wait
```

Use a host TLS reverse proxy such as the provided `nginx.conf.example`, replacing hostname and trusted certificate paths. Forward to loopback port 3000; do not point a load-balancer backend directly at a loopback-only port. Restrict ingress to HTTPS and approved administration. The example does not provision certificates, firewall rules or cloud resources. Validate proxy configuration before reload. The template is configuration-validated locally; VM deployment is not claimed.
