# What Gemini does in Relay CX

Gemini helps with two things: understanding the customer's message and
choosing which verified facts answer it. The backend checks the customer's
identity, reads the records, and controls all actions. Gemini cannot send a
case or choose a different customer's account.

## The steps

| Step | What it means |
|---|---|
| Understand the request | Gemini identifies the kind of help requested and any service the customer named. |
| Read the right sample records | A specialist uses a limited, read-only tool for the signed-in customer. |
| Choose verified facts | Gemini returns references to facts the tool already found. The app rejects missing or invented references. |
| Create a case | The backend does this only after the customer confirms the proposal. Gemini does not perform this step. |

The tool does not let Gemini provide account numbers or service URLs. The
backend supplies the permitted scope. The app shows the original checked facts
rather than trusting Gemini to rewrite them.

## If Gemini fails

The app reports that Gemini could not complete its step and shows a degraded
status. It does not describe a test simulation as a real Gemini response. The
saved events distinguish real calls from simulated failures.

## Run a live check

Set `GEMINI_API_KEY` and `GEMINI_MODEL` in a private local environment. Do not
put a real key in source code or send it in a chat. Then run:

```bash
python tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json
```

The latest saved result is in
[`live-gemini-evidence.json`](../evidence/current/live-gemini-evidence.json).
It shows one successful run with `gemini-3.8-flash`. Model access depends on
your Google account, so a new run may have a different result.

## A few terms

- **ADK:** Google's library for running model-based tasks and tools.
- **Tool:** A limited function the app allows a specialist to use.
- **Live run:** A request sent to the real Gemini service, not a test substitute.
- **Degraded:** The app could not use Gemini successfully, so it reports the
  problem instead of pretending it worked.
