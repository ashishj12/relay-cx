import pytest
from relay_api.agents.runtime import AdkProvider


@pytest.mark.parametrize(
    "name,level,budget",
    [("gemini-3.6-flash", "minimal", None), ("gemini-3.8-flash", "low", None), ("gemini-2.5-flash", None, 0)],
)
def test_low_latency_config_matches_model_capabilities(name, level, budget):
    config = AdkProvider(model=name).generation_config()
    assert config.temperature is None
    actual = config.thinking_config.thinking_level
    assert (actual.value.lower() if actual is not None else None) == level
    assert config.thinking_config.thinking_budget == budget


def test_single_account_fact_still_requires_actual_authorized_tool(stack, customer):
    from test_adk_agents import ScriptedModel, answer, tool
    from relay_api.domain.models import Chat

    service = stack[0]
    service.mode = "LIVE_AI"
    model = ScriptedModel(
        model="scripted",
        replies=[
            answer({"intent": "account", "service": "unknown", "confidence": 1.0}),
            tool("read_account"),
            answer(
                {
                    "fact_ids": [0],
                    "answer": "Your plan is Fiber 500; monthly plan price 79.99; account status active.",
                }
            ),
        ],
    )
    service.ai = AdkProvider(model=model)
    result = service.chat(customer, Chat(message="What is my plan?"))
    assert result["mode"] == "LIVE_AI" and "Fiber 500" in result["answer"]
    assert not model.replies
    events = service.store.trace_events(result["traceId"])
    assert any(
        e["eventType"] == "agent.tool_requested" and e["metadata"]["tool"] == "read_account" for e in events
    )
    assert any(
        e["eventType"] == "agent.output_validated"
        and e["metadata"].get("strategy") == "grounded_customer_reply"
        for e in events
    )
    assert sum(e["eventType"] == "tool.invoked" and e["component"] == "account-service" for e in events) == 1
