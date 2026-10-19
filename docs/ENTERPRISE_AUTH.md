# How sign-in works in the sample company services

The sample company services require a sign-in token before they return account,
billing, or service information. The token is a short-lived proof that the
sample user has signed in.

Only the sample health check and sign-in endpoint work without a token. A
missing or expired token is rejected. A request for another customer's record
is also rejected.

The backend keeps the sample-company token on the server. It is not sent to
the browser or to Gemini. The browser gets a separate session cookie. The
profile shown in the browser does not include the sample password or login
details.

## What happens when the sample service restarts

Docker stores hashed token identities and confirmed case receipts in a separate
enterprise database volume. Restarting the service preserves valid identities
and receipts. The API stores its account-level action ledger separately. After
an uncertain write it can look up the original operation key; a missing or
inconsistent receipt never authorizes another write. Local sample-service runs
without `MOCK_DATABASE_PATH` use temporary in-memory state.

## This is not real company sign-in

A real service needs company-managed identity, short-lived permissions,
protected network connections, and a way to check whether an uncertain case
was already created. The sample service is only for local evaluation.

Related checks are in `tests/integration/test_release_hardening.py`:

- `test_enterprise_requires_bearer_and_enforces_ownership`
- `test_enterprise_token_never_reaches_browser_or_events`
- `test_upstream_revocation_preserves_safe_handoff`
