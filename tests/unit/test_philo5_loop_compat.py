"""PHILO-5-02: the loop's compatibility table -- base outcomes kept.

Each row calls one migrated entry point (an HTTP route, an MCP tool or an MCP
resource) with one input and reduces the answer to its observable outcome: the
status or ``isError``, and the fields a client reads. The expected column is
the outcome on base ``6e707ff3``; this file imports no symbol PHILO-5-02 adds,
so it runs unchanged on a ``git archive 6e707ff3`` copy (the base column) and
on the built tree. Accepted stays accepted, refused stays refused, with the
same envelope (Astra's PHILO-5-01 scars: never slice an already-limited list;
never narrow accepted inputs; refusals keep their envelope).

The three NEW tools (``meeting.import``, ``monday_brief.shelf``,
``monday_brief.shelf_read``) have no base row: they did not exist.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

TOKEN = "philo5-02-compat"


class Hub:
    def __init__(self, client: Any) -> None:
        self.client = client

    def mcp(self, name: str, arguments: dict[str, Any]) -> tuple[bool, Any]:
        resp = self.client.post("/api/mcp", json={
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        result = resp.json()["result"]
        return result["isError"], json.loads(result["content"][0]["text"])

    def resource(self, uri: str) -> tuple[str, Any]:
        body = self.client.post("/api/mcp", json={
            "jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": uri},
        }).json()
        if "error" in body:
            return "error", body["error"]["code"]
        return "ok", json.loads(body["result"]["contents"][0]["text"])


@pytest.fixture(scope="module")
def hub(tmp_path_factory: pytest.TempPathFactory):
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    tmp = tmp_path_factory.mktemp("loop-compat")
    patch = pytest.MonkeyPatch()
    patch.setattr(db_core, "DEFAULT_DB_PATH", tmp / "compat.db")
    patch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp / "people.key"))
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    db = get_database()
    db.directories.upsert(directory_id="hs-seed-inbox", name="Inbox")
    for index in range(3):
        db.meetings.save_meeting(MeetingState(
            id=f"m-compat-{index}", started_at=datetime.datetime(2026, 9, 1 + index, 9),
            title=f"Compat {index}", tags=["compat"],
            segments=[TranscriptSegment(text=f"words {index}", speaker="Me", start_time=0.0, end_time=1.0)],
        ))
    db.meetings.save_meeting(MeetingState(id="m-empty", started_at=datetime.datetime(2026, 9, 5, 9), title="Empty"))
    # Two seeded Thoughts, so every row stands alone (xdist splits the rows
    # across workers, each with its own hub).
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    for index in range(2):
        RefinementThoughtService(db).create(
            Principal(PrincipalKind.OWNER, "owner"), request_id=f"compat-seed-{index}",
            raw_text=f"seed {index}", source={"kind": "typed"},
        )
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield Hub(client)
    reset_database()
    composition.install(composition.bare(label="pytest"))
    patch.undo()


def _http(response: Any, *fields: str) -> tuple[Any, ...]:
    body = response.json()
    picked = tuple(body.get(field) if isinstance(body, dict) else None for field in fields)
    return (response.status_code, *picked)


def _keys(value: Any, *names: str) -> tuple[bool, ...]:
    return tuple(isinstance(value, dict) and name in value for name in names)


# (label, call(hub) -> observed outcome, base outcome)
ROWS: list[tuple[str, Callable[[Hub], Any], Any]] = [
    # meeting.list
    ("http list default", lambda h: (h.client.get("/api/meetings").status_code, len(h.client.get("/api/meetings").json()["meetings"]), "next_cursor" in h.client.get("/api/meetings").json()), (200, 4, False)),
    ("http list limit=0 clamps to 1", lambda h: len(h.client.get("/api/meetings?limit=0").json()["meetings"]), 1),
    ("http list limit=1000", lambda h: len(h.client.get("/api/meetings?limit=1000").json()["meetings"]), 4),
    ("http list offset=2", lambda h: len(h.client.get("/api/meetings?offset=2").json()["meetings"]), 2),
    ("http list q refused", lambda h: _http(h.client.get("/api/meetings?q=x"), "error"), (422, "unsupported query parameter 'q'; use 'search'")),
    ("http list tag", lambda h: len(h.client.get("/api/meetings?tag=compat").json()["meetings"]), 3),
    ("mcp list default", lambda h: (lambda r: (r[0], len(r[1]["meetings"]), "next_cursor" in r[1]))(h.mcp("meeting.list", {})), (False, 4, True)),
    ("mcp list limit=2", lambda h: (lambda r: (r[0], len(r[1]["meetings"])))(h.mcp("meeting.list", {"limit": 2})), (False, 2)),
    ("mcp list limit=0 refused", lambda h: h.mcp("meeting.list", {"limit": 0})[0], True),
    ("mcp list cursor int", lambda h: (lambda r: (r[0], len(r[1]["meetings"])))(h.mcp("meeting.list", {"cursor": 3})), (False, 1)),
    ("mcp list bogus refused", lambda h: h.mcp("meeting.list", {"bogus": 1})[0], True),
    # meeting.read
    ("http get", lambda h: _http(h.client.get("/api/meetings/m-compat-0"), "id", "title"), (200, "m-compat-0", "Compat 0")),
    ("http get missing", lambda h: (h.client.get("/api/meetings/nope").status_code, h.client.get("/api/meetings/nope").json()), (404, {"error": "Meeting not found"})),
    ("mcp get", lambda h: (lambda r: (r[0], r[1]["id"], "planned_route" in r[1]))(h.mcp("meeting.get", {"meeting_id": "m-compat-0"})), (False, "m-compat-0", True)),
    ("mcp get include", lambda h: (lambda r: (r[0], r[1]["id"]))(h.mcp("meeting.get", {"meeting_id": "m-compat-0", "include": "segments"})), (False, "m-compat-0")),
    ("mcp get missing", lambda h: (lambda r: (r[0], r[1].get("code")))(h.mcp("meeting.get", {"meeting_id": "nope"})), (True, "not_found")),
    ("resource meeting", lambda h: (lambda r: (r[0], r[1]["id"]))(h.resource("holdspeak://meetings/m-compat-1")), ("ok", "m-compat-1")),
    ("resource meeting missing", lambda h: h.resource("holdspeak://meetings/nope"), ("error", -32002)),
    # meeting.summary.run
    ("http run missing", lambda h: _http(h.client.post("/api/meetings/nope/intelligence/run", json={}), "success", "error"), (404, False, "Meeting not found")),
    ("http run no transcript", lambda h: _http(h.client.post("/api/meetings/m-empty/intelligence/run", json={}), "code"), (409, "empty")),
    ("http run no body", lambda h: h.client.post("/api/meetings/m-empty/intelligence/run").status_code, 409),
    ("mcp run missing", lambda h: (lambda r: (r[0], r[1].get("code")))(h.mcp("meeting.run_intelligence", {"meeting_id": "nope", "expected_selection_hash": "x"})), (True, "not_found")),
    ("mcp run no transcript", lambda h: (lambda r: (r[0], r[1].get("code")))(h.mcp("meeting.run_intelligence", {"meeting_id": "m-empty", "expected_selection_hash": "x"})), (True, "empty")),
    ("mcp run hash required", lambda h: h.mcp("meeting.run_intelligence", {"meeting_id": "m-empty"})[0], True),
    # brief.latest before any brief
    ("http latest none", lambda h: (h.client.get("/api/brief/latest").status_code, h.client.get("/api/brief/latest").json()), (200, None)),
    ("mcp get none", lambda h: h.mcp("monday_brief.get", {}), (False, None)),
    ("resource brief none", lambda h: h.resource("holdspeak://briefs/latest"), ("ok", None)),
    ("http shelf none", lambda h: _http(h.client.get("/api/brief/shelf")), (200,)),
    # brief.generate and after
    ("http generate", lambda h: (lambda r: (r.status_code, *_keys(r.json(), "id", "period_label", "generated_label", "shelf")))(h.client.post("/api/brief/generate")), (200, True, True, True, True)),
    ("mcp generate same day", lambda h: (lambda r: (r[0], r[1]["id"] == h.client.get("/api/brief/latest").json()["id"], *_keys(r[1], "period_label", "shelf")))(h.mcp("monday_brief.generate", {})), (False, True, False, True)),
    ("mcp get generate=true", lambda h: (lambda r: (r[0], r[1]["id"] == h.client.get("/api/brief/latest").json()["id"]))(h.mcp("monday_brief.get", {"generate": True})), (False, True)),
    ("mcp generate bogus refused", lambda h: h.mcp("monday_brief.generate", {"bogus": 1})[0], True),
    ("resource brief", lambda h: (h.client.post("/api/brief/generate").status_code, *(lambda r: (r[0], r[1]["id"] == h.client.get("/api/brief/latest").json()["id"]))(h.resource("holdspeak://briefs/latest"))), (200, "ok", True)),
    ("http shelf write unknown item", lambda h: (lambda r: (r.status_code, r.json()))(h.client.post("/api/brief/items/nope/shelf", json={"state": "deferred"})), (404, {"detail": "Unknown brief item: nope"})),
    ("http shelf write non-string state", lambda h: (lambda r: (r.status_code, r.json()))(h.client.post("/api/brief/items/nope/shelf", json={"state": 3})), (422, {"detail": "state must be a string"})),
    ("http shelf write unknown state", lambda h: (lambda r: (r.status_code, r.json()))(h.client.post("/api/brief/items/nope/shelf", json={"state": "filed"})), (422, {"detail": "Unknown shelf state: filed"})),
    ("http shelf write no state = clear", lambda h: (lambda r: (r.status_code, r.json()))(h.client.post("/api/brief/items/nope/shelf", json={})), (404, {"detail": "Unknown brief item: nope"})),
    ("http shelf read", lambda h: (h.client.get("/api/brief/shelf").status_code, h.client.get("/api/brief/shelf").json()), (200, {})),
    # thought.create
    ("http thought create", lambda h: (lambda r: (r.status_code, *_keys(r.json(), "thought", "default_context_receipt")))(h.client.post("/api/thoughts", json={"request_id": "compat-http-1", "raw_text": "hello", "source": {"kind": "typed"}})), (201, True, True)),
    ("http thought create closed", lambda h: _http(h.client.post("/api/thoughts", json={"request_id": "x", "raw_text": "y", "extra": 1}), "error"), (422, "thought_create_request_invalid")),
    ("http thought create not an object", lambda h: _http(h.client.post("/api/thoughts", content=b"[]", headers={"Content-Type": "application/json"}), "error"), (400, "expected a JSON object")),
    ("mcp thought create", lambda h: (lambda r: (r[0], *_keys(r[1], "thought", "default_context_receipt")))(h.mcp("thought.create", {"request_id": "compat-mcp-1", "raw_text": "hello"})), (False, True, True)),
    ("mcp thought create closed", lambda h: (lambda r: (r[0], r[1].get("code")))(h.mcp("thought.create", {"request_id": "x", "raw_text": "y", "extra": 1})), (True, "mcp_invalid_params")),
    ("mcp thought create replay", lambda h: (lambda r: (r[0], r[1]["thought"]["id"]))(h.mcp("thought.create", {"request_id": "compat-mcp-1", "raw_text": "hello"}))[0], False),
    # thought.read / workbench / list
    ("http thought get missing", lambda h: h.client.get("/api/thoughts/nope").status_code, 404),
    ("http thought workbench missing", lambda h: h.client.get("/api/thoughts/nope/workbench").status_code, 404),
    ("http thought list", lambda h: (lambda r: (r.status_code, len(r.json()["items"]) >= 2))(h.client.get("/api/thoughts")), (200, True)),
    ("http thought list state", lambda h: _http(h.client.get("/api/thoughts?state=done"), "error"), (422, "thought_list_state_invalid")),
    ("http thought list limit", lambda h: _http(h.client.get("/api/thoughts?limit=abc"), "error"), (422, "thought_list_limit_invalid")),
    ("http thought list limit=1", lambda h: len(h.client.get("/api/thoughts?limit=1").json()["items"]), 1),
    ("resource thoughts unfinished", lambda h: (lambda r: (r[0], len(r[1]["items"]) >= 2))(h.resource("holdspeak://thoughts/unfinished")), ("ok", True)),
    ("resource thought missing", lambda h: h.resource("holdspeak://thoughts/nope"), ("error", -32002)),
    ("resource workbench missing", lambda h: h.resource("holdspeak://thoughts/nope/workbench"), ("error", -32002)),
    # thought.save
    ("http thought save unknown", lambda h: h.client.patch("/api/thoughts/nope/working", json={"expected_aggregate_revision": 1, "expected_working_revision": 1}).status_code, 404),
    ("http thought save closed", lambda h: _http(h.client.patch("/api/thoughts/nope/working", json={"extra": 1}), "error"), (422, "thought_update_request_invalid")),
    ("mcp thought save unknown", lambda h: (lambda r: (r[0], r[1].get("code")))(h.mcp("thought.update_working", {"thought_id": "nope", "expected_aggregate_revision": 1, "expected_working_revision": 1})), (True, "not_found")),
    ("mcp thought save schema", lambda h: h.mcp("thought.update_working", {"thought_id": "nope"})[0], True),
]


@pytest.mark.parametrize(("label", "call", "base"), ROWS, ids=[row[0] for row in ROWS])
def test_the_loop_keeps_its_base_outcome(hub: Hub, label: str, call: Callable[[Hub], Any], base: Any) -> None:
    assert call(hub) == base


def test_thought_save_and_reads_keep_their_base_shapes(hub: Hub) -> None:
    made = hub.client.post("/api/thoughts", json={"request_id": "compat-save", "raw_text": "body", "source": {"kind": "typed"}}).json()["thought"]
    tid = made["id"]
    saved = hub.client.patch(f"/api/thoughts/{tid}/working", json={
        "expected_aggregate_revision": made["aggregate_revision"],
        "expected_working_revision": made["working_revision"], "title": "Saved"})
    assert saved.status_code == 200 and set(saved.json()) == {"thought", "workbench"}
    stale = hub.client.patch(f"/api/thoughts/{tid}/working", json={
        "expected_aggregate_revision": made["aggregate_revision"],
        "expected_working_revision": made["working_revision"], "title": "Stale"})
    assert stale.status_code == 409
    current = saved.json()["thought"]
    is_error, out = hub.mcp("thought.update_working", {
        "thought_id": tid, "expected_aggregate_revision": current["aggregate_revision"],
        "expected_working_revision": current["working_revision"], "title": "Saved again"})
    assert is_error is False and set(out) == {"thought", "workbench"}
    is_error, stale_mcp = hub.mcp("thought.update_working", {
        "thought_id": tid, "expected_aggregate_revision": current["aggregate_revision"],
        "expected_working_revision": current["working_revision"], "title": "Stale"})
    assert is_error is True and stale_mcp["code"] == stale.json()["error"]
    got = hub.client.get(f"/api/thoughts/{tid}").json()
    assert set(got) == {"thought"} and got["thought"]["working_note"]["title"] == "Saved again"
    status, detail = hub.resource(f"holdspeak://thoughts/{tid}")
    assert status == "ok" and set(detail) == {"thought"} and detail["thought"]["id"] == tid
    workbench = hub.client.get(f"/api/thoughts/{tid}/workbench")
    assert workbench.status_code == 200
    status, via_resource = hub.resource(f"holdspeak://thoughts/{tid}/workbench")
    assert status == "ok" and set(via_resource) == set(workbench.json())
