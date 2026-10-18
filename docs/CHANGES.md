# Rebuild notes

The Docker login failure came from configuring the API for 127.0.0.1 while opening the frontend on localhost. Local HTTP loopback aliases now share the configured port policy; deployed domains require their exact origin. Wrong ports, foreign domains and deceptive hostname suffixes remain rejected. Login returns a complete validated session in one response. Frontend restoration ignores stale responses and exposes failures before rendering the workspace.

The frontend is organized by product feature: authentication, support, agents, review, operations and traces. Shared components are small and API contracts are typed. The new visual system uses locally bundled DM Sans and Newsreader, warm neutral surfaces, cobalt controls, clear forms and a conversation-focused workspace. Aceternity Parley, Twain, FieldRank and ToDesktop informed composition and product clarity; no site artwork or assets were copied. Layouts adapt to mobile, respect reduced motion and preserve keyboard-native dialogs.

Google ADK now executes the live router and specialist tools. Agent Studio exposes configured scope and recorded execution. The customer activity panel reads actual persisted events while requests run. The API separates evidence collection, case actions, authorized enterprise adapters and storage. The original challenge fixtures and contracts remain under resources/challenge, alongside preserved starter provenance.

Current execution evidence is regenerated for this rebuild. Mock enterprise records remain synthetic; single-process SQLite deployment, internal handoff storage and undeployed Google Cloud configuration are explicit boundaries. Independent challenge scoring is not claimed. The demo video is excluded by request.
