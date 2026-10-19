# Summary of changes

The reviewed application keeps the received customer records, API contracts, failure controls and all eight mandatory scenarios. The resource comparison in `evidence/current/starter-provenance.json` confirms 35 resource files are unchanged from the received project. The original standalone starter ZIP was unavailable, so this is not a claim of byte-for-byte provenance against that ZIP.

## Components retained and completed

| Area | Work retained or completed |
|---|---|
| Customer experience | Next.js, TypeScript and Bun workspace; customer chat, support handoff, Operations and Evaluation views |
| Gemini | Native Google ADK routing and specialist agents; controlled tools and a validated grounded-reply schema after enterprise retrieval |
| Enterprise integration | Supplied synthetic identity, account, billing, diagnostics and case services accessed over HTTP |
| Legacy integration | XML adapter, response normalization and independent legacy records used to detect conflicts |
| Security | Server-bound customer scope, deterministic ownership and roles, session cookies, confirmation and durable duplicate-action controls |
| Reliability | Bounded model/tool execution, limited safe retries, explicit strict-live failure handling and uncertain-write reconciliation |
| Observability | Correlated structured events, workflow traces, tool timings, escalation context and metrics derived from execution |
| Deployment | Non-root Docker services, health checks, SQLite persistence and documented GCP deployment configuration |

## Changes from this client review

- Corrected explicit service changes and follow-up context across customer turns.
- Made dependency failures and handoffs explain the next step clearly.
- Corrected stale in-flight activity and failed workflow states in operational views.
- Validated malformed private requests before ownership checks; consumed bounded POST bodies before early rejection.
- Serialized logout state changes with workflow writes and rejected empty chat messages.
- Rejected unsupported record references in generated replies, including references whose digits already appear in verified facts.
- Added customer, private-endpoint, grounded-reply and frontend regressions.
- Updated setup, environment, architecture, handover and Google CX mapping documentation; restored the attached canonical challenge statement and regenerated requirement evidence.

## Remaining limits

Fresh live Gemini success requires available quota; current provider failures are preserved in the evidence. Cloud configuration has been validated locally but not deployed. The API supports one process; Docker now persists hashed synthetic identities and case receipts in a separate enterprise volume. No independent qualification score is claimed. The demo video is excluded at the user's request. See `REMEDIATION.md` for the current repairs and `CLIENT_REVIEW.md` for the historical review.

## Follow-up repairs

See [REMEDIATION.md](REMEDIATION.md) for the safety, customer workflow, bounded concurrency, durable synthetic services and optional managed telemetry work after the independent review. Actual cloud deployment was deferred by the user; the source contains configuration placeholders rather than active credentials.
