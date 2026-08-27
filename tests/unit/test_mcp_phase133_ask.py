"""Phase 133 ask-family tests: dispatch, _run wrapping, and error paths."""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.mcp import server
from holdspeak.mcp import tools as mcp_tools
from holdspeak.mcp.families import ask as ask_family
from holdspeak.mcp.server import handle_message
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "ask-test")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Send a tools/call message and return the result dict."""
    response = handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert response is not None
    return response["result"]


def _call_ok(name: str, arguments: dict[str, Any]) -> Any:
    """Call a tool, assert no error, and return the parsed payload."""
    result = _call(name, arguments)
    assert result["isError"] is False, f"unexpected error: {result}"
    return json.loads(result["content"][0]["text"])


def _call_error(name: str, arguments: dict[str, Any]) -> str:
    """Call a tool, assert isError is True, return the error message."""
    result = _call(name, arguments)
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    return payload.get("error", "")


# ---------------------------------------------------------------------------
# Stub AskService
# ---------------------------------------------------------------------------

class StubAskService:
    """Minimal stub that records calls and returns canned data."""

    def __init__(self, **kwargs: Any) -> None:
        self._init_kwargs = kwargs
        self.calls: list[tuple[str, tuple, dict]] = []

    def resolve_grounding(self, principal: Principal, refs: list[str]) -> dict[str, Any]:
        self.calls.append(("resolve_grounding", (principal, refs), {}))
        return {"refs": refs, "titles": ["Title A"], "chars": 42, "blocks": []}

    async def ask(self, principal: Principal, *, question: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("ask", (principal,), {"question": question, **kwargs}))
        return {
            "output": "The answer is 42.",
            "model": "test-model",
            "provider": "local",
            "actual_placement": {"target": "this_machine"},
            "egress": {"scope": "local"},
            "grounding_claims": [],
        }

    def cancel(self, principal: Principal, invocation_id: str) -> dict[str, str]:
        self.calls.append(("cancel", (principal, invocation_id), {}))
        return {"invocation_id": invocation_id, "disposition": "cancelled"}

    def keep(self, principal: Principal, *, output: str, sources: list, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("keep", (principal,), {"output": output, "sources": sources, **kwargs}))
        return {"artifact_id": "artifact_stubbed123"}


@pytest.fixture
def _patch_ask(monkeypatch: pytest.MonkeyPatch):
    """Wire StubAskService into the ask family and auth."""
    stub = StubAskService()
    monkeypatch.setattr(ask_family, "_service", lambda: stub)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    return stub


# ---------------------------------------------------------------------------
# 1. Catalogue: the four assignment-safe tools appear with closed schemas
# ---------------------------------------------------------------------------

def test_ask_tools_appear_in_catalogue() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    names = {t["name"] for t in response["result"]["tools"]}
    expected = {"ask.resolve_grounding", "ask.run", "ask.cancel", "ask.keep"}
    assert expected <= names, f"missing: {expected - names}"
    assert "ask.models" not in names


def test_ask_tools_have_closed_schemas() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    for tool in response["result"]["tools"]:
        if tool["name"].startswith("ask."):
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert schema["additionalProperties"] is False


# ---------------------------------------------------------------------------
# 2. Dispatch tests: each tool dispatches to the correct service method
# ---------------------------------------------------------------------------

def test_dispatch_ask_resolve_grounding(_patch_ask) -> None:
    stub = _patch_ask
    payload = _call_ok("ask.resolve_grounding", {"refs": ["note:abc", "meeting:xyz"]})
    assert payload["refs"] == ["note:abc", "meeting:xyz"]
    assert stub.calls[-1][0] == "resolve_grounding"
    assert stub.calls[-1][1][1] == ["note:abc", "meeting:xyz"]


def test_dispatch_ask_run(_patch_ask) -> None:
    stub = _patch_ask
    payload = _call_ok("ask.run", {
        "question": "What is the meaning of life?",
        "lens": "TestLens",
        "max_tokens": 100,
        "temperature": 0.7,
    })
    assert payload["output"] == "The answer is 42."
    assert payload["model"] == "test-model"
    assert payload["egress"]["scope"] == "local"
    assert stub.calls[-1][0] == "ask"
    call_kwargs = stub.calls[-1][2]
    assert call_kwargs["question"] == "What is the meaning of life?"
    assert call_kwargs["lens"] == "TestLens"
    assert call_kwargs["max_tokens"] == 100
    assert call_kwargs["temperature"] == 0.7


def test_dispatch_ask_cancel(_patch_ask) -> None:
    stub = _patch_ask
    payload = _call_ok("ask.cancel", {"invocation_id": "ask_abc123"})
    assert payload["invocation_id"] == "ask_abc123"
    assert payload["disposition"] == "cancelled"
    assert stub.calls[-1][0] == "cancel"


def test_dispatch_ask_keep(_patch_ask) -> None:
    stub = _patch_ask
    payload = _call_ok("ask.keep", {
        "output": "Persisted answer.",
        "sources": [{"id": "note:1", "kind": "note", "title": "My note"}],
        "lens": "KeepLens",
        "prompt": "original question",
    })
    assert payload["artifact_id"] == "artifact_stubbed123"
    assert stub.calls[-1][0] == "keep"
    call_kwargs = stub.calls[-1][2]
    assert call_kwargs["output"] == "Persisted answer."
    assert call_kwargs["sources"] == [{"id": "note:1", "kind": "note", "title": "My note"}]
    assert call_kwargs["lens"] == "KeepLens"
    assert call_kwargs["prompt"] == "original question"


# ---------------------------------------------------------------------------
# 3. _run wrapping test for ask.run with a canned coroutine
# ---------------------------------------------------------------------------

def test_ask_run_wraps_async_via_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """ask.run dispatches the AskService.ask coroutine through _run()."""
    canned = {
        "output": "Wrapped answer.",
        "model": "wrapped-model",
        "provider": "test",
        "actual_placement": {},
        "egress": {"scope": "local"},
    }

    async def fake_ask(principal, *, question, **kw):
        return canned

    stub = StubAskService()
    stub.ask = fake_ask  # type: ignore[assignment]
    monkeypatch.setattr(ask_family, "_service", lambda: stub)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

    payload = _call_ok("ask.run", {"question": "test wrapping"})
    assert payload["output"] == "Wrapped answer."
    assert payload["model"] == "wrapped-model"


def test_run_helper_works_outside_event_loop() -> None:
    """The local _run() helper can execute a coroutine when no loop is active."""
    async def simple_coro():
        return {"ok": True}

    result = ask_family._run(simple_coro())
    assert result == {"ok": True}


# ---------------------------------------------------------------------------
# 4. Error-path tests through handle_message
# ---------------------------------------------------------------------------

def test_error_ask_run_missing_question(_patch_ask) -> None:
    error_msg = _call_error("ask.run", {})
    assert "question" in error_msg.lower()


def test_error_ask_run_empty_question(_patch_ask) -> None:
    error_msg = _call_error("ask.run", {"question": "   "})
    assert "question" in error_msg.lower()


def test_error_ask_cancel_missing_invocation_id(_patch_ask) -> None:
    error_msg = _call_error("ask.cancel", {})
    assert "invocation_id" in error_msg.lower()


def test_error_ask_cancel_empty_invocation_id(_patch_ask) -> None:
    error_msg = _call_error("ask.cancel", {"invocation_id": "  "})
    assert "invocation_id" in error_msg.lower()


def test_error_ask_keep_missing_output(_patch_ask) -> None:
    error_msg = _call_error("ask.keep", {})
    assert "output" in error_msg.lower()


def test_error_ask_keep_empty_output(_patch_ask) -> None:
    error_msg = _call_error("ask.keep", {"output": "  "})
    assert "output" in error_msg.lower()


def test_error_ask_resolve_grounding_missing_refs(_patch_ask) -> None:
    error_msg = _call_error("ask.resolve_grounding", {})
    assert "refs" in error_msg.lower()


def test_error_ask_cancel_unknown_invocation_id(_patch_ask) -> None:
    """Unknown invocation_id: cancel dispatches to the service which may raise;
    this test verifies the dispatch reaches the service and doesn't crash."""
    stub = _patch_ask
    # The stub returns successfully even for unknown IDs; what matters is
    # that the dispatch reaches the service.  For a real unknown-id error,
    # the service would raise and server.py would catch it as isError.
    payload = _call_ok("ask.cancel", {"invocation_id": "ask_nonexistent"})
    assert payload["invocation_id"] == "ask_nonexistent"
    assert stub.calls[-1][0] == "cancel"


def test_error_ask_cancel_service_raises_on_unknown_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the service raises on unknown invocation_id, MCP returns isError:true."""
    class RaisingService(StubAskService):
        def cancel(self, principal, invocation_id):
            raise KeyError(f"No in-flight invocation: {invocation_id}")

    monkeypatch.setattr(ask_family, "_service", lambda: RaisingService())
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

    error_msg = _call_error("ask.cancel", {"invocation_id": "ask_nonexistent"})
    assert "ask_nonexistent" in error_msg
