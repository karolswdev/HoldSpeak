"""Runs on, against a real hub: the hub half of the browser walks it replaces.

The test diet (2026-10-11): the browser walk of HS-201-09 checked the hub's
answers through the page. This file asks the same real hub (``_boot``: a
real MeetingWebServer, isolated HOME and DB) the same questions over HTTP,
in the order the Runs on face asks them, with the same local
OpenAI-compatible stub engine. No browser. The face's words for these
answers are fenced in web/src/desk/__tests__/runs-on.app.test.tsx.
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.engine_stub_rig import _StubHandler
from tests.e2e.glass_infra import _boot

TOKEN = "runs-on-hub"
SUMMARY_CAPABILITY = "meeting.deferred_analysis"
BAD_URL = "http://127.0.0.1:9/v1"  # discard port: always refuses

pytestmark = pytest.mark.timeout(120, method="thread")


def _call(base: str, method: str, path: str, body: Any = None) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else {}


def _ok(base: str, method: str, path: str, body: Any = None) -> Any:
    status, payload = _call(base, method, path, body)
    assert status < 300, (status, path, payload)
    return payload


@pytest.fixture()
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield base
    finally:
        server.stop()


@pytest.fixture()
def engine():
    """The same local stub the browser walk used when the LAN box was away."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _StubHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()


def _key_for(url: str) -> str:
    """endpointDraft.ts `endpointProfileId`: ``engine-<host-port slug>``."""
    host = url.split("://", 1)[1].split("/")[0]
    slug = "".join(c if c.isalnum() else "-" for c in host.lower()).strip("-")
    return f"engine-{slug}"[:96]


def _rows(base: str) -> dict[str, dict]:
    return {row["id"]: row for row in _ok(base, "GET", "/api/inference/assignments")["rows"]}


def _summary_task(base: str) -> dict:
    roster = _ok(base, "GET", "/api/inference/assignments")
    return next(t for t in roster["task_overrides"] if t["id"] == SUMMARY_CAPABILITY)


def _summary(base: str) -> dict:
    return _ok(base, "GET", "/api/concierge/detect")["summaryAssignment"]


def test_a_stranger_connects_an_engine_and_the_hub_keeps_his_choice(hub: str, engine: str) -> None:
    """replaces: tests/e2e/test_hs201_09_connect_engine_glass.py::TestConnectAnEngineFromTheFace::test_a_stranger_connects_an_engine_and_the_face_keeps_his_choice (hub half)

    Add engine -> bad address refused -> Check READY with the model -> Add
    (no wire) -> patch Meetings (the exact summary row) -> patch the Default
    -> Undo, Undo (summary back to inheritance) -> patch again over the
    tombstone.
    """
    base = hub
    key = _key_for(engine)

    # Nothing is assigned on this desk yet.
    assert _summary(base)["status"] == "unassigned"

    # A bad address: refused with a plain reason, never the socket's words.
    status, refused = _call(base, "POST", "/api/setup/discover-models", {"base_url": BAD_URL, "check_tools": True})
    assert status == 422 and refused["ok"] is False and refused["models"] == [], refused
    assert refused["detail"], refused
    assert "errno" not in refused["detail"].lower() and "urlopen" not in refused["detail"].lower(), refused

    # The engine's address: READY, and the model it serves is named.
    checked = _ok(base, "POST", "/api/setup/discover-models", {"base_url": engine, "check_tools": True})
    assert checked["ok"] is True and checked["models"] == [_StubHandler.MODEL], checked

    # Add: the Model Library defines it (endpointDraft.ts body); no assignment.
    host_port = engine.split("://", 1)[1].split("/")[0]
    defined = _ok(base, "POST", "/api/inference/model-library/define-endpoint", {
        "draft": {
            "request_id": "runs-on-hub-add", "profile_id": key, "expected_profile_revision": 0,
            "label": host_port, "provider_family": "openai_compatible", "model": _StubHandler.MODEL,
            "endpoint": engine, "requires_key": False,
        },
        "secret": None,
    })
    assert defined["provider"]["profile_id"] == key, defined
    revision = int(defined["provider"]["profile_revision"])
    assert revision >= 1
    detected = _ok(base, "GET", "/api/concierge/detect")
    assert any(e.get("profileId") == key for e in detected["engines"]), detected["engines"]
    wired = [
        row["id"] for row in _rows(base).values()
        if (row.get("assignment") or {}).get("entries")
        and row["inherited_from"] != "global"
        and any(e["profile_id"] == key for e in row["assignment"]["entries"])
    ]
    assert wired == [], f"an Add drew a wire: {wired}"

    # Patch Meetings: the group chain, then the exact summary row the queue reads.
    meetings = _rows(base)["meetings"]
    _ok(base, "POST", "/api/inference/assignments/set", {
        "command_id": "runs-on-hub-meetings", "expected_revision": meetings["expected_revision"],
        "scope": {"kind": "group", "group_id": "meetings"},
        "entries": [{"profile_id": key, "profile_revision": revision}],
    })
    before = _summary(base)
    chosen = _ok(base, "POST", "/api/concierge/summary-selection", {
        "commandId": "runs-on-hub-summary", "expectedAssignmentRevision": before["assignmentRevision"],
        "profileId": key, "profileRevision": revision,
    })
    assert chosen["result"]["state"] == "READY", chosen
    assigned = _summary(base)
    assert assigned["status"] == "assigned" and assigned["profileId"] == key, assigned
    assert int(assigned["profileRevision"]) >= 1

    # Patch the Default for AI work.
    default = _ok(base, "POST", "/api/inference/assignments/set", {
        "command_id": "runs-on-hub-default", "expected_revision": _rows(base)["global"]["expected_revision"],
        "scope": {"kind": "global"},
        "entries": [{"profile_id": key, "profile_revision": revision}],
    })
    assert default["scope"] == {"kind": "global"}, default
    assert [e["profile_id"] for e in default["entries"]] == [key], default

    # Undo, Undo: the Default, then Meetings and its summary row (inherited
    # before, so cleared back to inheritance, never re-written).
    _ok(base, "POST", "/api/inference/assignments/clear", {
        "command_id": "runs-on-hub-undo-default", "expected_revision": _rows(base)["global"]["expected_revision"],
        "scope": {"kind": "global"}, "capability_id": "ask.answer",
    })
    _ok(base, "POST", "/api/inference/assignments/clear", {
        "command_id": "runs-on-hub-undo-meetings", "expected_revision": _rows(base)["meetings"]["expected_revision"],
        "scope": {"kind": "group", "group_id": "meetings"}, "capability_id": SUMMARY_CAPABILITY,
    })
    _ok(base, "POST", "/api/inference/assignments/clear", {
        "command_id": "runs-on-hub-undo-summary", "expected_revision": _summary(base)["assignmentRevision"],
        "scope": {"kind": "capability", "capability_id": SUMMARY_CAPABILITY},
        "capability_id": SUMMARY_CAPABILITY,
    })
    assert _summary_task(base)["has_override"] is False

    # Back ON over the tombstone: the cleared row's revision does not refuse it.
    tombstone = _summary(base)["assignmentRevision"]
    assert tombstone >= 1, "the clear left no tombstone revision to present"
    again = _ok(base, "POST", "/api/concierge/summary-selection", {
        "commandId": "runs-on-hub-summary-again", "expectedAssignmentRevision": tombstone,
        "profileId": key, "profileRevision": revision,
    })
    assert again["result"]["state"] == "READY", again
    back_on = _summary(base)
    assert back_on["status"] == "assigned" and back_on["profileId"] == key, back_on
