# Try Relay CX

Relay CX is a demo support website. Use the fake customer accounts and fake
company records included with the project. You do not need a Gemini key for
the basic review.

## Start the app

From the project folder, run:

```bash
docker compose -p relay-review up --build --wait
```

Open `http://127.0.0.1:3000`.

- Sign in as Alex to try the customer pages.
- Sign in as `support.agent` or `admin` to see Operations and Evaluation.
- The sample usernames and passwords are in the main
  [README](../README.md).

When you are finished, stop the containers:

```bash
docker compose -p relay-review down
```

If you are not using Docker, see the install and test commands in the
[main README](../README.md).

## Try these requests

1. Ask: “What internet plan am I currently using?” Check the answer against the
   sample account.
2. Ask: “My service is not working.” Answer the app's question with “home
   internet.” The app should ask before reading protected service records.
3. Ask: “My home internet is slow.” Review the network and service checks. If
   sample results disagree, the app should ask a person to help.
4. Ask: “Create a support case.” Review the proposal and confirm it. Repeating
   the same confirmation should not create another case.
5. While signed in as Alex, ask for account `ACC-2002`. The app should refuse
   before reading that account.
6. Ask to check legacy subscriber status. The app should show a readable
   result, not raw XML.

Two test situations also simulate failures: SCN-007 tests a case-service
failure, and SCN-008 tests a Gemini failure. The app should explain the
problem rather than claiming that the task succeeded.

## Test modes

- **Reviewer mode** uses predictable test answers, so you can review without
  a Gemini key. The rest of the workflow still runs.
- **Live AI mode** sends requests to Gemini and needs a valid key and an
  available model.
- **Degraded mode** means the app could not use Gemini successfully.

For live AI instructions, see
[What Gemini does in Relay CX](./GEMINI_INVOCATIONS.md). A saved test result is
not an independent quality score, and the Google Cloud setup has not been
deployed.
