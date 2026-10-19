import httpx
from relay_api.domain.models import Chat


def test_mobile_data_query_uses_owned_mobile_legacy_record(stack):
    app = stack[0]
    session = app.login({"username": "jordan.lee", "password": "ReviewerPass-1002"})[1]
    result = app.chat(session, Chat(message="the mobile data is not working"))
    assert result["state"] == "RESOLVED"
    assert "Network service reports normal" in result["answer"]
    assert "subscriber active; network normal" in result["answer"]
    assert not app.store.escalations()
    assert not session.get("pending")
    events = app.store.trace_events(result["traceId"])
    assert any(
        e["eventType"] == "tool.finished"
        and e["component"] == "legacy-subscriber-status"
        and e["status"] == "success"
        for e in events
    )


def test_legacy_mobile_record_cannot_be_read_by_other_customer(stack, customer):
    app = stack[0]
    with httpx.Client(base_url=app.gateway.base, trust_env=False) as client:
        response = client.post(
            "/api/legacy/subscriber-status",
            content="<SubscriberStatusRequest><AccountNumber>ACC-2002</AccountNumber>"
            "<ServiceNumber>SVC-5002</ServiceNumber></SubscriberStatusRequest>",
            headers={
                "Authorization": "Bearer " + customer["enterpriseToken"],
                "Content-Type": "application/xml",
            },
        )
    assert response.status_code == 403
