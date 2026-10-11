"""A local OpenAI-compatible engine stub: GET .../models answers one model.

Moved verbatim from tests/e2e/test_hs201_09_connect_engine_glass.py (the
test diet, 2026-10-11) so that live rigs and the hub-level successor
(tests/integration/test_desk_runs_on_hub.py) share one stub.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any


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
