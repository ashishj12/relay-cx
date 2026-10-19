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

The demo has a small set of fake records, one successful legacy subscriber
example, and no service for looking up an uncertain case. Its database and
backend setup are for one process only. It has not been deployed to Google
Cloud or approved for real customer use.
