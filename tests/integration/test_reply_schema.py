from pydantic import Field
from relay_api.agents.runtime import AdkProvider
from relay_api.domain.models import Chat
from test_adk_agents import ScriptedModel, answer, tool


class RecordingModel(ScriptedModel):
    requests: list[dict] = Field(default_factory=list)

    async def generate_content_async(self, llm_request, stream=False):
        config = llm_request.config
        self.requests.append(
            {
                "mime": config.response_mime_type,
                "schema": config.response_json_schema,
                "toolCount": len(config.tools or []),
            }
        )
        async for response in super().generate_content_async(llm_request, stream):
            yield response


def test_specialist_enforces_schema_after_real_authorized_tool(stack):
    app = stack[0]
    session = app.login({"username": "jordan.lee", "password": "ReviewerPass-1002"})[1]
    app.mode = "LIVE_AI"
    reply = (
        "Your subscriber status is active. Network checks look normal and diagnostics found no device fault."
    )
    model = RecordingModel(
        model="scripted",
        replies=[
            answer({"intent": "network", "service": "mobile", "confidence": 1.0}),
            tool("diagnose_service"),
            answer({"fact_ids": [0, 1, 2], "answer": reply}),
        ],
    )
    app.ai = AdkProvider(model=model)
    result = app.chat(session, Chat(message="mobile data is not working"))
    assert result["mode"] == "LIVE_AI" and result["answer"] == reply
    assert model.requests[1]["mime"] is None and model.requests[1]["toolCount"] > 0
    final = model.requests[2]
    assert final["mime"] == "application/json" and final["toolCount"] == 0
    assert set(final["schema"]["required"]) == {"answer", "fact_ids"}
    assert not model.replies


def test_rejected_reply_reason_is_recorded_without_raw_text(stack, customer):
    app = stack[0]
    app.mode = "LIVE_AI"
    secret_reply = "This is not JSON; private-model-text"
    app.ai = AdkProvider(
        model=ScriptedModel(
            model="scripted",
            replies=[
                answer({"intent": "account", "service": "unknown", "confidence": 1.0}),
                tool("read_account"),
                answer({"answer": secret_reply}),
            ],
        )
    )
    result = app.chat(customer, Chat(message="my plan"))
    events = app.store.trace_events(result["traceId"])
    assert any(
        e["eventType"] == "agent.output_rejected" and e["metadata"]["reason"] == "reply_schema"
        for e in events
    )
    assert secret_reply not in str(events) and secret_reply not in result["answer"]
    assert result["mode"] == "DEGRADED"
