import json
import time
import httpx
import pytest
from relay_api.domain.models import Chat
from relay_api.infrastructure.enterprise import IntegrationError, parse_legacy


def test_enterprise_requires_bearer_and_enforces_ownership(stack, customer):
    app, mock, _ = stack
    with httpx.Client(base_url=app.gateway.base, trust_env=False) as client:
        assert client.get("/api/accounts/ACC-2001").status_code == 401
        assert client.post("/api/diagnostics", json={"serviceId": "SVC-5001"}).status_code == 401
        headers = {"Authorization": "Bearer " + customer["enterpriseToken"]}
        assert client.get("/api/accounts/ACC-2001", headers=headers).status_code == 200
        assert client.get("/api/accounts/ACC-2002", headers=headers).status_code == 403
        assert client.get("/api/customers/CUST-1002", headers=headers).status_code == 403
        assert (
            client.post("/api/diagnostics", headers=headers, json={"serviceId": "SVC-5002"}).status_code
            == 403
        )
        assert (
            client.post(
                "/api/support-cases",
                headers=headers,
                json={
                    "accountId": "ACC-2002",
                    "customerId": "CUST-1002",
                    "summary": "case",
                    "idempotencyKey": "foreign",
                },
            ).status_code
            == 403
        )
        profile = client.get("/api/customers/CUST-1001", headers=headers).json()
        assert not {"testPassword", "username", "email"}.intersection(profile)
        mock.TOKENS[customer["enterpriseToken"]]["expires"] = 0
        assert client.get("/api/accounts/ACC-2001", headers=headers).status_code == 401


def test_enterprise_token_never_reaches_browser_or_events(stack):
    app, _, url = stack
    with httpx.Client(base_url=url, trust_env=False) as client:
        login = client.post("/api/login", json={"username": "alex.morgan", "password": "ReviewerPass-1001"})
        session = app.store.session(client.cookies.get("cx_session"))
        secret = session["enterpriseToken"]
        assert secret not in login.text
        assert secret not in client.get("/api/session").text
        assert client.post("/api/chat", json={"message": "my plan"}).json()["state"] == "RESOLVED"
        assert secret not in json.dumps(app.store.events())
        assert secret not in app.store.log_path.read_text()


def test_upstream_revocation_preserves_safe_handoff(stack, customer):
    app, mock, _ = stack
    mock.TOKENS.pop(customer["enterpriseToken"])
    result = app.chat(customer, Chat(message="my plan"))
    assert result["state"] == "ESCALATED" and not result["facts"]
    assert app.store.escalations()[-1][1]["reason"] == "customer-profile:http_401"


def test_chunked_body_limit_cannot_be_bypassed(stack):
    def chunks():
        yield b'{"message":"'
        yield b"x" * 9000
        yield b'"}'

    with httpx.Client(base_url=stack[2], trust_env=False) as client:
        result = client.post("/api/chat", content=chunks(), headers={"Content-Type": "application/json"})
        assert result.status_code == 413


def test_partial_verified_network_facts_survive_legacy_failure(stack, customer):
    app = stack[0]
    customer["failures"] = {"legacy": "unavailable"}
    result = app.chat(customer, Chat(message="My home internet is down"))
    assert result["state"] == "ESCALATED"
    record = app.store.escalations()[-1][1]
    assert any("Network service" in fact for fact in record["facts"])
    assert "diagnostics" in record["completedSteps"]
    assert "legacy-subscriber-status" in record["failedTools"][0]["component"]


@pytest.mark.parametrize("stamp", ["not-a-date", "2026-10-18T00:00:00"])
def test_legacy_requires_aware_timestamp(stamp):
    from test_integrations import xml

    with pytest.raises(IntegrationError, match="invalid_timestamp"):
        parse_legacy(xml(RESP_TS=stamp), "ACC-2001", "SVC-5001")


def test_agent_wall_clock_deadline_cancels_run(monkeypatch):
    import asyncio
    from relay_api.agents.runtime import AdkProvider

    provider = AdkProvider(model="test")

    async def slow(*args):
        await asyncio.sleep(10)

    monkeypatch.setattr(provider, "_run", slow)
    monkeypatch.setenv("AI_TIMEOUT", "0.1")
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        provider.run(None, {})
    assert time.monotonic() - start < 1


def test_expired_proposal_can_be_replaced_without_executing(stack, customer):
    app, mock, _ = stack
    first = app.chat(customer, Chat(message="Create a support case"))
    customer["pending"]["created"] = time.time() - 601
    app.store.save(customer)
    second = app.chat(customer, Chat(message="Create a support case"))
    assert second["pendingAction"]["id"] != first["pendingAction"]["id"]
    assert second["state"] == "AWAITING_CONFIRMATION" and not mock.CASES


def test_duplicate_json_fields_are_rejected_before_schema_validation():
    from relay_api.infrastructure.enterprise import unique_object

    with pytest.raises(ValueError, match="duplicate_json_field"):
        json.loads('{"accountId":"ACC-2001","accountId":"ACC-2002"}', object_pairs_hook=unique_object)


def test_backup_snapshot_preserves_wal_state_and_refuses_overwrite(tmp_path):
    import importlib.util
    import sqlite3
    from pathlib import Path

    module_path = Path(__file__).resolve().parents[2] / "tools/backup_database.py"
    spec = importlib.util.spec_from_file_location("backup_tool", module_path)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    source, snapshot = tmp_path / "live.sqlite", tmp_path / "backup.sqlite"
    with sqlite3.connect(source) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE claims (id TEXT)")
        db.execute("INSERT INTO claims VALUES ('confirmed')")
        db.commit()
        tool.backup(source, snapshot)
    with sqlite3.connect(snapshot) as db:
        assert db.execute("SELECT id FROM claims").fetchone()[0] == "confirmed"
    with pytest.raises(FileExistsError):
        tool.backup(source, snapshot)


def test_low_confidence_classification_clarifies_before_protected_read(stack, customer, monkeypatch):
    from relay_api.domain.models import Interpretation

    app = stack[0]
    monkeypatch.setattr(
        app.ai, "interpret", lambda _: Interpretation(intent="account", service="unknown", confidence=0.2)
    )
    result = app.chat(customer, Chat(message="maybe that thing"))
    assert result["state"] == "NEEDS_CLARIFICATION"
    assert not any(e["eventType"] == "tool.invoked" for e in app.store.trace_events(result["traceId"]))


def test_degraded_outage_disagreement_is_not_hidden(stack, customer):
    app, mock, _ = stack
    mock.OUTAGES[0]["status"] = "outage"
    result = app.chat(customer, Chat(message="My home internet is down"))
    assert result["state"] == "ESCALATED"
    assert app.store.escalations()[-1][1]["reason"] == "conflicting_or_unknown_network_status"


def test_unicode_invalid_password_returns_401_instead_of_transport_failure(stack):
    with httpx.Client(base_url=stack[2], trust_env=False) as client:
        result = client.post("/api/login", json={"username": "alex.morgan", "password": "incorrect-\u2603"})
        assert result.status_code == 401
        assert result.json()["error"] == "authentication_failed"
