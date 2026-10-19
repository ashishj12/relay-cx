# Notes for the next person working on Relay CX

Relay CX is a demo that answers telecom questions using fake customer records.
The only action that changes data is creating a support case, and the customer
must confirm it first.

## Where to look

- `apps/web` contains the website.
- `apps/api/src/relay_api` contains the backend and workflow.
- `services/mock-telecom` contains the fake company services.
- `resources/challenge` contains sample records and test situations.
- `tests` contains automated checks.
- `evidence/current` contains saved test results.

## If you change something

For a new kind of question, update the request handling and add a test for the
expected answer and a test for an unsafe or failed case.

For a new company-service read, use a fixed backend route. Check the signed-in
customer before reading, and check the service response before showing it.
Never let the browser or Gemini choose an arbitrary URL or account.

For a new action, require a clear confirmation, prevent accidental duplicate
requests, and test what happens if the service fails after receiving it. Do not
automatically repeat an action if you cannot tell whether it succeeded.

## Looking into a failed request

1. Sign in as `support.agent`.
2. Open Operations and select the request.
3. Look for the failed step and its short error description.
4. Check whether the app has already made or proposed a case before trying
   again.

The app records activity in its local database. Do not delete the database to
clear an uncertain case result.

## Test failures

The tests start local fake services and use temporary databases. Some tests
need permission to use localhost. If an environment blocks local network
access, fix the environment rather than replacing real HTTP checks with fake
answers.

## Limits to remember

The demo has a small set of fake records, legacy subscriber records for both supplied customer accounts, and a session-scoped, read-only receipt lookup for uncertain cases. Its database and
backend setup are for one process only. It has not been deployed to Google
Cloud or approved for real customer use.


## Adding a read tool

1. Add the response contract to `apps/api/src/relay_api/domain/models.py` with ownership fields and bounded values.
2. Add a fixed-route method to `infrastructure/enterprise.py`. Call the session/workflow guard first, then validate record ownership inside the response normalizer. Do not accept arbitrary URLs.
3. Normalize the result in `application/evidence.py`. Preserve partial verified facts when a later dependency fails, and flag conflicting statuses.
4. Add the route-specific ADK tool in `agents/runtime.py`. Its identifiers must come from the authenticated session. Keep credentials and raw XML out of model context.
5. Add positive, unauthorized, malformed-response and timeout tests. Run the mandatory reviewer evaluation, then gather new live evidence when quota allows.

Changing routing also requires updating the deterministic reviewer classifier, `Interpretation`, agent catalog and scenario expectations. The last four redacted customer messages are the bounded model context. A later explicit service or intent takes precedence; do not silently replace the authenticated account.

## Before scaling

The API runs one process with per-account workflow locks, an eight-workflow admission limit and bounded queue waits. Do not add workers or replicas around the SQLite/action implementation. Introduce shared transactional action claims, durable enterprise receipts and a reconciliation API first. Docker persists hashed synthetic identities, receipts and idempotency keys in a separate enterprise volume; tokens retain their normal expiry across restarts. API action markers remain durable and uncertain writes remain blocked.

Account-level conversation and action records are separate from the browser session. Reauthentication restores the last 40 conversation messages and any unfinished proposal. Customer trace ownership follows the account across sessions. Never delete an uncertain marker to make a retry possible. See the new remediation regressions and `docs/REMEDIATION.md` for the reproduced failures and their checks.
