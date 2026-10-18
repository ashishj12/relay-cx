# Rebuild verification

The Docker localhost origin issue is covered by test_local_origins.py and the final container verifier, which signs in, restores sessions, asks for a grounded plan, checks customer role restrictions and signs out on both localhost and 127.0.0.1. Wrong origins remain denied. The same-origin gateway also accepts configured HTTPS termination without trusting arbitrary forwarded headers.

The API uses native Google ADK Runner and LlmAgent implementations in agents/runtime.py. Tests execute actual ADK tool dispatch with a scripted model; genuine provider execution is recorded separately in live-gemini-evidence.json. The successful paced live run includes routing, read_account, diagnose_service, clarification and confirmed case creation. A separate Docker browser run visibly showed the router, account specialist and read_account. No model controls writes or record ownership.

The frontend groups auth, support, agents, operations, review and trace code by feature, with shared controls and ordered styles. The obsolete direct SDK runtime and unused fonts were removed. Evidence collection and case execution have separate application modules. Challenge inputs, runtime services, tests, deployment and tooling are separate.

Current verification: 91 backend tests, six frontend tests, all eight mandatory scenarios with 160 assertions, type checking, a production build, final Docker image checks, client/source credential scans and an isolated source installation. Final source was refreshed in that isolated environment without changing its dependency locks and all checks were repeated. Runtime file hashes in clean-verification.json match the delivered source. Browser verification is recorded as interaction/visual checking, separately from automated tests.

The UI PDF has ten pages with bookmarks and an index, plus source PNGs under docs/ui. Genuine live UI screenshots are also included. No demo video is included. Enterprise identity/data are synthetic, the deployment is single-process, Google Cloud setup is prepared rather than deployed, and qualification scores require independent evaluation.
