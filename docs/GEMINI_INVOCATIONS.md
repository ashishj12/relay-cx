# Google ADK invocation register

Live mode uses google-adk 2.12.0 with the official Gemini model adapter. The configured model is recorded in ai.finished events. Root .env is ignored and excluded from archives. No credential, raw prompt, tool arguments or raw provider output is returned in telemetry.

| Agent | Input and behavior | Output validation | Authority |
|---|---|---|---|
| request_router | Up to four redacted customer messages; classify telecom intent and explicitly stated service | Native JSON schema plus strict Interpretation Pydantic validation | No tools or customer identifiers |
| account_agent | Account intent; calls read_account | Exact permutation of returned verified fact IDs | Read only, authenticated account |
| billing_agent | Billing intent; calls read_billing | Same Selection validation | Read only, authenticated account |
| service_agent | Network or legacy intent; calls diagnose_service | Same Selection validation | Read only, authorized service |
| action_controller | Deterministic application component; never an LLM agent | Exact action binding, expiry, reauthorization, durable claim, backend receipt | Case write only after explicit confirmation |

Source: agents/runtime.py, agents/catalog.py, application/evidence.py and application/case_actions.py. Each ADK Runner has an ephemeral session, a maximum of three model calls, an overall timeout and one SDK attempt per call. Durable customer history, identity, actions and traces belong to the application's SQLite store. Each tool accepts no IDs or URLs and closes over an already authorized request. Repeated tool calls reuse the same evidence. Raw enterprise values cannot become instructions or authorize writes. Only normalized facts reach fact selection; the renderer uses those original facts.

agent.invoked, agent.run_started, agent.tool_requested, agent.tool_returned and agent.run_finished events expose real execution. Agent Studio distinguishes configured capabilities from recorded invocations. Reviewer mode shares enterprise adapters and workflow controls but explicitly simulates interpretation and ordering; it does not emit successful live agent runs.

Provider errors, invalid schemas, skipped tools, incomplete fact permutations and quota errors produce visible DEGRADED mode and sanitized reasons. Tools do not retry unsafe writes. The live evaluator requires successful unsimulated model stages, actual ADK tools, clarification and confirmed case creation. LIVE_EVALUATION_PAUSE optionally paces live requests for low provider quotas; it does not change failure criteria.

Run python tools/evaluate.py --mode LIVE_AI --output evidence/current/live-gemini-evidence.json. A doubled model in tests is not evidence of genuine Gemini inference. Inspect current evidence for provider availability and execution status.
