"""PHILO-10-01: the Send contract, the saved destinations and the file channel.

Through the REAL hub on an isolated HOME (``TestClient`` over the hub's app and
``/api/mcp``), with the real producers: a published update from the Room's own
routes, a folder destination from ``channel.save_destination``, the file
channel's real write. A NEW capability: the red runs are the deliberate
mutations recorded in the evidence (``assets/story-01-proof/mutations.py.txt``).

* The nine operations are declared once and reach the ONE ``ChannelService``
  over HTTP and MCP (the rig's ``op`` step: ``test_philo10_rig_op.py``).
* Admission by effect: each admitted row is one kernel operation with one
  terminal receipt; each refusal class leaves its receipt; reads and previews
  leave none; an agent's send (and discard, save, remove) is refused
  ``owner_principal_required`` with a receipt; an agent's prepare completes
  under its own identity.
* The file channel: a new file per send (two sends, two files); the proof is
  the absolute path + the sha256 read back + the size; a name that leaves the
  folder is refused; FAILED only on the pinned create errors, UNKNOWN on any
  other error and on bytes that do not read back.
* What is sent is what was previewed: the preview is derived from the frozen
  bytes; a changed document refuses ``preview_changed``, a changed payload
  ``payload_changed``; an oversize payload ``payload_too_large:file``; the body
  never reaches argv, a kernel row, a receipt, the journal, a log or an error.
* Destinations: Edit parks and makes a new row; Remove parks; a destination
  changed or parked after prepare is refused before any effect, and the send
  row keeps the historical target.
* Send and Discard at once settle once. Manual rows read ``channel: manual``.
"""
from __future__ import annotations

import errno
import hashlib
import json
import logging
import os
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import (  # noqa: E402
    SENTINEL, DispatchSpy, Hub, _boot, destination, files, history, in_thread, op, ops, prepare, preview_digest, room,
    send, send_body, sends, sent_text, source,
)
from test_philo9_steward_admission import AGENT_ID, _agent, _tool  # noqa: E402

CHANNEL_OPS = ("channel.destinations", "channel.save_destination", "channel.remove_destination",
               "channel.check_destination", "channel.preview", "channel.prepare", "channel.discard",
               "channel.send", "channel.sends")
ADMITTED = ("channel.save_destination", "channel.remove_destination", "channel.prepare", "channel.discard",
            "channel.send")
SOURCE_KINDS = ["project_update", "desk_decision"]


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


# ── one declaration, one service, both transports ───────────────────────


def test_the_operations_are_declared_once_and_reach_one_service_over_http_and_mcp(hub: Hub) -> None:
    from holdspeak import operations

    declared = [d.name for d in operations.DESCRIPTORS if d.name.startswith("channel.")]
    # Secret saves are HTTP only; each secret is held, never an operation argument.
    assert declared == [*CHANNEL_OPS, "channel.save_email_key", "channel.save_slack_webhook"]
    registry = hub.root.operations
    service = hub.root.channel_service
    assert service is not None and hub.server.app is not None
    for name in CHANNEL_OPS:
        assert registry.target(name) is service, name
    listed = hub.client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    tools = {t["name"]: t for t in listed.json()["result"]["tools"]}
    for name in CHANNEL_OPS:
        descriptor = registry.descriptor(name)
        assert tools[name]["description"] == descriptor.description, name
        http = [e for e in descriptor.exposure if e.startswith("http:")]
        assert http and f"mcp:{name}" in descriptor.exposure, name
    assert "channel.save_email_key" not in tools
    assert "channel.save_slack_webhook" not in tools
    routes = {(m, r.path) for r in hub.server.app.routes for m in getattr(r, "methods", ()) or ()}
    for name in declared:
        for exposure in registry.descriptor(name).exposure:
            if exposure.startswith("http:"):
                method, path = exposure[5:].split(" ", 1)
                assert (method, path) in routes, exposure


def test_http_and_mcp_reach_the_same_rows(hub: Hub, tmp_path: Path) -> None:
    _pid, update = room(hub)
    dest = destination(hub, tmp_path / "out")
    is_error, prepared = hub.mcp("channel.prepare", {"document_ref": f"project_update:{update}", "destination_id": dest})
    assert is_error is False, prepared
    over_http = hub.client.get("/api/channels/sends", params={"document_ref": f"project_update:{update}"}).json()["sends"]
    assert [s["id"] for s in over_http] == [prepared["send"]["id"]]
    is_error, listed = hub.mcp("channel.sends", {"document_ref": f"project_update:{update}"})
    assert is_error is False and listed["sends"] == over_http


# ── admission by effect ─────────────────────────────────────────────────


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_each_admitted_row_is_one_operation_with_one_terminal_receipt(hub: Hub, tmp_path: Path, transport: str) -> None:
    _pid, update = room(hub)

    def call(name: str, args: dict[str, Any], http: Any) -> dict[str, Any]:
        if transport == "mcp":
            is_error, body = hub.mcp(name, args)
            assert is_error is False, (name, body)
            return body
        resp = http()
        assert resp.status_code == 200, (name, resp.text)
        return resp.json()

    c = hub.client
    folder = tmp_path / "out"
    folder.mkdir()
    saved = call("channel.save_destination", {"name": "Team", "channel": "file", "folder": str(folder)},
                 lambda: c.post("/api/channels/destinations", json={"name": "Team", "channel": "file", "folder": str(folder)}))
    dest = saved["destination"]["id"]
    first = call("channel.prepare", {"document_ref": f"project_update:{update}", "destination_id": dest},
                 lambda: c.post("/api/channels/sends", json={"document_ref": f"project_update:{update}", "destination_id": dest}))
    second = call("channel.prepare", {"document_ref": f"project_update:{update}", "destination_id": dest},
                  lambda: c.post("/api/channels/sends", json={"document_ref": f"project_update:{update}", "destination_id": dest}))
    discarded = call("channel.discard", {"send_id": second["send"]["id"]},
                     lambda: c.post(f"/api/channels/sends/{second['send']['id']}/discard", json={}))
    sent = call("channel.send", {"send_id": first["send"]["id"]},
                lambda: c.post("/api/channels/send", json={"send_id": first["send"]["id"]}))
    removed = call("channel.remove_destination", {"destination_id": dest},
                   lambda: c.delete(f"/api/channels/destinations/{dest}"))
    answers = {"channel.save_destination": [saved], "channel.prepare": [first, second], "channel.discard": [discarded],
               "channel.send": [sent], "channel.remove_destination": [removed]}
    for name, bodies in answers.items():
        rows = ops(hub, name)
        assert len(rows) == len(bodies), (name, rows)
        for row, body in zip(rows, bodies):
            assert body["operation_id"] == row["operation_id"] and body["receipt"]["state"] == "succeeded", name
            assert (row["state"], row["receipts"], row["principal_kind"]) == ("succeeded", 1, "owner"), row
    assert sent["outcome"] == "sent" and discarded["send"]["state"] == "discarded"
    assert removed["destination"]["state"] == "parked"


def test_reads_and_previews_leave_no_operation(hub: Hub, tmp_path: Path) -> None:
    _pid, update = room(hub)
    dest = destination(hub, tmp_path / "out")
    sent_id = prepare(hub, update, dest)["send"]["id"]
    before = len(ops(hub))
    c = hub.client
    assert c.get("/api/channels/destinations").status_code == 200
    assert c.post("/api/channels/preview", json={"document_ref": f"project_update:{update}", "destination_id": dest}).status_code == 200
    assert c.post(f"/api/channels/destinations/{dest}/check").json()["check"]["state"] == "ready"
    assert c.get("/api/channels/sends", params={"send_id": sent_id}).status_code == 200
    for name, args in (("channel.destinations", {}), ("channel.preview", {"document_ref": f"project_update:{update}", "destination_id": dest}),
                       ("channel.check_destination", {"destination_id": dest}), ("channel.sends", {})):
        is_error, body = hub.mcp(name, args)
        assert is_error is False, (name, body)
        assert "operation_id" not in body, name
    assert len(ops(hub)) == before


def _refused(hub: Hub, resp: Any, code: str, name: str) -> dict[str, Any]:
    body = resp.json()
    assert body.get("code") == code, body
    assert body.get("operation_id") and body.get("receipt"), f"{name}: a refusal without its receipt: {body}"
    row = op(hub, body["operation_id"])
    assert (row["name"], row["outcome"], row["receipts"]) == (name, code, 1), row
    return row


def test_each_refusal_class_leaves_its_receipt_and_sends_nothing(hub: Hub, tmp_path: Path) -> None:
    folder = tmp_path / "out"
    _pid, update = room(hub)
    _pid2, draft = room(hub, name="Draft room", publish=False)
    dest = destination(hub, folder)
    c = hub.client
    # destination not saved
    _refused(hub, c.post("/api/channels/sends", json={"document_ref": f"project_update:{update}", "destination_id": "chd_nope"}),
             "destination_not_saved", "channel.prepare")
    _refused(hub, c.post("/api/channels/send", json={"document_ref": f"project_update:{update}", "destination_id": "chd_nope",
                                                     "preview_digest": "0" * 64}),
             "destination_not_saved", "channel.send")
    # not published
    _refused(hub, c.post("/api/channels/sends", json={"document_ref": f"project_update:{draft}", "destination_id": dest}),
             "not_published", "channel.prepare")
    # preview changed: the digest he saw is not what would go now
    _refused(hub, c.post("/api/channels/send", json={"document_ref": f"project_update:{update}", "destination_id": dest,
                                                     "preview_digest": "0" * 64}),
             "preview_changed", "channel.send")
    # owner only (an agent's send): test_an_agents_send_is_refused_owner_principal_required
    assert files(folder) == [] and all(s["state"] == "prepared" for s in sends(hub))


@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required(
    hub: Hub, tmp_path: Path, source_kind: str,
) -> None:
    folder = tmp_path / "out"
    document_ref = source(hub, source_kind)
    dest = destination(hub, folder)
    prepared = prepare(hub, document_ref, dest)["send"]["id"]
    agent = _agent(hub)
    attempts = {
        "channel.send": ({"send_id": prepared}, lambda: agent.post("/api/channels/send", json={"send_id": prepared})),
        "channel.discard": ({"send_id": prepared},
                            lambda: agent.post(f"/api/channels/sends/{prepared}/discard", json={})),
        "channel.save_destination": ({"name": "Mine", "channel": "file", "folder": str(folder)},
                                     lambda: agent.post("/api/channels/destinations",
                                                        json={"name": "Mine", "channel": "file", "folder": str(folder)})),
        "channel.remove_destination": ({"destination_id": dest},
                                       lambda: agent.delete(f"/api/channels/destinations/{dest}")),
    }
    for name, (args, http) in attempts.items():
        is_error, body = _tool(agent, name, args)
        assert is_error, (name, body)
        row = op(hub, body["operation_id"])
        assert (body["code"], row["name"], row["principal_kind"], row["outcome"]) == (
            "owner_principal_required", name, "agent", "owner_principal_required"), (name, body, row)
        resp = http()
        assert resp.status_code == 403, (name, resp.text)
        assert op(hub, resp.json()["operation_id"])["outcome"] == "owner_principal_required", name
    assert files(folder) == []
    assert [s["state"] for s in sends(hub)] == ["prepared"]
    assert hub.db.channel_destinations.get(dest)["state"] == "active"


@pytest.mark.parametrize("transport", ["mcp", "http"])
@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner(
    hub: Hub, tmp_path: Path, transport: str, source_kind: str,
) -> None:
    folder = tmp_path / "out"
    document_ref = source(hub, source_kind)
    dest = destination(hub, folder)
    agent = _agent(hub)
    if transport == "mcp":
        is_error, body = _tool(agent, "channel.prepare", {"document_ref": document_ref, "destination_id": dest})
        assert is_error is False, body
    else:
        resp = agent.post("/api/channels/sends", json={"document_ref": document_ref, "destination_id": dest})
        assert resp.status_code == 200, resp.text
        body = resp.json()
    row = op(hub, body["operation_id"])
    assert (row["name"], row["state"], row["principal_kind"], row["principal_identity"]) == (
        "channel.prepare", "succeeded", "agent", AGENT_ID)
    assert body["send"]["state"] == "prepared"
    assert body["send"]["prepared_by"] == {"kind": "agent", "identity": AGENT_ID}
    assert files(folder) == []  # nothing left the machine
    # The owner sends what the agent prepared.
    sent = send(hub, {"send_id": body["send"]["id"]})
    assert sent.status_code == 200 and sent.json()["outcome"] == "sent", sent.text
    assert len(files(folder)) == 1


def test_the_channel_tools_sit_in_the_agents_project_palette() -> None:
    from holdspeak.mcp.palettes import resolve_palette

    assert set(CHANNEL_OPS) <= resolve_palette("PROJECT")


# ── the file channel ────────────────────────────────────────────────────


def test_two_sends_of_one_update_to_one_folder_make_two_files_with_their_proof(hub: Hub, tmp_path: Path) -> None:
    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    answers = []
    for key in ("press-1", "press-2"):
        resp = send(hub, send_body(hub, "send_id", update, dest, key))
        assert resp.status_code == 200, resp.text
        answers.append(resp.json())
    on_disk = files(folder)
    assert len(on_disk) == 2
    for answer in answers:
        proof = answer["send"]["proof"]
        path = Path(proof["path"])
        assert path.is_absolute() and path in on_disk
        data = path.read_bytes()
        assert proof["sha256"] == hashlib.sha256(data).hexdigest() == answer["send"]["payload_digest"]
        assert proof["size"] == len(data)
        assert answer["send"]["file_path"] == str(path)
        assert path.name.endswith(f"-rev-1-{answer['send']['id'].split('_')[-1][:8]}.md"), path.name
    rows = history(hub, update)
    assert [(r["channel"], r["outcome"], r["send_id"]) for r in rows] == [
        ("file", "sent", a["send"]["id"]) for a in answers]
    assert [json.loads(r["proof_json"]) for r in rows] == [a["send"]["proof"] for a in answers]


def test_the_suffix_and_exclusive_create_never_write_over_an_old_file(hub: Hub, tmp_path: Path) -> None:
    from holdspeak.services.channel_contract import FileChannel, render_update

    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    prepared = prepare(hub, update, dest)["send"]
    document = render_update(hub.db, update)
    taken = FileChannel().choose_path(str(folder.resolve()), document, prepared["id"])
    Path(taken).write_text("his own file")
    resp = send(hub, {"send_id": prepared["id"]})
    assert resp.status_code == 200 and resp.json()["outcome"] == "sent", resp.text
    assert Path(taken).read_text() == "his own file"
    assert resp.json()["send"]["file_path"] == taken[:-3] + "-2.md"


def test_a_name_that_leaves_the_folder_is_refused(hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_contract

    folder = tmp_path / "out"
    # The real producer sanitizes a hostile project name: the file stays in the folder.
    _pid, update = room(hub, name="../../../etc/escape")
    dest = destination(hub, folder)
    resp = send(hub, send_body(hub, "send_id", update, dest, "k-name"))
    assert resp.status_code == 200, resp.text
    assert Path(resp.json()["send"]["file_path"]).parent == folder.resolve()
    # A name that tries to leave the folder anyway is refused by name, before any effect.
    monkeypatch.setattr(channel_contract, "_slug", lambda name: "../../escape")
    spy = DispatchSpy(monkeypatch)
    refused = send(hub, send_body(hub, "send_id", update, dest, "k-escape"))
    _refused(hub, refused, "path_outside_folder", "channel.send")
    assert spy.calls == 0 and len(files(folder)) == 1
    outside = [q for q in tmp_path.resolve().glob("**/*.md") if q.parent != folder.resolve()]
    assert outside == [] and not (tmp_path / "escape").exists()


def test_a_create_refused_by_the_os_is_failed_and_writes_no_history(hub: Hub, tmp_path: Path) -> None:
    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    folder.chmod(0o500)
    try:
        resp = send(hub, send_body(hub, "send_id", update, dest, "k-eacces"))
    finally:
        folder.chmod(0o700)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert (body["outcome"], body["send"]["reason"]) == ("failed", "permission_denied")
    assert (op(hub, body["operation_id"])["state"], body["receipt"]["outcome"]) == ("failed", "permission_denied")
    assert files(folder) == [] and history(hub, update) == []


def test_an_error_off_the_pinned_list_and_bytes_that_do_not_read_back_are_unknown(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.services import channel_contract

    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    real_write = os.write

    def eio(fd: int, data: Any) -> int:
        raise OSError(errno.EIO, "I/O error")

    monkeypatch.setattr(channel_contract.os, "write", eio)
    first = send(hub, send_body(hub, "send_id", update, dest, "k-eio")).json()
    monkeypatch.setattr(channel_contract.os, "write", real_write)
    assert (first["outcome"], first["send"]["reason"]) == ("unknown", "write_eio"), first
    assert op(hub, first["operation_id"])["state"] == "indeterminate"
    # A malformed proof: the bytes on disk are not the payload.
    monkeypatch.setattr(channel_contract.os, "write", lambda fd, data: real_write(fd, bytes(data)[:-1] + b"X"))
    second = send(hub, send_body(hub, "send_id", update, dest, "k-mismatch")).json()
    assert (second["outcome"], second["send"]["reason"]) == ("unknown", "read_back_mismatch"), second
    assert [r["outcome"] for r in history(hub, update)] == ["unknown", "unknown"]


# ── what is sent is what was previewed ──────────────────────────────────


@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_the_preview_is_the_frozen_bytes_and_the_file_is_those_bytes(
    hub: Hub, tmp_path: Path, source_kind: str,
) -> None:
    folder = tmp_path / "out"
    if source_kind == "project_update":
        body = f"# Status\n\nThe cutover is on track. {SENTINEL}\n"
        _pid, update = room(hub, body=body)
        document_ref = f"project_update:{update}"
    else:
        document_ref = source(hub, source_kind)
    dest = destination(hub, folder)
    previewed = hub.client.post("/api/channels/preview", json={"document_ref": document_ref, "destination_id": dest}).json()
    prepared = prepare(hub, document_ref, dest)["send"]
    if source_kind == "project_update":
        # PHILO-15 B53: the sent bytes are the body under its heading.
        payload = sent_text(body)
        assert previewed["preview"]["text"] == prepared["preview"]["text"] == payload
    else:
        payload = prepared["preview"]["text"]
        assert previewed["preview"]["text"] == payload
    assert previewed["payload_digest"] == prepared["payload_digest"] == hashlib.sha256(payload.encode()).hexdigest()
    resp = send(hub, {"send_id": prepared["id"]}).json()
    assert Path(resp["send"]["proof"]["path"]).read_bytes() == payload.encode()


def test_a_changed_payload_is_refused_before_any_effect(hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    prepared = prepare(hub, update, dest)["send"]
    with hub.db._connection() as conn:
        conn.execute("UPDATE channel_sends SET payload=? WHERE id=?", (b"not what he saw", prepared["id"]))
    spy = DispatchSpy(monkeypatch)
    _refused(hub, send(hub, {"send_id": prepared["id"]}), "payload_changed", "channel.send")
    assert spy.calls == 0 and files(folder) == [] and sends(hub)[0]["state"] == "prepared"


def test_an_oversize_payload_is_refused_by_name(hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_contract

    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    prepared = prepare(hub, update, dest)["send"]
    monkeypatch.setitem(channel_contract.SIZE_LIMITS, "file", (10, "bytes"))
    _refused(hub, hub.client.post("/api/channels/sends", json={"document_ref": f"project_update:{update}", "destination_id": dest}),
             "payload_too_large:file", "channel.prepare")
    _refused(hub, send(hub, {"send_id": prepared["id"]}), "payload_too_large:file", "channel.send")
    assert files(folder) == []


def test_the_body_never_reaches_a_kernel_row_a_receipt_the_journal_a_log_or_an_error(
    hub: Hub, tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    folder = tmp_path / "out"
    _pid, update = room(hub, body=f"# Status\n\n{SENTINEL} on track.\n")
    dest = destination(hub, folder)
    caplog.set_level(logging.DEBUG)
    answers: list[str] = []
    ok = send(hub, send_body(hub, "send_id", update, dest, "k-1"))
    inline = send(hub, send_body(hub, "inline", update, dest, "k-2"))
    answers += [ok.text, inline.text]
    # refusals and a failure carry no body either
    prepared = prepare(hub, update, dest)["send"]["id"]
    with hub.db._connection() as conn:
        conn.execute("UPDATE channel_sends SET payload=? WHERE id=?", (f"{SENTINEL} tampered".encode(), prepared))
    changed = send(hub, {"send_id": prepared})
    answers.append(json.dumps({k: v for k, v in changed.json().items() if k != "send"}))
    folder.chmod(0o500)
    try:
        failed = send(hub, send_body(hub, "send_id", update, dest, "k-3"))
    finally:
        folder.chmod(0o700)
    answers.append(json.dumps({k: v for k, v in failed.json().items() if k != "send"}))
    for text in answers:
        payload_free = json.loads(text)
        payload_free.get("send", {}).pop("preview", None)  # the preview IS the body, by design
        assert SENTINEL not in json.dumps(payload_free), text[:400]
    with hub.db._connection() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'kernel%'")]
        for table in tables:
            for row in conn.execute(f"SELECT * FROM {table}"):
                assert SENTINEL not in json.dumps([str(v) for v in tuple(row)]), table
    assert SENTINEL not in caplog.text


def test_the_private_payload_file_is_0600_in_0700_and_its_digest_is_checked(tmp_path: Path) -> None:
    from holdspeak.services.channel_contract import ChannelRefused, private_payload_file, sha256

    payload = f"{SENTINEL}\nbody".encode()
    with private_payload_file(payload, sha256(payload)) as path:
        assert os.stat(path).st_mode & 0o777 == 0o600
        assert os.stat(os.path.dirname(path)).st_mode & 0o777 == 0o700
        assert Path(path).read_bytes() == payload
    assert not os.path.exists(path) and not os.path.exists(os.path.dirname(path))
    with pytest.raises(ChannelRefused) as refused:
        with private_payload_file(payload, "0" * 64):
            pytest.fail("the command ran with a changed payload")
    assert refused.value.code == "payload_changed"


def test_an_error_is_redacted_and_cut() -> None:
    from holdspeak.services.channel_contract import redact

    payload = f"line one of the body\n{SENTINEL} inside the body text\n".encode()
    text = f"gh: failed\nparse error near: {SENTINEL} inside the body text\n" + "x" * 500
    cleaned = redact(text, payload)
    assert SENTINEL not in cleaned and cleaned.startswith("gh: failed") and len(cleaned) <= 240


def test_an_excerpt_of_the_payload_and_a_secret_are_redacted() -> None:
    """Astra r1 finding 3: an excerpt (not a whole line) of the body, inside a CLI's error."""
    from holdspeak.services.channel_contract import redact

    payload = b"# Update\n\nThe SENTINEL-BODY-PRIVATE-94c2 cutover slipped by a week.\n"
    cleaned = redact("parse error near SENTINEL-BODY-PRIVATE-94c2", payload)
    assert "SENTINEL" not in cleaned and "94c2" not in cleaned and cleaned.startswith("parse error near"), cleaned
    assert "slipped by a" not in redact("gh: 422 near 'cutover slipped by a week' in body", payload)
    assert redact("gh: not found", payload) == "gh: not found"  # an error with no excerpt is kept
    secret = redact("HTTP 401 Authorization: Bearer abc123def ghp_abcdefghijklmnop1234 key s3cr3tvalue",
                    b"", secrets=["s3cr3tvalue"])
    assert not any(v in secret for v in ("abc123def", "ghp_", "s3cr3tvalue")), secret


# ── destinations: frozen twice, park never delete ───────────────────────


def test_edit_parks_the_old_row_and_a_send_prepared_to_it_is_refused_with_the_historical_target(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_folder, second_folder = tmp_path / "a", tmp_path / "b"
    _pid, update = room(hub)
    dest = destination(hub, first_folder)
    prepared = prepare(hub, update, dest)["send"]
    second_folder.mkdir()
    edited = hub.client.post("/api/channels/destinations", json={
        "name": "Team folder", "channel": "file", "folder": str(second_folder), "replaces": dest}).json()
    assert edited["replaced"] == dest and edited["destination"]["id"] != dest
    listed = hub.client.get("/api/channels/destinations", params={"include_parked": True}).json()["destinations"]
    assert {d["id"]: d["state"] for d in listed} == {dest: "parked", edited["destination"]["id"]: "active",
                                                     "holdspeak-folder": "active"}  # the built-in folder stays
    spy = DispatchSpy(monkeypatch)
    _refused(hub, send(hub, {"send_id": prepared["id"]}), "destination_parked", "channel.send")
    row = sends(hub)[0]
    assert row["state"] == "prepared" and json.loads(row["target_json"]) == {"folder": str(first_folder.resolve())}
    assert spy.calls == 0 and files(first_folder) == files(second_folder) == []


def test_a_destination_whose_target_changed_after_prepare_is_refused(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    real, other, link = tmp_path / "real", tmp_path / "other", tmp_path / "link"
    real.mkdir()
    other.mkdir()
    link.symlink_to(real)
    _pid, update = room(hub)
    dest = destination(hub, link)  # saved as its realpath
    prepared = prepare(hub, update, dest)["send"]
    spy = DispatchSpy(monkeypatch)
    # The folder moved: the saved path now resolves elsewhere.
    real.rename(tmp_path / "moved")
    (tmp_path / "real").symlink_to(other)
    _refused(hub, send(hub, {"send_id": prepared["id"]}), "destination_changed", "channel.send")
    # The saved row itself changed (a different target digest than the send froze).
    (tmp_path / "real").unlink()
    (tmp_path / "moved").rename(real)
    with hub.db._connection() as conn:
        conn.execute("UPDATE channel_destinations SET target_digest=? WHERE id=?", ("f" * 64, dest))
    _refused(hub, send(hub, {"send_id": prepared["id"]}), "destination_changed", "channel.send")
    assert spy.calls == 0 and files(real) == files(other) == []
    assert sends(hub)[0]["state"] == "prepared"


def test_remove_parks_and_keeps_history(hub: Hub, tmp_path: Path) -> None:
    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    assert send(hub, send_body(hub, "send_id", update, dest, "k")).json()["outcome"] == "sent"
    removed = hub.client.delete(f"/api/channels/destinations/{dest}")
    assert removed.status_code == 200 and removed.json()["destination"]["state"] == "parked"
    # Only the built-in HoldSpeak folder stays listed.
    assert [d["id"] for d in hub.client.get("/api/channels/destinations").json()["destinations"]] == ["holdspeak-folder"]
    assert hub.db.channel_destinations.get(dest)["state"] == "parked"
    assert [s["destination_id"] for s in sends(hub)] == [dest] and len(history(hub, update)) == 1
    again = hub.client.delete(f"/api/channels/destinations/{dest}")
    assert again.status_code == 409 and again.json()["code"] == "destination_parked"


@pytest.mark.parametrize("form", ["send_id", "inline"])
def test_a_remove_that_commits_before_the_boundary_wins_and_nothing_is_dispatched(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, form: str,
) -> None:
    """Astra r1 finding 2: Remove commits after the send's first destination read, before its boundary."""
    from holdspeak.services.channel_contract import FileChannel

    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    body = send_body(hub, form, update, dest, f"race-{form}")
    spy = DispatchSpy(monkeypatch)
    real = FileChannel.choose_path
    removed: list[Any] = []

    def choose_path(channel: Any, folder_: str, document: Any, send_id: str) -> str:
        if not removed:  # the Remove lands here: after the early read, before the boundary
            thread, box = in_thread(lambda: hub.client.delete(f"/api/channels/destinations/{dest}"))
            thread.join(30)
            removed.extend(box)
        return real(channel, folder_, document, send_id)

    monkeypatch.setattr(FileChannel, "choose_path", choose_path)
    resp = send(hub, body)
    assert removed and removed[0].status_code == 200, removed
    assert removed[0].json()["destination"]["state"] == "parked"
    _refused(hub, resp, "destination_parked", "channel.send")
    assert spy.calls == 0 and files(folder) == [] and history(hub, update) == []
    assert [s["state"] for s in sends(hub)] == (["prepared"] if form == "send_id" else [])


@pytest.mark.parametrize("form", ["send_id", "inline"])
def test_a_remove_after_the_boundary_parks_and_the_send_stands(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, form: str,
) -> None:
    folder = tmp_path / "out"
    _pid, update = room(hub)
    dest = destination(hub, folder)
    body = send_body(hub, form, update, dest, f"race-after-{form}")
    spy = DispatchSpy(monkeypatch, hold="before")
    thread, answer = in_thread(lambda: send(hub, body))
    assert spy.entered.wait(30)  # the boundary is committed; the effect has not run
    removed = hub.client.delete(f"/api/channels/destinations/{dest}")
    assert removed.status_code == 200 and removed.json()["destination"]["state"] == "parked"
    spy.release.set()
    thread.join(60)
    [sent] = answer
    assert sent.status_code == 200 and sent.json()["outcome"] == "sent", sent.text
    assert spy.calls == 1 and len(files(folder)) == 1 and len(history(hub, update)) == 1
    assert hub.db.channel_destinations.get(dest)["state"] == "parked"


def test_a_folder_marked_synced_is_badged_cloud(hub: Hub, tmp_path: Path) -> None:
    local = destination(hub, tmp_path / "local")
    synced = destination(hub, tmp_path / "synced", name="Synced", synced=True)
    badges = {d["id"]: d["badge"] for d in hub.client.get("/api/channels/destinations").json()["destinations"]}
    assert badges == {local: "local", synced: "cloud", "holdspeak-folder": "local"}


# ── Send and Discard at once: one wins ──────────────────────────────────


@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_send_and_discard_pressed_together_settle_once(hub: Hub, tmp_path: Path, source_kind: str) -> None:
    folder = tmp_path / "out"
    document_ref = source(hub, source_kind)
    dest = destination(hub, folder)
    winners = []
    for index in range(4):
        sid = prepare(hub, document_ref, dest)["send"]["id"]
        start = threading.Barrier(2)
        answers: dict[str, Any] = {}

        def press(kind: str) -> None:
            start.wait(5)
            answers[kind] = (hub.client.post("/api/channels/send", json={"send_id": sid}) if kind == "send"
                             else hub.client.post(f"/api/channels/sends/{sid}/discard", json={}))

        threads = [threading.Thread(target=press, args=(k,)) for k in ("send", "discard")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(60)
        codes = {k: v.status_code for k, v in answers.items()}
        assert sorted(codes.values()) == [200, 409], {k: v.text for k, v in answers.items()}
        loser = next(k for k, v in codes.items() if v == 409)
        body = answers[loser].json()
        assert body["code"] == "send_already_settled" and body.get("receipt"), body
        assert op(hub, body["operation_id"])["outcome"] == "send_already_settled"
        state = hub.db.channel_sends.get(sid)["state"]
        winner = next(k for k, v in codes.items() if v == 200)
        assert state == ("sent" if winner == "send" else "discarded")
        winners.append(winner)
    assert len(files(folder)) == winners.count("send")


@pytest.mark.parametrize("source_kind", SOURCE_KINDS)
def test_a_discard_pressed_while_the_send_dispatches_is_refused_and_the_send_stands(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source_kind: str,
) -> None:
    """The race above made deterministic: Discard lands after the send's boundary committed."""
    folder = tmp_path / "out"
    document_ref = source(hub, source_kind)
    dest = destination(hub, folder)
    sid = prepare(hub, document_ref, dest)["send"]["id"]
    spy = DispatchSpy(monkeypatch, hold="before")
    thread, answer = in_thread(lambda: hub.client.post("/api/channels/send", json={"send_id": sid}))
    assert spy.entered.wait(30)
    discarded = hub.client.post(f"/api/channels/sends/{sid}/discard", json={})
    spy.release.set()
    thread.join(60)
    _refused(hub, discarded, "send_already_settled", "channel.discard")
    [sent] = answer
    assert sent.status_code == 200 and sent.json()["outcome"] == "sent", sent.text
    assert hub.db.channel_sends.get(sid)["state"] == "sent" and len(files(folder)) == 1 and spy.calls == 1


# ── the manual channel is unchanged ─────────────────────────────────────


def test_manual_rows_read_channel_manual(hub: Hub, tmp_path: Path) -> None:
    pid, update = room(hub)
    marked = hub.client.post(f"/api/updates/{update}/delivered", json={"delivered_to": "Priya"})
    assert marked.status_code == 200, marked.text
    [row] = history(hub, update)
    assert (row["channel"], row["outcome"], row["send_id"], row["proof_json"]) == ("manual", "confirmed", None, None)
    listed = hub.client.get(f"/api/projects/{pid}/updates").json()["updates"]
    assert next(u for u in listed if u["id"] == update)["deliveries"][0]["channel"] == "manual"


def test_an_existing_database_gains_the_columns_and_its_rows_read_manual(tmp_path: Path) -> None:
    from holdspeak.db import Database

    path = tmp_path / "old.db"
    Database(path)
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE project_update_deliveries")
    conn.execute("CREATE TABLE project_update_deliveries (id TEXT PRIMARY KEY, update_id TEXT NOT NULL, project_id TEXT"
                 " NOT NULL, delivered_at TEXT NOT NULL, delivered_to TEXT, operation_id TEXT NOT NULL UNIQUE)")
    conn.execute("INSERT INTO project_update_deliveries VALUES ('pdel_old','u','p','t','Priya','op_old')")
    conn.execute("DROP TABLE channel_sends")
    conn.execute("DROP TABLE channel_destinations")
    conn.commit()
    conn.close()
    Database(path)  # opening it reconciles, additive only
    conn = sqlite3.connect(path)
    row = conn.execute("SELECT channel, outcome, send_id FROM project_update_deliveries WHERE id='pdel_old'").fetchone()
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert row == ("manual", "confirmed", None)
    assert {"channel_sends", "channel_destinations"} <= names


# ── discovery: the words ────────────────────────────────────────────────


def test_the_words_map_his_asks_and_never_say_an_agent_sends(hub: Hub) -> None:
    listed = hub.client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    tools = {t["name"]: t for t in listed.json()["result"]["tools"] if t["name"].startswith("channel.")}
    asks = {
        "where can I send": ("channel.destinations", "Where can I send"),
        "send my update to <destination>": ("channel.prepare", "send the update to <destination>"),
        "prepare a send": ("channel.prepare", "Prepare a send"),
        "what was sent": ("channel.sends", "What was sent"),
        "send it (the owner)": ("channel.send", "The owner's Send"),
    }
    for ask, (tool, words) in asks.items():
        assert words in tools[tool]["description"], (ask, tools[tool]["description"])
    for name, tool in tools.items():
        text = tool["description"].lower()
        assert "agent can send" not in text and "agents send" not in text and "agent sends" not in text, name
        assert "delivered to" not in text and "inbox" not in text, name
        if "agent" in text:
            assert "prepare" in text, name
    assert "only the owner sends" in tools["channel.send"]["description"].lower()
    assert "document_ref" in tools["channel.prepare"]["inputSchema"]["properties"]
    assert "destination_id" in tools["channel.prepare"]["inputSchema"]["properties"]
