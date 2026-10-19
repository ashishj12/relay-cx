# Changes from the supplied starter and updated archive

The supplied starter under `resources/challenge/starter-solution/` remains as provenance. Its synthetic records, XML service contract, event schema and eight scenario definitions remain unchanged. The runnable implementation uses those records through real HTTP adapters rather than importing final answers.

The updated archive retained the modular Python API, Next.js/TypeScript/Bun UI, ADK agents, action confirmation and SQLite event pipeline. Its frontend design is preserved in this release. Git history, installed dependencies, caches, runtime databases and inherited verification results are excluded from the submission.

This review closes an enterprise authentication gap: opaque synthetic bearer identities now accompany protected requests and the upstream services check identity, expiry and record ownership independently. Bearers remain server-side and are removed from customer profiles, browser contracts and event payloads. New tests exercise direct service calls, cross-customer diagnostics/case attempts and upstream revocation.

Agent stages now have a bounded wall-clock deadline in addition to an LLM call limit. The API enforces its body limit on streamed/chunked requests as well as declared lengths. External record types are strict and bounded; legacy timestamps must be timezone-aware. Verified partial network facts and prior evidence survive a downstream failure in the handoff. Trace lookups use indexed, owner-filtered SQL rather than loading all events.

Missing challenge source, requirement matrix, handover and operational instructions are restored. Verification results are regenerated from this source. Every requirement is mapped to source/test/scenario evidence with explicit limits. Local tests do not establish an independent review score or prove cloud deployment. The demo video remains excluded by the user's earlier instruction.

Browser verification caught and fixed a navigation regression in the updated UI: support conversations unmounted when opening Agent Studio, losing visible history and approval state. The conversation now stays mounted while other views are inspected, preserving in-flight requests, drafts, messages and pending approval. The health label now describes workspace liveness rather than implying every integration is available.

Synthetic credential comparison uses UTF-8 bytes so an incorrect Unicode password produces a controlled 401 rather than a transport failure. The regression is covered through the real login API.
