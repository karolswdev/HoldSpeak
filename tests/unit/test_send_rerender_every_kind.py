"""Sent documents, 2026-10-05: People text leaves old Brief sends; every kind re-renders at Send.

(a) A prepared or discarded Brief send frozen by the renderer before #767 held
the People overlay (names, who-owes-whom counts, the next 1:1) in plain text in
``channel_sends.payload``. The one-time repair at database open cuts it, keeps
the row and keeps its digest (a prepared row still refuses Send).

(b) The re-render check at Send (a prepared row leaves only when its frozen
bytes are the bytes its document renders now) covered the Brief only. It now
covers every kind in the document registry.

Through the real hub on an isolated HOME: real producers mint the nine
documents, the real prepare route freezes the bytes, the real send route
dispatches to a real FILE destination.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, destination, files, send, sends  # noqa: E402
from _philo11_documents import OWNER, mint_documents  # noqa: E402
from _philo12_artifacts import mint_meeting_synthesis  # noqa: E402

PERSON = "Priya Nair"
AGENDA = "Review the rollback plan"
PEOPLE_STRINGS = (PERSON, AGENDA, "They owe", "You owe", "Agenda:", "Next:", "## People", "*People*",
                  "<h2>People</h2>", "PEOPLE")


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(resp):
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def _reopen(hub: Hub) -> None:
    """Open the database again: the one-time repairs run in the schema reconcile."""
    from holdspeak.db import get_database, reset_database

    path = hub.db.db_path
    reset_database()
    get_database(path)


# ── (a) People text leaves old prepared and discarded Brief rows ─────────


def _brief_with_people(hub: Hub) -> str:
    c = hub.client
    _ok(c.post("/api/decisions", json={"title": "Freeze the old ledger on Nov 3", "status": "proposed",
                                       "decision_markdown": "Freeze the old ledger on Nov 3."}))
    _ok(c.post("/api/people/setup", json={}))
    person = _ok(c.post("/api/people/relationships", json={"display_name": PERSON}))["relationship"]["id"]
    one = _ok(c.post(f"/api/people/relationships/{person}/one-on-ones",
                     json={"visibility": "shared_intent"}))["one_on_one"]["id"]
    _ok(c.post(f"/api/people/one-on-ones/{one}/agenda",
               json={"body": AGENDA, "visibility": "shared_intent", "state": "open", "source": {"kind": "brief"}}))
    return f"monday_brief:{_ok(c.post('/api/brief/generate', json={}))['id']}"


def _old_renderer(hub: Hub):
    """The Brief renderer before #767: the stored items plus the People overlay (the parked code)."""
    from holdspeak.services import document_sources as sources

    clean = sources._brief_markdown

    def old(stored):
        overlay = sources._parked_brief_person_overlay(hub.db, stored)
        return clean(stored).rstrip("\n") + "\n" + "\n".join(sources._parked_brief_people_lines(overlay)) + "\n"

    return old


def test_old_prepared_and_discarded_brief_rows_lose_their_people_text(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.services import document_sources as sources

    c = hub.client
    ref = _brief_with_people(hub)
    dest = destination(hub, tmp_path / "out")
    with monkeypatch.context() as patch:
        patch.setattr(sources, "_brief_markdown", _old_renderer(hub))
        kept = _ok(c.post("/api/channels/sends", json={"document_ref": ref, "destination_id": dest}))["send"]
        dropped = _ok(c.post("/api/channels/sends", json={"document_ref": ref, "destination_id": dest,
                                                          "command_id": "old-brief-2"}))["send"]
    _ok(c.post(f"/api/channels/sends/{dropped['id']}/discard", json={}))
    before = {r["id"]: r for r in sends(hub)}
    assert set(before) == {kept["id"], dropped["id"]}, before
    for row in before.values():
        assert PERSON in bytes(row["payload"]).decode(), "the rig did not freeze the old People bytes"
    assert before[dropped["id"]]["state"] == "discarded"

    _reopen(hub)

    after = {r["id"]: r for r in sends(hub)}
    assert set(after) == set(before), "a row was removed"
    for send_id, row in after.items():
        text = bytes(row["payload"]).decode()
        for marker in PEOPLE_STRINGS:
            assert marker not in text, (send_id, marker, text)
        assert "Freeze the old ledger on Nov 3" in text, text  # the Brief items stay
        assert row["state"] == before[send_id]["state"]
        assert row["payload_digest"] == before[send_id]["payload_digest"]
    # The Send list still reads every row.
    listed = _ok(c.get("/api/channels/sends", params={"document_ref": ref}))["sends"]
    assert {r["id"] for r in listed} == set(before)
    # The prepared row still never leaves.
    refused = send(hub, {"send_id": kept["id"], "command_id": "old-brief-send"})
    assert refused.status_code == 409, refused.text
    assert files(tmp_path / "out") == []

    # Idempotent: a second open changes nothing.
    _reopen(hub)
    assert {r["id"]: bytes(r["payload"]) for r in sends(hub)} == {i: bytes(r["payload"]) for i, r in after.items()}


def test_old_brief_people_text_leaves_every_channel_byte_shape(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Slack, email and Confluence froze the People overlay inside JSON; the cut keeps the JSON valid.

    The rows are written the way the old code wrote them: the real channel
    serializers over the old renderer's document, into a prepared row and a
    discarded row. A sent row is history that left the desk; it is not touched.
    """
    from holdspeak.db.channels import scrub_brief_people_text
    from holdspeak.services import channel_cli, channel_slack, document_sources as sources
    from holdspeak.services.channel_contract import Document, sha256

    ref = _brief_with_people(hub)
    from holdspeak.services.monday_brief_service import MondayBriefService

    stored = MondayBriefService(hub.db).get_by_id(ref.split(":", 1)[1])
    unavailable = sources._brief_markdown(stored).rstrip("\n") + "\n\nPEOPLE · UNAVAILABLE\n"
    ready = _old_renderer(hub)(stored)
    assert PERSON in ready
    shapes = {}
    for label, body in (("ready", ready), ("unavailable", unavailable)):
        doc = Document(ref=ref, title="Monday Brief", body_md=body, slug="brief", label="BRIEF")
        shapes[f"slack-{label}"] = ("slack", channel_slack.SlackChannel().serialize(doc))
        shapes[f"confluence-{label}"] = ("confluence", channel_cli.ConfluenceChannel().serialize(doc))
        shapes[f"email-{label}"] = ("email", json.dumps(
            {"from": "a@example.com", "to": ["b@example.com"], "subject": "Monday Brief", "text": body},
            ensure_ascii=False, separators=(",", ":")).encode())
        shapes[f"file-{label}"] = ("file", body.encode())
    with hub.db._connection() as conn:
        for n, (name, (channel, payload)) in enumerate(shapes.items()):
            for state in ("prepared", "discarded", "sent"):
                conn.execute(
                    "INSERT INTO channel_sends (id, document_ref, destination_id, channel, account_json, target_json,"
                    " target_digest, payload, payload_digest, state, created_at) VALUES (?, ?, 'holdspeak-folder', ?, '{}', '{}',"
                    " 'x', ?, ?, ?, '2026-10-01T00:00:00+00:00')",
                    (f"old-{name}-{state}", ref, channel, payload, sha256(payload), state))
        changed = scrub_brief_people_text(conn)
        rows = {r["id"]: dict(r) for r in conn.execute("SELECT * FROM channel_sends WHERE id LIKE 'old-%'")}
    assert changed == len(shapes) * 2, changed
    for name, (channel, original) in shapes.items():
        for state in ("prepared", "discarded"):
            text = bytes(rows[f"old-{name}-{state}"]["payload"]).decode()
            for marker in PEOPLE_STRINGS:
                assert marker not in text, (name, state, marker, text)
            assert "Freeze the old ledger on Nov 3" in text, (name, text)
            if channel != "file":
                json.loads(text)  # still valid JSON: the Send list can preview it
        assert bytes(rows[f"old-{name}-sent"]["payload"]) == original  # history that left stays


# ── (b) every document kind re-renders at Send ───────────────────────────


KINDS = ("project_update", "monday_brief", "desk_decision", "meeting_decision", "decision_record",
         "meeting_summary", "meeting_digest", "meeting_followup", "artifact", "note")


def _mint_all(hub: Hub, tmp_path: Path) -> dict[str, str]:
    refs = mint_documents(hub.db, OWNER, people_keystore_path=tmp_path / "people.key")
    refs["artifact"] = mint_meeting_synthesis(hub.db)
    from holdspeak.services.primitive_service import PrimitiveService

    note = PrimitiveService(hub.db).create_note(OWNER, title="Pilot plan", body_markdown="We start on Monday.")
    refs["note"] = f"note:{note['id']}"
    from holdspeak.services.document_sources import DOCUMENT_SOURCES

    assert set(refs) == set(DOCUMENT_SOURCES) == set(KINDS)
    return refs


@pytest.mark.parametrize("kind", KINDS)
def test_every_kind_sends_unchanged_and_refuses_a_stale_prepared_row(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    from holdspeak.services import document_sources as sources

    c = hub.client
    refs = _mint_all(hub, tmp_path)
    ref = refs[kind]
    folder = tmp_path / "out"
    dest = destination(hub, folder)

    # Unchanged: the render is stable, so a fresh prepared row sends.
    fresh = _ok(c.post("/api/channels/sends", json={"document_ref": ref, "destination_id": dest}))["send"]
    sent = _ok(send(hub, {"send_id": fresh["id"], "command_id": f"fresh-{kind}"}))
    assert sent["send"]["state"] == "sent", sent
    assert len(files(folder)) == 1

    # Frozen by another renderer (as the Brief's People overlay was): refused, nothing leaves.
    real = sources.DOCUMENT_SOURCES[kind]

    class Older:
        def __init__(self) -> None:
            self.kind = real.kind

        def render(self, db, source_id):
            document = real.render(db, source_id)
            return type(document)(ref=document.ref, title=document.title,
                                  body_md=document.body_md + "\nOLDER RENDERER LINE\n",
                                  slug=document.slug, label=document.label)

    with monkeypatch.context() as patch:
        patch.setitem(sources.DOCUMENT_SOURCES, kind, Older())
        stale = _ok(c.post("/api/channels/sends", json={"document_ref": ref, "destination_id": dest,
                                                        "command_id": f"stale-prep-{kind}"}))["send"]
    assert "OLDER RENDERER LINE" in bytes(next(r for r in sends(hub) if r["id"] == stale["id"])["payload"]).decode()
    refused = send(hub, {"send_id": stale["id"], "command_id": f"stale-{kind}"})
    assert refused.status_code == 409, refused.text
    assert refused.json()["error_code"] == "preview_changed", refused.text
    assert len(files(folder)) == 1, "a stale prepared row left the desk"
    assert next(r for r in sends(hub) if r["id"] == stale["id"])["state"] == "prepared"


def test_a_prepared_desk_decision_refuses_after_its_source_changes(hub: Hub, tmp_path: Path) -> None:
    """A real source edit (not only another renderer) makes a prepared non-Brief row stale."""
    from holdspeak.services.primitive_service import PrimitiveService

    c = hub.client
    ref = _mint_all(hub, tmp_path)["desk_decision"]
    folder = tmp_path / "out"
    dest = destination(hub, folder)
    prepared = _ok(c.post("/api/channels/sends", json={"document_ref": ref, "destination_id": dest}))["send"]
    PrimitiveService(hub.db).update_decision(OWNER, ref.split(":", 1)[1],
                                             decision_markdown="Render from the durable source, revised.")
    refused = send(hub, {"send_id": prepared["id"], "command_id": "edited-decision"})
    assert refused.status_code == 409, refused.text
    assert refused.json()["error_code"] == "preview_changed", refused.text
    assert files(folder) == []
