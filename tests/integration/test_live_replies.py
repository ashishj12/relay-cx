from unittest.mock import patch
import pytest
from relay_api.agents.runtime import AdkProvider
from relay_api.ai.providers import Reviewer
from relay_api.domain.models import Chat


@pytest.mark.parametrize(
    "answer", ["Your bill is 999.00.", "Your connection is fixed.", "Visit https://example.com."]
)
def test_live_reply_rejects_unsupported_claims(answer):
    with pytest.raises(ValueError):
        AdkProvider.validate_reply(answer, ["Plan price 79.99; network normal."])


def test_live_failure_never_calls_deterministic_reviewer(stack, customer):
    from test_adk_agents import ScriptedModel, answer, tool

    app = stack[0]
    app.mode = "LIVE_AI"
    app.ai = AdkProvider(
        model=ScriptedModel(
            model="scripted",
            replies=[
                answer({"intent": "account", "service": "unknown", "confidence": 1.0}),
                tool("read_account"),
                answer({"fact_ids": [0], "answer": "Your account costs 999.00."}),
            ],
        )
    )
    with (
        patch.object(Reviewer, "interpret", side_effect=AssertionError("fallback forbidden")),
        patch.object(Reviewer, "select", side_effect=AssertionError("fallback forbidden")),
    ):
        result = app.chat(customer, Chat(message="What is my plan?"))
    assert result["state"] == "ESCALATED"
    assert result["mode"] == "DEGRADED"
    assert "I haven't changed your account" in result["answer"]
    assert "999.00" not in result["answer"]
    events = app.store.trace_events(result["traceId"])
    assert not any(e["eventType"] == "provider.fallback" for e in events)
    assert any(e["eventType"] == "provider.unavailable" for e in events)


def test_customer_sees_model_reply_instead_of_joined_facts(stack):
    from test_adk_agents import ScriptedModel, answer, tool

    app = stack[0]
    session = app.login({"username": "jordan.lee", "password": "ReviewerPass-1002"})[1]
    app.mode = "LIVE_AI"
    expected = (
        "I checked the information available for your account.\n\n"
        "Network status: normal; incident none.\n\n"
        "Diagnostics: no_device_fault_detected.\n\n"
        "Subscriber record: subscriber active; network normal; observed 2026-10-13T08:30:00Z."
    )
    app.ai = AdkProvider(
        model=ScriptedModel(
            model="scripted",
            replies=[
                answer({"intent": "network", "service": "mobile", "confidence": 1.0}),
                tool("diagnose_service"),
                answer({"fact_ids": [0, 1, 2], "answer": expected}),
            ],
        )
    )
    result = app.chat(session, Chat(message="the mobile data is not working"))
    assert result["mode"] == "LIVE_AI"
    assert result["answer"] == expected
    assert len(result["facts"]) == 3
    assert not app.ai._model.replies


@pytest.mark.parametrize("reply", ["Your case CASE-FAAA is open.", "Your account is ACC-500."])
def test_live_reply_rejects_unverified_references_even_when_numbers_match(reply):
    with pytest.raises(ValueError, match="unsupported_reference_claim"):
        AdkProvider.validate_reply(reply, ["Your plan is Fiber 500. Network status is normal."])


def test_live_reply_allows_reference_returned_by_actual_evidence():
    AdkProvider.validate_reply(
        "Network incident INC-9001 is degraded.", ["Network incident INC-9001 is degraded."]
    )
