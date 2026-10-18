"""Run real ADK Runner/tool dispatch with a scripted model, without network access."""

from collections.abc import AsyncGenerator
import json
from google.adk.models import BaseLlm, LlmResponse
from google.genai import types
from relay_api.agents.runtime import AdkProvider
from relay_api.domain.models import Chat


class ScriptedModel(BaseLlm):
    replies: list[types.Content]

    async def generate_content_async(self, llm_request, stream=False) -> AsyncGenerator[LlmResponse, None]:
        if not self.replies:
            raise AssertionError("Agent exceeded its expected model calls")
        yield LlmResponse(content=self.replies.pop(0))


def answer(value):
    return types.Content(role="model", parts=[types.Part(text=json.dumps(value))])


def tool(name):
    return types.Content(
        role="model", parts=[types.Part(function_call=types.FunctionCall(name=name, args={}))]
    )


def test_adk_runner_calls_authorized_account_tool(stack, customer):
    service, mock, _ = stack
    service.mode = "LIVE_AI"
    model = ScriptedModel(
        model="scripted",
        replies=[
            answer({"intent": "account", "service": "unknown", "confidence": 1.0}),
            tool("read_account"),
            answer({"fact_ids": [0]}),
        ],
    )
    service.ai = AdkProvider(model=model)
    result = service.chat(customer, Chat(message="What is my plan?"))
    assert result["mode"] == "LIVE_AI" and "Fiber 500" in result["answer"]
    events = [event for event in service.store.events() if event["traceId"] == result["traceId"]]
    assert any(
        event["eventType"] == "agent.tool_requested" and event["metadata"]["tool"] == "read_account"
        for event in events
    )
    assert any(
        event["eventType"] == "tool.finished" and event["component"] == "account-service" for event in events
    )
    assert (
        len(
            [
                event
                for event in events
                if event["eventType"] == "ai.finished" and event["status"] == "success"
            ]
        )
        == 2
    )
    assert not model.replies and not mock.CASES


def test_adk_caches_repeated_read_tool_calls(stack, customer):
    service = stack[0]
    service.mode = "LIVE_AI"
    model = ScriptedModel(
        model="scripted",
        replies=[
            answer({"intent": "billing", "service": "unknown", "confidence": 1.0}),
            tool("read_billing"),
            tool("read_billing"),
            answer({"fact_ids": [0, 1, 2]}),
        ],
    )
    service.ai = AdkProvider(model=model)
    result = service.chat(customer, Chat(message="Show my bill"))
    assert result["state"] == "RESOLVED" and result["mode"] == "LIVE_AI"
    events = [event for event in service.store.events() if event["traceId"] == result["traceId"]]
    assert (
        sum(event["eventType"] == "tool.invoked" and event["component"] == "billing" for event in events) == 1
    )


def test_adk_missing_required_tool_is_visible_fallback(stack, customer):
    service = stack[0]
    service.mode = "LIVE_AI"
    service.ai = AdkProvider(
        model=ScriptedModel(
            model="scripted",
            replies=[
                answer({"intent": "account", "service": "unknown", "confidence": 1.0}),
                answer({"fact_ids": [0]}),
            ],
        )
    )
    result = service.chat(customer, Chat(message="My plan"))
    assert result["mode"] == "DEGRADED" and "Fiber 500" in result["answer"]
    assert any(
        event["eventType"] == "provider.fallback"
        for event in service.store.events()
        if event["traceId"] == result["traceId"]
    )
