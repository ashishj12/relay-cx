# What has been checked

This project has been tested as a local demo using fake customer records. The
saved results are in
[`evidence/current/verification-summary.json`](../evidence/current/verification-summary.json).

## Checks recorded

- Backend tests passed.
- The eight sample customer situations passed in reviewer mode.
- The Docker setup and a fresh install passed.
- One recorded live Gemini evaluation passed.

These checks help show how the demo behaved at the time of testing. They are
not an independent qualification score and do not prove readiness for real
customers.

## Improvements in this version

- The fake company services check login tokens and customer ownership.
- Customer passwords and service credentials are kept out of browser
  responses and activity records.
- Support staff can inspect other screens without losing an open conversation.
- Requests and agent stages have limits.
- The app checks service responses and keeps useful results when it must hand
  a request to a person.
- Uncertain support-case requests are not automatically repeated.

## Before a real launch

This project has not been deployed to Google Cloud. It uses fake identity,
sample services, one backend process, and a local SQLite database. Real use
would require company sign-in, protected connections to real services, secure
data retention and backups, shared storage for multiple servers, operational
monitoring, and an independent security review.

The combined challenge source document referenced by older evidence notes is
missing from this working copy. The related sample materials are in
[`resources/challenge/`](../resources/challenge/). The demo video is not
included.
