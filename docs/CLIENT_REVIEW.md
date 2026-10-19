> Historical assessment of the pre-remediation build. See [current repairs and evidence](REMEDIATION.md).

# Client and reviewer assessment — 19 October 2026

This review uses the attached challenge overview as its requirements source and the current project at `C:\Study\Projects\relay-cx` as its baseline. The source copy used for testing excludes `.env`, private runtime state and dependency folders. No real customer systems were connected. The demo video remains excluded as previously requested.

## Findings fixed

| Finding | Change | Verification |
|---|---|---|
| A service correction could keep selecting the original service | Later explicit service and intent take precedence | `test_customer_review.py` |
| Follow-up requests lost their earlier context | Keep the last four redacted customer messages | `test_customer_review.py` |
| Enterprise failures gave a generic handoff message | Explain the failed dependency, expired sign-in, conflicting records or uncertain case outcome | Customer regression and failure scenarios |
| Activity briefly showed an earlier trace as current work | Bind in-flight activity to the latest unfinished request | Three frontend activity tests |
| Live failure banner implied a deterministic replacement answer | Explain unavailability without claiming a replacement answer | Frontend build and strict-live tests |
| Failed confirmations and failed account reads could appear as an unfinished authorization/fetch step in Operations | Use the final failure state and request outcome | Four workflow-outcome regression tests |
| Private case and diagnostic endpoints accepted missing or malformed identifiers | Validate identifiers, payload shape and idempotency keys before ownership checks or writes | `test_private_request_validation.py` |
| Unauthorized POST responses could reset connections on Windows | Drain the bounded body before early responses | Repeated-401 regression and full suite |
| Logout could save a stale session during an in-flight workflow | Serialize logout's session read and write with workflow state changes | Source review and existing HTTP/session checks |
| A model could include an unsupported reference containing no new digits | Reject record and case references absent from verified evidence | Grounded-reply reference regressions |
| Whitespace-only chat could consume a model request | Reject it before model or enterprise work | Request-validation regression |
| CI formatting and audit inputs were stale | Fix formatting, restore the canonical statement and update test references | Ruff and requirement-audit tools |
| Setup and runtime docs described older behavior | Document current modes, model output schema, account scopes, environment and deployment limits | Documentation and clean-install checks |

## Evidence and scope

The current machine-readable results are under `evidence/current`. `pytest.xml` covers backend success, isolation, confirmation/replay, uncertain writes, malformed data, timeouts, legacy normalization, provider failure, telemetry and the newly reproduced customer cases. `http-scenarios.json` covers all eight mandatory scenarios with 160 checks. Frontend verification includes 13 tests, TypeScript and a production build. The final backend suite passes 141 tests (one experimental Google ADK warning). Docker verification exercises the public gateway, both loopback names, roles, cookie/session restoration, scenario execution and non-root containers. Browser review also exercised invalid login, mobile diagnostics, confirmed case creation, cross-customer denial, session expiry, support handoff and all eight Evaluation scenarios at a 319 × 704 viewport; desktop layout was not separately verified in this audit.

The Google Cloud overlay is validated locally for private API/enterprise services, loopback web ingress, secure cookies and the persistent disk bind. This is configuration validation, not evidence of an actual cloud deployment. The resource provenance file compares the 35 resource files to the received project, not to an unavailable original standalone resource ZIP.

The release was extracted into a fresh directory, installed into a new Python environment with a frozen Bun install, and passed Ruff, 141 backend tests, eight real-HTTP scenarios, 13 frontend tests, TypeScript and a Next.js production build. `clean-verification.json` records the commands and tested source manifest. The final runtime matches all 101 runtime/configuration/test files from that clean verification; subsequently refreshed documentation and evidence are included in the final archive.

The requirement matrix contains 456 source-referenced clauses and scenario assertions: 436 have passing supporting local evidence, nine are blocked by provider quota, and 11 video-related clauses are excluded by user instruction. These are traceability statuses, not independent evaluator scores.

## Remaining boundaries

- Fresh live Gemini verification remains blocked: the final configured-model retry returned HTTP 429. No deterministic answer was substituted. The user plans to update local quota/model; a successful real-provider run is still required before claiming live readiness.
- This PoC uses synthetic account, billing, network and legacy records. Model inference is live in LIVE_AI; the enterprise data is still the supplied assessment data.
- The API is a single-process SQLite application. API action markers are durable, but synthetic enterprise tokens and case receipts are held in memory. A mock-service restart requires a fresh login; uncertain case actions require human reconciliation because no case-lookup API is supplied.
- Generated prose has schema, numeric, secret and action-claim checks. These are safeguards, not a formal proof that every possible paraphrase is semantically grounded. Deterministic permissions and write controls remain independent of the model.
- No independent Topcoder score, cloud deployment, distributed-throughput claim or demo video is asserted. Tests cover the named risks; no finite suite proves every possible edge case.

See `FINAL_COMPLIANCE_AUDIT.md` and `REQUIREMENT_EVIDENCE_MATRIX.md` for exact requirement text, source lines, implementation paths, tests, evidence and status. See `HANDOVER.md` for extension and troubleshooting steps.
