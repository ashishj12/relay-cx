import httpx
import pytest
from relay_api.core.origins import origin_allowed

@pytest.mark.parametrize("host", ["localhost", "127.0.0.1"])
def test_login_accepts_local_browser_alias(stack, monkeypatch, host):
    monkeypatch.setenv("PUBLIC_ORIGIN", "http://127.0.0.1:3000")
    with httpx.Client(base_url=stack[2], trust_env=False) as client:
        response = client.post(
            "/api/login",
            json={"username": "alex.morgan", "password": "ReviewerPass-1001"},
            headers={"Origin": f"http://{host}:3000"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["roles"] == ["customer"] and payload["accountId"] == "ACC-2001"
        assert isinstance(payload["history"], list)
        assert client.get("/api/session").json() == payload
        assert client.get("/api/agents").json()["framework"] == "google-adk"
        assert client.get("/api/activity").status_code == 200

@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3001",
        "http://localhost.evil:3000",
        "https://localhost:3000",
        "null",
        "http://user@localhost:3000",
        "http://localhost:3000/path",
    ],
)
def test_other_origins_remain_denied(origin):
    assert not origin_allowed(origin, "http://127.0.0.1:3000")


def test_production_origin_remains_exact():
    assert origin_allowed("https://relay.example", "https://relay.example")
    assert not origin_allowed("https://www.relay.example", "https://relay.example")

def test_activity_cannot_read_other_customer_events(stack):
    with (
        httpx.Client(base_url=stack[2], trust_env=False) as first,
        httpx.Client(base_url=stack[2], trust_env=False) as second,
    ):
        first.post("/api/login", json={"username": "alex.morgan", "password": "ReviewerPass-1001"})
        second.post("/api/login", json={"username": "jordan.lee", "password": "ReviewerPass-1002"})
        trace = first.post("/api/chat", json={"message": "my plan"}).json()["traceId"]
        assert any(event["traceId"] == trace for event in first.get("/api/activity").json())
        assert not any(event["traceId"] == trace for event in second.get("/api/activity").json())
