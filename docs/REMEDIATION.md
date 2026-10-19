# Repairs after the technical and customer reviews

The original review scored the previous build at 70/100. This document records repairs and their verification; it is not a replacement independent score or a claim of cloud qualification.

| Finding | Repair | Evidence |
|---|---|---|
| Unsupported model prose passed fact-ID and numeric checks | Current verified paragraphs are enumerated in the final model schema and independently validated. No new factual prose or reassigned prices is accepted. | `test_unsupported_prose_never_reaches_customer` |
| Fresh login allowed a duplicate after a lost case receipt | Account-level action ledger survives sessions. A retry looks up the original receipt; missing or inconsistent receipts never authorize another write. | `test_uncertain_case_is_not_repeated_after_fresh_login` |
| Passwords written as natural sentences survived redaction | Natural-language assignments, quoted passphrases and dotted tokens are removed before history/model processing. | Natural-language and passphrase canary regressions |
| Long model work held a global database lock | Independent account workflow locks, request-local provider callbacks and bounded HTTP/workflow admission replace the global I/O lock. | Independent-account and busy-request regressions |
| Human-support button depended on Gemini | Authenticated, deterministic `/api/handoff` saves a reference and available context without invoking a model. Typed requests to speak to a person use the same control. | HTTP and typed-human-request regressions |
| Saved-for-review message lacked a useful follow-up | Failures include the real saved reference. Handoffs state that the demo does not contact live staff or promise a callback/time. | Handoff regression and customer UI check |
| Unsupported plan changes and travel requests led to confusing results | Explicit capability controls explain what cannot be done and that nothing was changed/booked. A case proposal explains its effect before approval. | Unsupported-change/booking regressions |
| Reauthentication lost conversation context and prior trace access | Account conversation context and unfinished actions restore after sign-in; owned traces remain readable across sessions, other accounts remain denied. | Expiry, reauthentication and trace-isolation regressions |
| Trace summaries lacked actual records | Allowlisted normalized account/billing/service/receipt fields are included after validation; credentials and unnecessary profile fields are excluded. | Actual normalized bill trace regression |
| Synthetic tokens and receipts disappeared on container restart | Separate persistent enterprise database stores hashed identities, receipt bodies and unique operation keys. | Storage-reopen tests and Docker persistence verifier |
| Managed telemetry was documentation only | An opt-in ADC-authenticated worker exports the actual journal to Cloud Logging and parented Cloud Trace spans, with a durable per-project cursor and bounded retry. | Local transport/cursor tests; real cloud delivery is deferred |
| Scenarios could inherit another scenario's conversation/action state | Each scenario executes the same real workflow against HTTP services with independent initial storage. Its actual events/handoffs feed the reviewer view. | Eight mandatory scenario results |
| Fresh-release evidence could refer to an earlier root test run | The clean-release verifier now copies fresh XML and frontend result metadata from the independent installation. | `clean-verification.json` |

## Customer walkthrough

`RAHUL_CUSTOMER_REVIEW.md` records the original UI-only experience before repairs, including exact messages. It uses the supplied Jordan mobile account because no Rahul credentials are supplied. A same-day return was actually observed; a true next-day browser visit was not performed. The expiry/reauthentication regression advances the test clock in an isolated service, not the user's computer clock. Reviewer UI checks and live-provider checks must remain separately labelled.

## Grounding trade-off

Live factual answers are deliberately extractive. Gemini still interprets normal inquiries, calls the authorized tool through native ADK and returns the constrained final reply. This prevents the demonstrated invented-benefit and price-reassignment failures; it sacrifices unrestricted paraphrasing. Rejection is an explicit live failure with a review reference, never a hidden Reviewer substitute.

## Verification state

The final machine-readable results are under `evidence/current`. A newly extracted archive, fresh Python environment and frozen Bun install passed the checks below. `verification-summary.json` confirms that all 107 tested runtime/configuration/test files match the final runtime source; later documentation and evidence refreshes do not change those files. A failed Gemini call is not converted into a pass.

| Executed check | Result | Evidence |
|---|---|---|
| `python -m ruff check apps/api services tests tools` and `python -m ruff format --check apps/api services tests tools` | Pass | `clean-verification.json`, exact commands and output |
| `python -m pytest -q --junitxml=evidence/current/pytest.xml` | 166 passed; no failures or skipped tests | Fresh clean-install `pytest.xml` |
| `python tools/evaluate.py --mode REVIEWER` | All 8 scenarios; 160 assertions passed | `clean-http-scenarios.json` |
| `bun run test:web` | 13 tests, 37 assertions passed | `frontend-verification.json` |
| `bun run typecheck` and `bun run build` | Pass | `clean-verification.json` |
| `REVIEW_PORT=3110 COMPOSE_PROJECT_NAME=relay-repair-20261019 python tools/verify_containers.py` (environment variables set using the host shell) | Both loopback names, access controls, non-root containers and all 8 scenarios passed | `docker-verification.json` |
| `python tools/verify_persistence.py --project relay-repair-20261019 --origin http://127.0.0.1:3110` | Token and receipt survived enterprise restart; reauthenticated confirmation replay made no new tool call | `persistence-verification.json` |
| Browser walkthrough of repaired Reviewer application | Desktop and phone-sized view; clarification, refusal, approval, receipt, restored history and human review checked | `CUSTOMER_RETEST.md`, screenshots and `customer-retest.json` |
| Rebuilt active application in preserved LIVE_AI mode | Containers running; API/enterprise healthy; access controls and model-independent handoff passed | `active-upgrade.json`, `active-live-handoff.png` |
| Real Gemini evaluation | Failed: HTTP 429; no fallback reply used | `live-gemini-evidence.json` |
| Cloud configuration | Merged configuration validated; actual deployment deferred | `deployment-config.json` |

The source audit's requirement rows are a supporting checklist grouped around executable evidence, not independent per-clause acceptance or a replacement score. Qualification remains blocked by missing successful live evidence and independent evaluation. Neither a 100/100 score nor readiness for real customer operations is claimed.

## Applied local upgrade

The repairs were applied to `C:\Study\Projects\relay-cx` after checking the previous source hashes. Changed files and the previous ignored environment were backed up privately before replacement; a consistent application-state backup was also verified in the existing private Docker volume. All previous environment values, including mode, model and key, were preserved. Missing optional `GOOGLE_CLOUD_PROJECT`, `GCP_REGION`, `RELAY_API_IMAGE` and `RELAY_WEB_IMAGE` entries were appended for later setup. No credentials or runtime databases are included in the source ZIP.

## Deferred by the user

Actual GCP deployment is deferred until credits, project details and a spending limit are available. Optional cloud environment entries are supplied for later completion; local startup requires none of them. No resources, IAM roles, TLS certificates or billing setup have been provisioned. A successful current Gemini run still requires provider quota. The demo video remains excluded.

## Supported operating scope

Run one API process. Per-account synchronization is in-process; do not add replicas without shared transactional action claims and load verification. Use the two persistent volumes, protect backups and reconcile operations before restoring old state or rolling back to code that predates the account ledger. The cloud exporter is opt-in and transport-tested, not a claim of accepted cloud delivery. Customer data remains supplied/synthetic. No live human-support queue or callback service is connected.
