from relay_api.ai.providers import Reviewer
from relay_api.domain.models import Chat


def test_dropping_connection_does_not_reuse_previous_billing_intent():
    result = Reviewer().interpret(
        [
            "whats my data plan and last months bill?",
            "My internet keeps dropping since yesterday.",
        ]
    )
    assert result.intent == "network"
    assert result.service == "home-internet"


def test_latest_service_correction_overrides_earlier_service():
    result = Reviewer().interpret(["my home internet is down", "Actually I meant mobile"])
    assert result.intent == "network" and result.service == "mobile"


def test_new_explicit_intent_overrides_earlier_intent():
    result = Reviewer().interpret(["show my billing details", "what is my current plan?"])
    assert result.intent == "account"


def test_wrong_service_clarification_can_resume_on_owned_service(stack):
    app = stack[0]
    session = app.login({"username": "jordan.lee", "password": "ReviewerPass-1002"})[1]
    assert app.chat(session, Chat(message="my home internet is down"))["state"] == "NEEDS_CLARIFICATION"
    result = app.chat(session, Chat(message="Actually I meant mobile"))
    assert result["state"] == "RESOLVED" and "subscriber active" in result["answer"]


def test_followup_retains_previous_request_context(stack, customer):
    app = stack[0]
    app.chat(customer, Chat(message="show my billing details"))
    result = app.chat(customer, Chat(message="can you check that again?"))
    assert result["state"] == "RESOLVED" and "Billing service" in result["answer"]


def test_enterprise_failure_explains_dependency_to_customer(stack, customer):
    app = stack[0]
    customer["failures"] = {"billing": "unavailable"}
    result = app.chat(customer, Chat(message="show my bill"))
    assert result["state"] == "ESCALATED"
    assert "billing" in result["answer"].lower() and "unavailable" in result["answer"].lower()
    assert result["escalationId"] in result["answer"]
