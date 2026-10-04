"""Inventory gap 5 (2026-10-03): the sent Brief carries no People data.

Through the REAL hub on an isolated HOME: a person, a 1:1 and an agenda item
made by the People routes (the encrypted sidecar on a file key), a Brief from
``/api/brief/generate``, then the real preview and the real send to a FILE
destination. The Brief on the desk still shows the person; the preview, the
saved file and the stored ``channel_sends`` row hold none of the People text.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, destination, files, send, sends  # noqa: E402

PERSON = "Priya Nair"
AGENDA = "Review the rollback plan"
PEOPLE_STRINGS = (PERSON, "Priya", AGENDA, "They owe", "You owe", "Agenda:", "Next:", "## People", "PEOPLE")


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(resp):
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def test_the_sent_brief_holds_no_people_data(hub: Hub, tmp_path: Path) -> None:
    c = hub.client
    _ok(c.post("/api/decisions", json={"title": "Freeze the old ledger on Nov 3", "status": "proposed",
                                       "decision_markdown": "Freeze the old ledger on Nov 3."}))
    _ok(c.post("/api/people/setup", json={}))
    person = _ok(c.post("/api/people/relationships", json={"display_name": PERSON}))["relationship"]["id"]
    _ok(c.post(f"/api/people/relationships/{person}/owner-aliases", json={"alias": "Priya"}))
    one = _ok(c.post(f"/api/people/relationships/{person}/one-on-ones",
                     json={"visibility": "shared_intent"}))["one_on_one"]["id"]
    _ok(c.post(f"/api/people/one-on-ones/{one}/agenda",
               json={"body": AGENDA, "visibility": "shared_intent", "state": "open", "source": {"kind": "brief"}}))
    brief = _ok(c.post("/api/brief/generate", json={}))
    ref = f"monday_brief:{brief['id']}"

    # The Brief on the desk is unchanged: it shows the person.
    on_desk = _ok(c.get(f"/api/brief/{brief['id']}"))
    assert any(s.get("display_name") == PERSON for s in on_desk.get("person_sections", [])), on_desk

    folder = tmp_path / "out"
    dest = destination(hub, folder)
    preview = _ok(c.post("/api/channels/preview", json={"document_ref": ref, "destination_id": dest}))
    shown = str(preview["preview"])
    assert "Freeze the old ledger on Nov 3" in shown, shown
    for text in PEOPLE_STRINGS:
        assert text not in shown, (text, shown)

    sent = _ok(send(hub, {"document_ref": ref, "destination_id": dest,
                          "preview_digest": preview["payload_digest"], "command_id": "brief-no-people-1"}))
    assert sent["send"]["state"] == "sent", sent
    saved = files(folder)
    assert len(saved) == 1, saved
    on_disk = saved[0].read_text()
    assert "Freeze the old ledger on Nov 3" in on_disk
    rows = [r for r in sends(hub) if r["document_ref"] == ref]
    assert len(rows) == 1, rows
    for text in PEOPLE_STRINGS:
        assert text not in on_disk, (text, on_disk)
        assert text not in str(rows[0]["payload"]), text
        assert text not in str(rows[0]["document_json"]), text
