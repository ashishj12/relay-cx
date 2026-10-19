import pytest
from relay_api.agents.runtime import AdkProvider
from relay_api.domain.models import Chat


@pytest.mark.parametrize("live", [False, True])
def test_mobile_query_on_home_account_explains_service_scope(stack, customer, live):
    app = stack[0]
    if live:
        from test_adk_agents import ScriptedModel, answer, tool

        app.mode = "LIVE_AI"
        app.ai = AdkProvider(
            model=ScriptedModel(
                model="scripted",
                replies=[
                    answer({"intent": "network", "service": "mobile", "confidence": 1.0}),
                    tool("diagnose_service"),
                    # Exhausting the model also proves the known ownership result survives
                    # a provider failure while it is handling the rejected tool request.
                ],
            )
        )
    result = app.chat(customer, Chat(message="mobile data is not working"))
    assert result["state"] == "NEEDS_CLARIFICATION"
    assert "home internet" in result["answer"] and "no mobile service" in result["answer"]
    assert "sign in with the account that owns it" in result["answer"]
    assert not app.store.escalations()
    assert not result["facts"] and not customer.get("pending")
    events = app.store.trace_events(result["traceId"])
    assert not any(
        e["eventType"] == "tool.invoked"
        and e["component"] in {"diagnostics", "legacy-subscriber-status", "network-outage"}
        for e in events
    )
    assert not any(e["eventType"] == "provider.fallback" for e in events)
