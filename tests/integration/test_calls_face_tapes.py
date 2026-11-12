"""Calls face answers from the declared routes and the real call record/runner.

No phone, engine, owner state or external destination is used. Set
HOLDSPEAK_WIRE_WRITE=1 to refresh the face tape.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.unit.test_desk_ask_ai import _owner_edge, hub  # noqa: F401

TAPE = Path(__file__).resolve().parents[2] / "web/src/desk/calls/__fixtures__/calls.face.json"


def test_calls_face_tape(hub, monkeypatch):
    from holdspeak.calls import service as calls_service
    from holdspeak.calls.runner import CallRecord, CallRunner, Line
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import calls as routes

    monkeypatch.setenv("HOLDSPEAK_CALLS", "off")
    monkeypatch.setenv("HOLDSPEAK_LINE", "off")
    service = calls_service.CallsService()
    monkeypatch.setattr(calls_service, "CALLS", service)
    monkeypatch.setattr(routes, "CALLS", service)
    monkeypatch.setattr("holdspeak.calls.runner.time.time", lambda: 1794481447.0)
    # The declared port is the CallsService singleton, looked up per operation.
    record = CallRecord(phone_call_id="face", id="call-face", direction="in", remote="sip:+15550100142@example.test",
                        state="live", started_at=1794481200, answered_at=1794481201)
    record.transcript = [Line("holdspeak", "What can I do?", 1794481202), Line("caller", "Review the platform plan.", 1794481206)]
    record.hold = {"call_id": "send-plan", "tool": "channel.send", "words": "Send the platform plan to the team"}
    record.results = [{"kind": "note", "label": "Platform plan", "ref": "note:platform-plan", "effect": "wrote"}]
    for index, outcome in enumerate(("done", "no_answer")):
        previous = CallRecord(phone_call_id=f"previous-{index}", id=f"call-previous-{index}", direction="out",
                              remote=record.remote, state="ended", started_at=1794480000 + index * 300,
                              answered_at=1794480001 if index == 0 else None,
                              ended_at=1794480152 + index * 300, outcome=outcome)
        if index == 0:
            previous.transcript = [Line("caller", "Read the morning brief.", 1794480005)]
        service._keep(previous)
    service._keep(record)
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService
    PrimitiveService(hub.db).create_note(Principal(PrincipalKind.OWNER, "calls-face"), note_id="platform-plan",
                                        title="Platform plan", body_markdown="Keep the platform plan.")
    class Phone:
        async def hangup(self, **kwargs):
            return SimpleNamespace(ok=True, code=0, data={"outcome": "done"})
    runner = CallRunner(Phone(), record, turns=SimpleNamespace(decide=lambda *args: True), passphrase="",
                        allowed_numbers=[], greeting="Hello", emit=lambda *args: None, save_note=service._save_note)
    service._runners[record.id] = runner
    app = _owner_edge(FastAPI())
    app.include_router(routes.build_calls_router(WebContext(get_state=lambda: {})))
    def request(client, method, path, **kwargs):
        reply = client.request(method, path, **kwargs)
        assert reply.status_code == 200, reply.text
        return reply.json()
    with TestClient(app) as client:
        tape = {"_producer": "tests/integration/test_calls_face_tapes.py; real declared HTTP routes, CallRecord and CallRunner; fake phone/held-tool edges only"}
        tape["held"] = request(client, "GET", "/api/calls/call-face")
        tape["listed"] = request(client, "GET", "/api/calls")
        tape["denied"] = request(client, "POST", "/api/calls/call-face/decide", json={"decision": "deny"})
        record.hold = dict(tape["held"]["hold"])
        tape["approved"] = request(client, "POST", "/api/calls/call-face/decide", json={"decision": "approve"})
        tape["ended"] = request(client, "POST", "/api/calls/call-face/hangup", json={})
        tape["detail"] = request(client, "GET", "/api/calls/call-face")
        tape["recent"] = request(client, "GET", "/api/calls")
        # Place acknowledges a new identity. Serialize its summary through the
        # real list producer rather than reusing an ended call in a UI reply.
        placed = CallRecord(phone_call_id="new-face", id="call-new-face", direction="out", remote=record.remote,
                            state="live", started_at=1794481200, answered_at=1794481201)
        placed.transcript = record.transcript[:2]
        placed.hold = {**tape["held"]["hold"], "call_id": "send-new-plan"}
        service._keep(placed)
        tape["placed"] = next(call for call in request(client, "GET", "/api/calls")["calls"] if call["id"] == placed.id)

    assert tape["approved"]["hold"] is None and tape["approved"]["results"][-1]["effect"] == "sent"
    assert tape["detail"]["transcript"] and tape["detail"]["note_ref"]
    note_id = tape["detail"]["note_ref"].split(":", 1)[1]
    assert "Review the platform plan." in hub.db.notes.get(note_id).body_markdown
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        TAPE.write_text(json.dumps(tape, indent=2) + "\n")
    stored = json.loads(TAPE.read_text())
    assert stored["held"]["hold"] == tape["held"]["hold"]
    assert stored["approved"]["results"] == tape["approved"]["results"]
    assert stored["detail"]["state"] == "ended"


# The established Phone rig supplies a paired fake device, NullPush and no
# number transport. Keep the returned reads instead of hand-applying a state.
from tests.unit.test_phone_calls import phone  # noqa: E402,F401


def test_phone_call_verbs_face_tape(phone, monkeypatch):
    from holdspeak.phone import service as phone_service
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.phone import build_phone_router

    monkeypatch.setattr(phone_service, "default_phone_service", lambda db=None: phone)
    phone.timers.ring_seconds = 30
    app = _owner_edge(FastAPI())
    app.include_router(build_phone_router(WebContext(get_state=lambda: {})))
    agent = Principal(PrincipalKind.AGENT, "calls-face")
    held = phone.call(agent, reason="Review the platform plan")
    assert held["state"] == "held"
    with TestClient(app) as client:
        def read():
            reply = client.get("/api/phone/calls")
            assert reply.status_code == 200, reply.text
            return reply.json()
        before = read()
        reply = client.post(f"/api/phone/calls/{held['call_id']}/ring", json={})
        assert reply.status_code == 200, reply.text
        ring = {"before": before, "response": reply.json(), "after": read(), "id": held["call_id"]}
        phone.decline(held["call_id"])
        before = read()
        reply = client.post(f"/api/phone/calls/{held['call_id']}/again", json={})
        assert reply.status_code == 200, reply.text
        again = {"before": before, "response": reply.json(), "after": read(), "id": held["call_id"]}
    assert any(call["state"] == "ringing" for call in ring["after"]["calls"])
    assert any(call["state"] == "ringing" for call in again["after"]["calls"])
    path = TAPE.with_name("phone.verbs.face.json")
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(json.dumps({"_producer": "test_calls_face_tapes.py::test_phone_call_verbs_face_tape; real Phone HTTP routes; paired fake phone, NullPush, no number", "ring": ring, "again": again}, indent=2) + "\n")
    stored = json.loads(path.read_text())
    assert stored["ring"]["response"]["state"] == "ringing"
    assert any(call["state"] == "ringing" for call in stored["again"]["after"]["calls"])
