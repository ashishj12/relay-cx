# Keeping customer information safe

Relay CX is a demo with fake customer data. It includes some safety checks, but
it is not approved for real customer information.

## Who can see what

- A customer must sign in before the app reads protected records.
- The backend checks that a record belongs to the signed-in customer.
- The support role can review activity but cannot act as a customer.
- Gemini cannot choose an account, service address, or web link.
- The app checks company-service answers before showing them.

The browser gets a session cookie. The separate token used to contact the
sample company stays on the backend. Passwords, tokens, raw Gemini responses,
and raw XML should not appear in activity records.

## Creating a support case

The app first shows a proposed case. The customer must confirm that proposal
through the confirmation control. Typing “yes” in chat does not create a case.
The app checks the customer's access again before sending it.

If the app cannot tell whether the company created a case, it stops and asks
for human review. It does not send the same request again automatically.
Because the fake company has no case-lookup feature, a person may need to check
the result separately.

## What the demo protects against

- Requests made without signing in.
- Attempts to read another customer's records.
- Model output that tries to change the customer's identity.
- Repeated confirmation of the same case.
- Invalid service replies and unsafe XML.
- Accidentally showing tokens in the browser or activity records.

Automated tests cover these examples, but passing tests cannot prove that every
attack is prevented.

## What a real service still needs

Before handling real customers, the project would need:

- company-managed sign-in and permissions;
- protected connections to the company's real services;
- encryption, backup access controls, and rules for deleting old data;
- monitoring, rate limits, and a response plan for incidents;
- a shared database and safe case handling if more than one backend is used;
- an independent security review.

Today, sign-in and company services are fake, activity is kept in a local
SQLite file, and the app is designed for one backend process. Do not expose
the backend or fake company services directly to the internet. See the
[deployment guide](../deployment/README.md) for more limits.
