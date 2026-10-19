# Requirements: a simple checklist

This page is a plain-language summary of what the sample project is expected
to demonstrate. The saved requirement-by-requirement data is in
[`compliance-audit.json`](../evidence/current/compliance-audit.json).

## What the app should do

| Area | In plain language | Where to look |
|---|---|---|
| Understand questions | Use Gemini for live interpretation, or clearly label reviewer/test mode. | `docs/GEMINI_INVOCATIONS.md`; `evidence/current/live-gemini-evidence.json` |
| Protect customer records | Sign in first and only show records belonging to that customer. | `docs/SECURITY.md`; tests and scenarios |
| Use company services safely | Read through fixed backend tools and check the answers before showing them. | `docs/ARCHITECTURE.md`; integration tests |
| Ask before taking action | Show a case proposal and wait for the customer to confirm it. | `docs/SECURITY.md`; scenario tests |
| Handle failures honestly | Say when a step failed; do not claim success or repeat an uncertain case. | `docs/REVIEWER_GUIDE.md`; failure scenarios |
| Keep a useful history | Record the steps so support staff can review what happened. | `docs/ARCHITECTURE.md`; event and trace tests |
| Run the same way for review | Provide setup instructions and repeatable local scenarios. | `docs/REVIEWER_GUIDE.md`; clean-install evidence |
| Describe real-world limits | Say what is still fake, local, or not deployed. | `docs/SECURITY.md`; deployment guide |

## What the saved checks say

The saved summary reports 445 requirement checks as `PASS` and 11 as
`EXCLUDED`. A `PASS` means the recorded local or fake-service check passed. It
does not mean every possible case has been tested. `EXCLUDED` means the item
was not counted as a required check.

The latest summary also reports 105 backend tests passed, reviewer scenarios
passed, Docker passed, a clean install passed, and one live Gemini run passed.
These are saved results for a particular version, not a new test run.

## What is still unknown

- No independent evaluator has given the project a qualification score.
- No Google Cloud deployment has been performed.
- The original combined challenge document cited by some old requirement rows
  is missing from this working copy. Related files are in
  [`resources/challenge/`](../resources/challenge/), but they are not the same
  combined source file.
- The demo video is not included.

For the full machine-readable list and its supporting evidence, open
[`evidence/current/compliance-audit.json`](../evidence/current/compliance-audit.json).
