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
    # Both secret saves are owner only and HTTP only, with held inputs.
    assert [d.name for d in operations.DESCRIPTORS if d.owner_only] == [
        "meeting.import", "channel.save_email_key", "channel.save_slack_webhook", "agent_hooks.install",
        "people_access.set",  # Conductor R7: only the owner sets People MCP access
        "calendar.open_settings",  # PHILO-15 04: only the owner opens the Calendars privacy pane
        "project.repository.register",  # PHILO-15 16: only the owner names a Project's repository
        "agent.hand",  # Conductor K2: only the owner hands an item to an agent
    ]
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


def _p_kernel_receipt_read(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    # PHILO-7-02: the receipt readback declares {view, consistency, objects}.
    made = hub.client.post("/api/decisions", json={"title": "Shape"}).json()
    return hub.root.operations.invoke(OWNER, "kernel.receipt.read", {"operation_id": str(made.get("operation_id") or "op_none")})


def _p_memory_observations_read(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    # Memory slice 4: the observations read declares {observations, count}.
    return hub.root.operations.invoke(OWNER, "memory.observations.read", {})


def _p_memory_page_read(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    # Memory slice 5: the page read declares {page} (null with no page).
    return hub.root.operations.invoke(OWNER, "memory.page.read", {"scope": "desk", "slug": "what-i-owe"})


def _p_project_item_list(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    # PHILO-9-01: project.item.list declares {items, limit, offset} (no total).
    made = hub.client.post("/api/projects", json={"name": "Shape"}).json()["project"]
    return hub.root.operations.invoke(OWNER, "project.item.list", {"project_id": made["id"]})



# ── PHILO-9-02: the steward and connector rows declare their shapes too ──


def _project(hub: Hub, name: str = "Shape") -> str:
    return hub.client.post("/api/projects", json={"name": name}).json()["project"]["id"]


def _nudge_step(hub: Hub, state: str = "proposed") -> str:
    """A proposed github_comment step, as the steward's PROPOSE phase writes it."""
    import uuid

    pid = _project(hub, "Nudge shape")
    run_id, step_id = f"pstrun_{uuid.uuid4().hex}", f"pststep_{uuid.uuid4().hex}"
    hub.db.steward_runs.insert_run(run_id=run_id, project_id=pid, requested_by="owner")
    hub.db.steward_runs.update_run_state(run_id, state="completed")
    hub.db.steward_steps.insert_step(
        step_id=step_id, run_id=run_id, phase="propose", state=state, effect_kind="github_comment",
        idempotency_key=f"nudge:{pid}:example/payments:7:reviewer",
        expected_state_json=json.dumps({"repo": "example/payments", "pr_number": 7, "reviewer_login": "reviewer"}))
    hub.root.operations.invoke(OWNER, "project.configure_steward", {
        "project_id": pid, "eligible_effect_kinds": ["github_comment"]})
    return step_id


def _started_run(hub: Hub) -> tuple[str, dict[str, Any]]:
    pid = _project(hub, "Run shape")
    return pid, hub.root.operations.invoke(OWNER, "project.run_steward", {"project_id": pid})


def _p_configure_steward(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    return hub.root.operations.invoke(OWNER, "project.configure_steward", {"project_id": _project(hub)})


def _p_run_steward(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    return _started_run(hub)[1]


def _p_stop_steward(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    import threading

    # Hold the run's worker so the stop reaches a run that is still working.
    svc, release = hub.root.project_steward_service, threading.Event()
    real = svc._work

    def held(*args: Any, **kwargs: Any) -> Any:
        release.wait(20)
        return real(*args, **kwargs)

    monkeypatch.setattr(svc, "_work", held)
    _pid, started = _started_run(hub)
    try:
        return hub.root.operations.invoke(OWNER, "project.stop_steward", {"run_id": started["run_id"]})
    finally:
        release.set()


def _p_get_steward_run(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _pid, started = _started_run(hub)
    return hub.root.operations.invoke(OWNER, "project.get_steward_run", {"run_id": started["run_id"]})


def _p_steward_trigger(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    import holdspeak.workbench_conductor as conductor

    # The running hub wires the conductor's services (restored after the test).
    monkeypatch.setattr(conductor, "_watch_service", hub.root.watch_service)
    monkeypatch.setattr(conductor, "_steward_service", hub.root.project_steward_service)
    return hub.root.operations.invoke(OWNER, "project.steward.trigger", {})


def _p_nudge_send(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    # The process edge only: a canned `gh pr comment` answer (no network).
    import subprocess

    def gh(argv: list[str], **_kwargs: Any) -> Any:
        return subprocess.CompletedProcess(argv, 0, "https://github.com/example/payments/pull/7#issuecomment-1\n", "")

    monkeypatch.setattr(hub.root.project_steward_service, "_subprocess_runner", gh)
    # The TRANSPORTED answer (Codex Astra r3): the comment's receipt and the kernel's, both.
    resp = hub.client.post(f"/api/nudges/{_nudge_step(hub)}/send", json={"text": "A look, please."})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _p_nudge_dismiss(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    return hub.root.operations.invoke(OWNER, "nudge.dismiss", {"step_id": _nudge_step(hub)})


def _rig(monkeypatch: Any, tmp_path: Path) -> Hub:
    """A hub whose `gh` and `acli` are canned runners (the process edge; no network)."""
    from tests.unit.test_philo9_b1_connections import _boot
    from tests.unit.test_philo9_steward_admission import Runner

    folder = tmp_path / "rig"
    folder.mkdir(exist_ok=True)
    return _boot(folder, monkeypatch, Runner(), Runner())


def _p_watch_evaluate(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    from tests.unit.test_philo9_steward_admission import _door_project

    rig = _rig(monkeypatch, tmp_path)
    _pid, watch_id = _door_project(rig)
    return rig.root.operations.invoke(OWNER, "project.watch.evaluate", {"watch_id": watch_id},
                                      held={"graduated_only": False})


def _p_add_suggested_source(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    from tests.unit.test_philo9_steward_admission import _suggest

    rig = _rig(monkeypatch, tmp_path)
    pid = _project(rig, "Source shape")
    _suggest(rig, pid)
    return rig.root.operations.invoke(OWNER, "project.add_suggested_source", {
        "project_id": pid, "reference": "example/payments"})


def _p_dismiss_suggested_source(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    from tests.unit.test_philo9_steward_admission import _suggest

    rig = _rig(monkeypatch, tmp_path)
    pid = _project(rig, "Source shape")
    _suggest(rig, pid)
    return rig.root.operations.invoke(OWNER, "project.dismiss_suggested_source", {
        "project_id": pid, "reference": "example/payments"})


def _p_connection_list(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    return hub.root.operations.invoke(OWNER, "connection.list", {})


def _p_mark_update_delivered(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    pid = _project(hub, "Delivery shape")
    uid = hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    hub.client.post(f"/api/updates/{uid}/publish", json={})
    return hub.root.operations.invoke(OWNER, "project.mark_update_delivered", {
        "update_id": uid, "delivered_to": "the team"})


def _channel(hub: Hub, tmp_path: Path) -> tuple[str, str]:
    """PHILO-10-01: a published update and a saved folder destination, through the real registry."""
    pid = _project(hub, "Send shape")
    uid = hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    # PHILO-15 B64: an update with no verified claim is refused; the owner's saved line is reviewed.
    hub.client.put(f"/api/updates/{uid}", json={"body_md": "## Progress\n\nThe ledger cutover is on track.\n"})
    hub.client.post(f"/api/updates/{uid}/publish", json={})
    folder = tmp_path / "send-shape"
    folder.mkdir(exist_ok=True)
    saved = hub.root.operations.invoke(OWNER, "channel.save_destination", {
        "name": "Shape folder", "channel": "file", "folder": str(folder)})
    return uid, saved["destination"]["id"]


def _p_channel_save_destination(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    folder = tmp_path / "save-shape"
    folder.mkdir()
    return hub.root.operations.invoke(OWNER, "channel.save_destination", {
        "name": "Save shape", "channel": "file", "folder": str(folder)})


def _p_channel_destinations(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _channel(hub, tmp_path)
    return hub.root.operations.invoke(OWNER, "channel.destinations", {})


def _p_channel_remove_destination(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _uid, dest = _channel(hub, tmp_path)
    return hub.root.operations.invoke(OWNER, "channel.remove_destination", {"destination_id": dest})


def _p_channel_check_destination(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _uid, dest = _channel(hub, tmp_path)
    return hub.root.operations.invoke(OWNER, "channel.check_destination", {"destination_id": dest})


def _p_channel_preview(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    uid, dest = _channel(hub, tmp_path)
    return hub.root.operations.invoke(OWNER, "channel.preview", {"document_ref": f"project_update:{uid}", "destination_id": dest})


def _p_channel_prepare(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    uid, dest = _channel(hub, tmp_path)
    return hub.root.operations.invoke(OWNER, "channel.prepare", {"document_ref": f"project_update:{uid}", "destination_id": dest})


def _p_channel_discard(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    prepared = _p_channel_prepare(hub, monkeypatch, tmp_path)
    return hub.root.operations.invoke(OWNER, "channel.discard", {"send_id": prepared["send"]["id"]})


def _p_channel_send(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    prepared = _p_channel_prepare(hub, monkeypatch, tmp_path)
    return hub.root.operations.invoke(OWNER, "channel.send", {"send_id": prepared["send"]["id"]})


def _p_channel_save_email_key(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    """PHILO-10-03: the key HELD by the transport, the memory store (never the real keychain)."""
    from holdspeak.services import channel_email

    memory = channel_email.MemoryEmailKeyStore()
    monkeypatch.setattr(channel_email, "KEY_STORE", lambda: memory)
    return hub.root.operations.invoke(OWNER, "channel.save_email_key", {"key_ref": "sendgrid"},
                                      held={"api_key": "SG.shape-fence-synthetic"})


def _p_channel_save_slack_webhook(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    """The actual held-secret producer, with memory custody and no network."""
    from holdspeak.services import channel_slack

    memory = channel_slack.MemorySlackKeyStore()
    monkeypatch.setattr(channel_slack, "KEY_STORE", lambda: memory)
    result = hub.root.operations.invoke(OWNER, "channel.save_slack_webhook", {},
        held={"webhook_url": "https://hooks.slack.com/services/T_SHAPE/B_SHAPE/synthetic"})
    assert result["saved"] is True
    assert memory.values == {f"slack:{result['key_ref']}":
                             "https://hooks.slack.com/services/T_SHAPE/B_SHAPE/synthetic"}
    return result


def _p_channel_sends(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _p_channel_send(hub, monkeypatch, tmp_path)
    return hub.root.operations.invoke(OWNER, "channel.sends", {})


def _p_agent_hooks_install(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    """The real installer, on a temp home and a PATH that has claude."""
    service = hub.root.operations.target("agent_hooks.install")
    service._home = lambda: tmp_path / "agent-home"
    service._which = lambda name: f"/opt/bin/{name}" if name == "claude" else None
    service._environ = {}
    target = service.agent_settings_target("claude")
    return hub.root.operations.invoke(OWNER, "agent_hooks.install", {"agent": "claude", "settings_path": target})


def _p_people_access_set(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    """The real setter, on a config file in the test's directory."""
    import holdspeak.config as config_facade

    monkeypatch.setattr(config_facade, "CONFIG_FILE", tmp_path / "config.json")
    return hub.root.operations.invoke(OWNER, "people_access.set", {"mode": "read"})


# PHILO-16 16b: the desk's windows (the real service on the hub's database).
def _window_op(hub: Hub, name: str, args: dict[str, Any]) -> Any:
    return hub.root.operations.invoke(OWNER, name, args)


def _p_windows_list(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _window_op(hub, "windows.open", {"window_id": "chair:brief"})
    return _window_op(hub, "windows.list", {})


def _p_windows_open(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    return _window_op(hub, "windows.open", {"window_id": "chair:brief"})


def _p_windows_close(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _window_op(hub, "windows.open", {"window_id": "chair:week"})
    return _window_op(hub, "windows.close", {"window_id": "chair:week"})


def _p_windows_raise(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _window_op(hub, "windows.open", {"window_id": "chair:brief"})
    _window_op(hub, "windows.open", {"window_id": "chair:needs"})
    return _window_op(hub, "windows.raise", {"window_id": "chair:brief"})


def _p_windows_arrange(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _window_op(hub, "windows.open", {"window_id": "chair:brief"})
    return _window_op(hub, "windows.arrange", {"rects": {"chair:brief": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"}}})


def _p_windows_seat(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    _window_op(hub, "windows.open", {"window_id": "chair:brief"})
    return _window_op(hub, "windows.seat", {"window_id": "chair:brief", "seated": True})


def _p_calendar_open_settings(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    """The real service and kernel path; only the macOS open is a double."""
    service = hub.root.operations.target("calendar.open_settings")
    monkeypatch.setattr(service, "_macos", type("Mac", (), {"open_privacy_settings": staticmethod(lambda: True)}))
    return hub.root.operations.invoke(OWNER, "calendar.open_settings", {})


def _p_project_repository_register(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    """The real service, kernel path and route; the registrations file is the test's."""
    from holdspeak.services.project_repository import ProjectRepositories

    with hub.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-repo00000001', 'Repo')")
    service = hub.root.operations.target("project.repository.register")
    monkeypatch.setattr(service, "repositories", ProjectRepositories(
        store_path=tmp_path / "project_repositories.json", clone_root=tmp_path / "clones"))
    resp = hub.client.post("/api/projects/proj-repo00000001/repository", json={"repository": "acme/railsproj"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _p_agent_hand(hub: Hub, monkeypatch: Any, tmp_path: Path) -> Any:
    # The process edge only: tmux and the agent are the canned runner of the
    # launch rig (git is real); the hub's own AgentHandService and route run.
    from tests.unit.test_agent_hand import _rig as hand_rig, _seed

    _seed(hub.root.db)
    rig = hand_rig(tmp_path / "hand", hub.root.db, monkeypatch)
    service = hub.root.agent_hand_service
    monkeypatch.setattr(service, "_launch_service", lambda: rig.service)
    monkeypatch.setattr(service, "_gate_path", rig.gate_path)
    monkeypatch.setattr(service, "_project_map", {"projects": {}})
    monkeypatch.setattr(service, "_control_mode", lambda: "yolo")
    resp = hub.client.post("/api/agent/hand", json={"kind": "action", "id": "ai_1"})
    assert resp.status_code == 202, resp.text
    return resp.json()


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
    "kernel.receipt.read": _p_kernel_receipt_read,
    "memory.observations.read": _p_memory_observations_read,
    "memory.page.read": _p_memory_page_read,
    "project.item.list": _p_project_item_list,
    "project.configure_steward": _p_configure_steward,
    "project.run_steward": _p_run_steward,
    "project.stop_steward": _p_stop_steward,
    "project.get_steward_run": _p_get_steward_run,
    "project.steward.trigger": _p_steward_trigger,
    "nudge.send": _p_nudge_send,
    "nudge.dismiss": _p_nudge_dismiss,
    "project.watch.evaluate": _p_watch_evaluate,
    "project.add_suggested_source": _p_add_suggested_source,
    "project.dismiss_suggested_source": _p_dismiss_suggested_source,
    "connection.list": _p_connection_list,
    "project.mark_update_delivered": _p_mark_update_delivered,
    # PHILO-10-01: the Send.
    "channel.destinations": _p_channel_destinations,
    "channel.save_destination": _p_channel_save_destination,
    "channel.remove_destination": _p_channel_remove_destination,
    "channel.check_destination": _p_channel_check_destination,
    "channel.preview": _p_channel_preview,
    "channel.prepare": _p_channel_prepare,
    "channel.discard": _p_channel_discard,
    "channel.send": _p_channel_send,
    "channel.sends": _p_channel_sends,
    "channel.save_email_key": _p_channel_save_email_key,
    "channel.save_slack_webhook": _p_channel_save_slack_webhook,
    # The Conductor K1: the one-press hook install.
    "agent_hooks.install": _p_agent_hooks_install,
    # Conductor R7: People MCP access.
    "people_access.set": _p_people_access_set,
    # PHILO-15 04: the Calendars privacy pane.
    "calendar.open_settings": _p_calendar_open_settings,
    # PHILO-15 16: a Project's repository.
    "project.repository.register": _p_project_repository_register,
    # Conductor K2: Hand to agent.
    "agent.hand": _p_agent_hand,
    # PHILO-16 16b: the desk's windows.
    "windows.list": _p_windows_list,
    "windows.open": _p_windows_open,
    "windows.close": _p_windows_close,
    "windows.raise": _p_windows_raise,
    "windows.arrange": _p_windows_arrange,
    "windows.seat": _p_windows_seat,
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
