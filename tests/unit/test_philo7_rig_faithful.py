"""PHILO-7-01 round two (Astra's check on built, finding 1): the rig sends the SAME request.

The rig's ``op`` step projects a canonical operation onto the existing MCP
envelope (``scripts/graph_walk.py`` ``_op_request``). ``desk.get`` and
``desk.delete`` carry only ``kind`` and ``id``. Before this round, the read and
delete projections kept the id and DROPPED every other argument, so:

* a refused call became an execution — ``note.delete {note_id, owner:
  "forged"}`` is refused by the registry (``authority_in_arguments``), but the
  projected call deleted the note;
* valid Thought revisions disappeared — ``note.delete`` with the right cursors
  succeeds through ``invoke`` directly, but the projected call lost them and
  was refused ``thought_expected_revision_required``.

The rule now fenced, through the REAL hub (``MeetingWebServer`` over
``/api/mcp``): a projection either carries every argument of the case, or the
rig refuses the step by name (``Blocked``) before any request is sent. Never a
silent drop.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition
from scripts import graph_walk as gw

TOKEN = "philo7-01-rig"
OWNER = Principal(PrincipalKind.OWNER, "owner")


class _RealHub:
    """The rig's ``hub.mcp`` seam over the real hub app's ``POST /api/mcp``."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def mcp(self, request: dict[str, Any]) -> dict[str, Any]:
        resp = self.client.post("/api/mcp", json=request)
        return resp.json()


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "rig.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield composition.installed(), client
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _sent_arguments(request: dict[str, Any]) -> dict[str, Any]:
    arguments = request["params"]["arguments"]
    return {**arguments, **(arguments.get("data") or {})}


def test_a_refused_call_never_becomes_an_execution_through_the_rig(hub) -> None:
    root, client = hub
    note = client.post("/api/notes", json={"id": "n", "title": "Keep me"})
    assert note.status_code == 201
    args = {"note_id": "n", "owner": "forged"}
    # Direct: the registry refuses it by name.
    from holdspeak import operations

    with pytest.raises(operations.OperationRefused) as refused:
        root.operations.invoke(OWNER, "note.delete", args)
    assert refused.value.code == "authority_in_arguments"
    # Through the rig: the same request, or a named refusal of the step.
    try:
        record = gw._op_call(_RealHub(client), "note.delete", args)
    except gw.Blocked as exc:
        assert "owner" in str(exc), exc
    else:
        assert record["refusal"] is not None, f"the rig executed a refused call: {record['request']}"
    assert client.get("/api/notes/n").status_code == 200, "the note was deleted by a call the registry refuses"


def test_valid_thought_revisions_never_disappear_through_the_rig(hub) -> None:
    root, client = hub
    assert client.post("/api/directories", json={"id": "hs-seed-inbox", "name": "Inbox"}).status_code == 201
    thought = client.post("/api/thoughts", json={"request_id": "rig-1", "raw_text": "raw", "source": {"kind": "typed"}}).json()["thought"]
    args = {"note_id": thought["working_note"]["id"],
            "expected_aggregate_revision": thought["aggregate_revision"],
            "expected_lifecycle_revision": thought["lifecycle_revision"]}
    try:
        record = gw._op_call(_RealHub(client), "note.delete", args)
    except gw.Blocked as exc:
        assert "expected_aggregate_revision" in str(exc), exc
        # Blocked before any request: the note is untouched.
        assert client.get(f"/api/notes/{args['note_id']}").status_code == 200
        return
    sent = _sent_arguments(record["request"])
    missing = sorted(set(args) - {"note_id"} - set(sent))
    assert not missing, (f"the rig dropped {missing}; the hub answered "
                         f"{record['refusal'] or record['response']}")


READ_DELETE = ["note.read", "note.delete", "zone.read", "zone.delete", "kb.read", "kb.delete", "decision.read"]


@pytest.mark.parametrize("name", READ_DELETE)
def test_no_read_or_delete_projection_drops_an_argument(name) -> None:
    id_field = {"note": "note_id", "zone": "directory_id", "kb": "kb_id", "decision": "decision_id"}[name.split(".")[0]]
    args = {id_field: "x", "extra_field": 1}
    try:
        request = gw._op_request(name, args, 1)
    except gw.Blocked as exc:
        assert "extra_field" in str(exc)
        return
    assert "extra_field" in json.dumps(request), f"{name} dropped extra_field: {request}"


def test_an_id_only_read_and_delete_still_project() -> None:
    request = gw._op_request("zone.delete", {"directory_id": "z"}, 1)
    assert request["params"] == {"name": "desk.delete", "arguments": {"kind": "directories", "id": "z"}}
    request = gw._op_request("note.read", {"note_id": "n"}, 2)
    assert request["params"] == {"name": "desk.get", "arguments": {"kind": "notes", "id": "n"}}
