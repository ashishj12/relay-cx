import httpx
import pytest


@pytest.mark.parametrize(
    "payload",
    [
        {"customerId": None, "accountId": None, "summary": "test", "idempotencyKey": "missing-owner"},
        {"customerId": "CUST-1001", "accountId": "ACC-2001", "summary": "test", "idempotencyKey": []},
        [],
    ],
)
def test_private_case_api_rejects_missing_or_malformed_identity(stack, customer, payload):
    app, mock, _ = stack
    with httpx.Client(base_url=app.gateway.base, trust_env=False) as c:
        result = c.post(
            "/api/support-cases",
            json=payload,
            headers={"Authorization": "Bearer " + customer["enterpriseToken"]},
        )
    assert result.status_code == 400
    assert not mock.CASES


@pytest.mark.parametrize("payload", [{"serviceId": None}, {"serviceId": []}, []])
def test_private_diagnostics_requires_valid_service_parameter(stack, customer, payload):
    with httpx.Client(base_url=stack[0].gateway.base, trust_env=False) as c:
        result = c.post(
            "/api/diagnostics",
            json=payload,
            headers={"Authorization": "Bearer " + customer["enterpriseToken"]},
        )
    assert result.status_code == 400


def test_whitespace_chat_is_rejected_before_model_or_tools(stack):
    app, _, url = stack
    with httpx.Client(base_url=url, trust_env=False) as c:
        c.post(
            "/api/login", json={"username": "alex.morgan", "password": "ReviewerPass-1001"}
        ).raise_for_status()
        before = len(app.store.events())
        assert c.post("/api/chat", json={"message": "   \n  "}).status_code == 400
    assert not any(e["eventType"] in {"agent.invoked", "tool.invoked"} for e in app.store.events()[before:])


def test_unauthenticated_post_returns_401_without_connection_reset(stack):
    with httpx.Client(base_url=stack[0].gateway.base, trust_env=False) as c:
        for _ in range(5):
            response = c.post("/api/diagnostics", json={"serviceId": "SVC-5001"})
            assert response.status_code == 401
