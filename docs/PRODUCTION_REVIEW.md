# Review of the updated Relay CX archive

The updated ZIP is the source of truth for this review. Its UI design is preserved. The supplied challenge text is retained verbatim in docs/challenge/ORIGINAL_CHALLENGE.md and its requirements are mapped to current code/tests/scenarios in REQUIREMENT_EVIDENCE_MATRIX.md. This is engineering evidence for independent review; no Claude/Qwen execution, qualification score or acceptance guarantee is claimed.

## Findings addressed

| Finding | Change and evidence |
|---|---|
| Enterprise access token discarded after login | Server-side bearer propagation; independent upstream expiry/ownership checks; direct HTTP security tests |
| Customer profile returned fixture credentials | Profile strips username/testPassword/email; browser and event secret-leak assertions |
| Navigation lost conversation and approval | Keep support component mounted during other views; real Docker browser verification of history, navigation, approval and refresh |
| Agent stage could exceed proxy deadline | Per-stage wall-clock cap plus three-call ADK bound; cancellation regression |
| Chunked body could bypass Content-Length guard | Streaming size check before JSON parsing; real chunked HTTP regression |
| Permissive enterprise scalar coercion | Strict bounded Pydantic records and duplicate JSON field rejection |
| Incomplete conflict comparison | Exact network/subscriber status reconciliation; conflict regression and handoff |
| Partial evidence lost on later failure | Retain current verified facts and timestamped prior evidence in correlated handoffs |
| Expired proposal could not be replaced | Expiry event and fresh proposal without write; expiry regression |
| XML accepted invalid/naive timestamps | Require a timezone-aware parsed timestamp; encoding/DTD/identity/status tests retained |
| Missing handover and stale evidence | Rebuild docs, runbook, full matrix, clean install and current execution results |
| Shipping Git/dependencies/history | Source allowlist, env/key scan, per-file hashes and fresh ZIP validation |

## Verification and remaining conditions

See evidence/current/verification-summary.json for current executable results and source freshness. Backend tests cover positive, negative, concurrency/restart, malformed contracts and ADK behavior. The eight scenarios run through real HTTP services; Docker checks include the Next.js gateway. Clean verification extracts the archive, verifies manifest hashes, installs dependencies afresh, tests both languages, runs scenarios and builds the frontend. Provider simulations are labeled and never counted as live inference.

Fresh credentialed Google ADK evaluation passes with Gemini 3.8 Flash: account inquiry, service clarification, resumed network/XML diagnostics, case proposal and explicit confirmed case creation. Every recorded model stage succeeds without simulated output or deterministic fallback. The configured model is visible in ai.finished events and the live evaluator checks actual read_account/diagnose_service tool requests. See evidence/current/live-gemini-evidence.json.

Earlier Gemini 3.5 Flash calls returned HTTP 429 and the older 2.5 Flash model returned HTTP 404 despite appearing in discovery. Those failures are retained separately with availability diagnostics. They demonstrate explicit DEGRADED behavior, not live success. The sample environment now names the verified 3.8 Flash model; reviewers must configure their own enabled model/key for live execution. Reviewer mode remains credential-free.

GCP architecture/build preparation is included; cloud resources were not provisioned. Local synthetic deployment uses a single API process, SQLite WAL and process-local upstream token/case stores. Horizontal scaling, durable enterprise idempotency/reconciliation, federated identity, DLP/retention and managed telemetry export remain documented real-world deployment work. The challenge permits a deployment approach and synthetic services; this release does not claim public carrier-production certification. Demo video remains excluded by user instruction. Independent scoring remains pending.
