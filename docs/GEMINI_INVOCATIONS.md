# Gemini invocation register

LIVE_AI uses native Google ADK LlmAgent and Runner components with the Gemini Developer API. The API key and model come from ignored local environment settings; no customer, account or service identifier is accepted from a model tool argument.

| Stage | Actual invocation | Data supplied | Authority |
|---|---|---|---|
| Interpretation | request_router | Last four redacted customer messages | Validated intent, service and confidence only |
| Evidence retrieval | account_agent, billing_agent or service_agent | Validated route and the current question | A single read-only tool closes over the authenticated account |
| Reply | Same specialist after its tool returns | Verified fact IDs and approved factual paragraphs | Choose a verified answer; no new factual wording |

The final structured schema enumerates answers composed from the current verified records. The model must return every fact ID and the factual paragraphs unchanged, optionally with an approved introduction. A separate backend validator checks the same contract. This is intentionally extractive: unrestricted prose cannot be proven grounded merely by checking its numbers or attaching source IDs. Model interpretation and native tool calling remain mandatory in normal LIVE_AI inquiries. An invalid or missing model reply stops the answer and saves an escalation; no Reviewer answer is substituted.

Explicit customer controls do not need AI authority. Sign-in, ownership, human-review requests, unsupported-operation refusals and confirmed case execution are deterministic. Human support therefore remains usable when the model is unavailable. Reviewer mode replaces only interpretation and fact ordering; it still runs actual HTTP adapters, validation, actions and telemetry.

A normal inquiry uses interpretation, specialist tool selection and final structured reply. Each ADK run is capped at three LLM calls and a 40-second maximum stage deadline. SDK transport attempts are limited to three for transient 408/5xx errors; 429 and authentication errors are not retried. Queue admission is separately bounded, with eight admitted workflows and two-second waits for capacity/account ownership. Different accounts can progress independently. Provider callback state is request-local.

Events record actual agent/tool execution and sanitized rejection categories. Account, price, bill-period and service fields appear in allowlisted trace summaries; credentials and raw model output do not. Logs do not claim that a scripted test is actual Gemini inference.

Run `python tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json` for real-provider proof. A quota error is a failed live verification, even when all controlled-model and offline scenarios pass. GCP credit is not required for Reviewer mode. Availability and billing of the configured Gemini project must be checked separately.
