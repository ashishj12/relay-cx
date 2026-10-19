# Project check results

This page summarizes the latest saved checks. It is written for orientation;
the detailed requirement list is in the
[evidence matrix](./REQUIREMENT_EVIDENCE_MATRIX.md).

| Check | Saved result |
|---|---|
| Backend tests | 105 passed |
| Reviewer scenarios | Passed |
| Docker run | Passed |
| Fresh install | Passed |
| Live Gemini run | Passed for the recorded run |
| Independent qualification score | Not available |
| Google Cloud deployment | Not performed |

These results come from the saved
[`verification summary`](../evidence/current/verification-summary.json). They
describe the tested version and its fake company services. They are not a
promise that every possible request is safe or that the app is ready for real
customers.

## What still needs to happen

- An independent evaluator must provide the qualification score.
- The original combined challenge document is missing from this working copy.
  Sample challenge materials remain in
  [`resources/challenge/`](../resources/challenge/), but older line references
  to that missing document cannot be checked here.
- The demo video is not included. Supply it separately if the evaluator asks
  for one.
- Before a real launch, complete the work in the
  [security](./SECURITY.md) and [deployment](../deployment/README.md) guides.
