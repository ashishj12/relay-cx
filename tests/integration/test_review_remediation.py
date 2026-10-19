import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock
import httpx
import pytest
from relay_api.agents.runtime import AdkProvider
from relay_api.ai.providers import redact
from relay_api.domain.models import Chat, Confirmation
from relay_api.infrastructure.enterprise import IntegrationError
from relay_api.infrastructure.storage import WorkflowBusy
from test_adk_agents import ScriptedModel, answer, tool


@pytest.mark.parametrize(
    "prose",
    [
        "Your plan includes unlimited international roaming.",
        "Your monthly plan price is 500.",
        "Your plan is Fiber 500; monthly plan price 500; account status active.",
        "Your plan is Fiber 500; monthly plan price 79.99; account status suspended.",
    ],
)
def test_unsupported_prose_never_reaches_customer(stack, customer, prose):
    service = stack[0]
    service.mode = "LIVE_AI"
    service.ai = AdkProvider(
        model=ScriptedModel(
            model="controlled",
            replies=[
                answer({"intent": "account", "service": "unknown", "confidence": 1.0}),
                tool("read_account"),
                answer({"fact_ids": [0], "answer": prose}),
            ],
        )
    )
    response = service.chat(customer, Chat(message="What is my plan?"))
    assert response["state"] == "ESCALATED"
    assert response["mode"] == "DEGRADED"
    assert prose not in response["answer"]
    assert response["escalationId"] in response["answer"]
    assert not any(
        e["eventType"] == "provider.fallback" for e in service.store.trace_events(response["traceId"])
    )


@pytest.mark.parametrize(
    "text",
    [
        "My password is SYNTHETIC_CANARY.",
        "password=SYNTHETIC_CANARY",
        "the token was SYNTHETIC_CANARY",
        "api key: SYNTHETIC_CANARY",
        "my passcode equals SYNTHETIC_CANARY",
    ],
)
def test_natural_language_secret_is_removed(text):
    assert "SYNTHETIC_CANARY" not in redact(text)


def test_uncertain_case_is_not_repeated_after_fresh_login(stack, customer):
    service, mock, _ = stack
    proposed = service.chat(customer, Chat(message="Create a support case for my internet issue."))
    original = service.gateway.create_case

    def lose_receipt(*args, **kwargs):
        original(*args, **kwargs)
        raise IntegrationError("case-management", "transport_or_timeout", True)

    service.gateway.create_case = lose_receipt
    result = service.confirm(customer, Confirmation(actionId=proposed["pendingAction"]["id"], confirm=True))
    assert result["state"] == "ESCALATED" and len(mock.CASES) == 1
    service.gateway.create_case = original
    second = service.login({"username": "alex.morgan", "password": "ReviewerPass-1001"})[1]
    assert second["pending"]["id"] == proposed["pendingAction"]["id"]
    assert second["pending"]["status"] == "uncertain"
    assert second["history"] == customer["history"]
    retry = service.chat(second, Chat(message="Create a support case for my internet issue."))
    assert retry["state"] == "RESOLVED" and len(mock.CASES) == 1
    assert retry["caseId"] in mock.CASES
    replay = service.confirm(second, Confirmation(actionId=second["pending"]["id"], confirm=True))
    assert replay["state"] == "RESOLVED" and replay["caseId"] == retry["caseId"] and len(mock.CASES) == 1


def test_human_support_does_not_depend_on_ai(stack):
    service, _, url = stack
    service.mode = "LIVE_AI"
    service.ai = Mock(side_effect=AssertionError("human request must not invoke AI"))
    service.ai.interpret.side_effect = AssertionError("human request must not invoke AI")
    with httpx.Client(base_url=url, trust_env=False) as client:
        assert client.post("/api/handoff", json={}).status_code == 401
        client.post(
            "/api/login", json={"username": "jordan.lee", "password": "ReviewerPass-1002"}
        ).raise_for_status()
        result = client.post("/api/handoff", json={})
        result.raise_for_status()
        reply = result.json()
        assert reply["state"] == "ESCALATED"
        assert reply["escalationId"] in reply["answer"]
        assert "does not contact a live support team" in reply["answer"]
        assert "No response time" in reply["answer"]
        service.ai.interpret.assert_not_called()


def test_different_customers_do_not_share_a_workflow_lock(stack, customer):
    service = stack[0]
    second = service.login({"username": "jordan.lee", "password": "ReviewerPass-1002"})[1]
    entered, release = threading.Event(), threading.Event()

    def hold_first():
        with service.store.workflow(customer):
            entered.set()
            assert release.wait(5)

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(hold_first)
        assert entered.wait(2)
        try:
            result = pool.submit(service.chat, second, Chat(message="my plan")).result(timeout=2)
            assert result["state"] == "RESOLVED" and "Mobile Unlimited" in result["answer"]
            with pytest.raises(WorkflowBusy):
                with service.store.workflow(customer, wait=0.05):
                    pass
        finally:
            release.set()
        first.result()


def test_unsupported_change_never_opens_a_case_or_claims_success(stack, customer):
    service, mock, _ = stack
    reply = service.chat(customer, Chat(message="can you add international roaming to my plan?"))
    assert reply["state"] == "NEEDS_CLARIFICATION"
    assert "I can't change your plan" in reply["answer"]
    assert "Nothing has been changed" in reply["answer"]
    assert not mock.CASES and not reply.get("pendingAction")


def test_reauthentication_restores_context_after_expiry(stack, customer, monkeypatch):
    service = stack[0]
    service.chat(customer, Chat(message="My internet is slow"))
    token, fresh = service.login({"username": "alex.morgan", "password": "ReviewerPass-1001"})
    assert fresh["history"] == customer["history"]
    import relay_api.infrastructure.storage as storage

    original = time.time
    monkeypatch.setattr(storage.time, "time", lambda: original() + 86401)
    assert service.store.session(token) is None
    next_day = service.login({"username": "alex.morgan", "password": "ReviewerPass-1001"})[1]
    assert next_day["messages"] == customer["messages"]
    assert next_day["history"] == customer["history"]


def test_typed_human_request_and_unsupported_booking_do_not_require_ai(stack, customer):
    service = stack[0]
    service.mode = "LIVE_AI"
    service.ai = Mock()
    service.ai.interpret.side_effect = AssertionError("control request must not depend on AI")
    reply = service.chat(customer, Chat(message="can i speak to a person please"))
    assert reply["state"] == "ESCALATED" and reply["escalationId"] in reply["answer"]
    reply = service.chat(customer, Chat(message="can you book me a taxi to the airport?"))
    assert "I can't book taxis" in reply["answer"]
    assert "No booking has been made" in reply["answer"]
    service.ai.interpret.assert_not_called()


def test_prior_owned_trace_remains_readable_after_reauthentication(stack, customer):
    service = stack[0]
    result = service.chat(customer, Chat(message="my plan"))
    second = service.login({"username": "alex.morgan", "password": "ReviewerPass-1001"})[1]
    other = service.login({"username": "jordan.lee", "password": "ReviewerPass-1002"})[1]
    assert service.store.trace_events(result["traceId"], second["id"])
    assert not service.store.trace_events(result["traceId"], other["id"])


@pytest.mark.parametrize(
    "text",
    [
        "My password is a SYNTHETIC_CANARY phrase. Please check my bill.",
        'password="a SYNTHETIC_CANARY phrase"',
        "my token is first.SYNTHETIC_CANARY.signature. Please help.",
    ],
)
def test_passphrases_and_dotted_tokens_are_not_partially_redacted(text):
    assert "SYNTHETIC_CANARY" not in redact(text)


def test_combined_plan_and_bill_question_covers_both_with_the_actual_period(stack):
    service = stack[0]
    customer = service.login({"username": "jordan.lee", "password": "ReviewerPass-1002"})[1]
    reply = service.chat(customer, Chat(message="whats my data plan and last months bill?"))
    assert reply["state"] == "RESOLVED"
    assert "Mobile Unlimited" in reply["answer"] and "2026-09" in reply["answer"]
    assert "65.00" in reply["answer"]


def test_busy_request_has_a_bounded_wait_a_trace_and_no_side_effect(stack, customer):
    service, mock, url = stack
    with httpx.Client(base_url=url, trust_env=False, timeout=6) as client:
        client.post(
            "/api/login", json={"username": "alex.morgan", "password": "ReviewerPass-1001"}
        ).raise_for_status()
        with service.store.workflow(customer):
            started = time.monotonic()
            response = client.post("/api/chat", json={"message": "my plan"})
            assert response.status_code == 503 and time.monotonic() - started < 5
            assert response.json()["error"] == "request_busy"
            events = service.store.trace_events(response.json()["traceId"])
            assert any(
                event["eventType"] == "request.finished" and event["status"] == "failure" for event in events
            )
            assert not mock.CASES
        assert client.post("/api/chat", json={"message": "my plan"}).json()["state"] == "RESOLVED"


def test_tool_trace_contains_the_actual_normalized_bill_without_credentials(stack, customer):
    service = stack[0]
    result = service.chat(customer, Chat(message="my bill"))
    event = next(
        event
        for event in service.store.trace_events(result["traceId"])
        if event["eventType"] == "tool.finished" and event["component"] == "billing"
    )
    record = event["metadata"]["outputSummary"]["record"]
    assert record["total"] == 84.99 and record["period"] == "2026-09"
    assert record["accountId"] == customer["accountId"]
    assert "accessToken" not in str(event) and "password" not in str(event)
