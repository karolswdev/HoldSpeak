"""MCP/SOA contract for the one-turn Thought refinement lifecycle."""
from __future__ import annotations

import asyncio
import io
import json
import threading
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.mcp import resources, server
from holdspeak.mcp.families import thought as thought_family
from holdspeak.mcp.refinement_runtime import SidecarRefinementRuntime
from holdspeak.mcp.server import handle_message
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError
from holdspeak.services.refinement_coordinator import RefinementCoordinator
from holdspeak.services.refinement_thought_service import (
    INBOX_DIRECTORY_ID,
    RefinementThoughtService,
)

OWNER = Principal(PrincipalKind.OWNER, "mcp-thought-test")


def _call(name: str, arguments: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    response = handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert response is not None
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


class StubApplication:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def refine(self, principal: Principal, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("refine", kwargs))
        return {"thought": {"id": kwargs["thought_id"]}, "continuity": {"state": "reserved", "invocation_id": "rinv_1"}}

    async def stop(self, principal: Principal, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("stop", kwargs))
        return {"thought": {"id": kwargs["thought_id"], "continuity": {"state": "named_failure", "code": "owner_stopped"}}}

    def reconcile(self, principal: Principal, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("reconcile", kwargs))
        return {"thought": {"id": kwargs["thought_id"], "continuity": {"state": "review_ready"}}}

    def act_on_review(self, principal: Principal, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("act", kwargs))
        return {"thought": {"id": kwargs["thought_id"]}, "receipt": {"kind": kwargs["action"]}}


@pytest.fixture
def stubbed_family(monkeypatch: pytest.MonkeyPatch) -> StubApplication:
    app = StubApplication()
    monkeypatch.setattr(thought_family, "_service", lambda: app)
    monkeypatch.setattr(thought_family, "_run", asyncio.run)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    return app


def test_catalogue_is_closed_and_never_accepts_browser_authoritative_material() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    tools = {row["name"]: row for row in response["result"]["tools"]}
    expected = {
        "thought.refine", "thought.reconcile", "thought.stop_refinement",
        "thought.answer_review", "thought.accept_review", "thought.reject_review",
    }
    assert expected <= set(tools)
    forbidden = {"prompt", "model", "raw_text", "working_text", "context", "grounding"}
    for name in expected:
        schema = tools[name]["inputSchema"]
        assert schema["additionalProperties"] is False
        assert forbidden.isdisjoint(schema["properties"])
    assert "answer" in tools["thought.answer_review"]["inputSchema"]["properties"]
    assert "answer" not in tools["thought.accept_review"]["inputSchema"]["properties"]
    assert "answer" not in tools["thought.reject_review"]["inputSchema"]["properties"]


def test_all_commands_dispatch_through_the_same_application_boundary(stubbed_family: StubApplication) -> None:
    cursors = {
        "expected_aggregate_revision": 3,
        "expected_working_revision": 2,
        "expected_attachment_revision": 1,
    }
    error, refined = _call("thought.refine", {"thought_id": "thought_1", "request_id": "request_1", **cursors})
    assert not error and refined["continuity"]["invocation_id"] == "rinv_1"
    error, reconciled = _call("thought.reconcile", {"thought_id": "thought_1", "expected_aggregate_revision": 3, "invocation_id": "rinv_1"})
    assert not error and reconciled["thought"]["continuity"]["state"] == "review_ready"
    error, stopped = _call("thought.stop_refinement", {"thought_id": "thought_1", "invocation_id": "rinv_1", "expected_aggregate_revision": 3})
    assert not error and stopped["thought"]["continuity"]["code"] == "owner_stopped"
    for action in ("answer", "accept", "reject"):
        payload = {"thought_id": "thought_1", "review_result_id": "rresult_1", "request_id": f"request_{action}", **cursors}
        if action == "answer":
            payload["answer"] = "Friday."
        error, result = _call(f"thought.{action}_review", payload)
        assert not error and result["receipt"]["kind"] == action
    assert [name for name, _ in stubbed_family.calls] == [
        "refine", "reconcile", "stop", "act", "act", "act"
    ]
    assert [kwargs["action"] for name, kwargs in stubbed_family.calls if name == "act"] == ["answer", "accept", "reject"]


def test_service_errors_keep_named_code_and_current_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    class Refusing(StubApplication):
        def reconcile(self, principal: Principal, **kwargs: Any) -> dict[str, Any]:
            raise ConflictError(
                "working thought changed elsewhere",
                code="thought_revision_conflict",
                context={"current": {"id": "thought_1", "aggregate_revision": 4}},
            )

    monkeypatch.setattr(thought_family, "_service", Refusing)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    is_error, payload = _call("thought.reconcile", {"thought_id": "thought_1", "expected_aggregate_revision": 3})
    assert is_error
    assert payload == {
        "error": "working thought changed elsewhere",
        "code": "thought_revision_conflict",
        "current": {"id": "thought_1", "aggregate_revision": 4},
    }


def test_resource_errors_keep_named_code_in_jsonrpc_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(_uri: str, _principal: Principal) -> Any:
        raise ConflictError(
            "review is no longer current",
            code="refinement_review_superseded",
            context={"current": {"id": "thought_1"}},
        )

    monkeypatch.setattr(server, "read_resource", refuse)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    response = handle_message({
        "jsonrpc": "2.0", "id": 7, "method": "resources/read",
        "params": {"uri": "holdspeak://thoughts/thought_1/reviews/rresult_1"},
    })
    assert response is not None
    assert response["error"] == {
        "code": -32002,
        "message": "review is no longer current",
        "data": {
            "code": "refinement_review_superseded",
            "current": {"id": "thought_1"},
        },
    }


def test_resources_are_owner_context_and_do_not_expose_internal_execution_ids(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    db = Database(tmp_path / "thought-resource.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    thought = RefinementThoughtService(db).create(
        OWNER, request_id="capture-1", raw_text="private original", source={"kind": "typed"}
    )
    monkeypatch.setattr(resources, "get_database", lambda: db)
    catalog = resources.list_resources()
    assert any(row["uri"] == "holdspeak://thoughts/unfinished" for row in catalog["resources"])
    templates = {row["uriTemplate"] for row in catalog["resourceTemplates"]}
    assert "holdspeak://thoughts/{thought_id}" in templates
    assert "holdspeak://thoughts/{thought_id}/reviews/{review_result_id}" in templates

    listing = json.loads(resources.read_resource("holdspeak://thoughts/unfinished", OWNER)["contents"][0]["text"])
    assert listing["items"][0]["id"] == thought["id"]
    detail_text = resources.read_resource(f"holdspeak://thoughts/{thought['id']}", OWNER)["contents"][0]["text"]
    detail = json.loads(detail_text)
    assert detail["thought"]["working_note"]["body_markdown"] == "private original"
    assert "raw_text" not in detail_text
    assert "ask_invocation_id" not in detail_text
    assert "kernel_operation_id" not in detail_text


def test_sidecar_runtime_uses_a_persistent_loop_and_never_recovers_web_work() -> None:
    class FakeCoordinator:
        def __init__(self) -> None:
            self.started_with: bool | None = None
            self.closed = False

        async def start(self, *, recover_abandoned: bool = True) -> list[str]:
            self.started_with = recover_abandoned
            return []

        async def shutdown(self) -> None:
            self.closed = True

    coordinator = FakeCoordinator()
    runtime = SidecarRefinementRuntime(lambda: coordinator)  # type: ignore[arg-type]
    runtime.start()
    try:
        async def loop_thread() -> int:
            return threading.get_ident()

        first_thread = runtime.call(loop_thread())
        second_thread = runtime.call(loop_thread())
        assert first_thread == second_thread
        assert coordinator.started_with is False
    finally:
        runtime.close()
    assert coordinator.closed


def test_sidecar_start_does_not_terminalize_a_web_owned_live_invocation(tmp_path: Any) -> None:
    db = Database(tmp_path / "shared-runtime.db")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    thoughts = RefinementThoughtService(db)
    thought = thoughts.create(
        OWNER, request_id="web-capture", raw_text="web-owned", source={"kind": "typed"}
    )
    invocation = thoughts.reserve_refinement(
        OWNER,
        thought["id"],
        request_id="web-refine",
        expected_aggregate_revision=thought["aggregate_revision"],
        expected_working_revision=thought["working_revision"],
        expected_attachment_revision=thought["attachment_revision"],
    )

    runtime = SidecarRefinementRuntime(lambda: RefinementCoordinator(db))
    runtime.start()
    try:
        current = thoughts.get(OWNER, thought["id"])
        assert current["continuity"] == {
            "state": "reserved",
            "invocation_id": invocation["id"],
            "review_result_id": None,
            "code": "",
        }
        with db._connection() as conn:
            attempts = conn.execute(
                "SELECT state FROM refinement_invocation_attempts WHERE invocation_id=?",
                (invocation["id"],),
            ).fetchall()
        assert [row["state"] for row in attempts] == ["reserved"]
    finally:
        runtime.close()


def test_serve_owns_one_runtime_for_the_whole_stdio_session(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class FakeRuntime:
        def start(self) -> None: events.append("start")
        def close(self) -> None: events.append("close")

    monkeypatch.setattr("holdspeak.mcp.refinement_runtime.SidecarRefinementRuntime", FakeRuntime)
    monkeypatch.setattr(thought_family, "configure_runtime", lambda value: events.append("bind" if value else "unbind"))
    stdin = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\n')
    stdout = io.StringIO()
    assert server.serve(stdin, stdout) == 0
    assert events == ["start", "bind", "unbind", "close"]
    assert json.loads(stdout.getvalue())["result"] == {}
