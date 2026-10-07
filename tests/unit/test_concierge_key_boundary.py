"""PHILO-15 02 (Astra r1): a key typed on the Concierge never reaches a log.

A key with a newline made the HTTP library raise
``Invalid header value b'Bearer <key>'`` and that text was logged. These
fences run the REAL header construction (urllib / the loopback getter against
a real local HTTP server), not a stub getter.
"""

from __future__ import annotations

import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak import setup_runtime
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

SECRET = "astra966-synthetic-secret"


class _Models(BaseHTTPRequestHandler):
    required = f"Bearer {SECRET}"

    def do_GET(self):  # noqa: N802
        if self.headers.get("Authorization") != self.required:
            self.send_response(401)
            self.end_headers()
            return
        body = b'{"data":[{"id":"qwen3.8-27b"}]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


@pytest.fixture()
def server():
    httpd = HTTPServer(("127.0.0.1", 0), _Models)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}/v1"
    httpd.shutdown()


def _client() -> TestClient:
    return TestClient(MeetingWebServer(WebRuntimeCallbacks(
        on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}),
    )).app)


def _no_secret(caplog: pytest.LogCaptureFixture, *needles: str) -> None:
    for record in caplog.records:
        line = record.getMessage()
        for needle in needles:
            assert needle not in line, line


@pytest.mark.parametrize("bad", [f"{SECRET}\ninvalid", f"{SECRET}\rx", f"{SECRET} two", f"{SECRET}\x00"])
def test_a_malformed_key_is_refused_before_any_header_and_never_logged(server, caplog, bad) -> None:
    caplog.set_level(logging.DEBUG)
    response = _client().post("/api/setup/discover-models", json={"base_url": server, "api_key": bad})
    assert response.status_code == 400
    assert response.json() == {
        "ok": False, "models": [], "detail": "Key has characters a header cannot carry.", "reason": "key_invalid",
    }
    assert SECRET not in response.text
    _no_secret(caplog, SECRET, "Bearer")


def test_a_malformed_key_from_any_caller_builds_no_header(server, caplog) -> None:
    """The runtime refuses it too (a stored or env key takes the same path)."""
    caplog.set_level(logging.DEBUG)
    result = setup_runtime.discover_endpoint_models(server, api_key=f"{SECRET}\ninvalid")
    assert result["reason"] == "key_invalid" and result["ok"] is False
    _no_secret(caplog, SECRET, "Bearer")


def test_a_valid_key_passes_through_the_real_header_and_is_never_logged(server, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    response = _client().post("/api/setup/discover-models", json={"base_url": server, "api_key": SECRET})
    assert response.status_code == 200
    assert response.json()["models"] == ["qwen3.8-27b"]
    assert SECRET not in response.text
    _no_secret(caplog, SECRET)


def test_a_server_that_wants_a_key_reads_key_required(server, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    response = _client().post("/api/setup/discover-models", json={"base_url": server, "api_key": "wrong-key"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Key required"
    assert response.json()["reason"] == "key_required"
    _no_secret(caplog, "wrong-key")


def test_a_failed_contact_with_a_key_logs_the_class_not_the_text(caplog) -> None:
    """Whatever the transport raises, its text (which can carry the header)
    stays out of the log when a key was supplied."""
    caplog.set_level(logging.DEBUG)

    def getter(_url, *, headers, timeout):
        raise ValueError(f"Invalid header value {headers['Authorization']!r}")

    result = setup_runtime.discover_endpoint_models("http://127.0.0.1:9/v1", api_key=SECRET, http_get=getter)
    assert result["ok"] is False
    _no_secret(caplog, SECRET, "Bearer")
    assert any("ValueError" in r.getMessage() for r in caplog.records)
