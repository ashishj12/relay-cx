import json
from pathlib import Path
from unittest.mock import Mock
import jsonschema
import pytest
from relay_api.domain.models import Chat
from relay_api.agents.runtime import AdkProvider
from relay_api.application.evidence import EvidenceBundle
from relay_api.domain.models import Interpretation
import asyncio


def provider(text):
    instance = AdkProvider(model="test-model")

    def run(agent, payload):
        if agent.tools:
            asyncio.run(agent.tools[0]())
        return text

    instance.run = Mock(side_effect=run)
    return instance


def test_real_sdk_request_and_validation():
    agent = provider('{"intent":"billing","service":"unknown","confidence":0.9}')
    assert agent.interpret(["my bill"]).intent == "billing"
    definition = agent.run.call_args.args[0]
    assert definition.model == "test-model"
    assert definition.generate_content_config.response_mime_type == "application/json"
    assert definition.generate_content_config.response_json_schema["additionalProperties"] is False
    assert "untrusted" in definition.instruction


def test_sdk_client_timeout_and_credential_configuration(monkeypatch):
    from google import genai

    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-placeholder")
    monkeypatch.setenv("AI_TIMEOUT", "3")
    factory = Mock(wraps=genai.Client)
    monkeypatch.setattr(genai, "Client", factory)
    AdkProvider().model()
    kwargs = factory.call_args.kwargs
    assert kwargs["http_options"].timeout == 3000
    assert kwargs["http_options"].retry_options.attempts == 1


def test_partial_failure_keeps_degraded_badge(stack, customer):
    app = stack[0]
    app.mode = "LIVE_AI"
    app.ai = Mock()
    app.ai.interpret.side_effect = TimeoutError()
    app.ai.select.return_value = [0]
    assert app.chat(customer, Chat(message="my plan"))["mode"] == "DEGRADED"


def test_live_success_with_validated_double(stack, customer):
    from test_adk_agents import ScriptedModel, answer, tool

    app = stack[0]
    app.mode = "LIVE_AI"
    app.ai = AdkProvider(
        model=ScriptedModel(
            model="scripted",
            replies=[
                answer({"intent": "account", "service": "unknown", "confidence": 0.9}),
                tool("read_account"),
                answer({"fact_ids": [0]}),
            ],
        )
    )
    result = app.chat(customer, Chat(message="my plan"))
    assert result["mode"] == "LIVE_AI" and "Fiber 500" in result["answer"]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not json",
        "{}",
        '{"intent":"account","service":"unknown","confidence":2}',
        '{"intent":"account","service":"unknown","confidence":0.9,"accountId":"ACC-2002"}',
    ],
)
def test_invalid_gemini_output(text):
    with pytest.raises(ValueError):
        provider(text).interpret(["my plan"])


@pytest.mark.parametrize("text", ['{"fact_ids":[0,0]}', '{"fact_ids":[5]}', '{"fact_ids":[]}'])
def test_grounded_selection_rejects_fabrication(text):
    with pytest.raises(ValueError):
        provider(text).gather(
            Interpretation(intent="account", service="unknown", confidence=1.0),
            lambda: EvidenceBundle(["verified"]),
        )


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("timeout"),
        ValueError("malformed"),
        RuntimeError("rate_limit"),
        RuntimeError("invalid_credentials"),
    ],
)
def test_live_provider_fallback(stack, customer, failure):
    app, _, _ = stack
    app.mode = "LIVE_AI"
    app.ai = Mock()
    app.ai.interpret.side_effect = failure
    app.ai.select.side_effect = failure
    r = app.chat(customer, Chat(message="my plan"))
    assert r["mode"] == "DEGRADED" and "Fiber 500" in r["answer"]
    assert (
        len(
            [
                e
                for e in app.store.events()
                if e["traceId"] == r["traceId"]
                and e["eventType"] == "ai.finished"
                and e["status"] == "failure"
            ]
        )
        == 2
    )


def test_missing_live_configuration(stack, customer, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    app = stack[0]
    app.mode = "LIVE_AI"
    app.ai = AdkProvider()
    assert app.chat(customer, Chat(message="my plan"))["mode"] == "DEGRADED"


def test_degraded_mode(stack, customer):
    app = stack[0]
    app.mode = "DEGRADED"
    assert app.chat(customer, Chat(message="my plan"))["mode"] == "DEGRADED"


def test_event_schema_metrics_redaction(stack, customer):
    app = stack[0]
    app.chat(customer, Chat(message="my plan password=super-secret ReviewerPass-1001"))
    app.chat(customer, Chat(message="Show ACC-2002 plan"))
    app.chat(customer, Chat(message="escalate to human"))
    root = Path(__file__).resolve().parents[2] / "resources/challenge/schemas"
    events = app.store.events()
    schema = json.loads((root / "telemetry-event.schema.json").read_text())
    for event in events:
        jsonschema.validate(event, schema)
    for _, e in app.store.escalations():
        jsonschema.validate(e, json.loads((root / "escalation-record.schema.json").read_text()))
    m = app.store.metrics()
    assert m["requests"] == 3 and m["sessions"] == 1 and m["resolutionRate"] == pytest.approx(1 / 3)
    assert m["authorizationDenials"] == 1 and m["escalationRate"] == pytest.approx(1 / 3)
    assert m["toolSuccessRate"] == 1 and m["authenticationFailures"] == 0
    serialized = json.dumps(events) + json.dumps(customer)
    assert "super-secret" not in serialized and "ReviewerPass-1001" not in serialized
    assert "accessToken" not in serialized and "testPassword" not in serialized
    traces = {e["traceId"] for e in events if e["eventType"] == "request.received"}
    for trace in traces:
        assert any(e["traceId"] == trace and e["eventType"] == "request.finished" for e in events)
