# Independent reviewer guide

This guide applies equally to human and automated reviewers. No reviewer-specific prompts, hidden instructions, fixed scores or model integrations are embedded. The project uses Gemini; Claude and Qwen are not runtime dependencies.

## Start without credentials

Copy `.env.example` to `.env`, leave `APP_MODE=REVIEWER`, then run `docker compose -p relay-review up --build --wait`. Open `http://localhost:3000` (127.0.0.1 on the same port also works). Sign in as Alex for customer workflows or `support.agent` for Operations and Evaluation; passwords are in README and are synthetic. An initial `/api/session` 401 while signed out is expected; a successful login returns a complete session.

For the CLI install the pinned Python requirements and frozen Bun lock as README describes. Run `python -m pytest -q`, `python tools/evaluate.py --mode REVIEWER`, `bun run test:web`, `bun run typecheck`, `bun run build`. The HTTP evaluator starts its own services on ephemeral loopback ports and cleans them up. Its eight scenarios use the same guards, gateway, XML parser, action confirmation, persistence and telemetry as the UI. Only AI interpretation/fact ordering is deterministic. Assertions in `evaluation/scenarios.py` are independent of the workflow implementation and inspect positive and prohibited behavior.

## What to inspect

1. Grounded plan: ask “What is my current plan?” and compare the account-service event/facts.
2. Clarification: “My service is not working”, then “home internet”; no protected read should precede clarification.
3. Reconciliation: “My home internet is slow”; inspect network, diagnostics and XML evidence. Divergence escalates.
4. Action: “Create a support case”; observe a proposal, explicitly confirm, and repeat the same confirmation. One case reference is returned.
5. Isolation: request ACC-2002 while signed in as Alex. The request fails before a protected tool invocation.
6. XML: “Check my legacy subscriber status”; inspect normalized status, not raw XML.
7. Enterprise failure: SCN-007 records a failed case write and human handoff; it cannot claim completion or automatically replay an uncertain write.
8. Provider failure: SCN-008 explicitly simulates provider unavailability, records failure/fallback and returns authorized enterprise facts in DEGRADED mode.

Operations metrics derive from actual persisted events. Trace visibility is session-scoped for customers and support-scoped for staff. Support cannot impersonate a customer for protected reads. `/api/activity` shows only the current session. Upstream services also reject missing/expired bearer identities and foreign records.

## Live evidence and boundaries

Set `APP_MODE=LIVE_AI`, `GEMINI_API_KEY` and an enabled `GEMINI_MODEL` only in an ignored local environment or secret store. Run `python tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json`. On low quotas set `LIVE_EVALUATION_PAUSE=65` in the shell. The live gate requires real ADK router/tool events and all five workflow turns to succeed without fallback. A fake SDK response, deterministic scenario result or old evidence cannot satisfy that gate. A provider failure is recorded as FAIL/BLOCKED and is not converted into live success.

Review `docs/REQUIREMENT_EVIDENCE_MATRIX.md` and `evidence/current/` together. PASS means the cited local synthetic checks passed, not an external qualification score. Cloud configuration is prepared, not deployed. The synthetic mock's token/case stores are process-local and a restart invalidates upstream sessions; log in again. The app's durable action claim prevents reissuing an uncertain action but cannot reconcile a lost upstream result without a case lookup service. Use a single API process. The demo video is excluded by user request and remains an explicit submission gap if the evaluator requires it.
