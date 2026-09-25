"""PHILO-5-02 round two: the fences Astra's check on built asked for.

Every fence runs against the REAL hub (``MeetingWebServer``) over an isolated
database, through the helpers of ``test_philo5_the_loop.py``. What each proves,
and what turned it red on round one (``fca54146``):

* **The owner boundary on ``meeting.import``** (finding 1). A DESK credential
  issued through the real settings route, calling from a non-loopback client
  over ``/api/mcp``, is refused ``owner_required`` and the hub never looks at
  the file: zero opens, zero ``is_file``, zero ``os.access`` on the target, and
  no meeting. The same file then imports for the local owner, and the observer
  sees that open, so the zero above is not vacuous. Red on round one: the agent
  import succeeded (Astra's ``48a3fa11``).
* **Declared result shapes are the producers' shapes** (finding 2). For EVERY
  descriptor whose ``result`` declares a braced shape (``{a, b, ...}``), the
  real producer runs through the hub's registry and the declared top-level keys
  are present. Red on round one: ``thought.list`` declared ``thoughts``; the
  producer returns ``items``.
* **Shelf writes traverse the registry** (finding 3). HTTP and MCP shelf write
  and read are each recorded by the hub's ONE ``invoke``. Retained mutations
  M12 (MCP shelf write bypasses ``invoke``) and M13 (HTTP shelf write bypasses
  ``invoke``) turn it red.
"""
from __future__ import annotations

import builtins
import json
import os
import pathlib
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

import pytest

from holdspeak import operations
from holdspeak.principals import Principal, PrincipalKind
from tests.unit.test_philo5_the_loop import (  # noqa: F401  (fixtures by name)
    FIXTURE_TXT,
    Hub,
    _summary_ready_meeting,
    _thought,
    _wait_imported,
    hub,
    recorded,
)

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
REMOTE_HOST = "192.0.2.123"  # TEST-NET-1: never loopback


# ── finding 1: the owner boundary, with a genuinely issued credential ─────


def _observe(monkeypatch: pytest.MonkeyPatch, target: Path) -> list[str]:
    """Record every filesystem touch of *target* the import intake could make."""
    touches: list[str] = []
    wanted = os.fspath(target)

    def hit(kind: str, path: Any) -> None:
        try:
            if os.fspath(path) == wanted:
                touches.append(kind)
        except TypeError:
            pass

    real_open, real_is_file, real_exists = pathlib.Path.open, pathlib.Path.is_file, pathlib.Path.exists
    real_access, real_builtin_open = os.access, builtins.open

    def path_open(self: Path, *a: Any, **k: Any) -> Any:
        hit("Path.open", self)
        return real_open(self, *a, **k)

    def path_is_file(self: Path, *a: Any, **k: Any) -> bool:
        hit("Path.is_file", self)
        return real_is_file(self, *a, **k)

    def path_exists(self: Path, *a: Any, **k: Any) -> bool:
        hit("Path.exists", self)
        return real_exists(self, *a, **k)

    def access(path: Any, *a: Any, **k: Any) -> bool:
        hit("os.access", path)
        return real_access(path, *a, **k)

    def builtin_open(file: Any, *a: Any, **k: Any) -> Any:
        hit("open", file)
        return real_builtin_open(file, *a, **k)

    monkeypatch.setattr(pathlib.Path, "open", path_open)
    monkeypatch.setattr(pathlib.Path, "is_file", path_is_file)
    monkeypatch.setattr(pathlib.Path, "exists", path_exists)
    monkeypatch.setattr(os, "access", access)
    monkeypatch.setattr(builtins, "open", builtin_open)
    return touches


def _rpc(client: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def _agent_client(hub: Hub, token: str, host: str) -> Any:
    """A client that carries ONLY the agent credential (the hub's TestClient
    otherwise adds the owner's ``x-holdspeak-token`` by default)."""
    from starlette.testclient import TestClient

    client = TestClient(hub.server.app, client=(host, 50000))
    client.headers.pop("x-holdspeak-token", None)
    client.headers.update({"Authorization": f"Bearer {token}"})
    assert "x-holdspeak-token" not in client.headers
    return client


def _issue_desk_credential(hub: Hub) -> str:
    """Enable remote MCP and issue a DESK credential through the REAL routes."""
    enabled = hub.client.put("/api/settings/remote", json={"enabled": True})
    assert enabled.status_code == 200 and enabled.json()["enabled"] is True, enabled.text
    issued = hub.client.post("/api/settings/remote/credentials",
                             json={"identity": "remote-desk-agent", "palette": "DESK"})
    assert issued.status_code == 200, issued.text
    assert issued.json()["palette"] == "DESK"
    return issued.json()["token"]


def test_a_remote_desk_credential_cannot_make_the_hub_read_a_file(hub: Hub, tmp_path: Path, monkeypatch) -> None:
    token = _issue_desk_credential(hub)
    remote = _agent_client(hub, token, REMOTE_HOST)
    # The credential is genuine: the remote agent may read the desk.
    listed = _rpc(remote, "meeting.list", {})
    assert listed["result"]["isError"] is False, listed

    target = tmp_path / "owner-private.txt"
    target.write_bytes(FIXTURE_TXT.read_bytes())
    touches = _observe(monkeypatch, target)

    refused = _rpc(remote, "meeting.import", {"path": str(target), "title": "owner-private"})
    assert "result" in refused, refused
    assert refused["result"]["isError"] is True, refused
    payload = json.loads(refused["result"]["content"][0]["text"])
    assert payload["code"] == "owner_required", payload
    assert touches == [], f"the hub touched the file for a remote agent: {touches}"
    is_error, listing = hub.mcp("meeting.list", {})
    assert is_error is False and listing["meetings"] == [], listing

    # The same credential from loopback is still an agent: refused the same way.
    local_agent = _agent_client(hub, token, "127.0.0.1")
    again = _rpc(local_agent, "meeting.import", {"path": str(target)})
    assert json.loads(again["result"]["content"][0]["text"])["code"] == "owner_required", again
    assert touches == []

    # The local owner imports the same file, and the observer sees the open.
    is_error, intake = hub.mcp("meeting.import", {"path": str(target), "title": "owner-private"})
    assert is_error is False, intake
    assert "Path.open" in touches or "open" in touches, touches
    done = _wait_imported(hub, intake["meeting_id"])
    assert done["title"] == "owner-private" and done["segments"]


def test_the_http_upload_refuses_a_non_owner_before_storing_the_body(hub: Hub, monkeypatch) -> None:
    """Every path to the operation: the HTTP route authorizes before the temp file.

    The hub's edge gate already refuses an agent on this route, so the route is
    mounted alone over the hub's own context, behind a middleware that makes the
    caller an agent: what answers is the ROUTE's boundary.
    """
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from holdspeak.web.routes import meeting_import as import_route

    stored: list[str] = []
    real = tempfile.NamedTemporaryFile

    def tracking(*a: Any, **k: Any) -> Any:
        stored.append("tmp")
        return real(*a, **k)

    monkeypatch.setattr(import_route.tempfile, "NamedTemporaryFile", tracking)
    app = FastAPI()
    agent = Principal(PrincipalKind.AGENT, "remote-desk-agent")

    @app.middleware("http")
    async def _as_agent(request: Any, call_next: Callable[..., Any]) -> Any:
        request.state.principal = agent
        return await call_next(request)

    app.include_router(import_route.build_meeting_import_router(hub.root.web_context))
    client = TestClient(app, client=("127.0.0.1", 50000))
    resp = client.post("/api/meetings/import",
                       files={"file": ("a.txt", FIXTURE_TXT.read_bytes(), "text/plain")})
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "owner_required"
    assert stored == []
    # The owner through the hub still imports over HTTP.
    upload = hub.client.post("/api/meetings/import",
                             files={"file": ("a.txt", FIXTURE_TXT.read_bytes(), "text/plain")})
    assert upload.status_code == 202, upload.text
    _wait_imported(hub, upload.json()["meeting_id"])


def test_the_contract_refuses_a_non_owner_before_anything_else(tmp_path: Path) -> None:
    from holdspeak.db import Database
    from holdspeak.services.meeting_service import MeetingService

    registry = operations.bind_available({"meeting_service": MeetingService(Database(tmp_path / "h.db"))})
    for principal in (None, Principal(PrincipalKind.AGENT, "a"), Principal(PrincipalKind.NODE, "n"),
                      Principal(PrincipalKind.SERVICE, "s"), Principal(PrincipalKind.NONE, "")):
        with pytest.raises(operations.OperationOwnerRequired) as exc:
            # No held inputs and bad arguments: the owner refusal still comes first.
            registry.invoke(principal, "meeting.import", {"nope": 1})
        assert exc.value.code == "owner_required"
    assert operations.MEETING_IMPORT.owner_only is True
    assert [d.name for d in operations.DESCRIPTORS if d.owner_only] == ["meeting.import"]
    assert "owner_required" in operations.MEETING_IMPORT.export()["refusals"]


# ── finding 2: every declared result shape is the producer's shape ────────


def _declared_keys(result: str) -> list[str] | None:
    """Top-level keys of a braced result declaration, else None."""
    text = result.strip()
    if not text.startswith("{"):
        return None
    depth, end = 0, None
    for index, char in enumerate(text):
        if char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
            if depth == 0:
                end = index
                break
    assert end is not None, result
    parts, buf, depth = [], "", 0
    for char in text[1:end]:
        if char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(buf)
            buf = ""
            continue
        buf += char
    parts.append(buf)
    return [part.split(":")[0].split("(")[0].strip() for part in parts]


#: A braced declaration whose keys are data (a map), not field names.
MAP_SHAPES = {"brief.shelf.read"}


def _p_meeting_list(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    return hub.root.operations.invoke(OWNER, "meeting.list", {})


def _p_meeting_import(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    from holdspeak.config import Config

    held = tmp_path / "held.txt"
    shutil.copyfile(FIXTURE_TXT, held)
    result = hub.root.operations.invoke(OWNER, "meeting.import", {"filename": "shape.txt"}, held={
        "tmp_path": held, "config": Config.load(), "transcriber_factory": lambda cfg: None})
    _wait_imported(hub, result["meeting_id"])
    return result


def _p_summary_run(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    selection_hash = _summary_ready_meeting(hub, monkeypatch, "m-shape")
    return hub.root.operations.invoke(OWNER, "meeting.summary.run",
                                      {"meeting_id": "m-shape", "expected_selection_hash": selection_hash})


def _brief_item(hub: Hub) -> str:
    is_error, made = hub.mcp("desk.create", {"kind": "decisions", "data": {"title": "Shape"}})
    assert is_error is False, made
    is_error, brief = hub.mcp("monday_brief.generate", {})
    assert is_error is False, brief
    return brief["sections"]["decisions"][0]["id"]


def _p_shelf_write(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    return hub.root.operations.invoke(OWNER, "brief.shelf.write", {"item_id": _brief_item(hub), "state": "deferred"})


def _p_shelf_read(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    item = _brief_item(hub)
    hub.root.operations.invoke(OWNER, "brief.shelf.write", {"item_id": item, "state": "acknowledged"})
    return hub.root.operations.invoke(OWNER, "brief.shelf.read", {})


def _p_thought_create(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    return hub.root.operations.invoke(OWNER, "thought.create", {"request_id": "shape-1", "raw_text": "shape"})


def _p_thought_save(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    thought = _thought(hub, "shape-2")
    return hub.root.operations.invoke(OWNER, "thought.save", {
        "thought_id": thought["id"], "expected_aggregate_revision": thought["aggregate_revision"],
        "expected_working_revision": thought["working_revision"], "title": "saved"})


def _p_thought_list(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _thought(hub, "shape-3")
    return hub.root.operations.invoke(OWNER, "thought.list", {})


def _p_zone_read(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    # PHILO-7-01: zone.read declares {directory, member_ids, members}.
    made = hub.root.operations.invoke(OWNER, "zone.create", {"name": "Shape"})
    return hub.root.operations.invoke(OWNER, "zone.read", {"directory_id": made["id"]})


PRODUCERS: dict[str, Callable[[Hub, Any, Path], Any]] = {
    "meeting.list": _p_meeting_list,
    "meeting.import": _p_meeting_import,
    "meeting.summary.run": _p_summary_run,
    "brief.shelf.write": _p_shelf_write,
    "brief.shelf.read": _p_shelf_read,
    "thought.create": _p_thought_create,
    "thought.save": _p_thought_save,
    "thought.list": _p_thought_list,
    "zone.read": _p_zone_read,
}


def test_every_braced_declaration_has_a_producer_here() -> None:
    declared = {d.name for d in operations.DESCRIPTORS if _declared_keys(d.result) is not None}
    assert declared == set(PRODUCERS), "a descriptor declares a shape this fence does not run"


@pytest.mark.parametrize("name", sorted(PRODUCERS))
def test_the_declared_result_shape_is_the_producers_shape(name: str, hub: Hub, monkeypatch, tmp_path) -> None:
    descriptor = operations.DESCRIPTORS[[d.name for d in operations.DESCRIPTORS].index(name)]
    keys = _declared_keys(descriptor.result)
    result = PRODUCERS[name](hub, monkeypatch, tmp_path)
    assert isinstance(result, dict), (name, type(result))
    if name in MAP_SHAPES:
        assert result and all(isinstance(k, str) and isinstance(v, str) for k, v in result.items()), result
        return
    missing = [key for key in keys or [] if key not in result]
    assert not missing, f"{name} declares {keys}; the producer returned {sorted(result)}"


# ── finding 3: shelf writes and reads traverse the ONE registry ───────────


def test_shelf_writes_and_reads_traverse_the_registry_on_both_transports(hub: Hub, recorded: list[str]) -> None:
    item = _brief_item(hub)
    recorded.clear()
    written = hub.client.post(f"/api/brief/items/{item}/shelf", json={"state": "acknowledged"})
    assert written.status_code == 200, written.text
    assert hub.client.get("/api/brief/shelf").json() == {item: "acknowledged"}
    assert recorded == ["brief.shelf.write", "brief.shelf.read"], f"HTTP shelf left the registry: {recorded}"

    recorded.clear()
    is_error, out = hub.mcp("monday_brief.shelf", {"item_id": item, "state": "deferred"})
    assert is_error is False and out == {"item_id": item, "state": "deferred"}, out
    assert hub.mcp("monday_brief.shelf_read", {}) == (False, {item: "deferred"})
    assert recorded == ["brief.shelf.write", "brief.shelf.read"], f"MCP shelf left the registry: {recorded}"
