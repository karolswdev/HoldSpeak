"""The Primitive Framework — the LIVE cross-surface sync loop, end-to-end.

Wave 2 proved sync with per-router unit fakes. This proves the loop against the
REAL ASGI app (`MeetingWebServer._create_app`, the same factory production runs):
the CRUD primitives router and the sync router are wired together over ONE real
tmp-path Database, and the exact wire shapes the two authoring surfaces emit
round-trip and reconcile in that single store.

The two surfaces, on the same hub:

- **Web** authors with the CRUD verbs (`POST /api/notes`, `POST /api/agents`,
  `POST /api/kbs`, ...). The hub stamps `last_modified`/`created_at`.
- **iPad** authors by pushing a `ChangeSet` (`POST /api/sync/push`) — per kind a
  list of ``{meta:{id, kind, last_modified, deleted}, value}`` records with
  snake_case `value` payloads (the Phase-0 contract coder's wire shape).

Both must show up in `GET /api/sync/pull` AND through the CRUD `GET` routes, and
the LWW + tombstone rules must hold across the surfaces. The `value` field sets on
the wire are asserted byte-for-byte against THE_PRIMITIVE_FRAMEWORK.md — that
exact-key agreement IS the cross-surface contract.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.requires_meeting]

from holdspeak.db import Database, get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


# ── The canonical snake_case `value` field sets (THE_PRIMITIVE_FRAMEWORK.md) ──
# These are the cross-surface agreement: every surface's `value` payload on the
# wire MUST carry exactly these keys. (The hub `to_dict` adds `updated_at` to the
# note value as a device-local stamp; it is not part of the agreement, so we
# compare the contract keys as a subset where the hub is the emitter and assert
# the contract keys exactly where the test controls the payload.)
NOTE_KEYS = {"id", "title", "body_markdown", "tags",
             "created_at", "updated_at", "last_modified", "deleted"}
AGENT_KEYS = {"id", "name", "avatar", "role", "system_prompt", "user_template",
              "tools", "kb_id", "created_at", "last_modified", "deleted"}
KB_KEYS = {"id", "name", "member_ids", "created_at", "last_modified", "deleted"}
META_KEYS = {"id", "kind", "last_modified", "deleted"}


@pytest.fixture
def env():
    """Boot the REAL app over a real tmp Database; yield (db, TestClient)."""
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(temp_dir / "holdspeak.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    client = TestClient(server.app)
    try:
        yield db, client
    finally:
        reset_database()
        shutil.rmtree(temp_dir, ignore_errors=True)


def _bucket_by_id(records, rec_id):
    for rec in records:
        if rec["meta"]["id"] == rec_id:
            return rec
    return None


def test_web_authored_note_and_agent_appear_in_pull(env) -> None:
    """Author a Note + Agent the WEB way; they ride `pull` as `{meta, value}`."""
    db, client = env

    note = client.post(
        "/api/notes",
        json={"title": "Spec", "body_markdown": "# body", "tags": ["a", "b"]},
    )
    assert note.status_code == 201
    nid = note.json()["note"]["id"]

    agent = client.post(
        "/api/agents",
        json={
            "name": "Summarizer", "avatar": "🤖", "role": "assistant",
            "system_prompt": "You summarize.", "user_template": "Summarize: {input}",
            "tools": ["web"], "kb_id": None,
        },
    )
    assert agent.status_code == 201
    aid = agent.json()["agent"]["id"]

    pulled = client.get("/api/sync/pull").json()

    note_rec = _bucket_by_id(pulled["notes"], nid)
    assert note_rec is not None
    assert set(note_rec["meta"]) == META_KEYS
    assert note_rec["meta"]["kind"] == "note"
    assert note_rec["meta"]["deleted"] is False
    assert note_rec["meta"]["last_modified"].endswith("Z")
    # The note value carries every contract key (hub adds updated_at as a stamp).
    assert NOTE_KEYS.issubset(set(note_rec["value"]))
    assert note_rec["value"]["title"] == "Spec"
    assert note_rec["value"]["tags"] == ["a", "b"]

    agent_rec = _bucket_by_id(pulled["agents"], aid)
    assert agent_rec is not None
    assert agent_rec["meta"]["kind"] == "agent"
    # The agent value is EXACTLY the contract field set.
    assert set(agent_rec["value"]) == AGENT_KEYS
    assert agent_rec["value"]["name"] == "Summarizer"
    assert agent_rec["value"]["user_template"] == "Summarize: {input}"
    assert agent_rec["value"]["tools"] == ["web"]


def test_ipad_changeset_push_is_readable_via_crud_and_pull(env) -> None:
    """Push the IPAD way (a ChangeSet) → readable via CRUD GET and next pull."""
    db, client = env
    lm = "2030-06-26T12:00:00Z"
    changeset = {
        "notes": [{
            "meta": {"id": "ipad_note_1", "kind": "note",
                     "last_modified": lm, "deleted": False},
            "value": {
                "id": "ipad_note_1", "title": "From the iPad",
                "body_markdown": "drawn on the desk", "tags": ["mobile"],
                "created_at": "2030-06-26T11:00:00Z",
                "updated_at": lm, "last_modified": lm, "deleted": False,
            },
        }],
        "agents": [{
            "meta": {"id": "ipad_agent_1", "kind": "agent",
                     "last_modified": lm, "deleted": False},
            "value": {
                "id": "ipad_agent_1", "name": "Tailored Persona", "avatar": "🎯",
                "role": "expert", "system_prompt": "Be precise.",
                "user_template": "{input}", "tools": [], "kb_id": "ipad_kb_1",
                "created_at": "2030-06-26T11:00:00Z",
                "last_modified": lm, "deleted": False,
            },
        }],
        "kbs": [{
            "meta": {"id": "ipad_kb_1", "kind": "kb",
                     "last_modified": lm, "deleted": False},
            "value": {
                "id": "ipad_kb_1", "name": "Field Notes",
                "member_ids": ["ipad_note_1"],
                "created_at": "2030-06-26T11:00:00Z",
                "last_modified": lm, "deleted": False,
            },
        }],
    }
    push = client.post("/api/sync/push", json=changeset)
    assert push.status_code == 200, push.text
    rcv = push.json()["received"]
    assert rcv["notes"] == 1 and rcv["agents"] == 1 and rcv["kbs"] == 1

    # Readable via the CRUD GET routes (the web surface's read path).
    note = client.get("/api/notes/ipad_note_1")
    assert note.status_code == 200
    assert note.json()["note"]["title"] == "From the iPad"
    assert note.json()["note"]["tags"] == ["mobile"]

    agent = client.get("/api/agents/ipad_agent_1")
    assert agent.status_code == 200
    assert agent.json()["agent"]["name"] == "Tailored Persona"
    assert agent.json()["agent"]["kb_id"] == "ipad_kb_1"

    kb = client.get("/api/kbs/ipad_kb_1")
    assert kb.status_code == 200
    assert kb.json()["kb"]["member_ids"] == ["ipad_note_1"]

    # And readable via the next pull, with the iPad's last_modified preserved.
    pulled = client.get("/api/sync/pull").json()
    note_rec = _bucket_by_id(pulled["notes"], "ipad_note_1")
    assert note_rec is not None
    assert note_rec["meta"]["last_modified"] == lm
    assert note_rec["meta"]["kind"] == "note"
    assert NOTE_KEYS.issubset(set(note_rec["value"]))
    agent_rec = _bucket_by_id(pulled["agents"], "ipad_agent_1")
    assert agent_rec is not None and set(agent_rec["value"]) == AGENT_KEYS
    kb_rec = _bucket_by_id(pulled["kbs"], "ipad_kb_1")
    assert kb_rec is not None and set(kb_rec["value"]) == KB_KEYS


def test_cross_surface_round_trip_web_authored_then_pulled(env) -> None:
    """THE proof in miniature: a note authored on the WEB shows up in the pull a
    second surface (the iPad) would read — through the real shared store."""
    db, client = env
    created = client.post("/api/notes", json={"title": "cross", "body_markdown": "x"})
    nid = created.json()["note"]["id"]

    # The iPad pulls: the web-authored note is there with a proper envelope.
    pulled = client.get("/api/sync/pull").json()
    rec = _bucket_by_id(pulled["notes"], nid)
    assert rec is not None
    assert rec["meta"]["kind"] == "note" and rec["meta"]["deleted"] is False
    assert rec["value"]["title"] == "cross"


def test_last_write_wins_older_push_does_not_clobber_newer(env) -> None:
    """A web-authored note (real now-stamp) is NOT clobbered by an older push;
    a newer push DOES win — across the two surfaces, in the real store."""
    db, client = env
    created = client.post("/api/notes", json={"title": "Web wins", "body_markdown": "v1"})
    nid = created.json()["note"]["id"]
    web_lm = created.json()["note"]["last_modified"]
    assert web_lm  # the hub stamped a real ISO timestamp (≈ now, year 2026)

    # iPad pushes an OLDER edit for the same id → must be skipped.
    stale = {"notes": [{
        "meta": {"id": nid, "kind": "note",
                 "last_modified": "2000-01-01T00:00:00Z", "deleted": False},
        "value": {"title": "Stale iPad edit", "body_markdown": "OLD"},
    }]}
    resp = client.post("/api/sync/push", json=stale)
    assert resp.status_code == 200
    assert resp.json()["received"]["notes"] == 0  # skipped by LWW
    assert client.get(f"/api/notes/{nid}").json()["note"]["title"] == "Web wins"

    # iPad pushes a NEWER edit → must win.
    fresh = {"notes": [{
        "meta": {"id": nid, "kind": "note",
                 "last_modified": "2099-01-01T00:00:00Z", "deleted": False},
        "value": {"title": "Fresh iPad edit", "body_markdown": "NEW"},
    }]}
    resp = client.post("/api/sync/push", json=fresh)
    assert resp.status_code == 200
    assert resp.json()["received"]["notes"] == 1
    got = client.get(f"/api/notes/{nid}").json()["note"]
    assert got["title"] == "Fresh iPad edit" and got["body_markdown"] == "NEW"

    # And the winning value rides the next pull with the iPad's last_modified.
    rec = _bucket_by_id(client.get("/api/sync/pull").json()["notes"], nid)
    assert rec["meta"]["last_modified"] == "2099-01-01T00:00:00Z"
    assert rec["value"]["title"] == "Fresh iPad edit"


def test_tombstone_hides_record_but_still_rides_pull(env) -> None:
    """A newer `deleted:true` push removes the record from the non-deleted view
    (CRUD GET 404) but the tombstone still propagates on pull."""
    db, client = env
    created = client.post("/api/notes", json={"title": "to delete", "body_markdown": "x"})
    nid = created.json()["note"]["id"]
    assert client.get(f"/api/notes/{nid}").status_code == 200

    tomb = {"notes": [{
        "meta": {"id": nid, "kind": "note",
                 "last_modified": "2099-01-01T00:00:00Z", "deleted": True},
        "value": {"title": "to delete"},
    }]}
    assert client.post("/api/sync/push", json=tomb).status_code == 200

    # Vanished from the non-deleted view (CRUD GET + list).
    assert client.get(f"/api/notes/{nid}").status_code == 404
    assert _bucket_by_id(
        [{"meta": {"id": n["id"]}} for n in client.get("/api/notes").json()["notes"]],
        nid,
    ) is None

    # But the tombstone still rides the pull (deleted=True), so other surfaces
    # learn of the delete.
    rec = _bucket_by_id(client.get("/api/sync/pull").json()["notes"], nid)
    assert rec is not None
    assert rec["meta"]["deleted"] is True


def test_malformed_changeset_is_rejected_and_not_merged(env) -> None:
    """A record missing meta.kind (or an unknown kind) is a 422 and merges
    nothing — the envelope guard protects the live store."""
    db, client = env
    bad = {"notes": [{
        "meta": {"id": "x1", "kind": "not_a_kind",
                 "last_modified": "2030-01-01T00:00:00Z", "deleted": False},
        "value": {"title": "nope"},
    }]}
    resp = client.post("/api/sync/push", json=bad)
    assert resp.status_code == 422
    assert client.get("/api/notes/x1").status_code == 404
