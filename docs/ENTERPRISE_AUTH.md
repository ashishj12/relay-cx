# Enterprise authentication extension

The original supplied OpenAPI and XML contracts remain unchanged under resources/challenge. The runnable synthetic service adds bearer authentication and record-ownership checks around those same paths. `/health` and `/api/auth/login` are the only unauthenticated endpoints. A successful synthetic login returns an opaque random `accessToken` with a bounded lifetime. Protected JSON and XML calls require `Authorization: Bearer <token>`; missing/expired tokens return 401 and foreign account/customer/service/postal-code scopes return 403.

The gateway retains this token only in server-side session storage and sends it in headers to the configured fixed enterprise origin. It never becomes a model argument, browser field or trace value. Bearer/header failures are sanitized categories. The browser receives a separate opaque cookie, indexed server-side by its SHA-256 digest. The profile response excludes testPassword, username and email.

Synthetic bearer/case stores are intentionally in process memory; restarting the mock invalidates bearer sessions and loses its case index. API action state remains durable; an interrupted or uncertain write cannot automatically reissue even after restart. Log in again after a mock restart. A real deployment needs federated identity, renewable scoped credentials, TLS/private transport and durable upstream idempotency/reconciliation.

Regression tests: `test_enterprise_requires_bearer_and_enforces_ownership`, `test_enterprise_token_never_reaches_browser_or_events`, `test_upstream_revocation_preserves_safe_handoff` in tests/integration/test_release_hardening.py.
