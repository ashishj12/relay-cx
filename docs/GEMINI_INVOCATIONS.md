# Google ADK invocation register

Live mode uses native Google ADK LlmAgent and Runner components. Gemini classifies the request, the relevant specialist calls an authorized tool, and Gemini writes the customer-facing answer from the returned normalized facts. The backend returns that answer rather than joining fixture strings. The enterprise services still use the supplied challenge data; live AI does not mean a connection to a real telecom operator.

| Agent | Behavior | Authority |
|---|---|---|
| request_router | Classify redacted customer messages into intent, service and confidence | No enterprise tools |
| account_agent | Call read_account and answer using its verified results | Read only, authenticated account |
| billing_agent | Call read_billing and explain verified charges | Read only, authenticated account |
| service_agent | Call diagnose_service and explain verified network, diagnostic and legacy results | Read only, authorized service |
| action_controller | Propose, confirm and verify cases in application code | Write only after explicit confirmation |

Tools accept no customer IDs or URLs from the model. They close over the authorized session and cache repeated reads. Strict Pydantic validation requires the model to include every verified fact ID exactly once and provide a bounded answer. Additional checks reject new numeric claims, URLs, leaked credentials and unsupported action-completion language. These checks supplement instructions to stay within source evidence; they are not a proof of semantic equivalence. Conflicts and integration failures still stop the normal answer. Model text cannot change permissions, modify account records or create cases.

A typical inquiry makes three logical model calls: interpretation, the specialist tool request, and the specialist's grounded reply. The previous single-fact shortcut is removed so even account inquiries receive a Gemini-authored answer. Clarification and sensitive action confirmations remain controlled by the application.

LIVE_AI never invokes Reviewer after a model failure. Timeout, invalid output, missing configuration or provider errors emit ai.finished with failure and provider.unavailable, preserve an escalation record and return a clear operational error. The request is marked DEGRADED, but its error is not a successful answer and contains no substituted deterministic explanation. Explicit REVIEWER and configured DEGRADED modes retain deterministic behavior for offline evaluation.

HTTP 429 and authentication errors are not retried. Transient HTTP 408/500/502/503/504 responses have at most three SDK attempts with backoff and jitter, all within the stage deadline. AI_TIMEOUT controls each stage, with a 40-second maximum. The local Docker environment uses 15 seconds. A multi-stage request can take longer than one stage deadline. Lower reasoning effort remains enabled for supported Flash models; successful immediate answers cannot be guaranteed when the provider is slow or unavailable.

Execution events record agent runs, tool requests, tool returns, output validation and sanitized provider outcomes. No credential or raw provider output is included in telemetry. Source facts remain available in the response and execution trace separately from the generated answer.

Run `python tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json` to collect fresh live evidence. Scripted tests prove the control paths, not genuine model inference. Historical release evidence predates this reply change; consult the scoped hotfix evidence for current verification. No cloud deployment is claimed.

Final-reply format: after an authorized tool returns evidence, the ADK before-model callback requests application/json with the GroundedReply schema and disables further advertised tools for that response. The initial tool-selection request remains unconstrained so real tool calling still works. Validation failures emit agent.output_rejected with a controlled reason code (schema, fact selection, numeric claim, secret/URL or action claim); raw reply text is never included. Reference: [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).
