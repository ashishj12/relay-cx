# What changed

This version keeps the sample records and eight sample test situations. The
app uses the sample services over HTTP instead of reading pre-written answers.

## Changes you may notice

- The sample company checks a sign-in token before returning protected records.
- The app checks that a record belongs to the signed-in customer.
- A case is sent only after the customer confirms the exact proposal.
- The app will not automatically repeat a case request if it cannot tell
  whether the first request succeeded.
- Long or incomplete requests are checked and reported clearly.
- If part of a request succeeds before another part fails, the useful results
  are kept for the support handoff.
- Support staff can move between screens without losing the open conversation.
- The health label describes whether the app is running; it does not promise
  that every service is available.

## About the test results

The saved test results describe this code and the fake services. They are not
an independent quality score and do not prove that a real cloud deployment
works.
