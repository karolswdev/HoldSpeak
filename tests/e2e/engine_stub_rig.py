"""A local OpenAI-compatible engine stub: GET .../models answers one model.

Moved verbatim from tests/e2e/test_hs201_09_connect_engine_glass.py (the
test diet, 2026-10-11) so that live rigs and the hub-level successor
(tests/integration/test_desk_runs_on_hub.py) share one stub.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any


def completion_reply(request: dict[str, Any], payload: bytes) -> tuple[str, bytes]:
    """A chat completion as a real OpenAI-compatible server sends it: the
    JSON body, or (``"stream": true``) the same answer as server-sent events.

    The hub streams an Ask's answer (Ask hub gap 1) as it streams a thread
    turn; llama.cpp, Ollama, vLLM and OpenAI all answer a streamed request
    this way."""
    if not request.get("stream"):
        return "application/json", payload
    completion = json.loads(payload)
    choice = (completion.get("choices") or [{}])[0]
    content = str((choice.get("message") or {}).get("content") or "")
    chunk = {"id": completion.get("id", "stub"), "object": "chat.completion.chunk",
             "model": completion.get("model", ""), "created": 0}
    events = [
        {**chunk, "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}]},
        {**chunk, "choices": [{"index": 0, "delta": {}, "finish_reason": choice.get("finish_reason") or "stop"}]},
    ]
    if completion.get("usage"):
        events.append({**chunk, "choices": [], "usage": completion["usage"]})
    body = "".join(f"data: {json.dumps(event)}\n\n" for event in events) + "data: [DONE]\n\n"
    return "text/event-stream", body.encode()


class _StubHandler(BaseHTTPRequestHandler):
    MODEL = "stub-openai-compatible"

    def do_GET(self) -> None:  # noqa: N802 - http.server contract
        if self.path.rstrip("/").endswith("/models"):
            body = json.dumps(
                {"object": "list", "data": [{"id": self.MODEL, "object": "model"}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_args: Any) -> None:  # keep the rig's output clean
        return
