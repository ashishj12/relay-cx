import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from google import genai
from google.genai import errors
from relay_api.agents.runtime import AdkProvider


@pytest.mark.parametrize(
    "statuses,expected_calls", [([503, 503, 200], 3), ([503, 503, 503], 3), ([401], 1), ([429], 1)]
)
def test_async_provider_retry_is_bounded_and_transient_only(monkeypatch, statuses, expected_calls):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            code = statuses[min(len(calls), len(statuses) - 1)]
            calls.append(code)
            body = (
                {
                    "candidates": [
                        {"content": {"role": "model", "parts": [{"text": "OK"}]}, "finishReason": "STOP"}
                    ]
                }
                if code == 200
                else {
                    "error": {
                        "code": code,
                        "message": "synthetic provider response",
                        "status": "UNAVAILABLE" if code == 503 else "UNAUTHENTICATED",
                    }
                }
            )
            raw = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    real_client = genai.Client
    captured = {}

    def factory(**kwargs):
        captured["options"] = kwargs["http_options"]
        raise RuntimeError("capture_configuration_only")

    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(genai, "Client", factory)
    with pytest.raises(RuntimeError, match="capture_configuration_only"):
        AdkProvider().model()
    options = captured["options"].model_copy(
        update={"base_url": f"http://127.0.0.1:{server.server_port}", "timeout": 3000}
    )

    async def request():
        client = real_client(api_key="synthetic-test-key", http_options=options)
        try:
            return await client.aio.models.generate_content(model="test-model", contents="Reply OK")
        finally:
            await client.aio.aclose()
            client.close()

    try:
        if statuses[-1] == 200:
            assert asyncio.run(request()).text == "OK"
        else:
            with pytest.raises(errors.APIError):
                asyncio.run(request())
        assert len(calls) == expected_calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
