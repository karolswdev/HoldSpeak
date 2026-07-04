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

import json
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
              "tools", "kb_id", "profile_id", "created_at", "last_modified", "deleted",
    "manual_context", "use_zone_context",  # v7 (Phase 77): the pinned context rides the wire
}
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


# ── Equilibrium 23-04: meeting + artifact content live-merges (not just inbox) ──
# The desktop footnote: a meeting/artifact pushed from a peer must round-trip into
# its REAL table and be queryable through the normal read paths, matching the desk
# primitives. These prove readability (not inboxing), plus LWW + tombstone.

def _meeting_changeset(meeting_id, lm, *, title="Pushed meeting", deleted=False):
    """A pushed meeting record in the `MeetingState.to_dict` wire shape."""
    return {
        "meta": {"id": meeting_id, "kind": "meeting",
                 "last_modified": lm, "deleted": deleted},
        "value": {
            "id": meeting_id,
            "started_at": lm,
            "ended_at": None,
            "title": title,
            "tags": ["mobile"],
            "segments": [{
                "text": "spoken on the iPad", "speaker": "Me",
                "speaker_id": None, "start_time": 0.0, "end_time": 2.5,
                "is_bookmarked": False, "device_id": None,
            }],
            "bookmarks": [],
            "intel": None,
            "intel_status": {"state": "disabled", "detail": None,
                             "requested_at": None, "completed_at": None},
            "mic_label": "Me", "remote_label": "Remote", "web_url": None,
        },
    }


def _artifact_changeset(artifact_id, meeting_id, lm, *, title="Pushed artifact", deleted=False):
    """A pushed artifact record in the Phase-0 `Artifact` contract shape."""
    return {
        "meta": {"id": artifact_id, "kind": "artifact",
                 "last_modified": lm, "deleted": deleted},
        "value": {
            "id": artifact_id,
            "meeting_id": meeting_id,
            "artifact_type": "summary",
            "title": title,
            "body_markdown": "# From the iPad\n\nlive-merged",
            "structured_json": {"k": "v"},
            "confidence": 0.8,
            "status": "draft",
            "plugin_id": "mobile",
            "plugin_version": "1.0",
            "sources": [{"source_type": "segment", "source_ref": "seg-1"}],
        },
    }


def test_pushed_meeting_and_artifact_are_readable_via_crud_and_pull(env) -> None:
    """A meeting + its artifact pushed the IPAD way live-merge into their real
    tables and are queryable via the normal read paths (NOT just inboxed)."""
    db, client = env
    lm = "2030-06-26T12:00:00Z"
    changeset = {
        "meetings": [_meeting_changeset("ipad_meeting_1", lm)],
        "artifacts": [_artifact_changeset("ipad_artifact_1", "ipad_meeting_1", lm)],
    }
    push = client.post("/api/sync/push", json=changeset)
    assert push.status_code == 200, push.text
    rcv = push.json()["received"]
    assert rcv["meetings"] == 1 and rcv["artifacts"] == 1

    # Readable via the normal meeting read path (GET /api/meetings/{id}).
    meeting = client.get("/api/meetings/ipad_meeting_1")
    assert meeting.status_code == 200
    body = meeting.json()
    assert body["title"] == "Pushed meeting"
    assert body["tags"] == ["mobile"]
    assert len(body["segments"]) == 1
    assert body["segments"][0]["text"] == "spoken on the iPad"

    # Readable via the normal artifact read path (GET .../artifacts).
    arts = client.get("/api/meetings/ipad_meeting_1/artifacts")
    assert arts.status_code == 200
    rows = arts.json()["artifacts"]
    assert len(rows) == 1
    assert rows[0]["id"] == "ipad_artifact_1"
    assert rows[0]["title"] == "Pushed artifact"
    assert rows[0]["body_markdown"] == "# From the iPad\n\nlive-merged"
    assert rows[0]["structured_json"] == {"k": "v"}
    assert rows[0]["sources"] == [{"source_type": "segment", "source_ref": "seg-1"}]

    # And both ride the next pull (the round-trip a second surface would read).
    pulled = client.get("/api/sync/pull").json()
    assert _bucket_by_id(pulled["meetings"], "ipad_meeting_1") is not None
    assert _bucket_by_id(pulled["artifacts"], "ipad_artifact_1") is not None


def test_pushed_meeting_lww_older_does_not_clobber_newer(env) -> None:
    """An older pushed meeting edit does NOT clobber a newer stored one; a newer
    push wins — LWW on last_modified, in the real meetings table."""
    db, client = env
    newer = "2030-06-26T12:00:00Z"
    older = "2020-01-01T00:00:00Z"
    assert client.post(
        "/api/sync/push",
        json={"meetings": [_meeting_changeset("m_lww", newer, title="Newer")]},
    ).status_code == 200

    # Older push for the same id → skipped.
    resp = client.post(
        "/api/sync/push",
        json={"meetings": [_meeting_changeset("m_lww", older, title="Stale")]},
    )
    assert resp.json()["received"]["meetings"] == 0
    assert client.get("/api/meetings/m_lww").json()["title"] == "Newer"

    # A strictly newer push → wins.
    newest = "2040-01-01T00:00:00Z"
    resp = client.post(
        "/api/sync/push",
        json={"meetings": [_meeting_changeset("m_lww", newest, title="Newest")]},
    )
    assert resp.json()["received"]["meetings"] == 1
    assert client.get("/api/meetings/m_lww").json()["title"] == "Newest"


def test_pushed_meeting_tombstone_removes_it(env) -> None:
    """A newer `deleted:true` meeting push removes it from the live store."""
    db, client = env
    lm = "2030-06-26T12:00:00Z"
    client.post("/api/sync/push", json={"meetings": [_meeting_changeset("m_tomb", lm)]})
    assert client.get("/api/meetings/m_tomb").status_code == 200

    later = "2031-01-01T00:00:00Z"
    resp = client.post(
        "/api/sync/push",
        json={"meetings": [_meeting_changeset("m_tomb", later, deleted=True)]},
    )
    assert resp.json()["received"]["meetings"] == 1
    assert client.get("/api/meetings/m_tomb").status_code == 404


def test_pushed_artifact_lww_and_tombstone(env) -> None:
    """Artifact LWW + tombstone hold in the real artifacts table."""
    db, client = env
    lm = "2030-06-26T12:00:00Z"
    # Need a meeting for the artifact FK; push it first.
    client.post("/api/sync/push", json={
        "meetings": [_meeting_changeset("a_meet", lm)],
        "artifacts": [_artifact_changeset("a_art", "a_meet", lm, title="v1")],
    })
    rows = client.get("/api/meetings/a_meet/artifacts").json()["artifacts"]
    assert rows[0]["title"] == "v1"

    # Older push → skipped.
    older = "2020-01-01T00:00:00Z"
    resp = client.post("/api/sync/push", json={
        "artifacts": [_artifact_changeset("a_art", "a_meet", older, title="stale")],
    })
    assert resp.json()["received"]["artifacts"] == 0
    assert client.get("/api/meetings/a_meet/artifacts").json()["artifacts"][0]["title"] == "v1"

    # Newer push → wins.
    newer = "2040-01-01T00:00:00Z"
    resp = client.post("/api/sync/push", json={
        "artifacts": [_artifact_changeset("a_art", "a_meet", newer, title="v2")],
    })
    assert resp.json()["received"]["artifacts"] == 1
    assert client.get("/api/meetings/a_meet/artifacts").json()["artifacts"][0]["title"] == "v2"

    # Newer tombstone → removed.
    newest = "2050-01-01T00:00:00Z"
    resp = client.post("/api/sync/push", json={
        "artifacts": [_artifact_changeset("a_art", "a_meet", newest, deleted=True)],
    })
    assert resp.json()["received"]["artifacts"] == 1
    assert client.get("/api/meetings/a_meet/artifacts").json()["artifacts"] == []


def test_profile_syncs_shape_only_and_agent_carries_profile_id(env) -> None:
    """Phase 24 (HSM-24-04): a RuntimeProfile pushed from the iPad round-trips through the hub
    SHAPE ONLY — the API key NEVER persists or appears in a pull — and an agent's profile_id rides."""
    db, client = env
    lm = "2030-06-27T09:00:00Z"
    changeset = {
        "profiles": [{
            "meta": {"id": "prof_claude", "kind": "profile", "last_modified": lm, "deleted": False},
            "value": {
                "id": "prof_claude", "name": "Claude", "kind": "openAICompatible",
                "model_file": "", "base_url": "https://api.anthropic.com/v1",
                "model": "claude-3.5-sonnet", "context_limit": 200000, "requires_key": True,
                # A hostile/extra key field MUST NOT be persisted — the field map has no key.
                "api_key": "sk-SHOULD-NEVER-PERSIST",
                "created_at": "2030-06-27T08:00:00Z", "last_modified": lm, "deleted": False,
            },
        }],
        "agents": [{
            "meta": {"id": "ag_on_claude", "kind": "agent", "last_modified": lm, "deleted": False},
            "value": {
                "id": "ag_on_claude", "name": "Scout", "avatar": "a21", "role": "researcher",
                "system_prompt": "Be precise.", "user_template": "{input}", "tools": [],
                "kb_id": None, "profile_id": "prof_claude",
                "created_at": "2030-06-27T08:00:00Z", "last_modified": lm, "deleted": False,
            },
        }],
    }
    push = client.post("/api/sync/push", json=changeset)
    assert push.status_code == 200, push.text
    assert push.json()["received"]["profiles"] == 1 and push.json()["received"]["agents"] == 1

    # The profile is stored as shape; the agent carries its profile_id.
    stored = db.profiles.get("prof_claude")
    assert stored is not None and stored.kind == "openAICompatible" and stored.context_limit == 200000
    assert db.agents.get("ag_on_claude").profile_id == "prof_claude"

    # THE NEVER-SYNC INVARIANT: no key material persisted, and none appears in a pull.
    pulled = client.get("/api/sync/pull").json()
    prof_rec = _bucket_by_id(pulled["profiles"], "prof_claude")
    assert prof_rec is not None
    blob = json.dumps(pulled)
    assert "api_key" not in blob and "SHOULD-NEVER-PERSIST" not in blob
    assert "api_key" not in prof_rec["value"] and "apiKey" not in prof_rec["value"]


# The agreed cross-surface RuntimeProfile shape (matches db.models.ProfileRecord.to_dict and the
# Apple Contracts/Primitives.swift RuntimeProfile fields). NO key field exists anywhere in it — the
# secret is each surface's own custodian (iPad Keychain / hub env secrets), joined at run time.
_PROFILE_SHAPE_KEYS = {
    "id", "name", "kind", "model_file", "base_url", "model",
    "context_limit", "requires_key", "created_at", "last_modified", "deleted",
}


def test_profile_never_sync_holds_across_every_read_surface(env) -> None:
    """HSM-24-06 (the phase gate): one profile, observed in equilibrium. The SAME profile is served
    SHAPE-ONLY through every surface's read path — the sync pull AND the web/API CRUD routes — with
    the exact agreed field set and NO key material on any of them. This is the cross-surface
    never-sync security crux: a key supplied to ANY ingress (sync push or the REST body) is dropped,
    so it can never reappear on a surface that reads the hub."""
    db, client = env
    lm = "2030-06-27T09:00:00Z"

    # Ingress 1 — the sync push (the iPad's path), carrying a hostile key.
    push = client.post("/api/sync/push", json={
        "profiles": [{
            "meta": {"id": "prof_x", "kind": "profile", "last_modified": lm, "deleted": False},
            "value": {
                "id": "prof_x", "name": "Claude", "kind": "openAICompatible",
                "model_file": "", "base_url": "https://api.anthropic.com/v1",
                "model": "claude-3.5-sonnet", "context_limit": 200000, "requires_key": True,
                "api_key": "sk-FROM-SYNC-MUST-VANISH",
                "created_at": "2030-06-27T08:00:00Z", "last_modified": lm, "deleted": False,
            },
        }],
    })
    assert push.status_code == 200, push.text

    # Ingress 2 — the REST CRUD (the web's path), also carrying a hostile key.
    created = client.post("/api/profiles", json={
        "id": "prof_y", "name": "OpenRouter", "kind": "openAICompatible",
        "base_url": "https://openrouter.ai/api/v1", "model": "anthropic/claude-sonnet-4",
        "context_limit": 200000, "requires_key": True,
        "api_key": "sk-FROM-REST-MUST-VANISH",
    })
    assert created.status_code == 201, created.text

    # Every READ surface a downstream surface consumes: the sync pull + both CRUD reads.
    pulled = client.get("/api/sync/pull").json()
    listed = client.get("/api/profiles").json()["profiles"]
    got_x = client.get("/api/profiles/prof_x").json()["profile"]
    got_y = client.get("/api/profiles/prof_y").json()["profile"]

    # 1) The shape is exactly the agreed cross-surface field set — no more, no less, no key.
    for served in (got_x, got_y, *listed):
        assert set(served.keys()) == _PROFILE_SHAPE_KEYS, set(served.keys()) ^ _PROFILE_SHAPE_KEYS

    # 2) No key material survives on ANY read surface, from EITHER ingress.
    surfaces_blob = json.dumps([pulled, listed, got_x, got_y])
    for needle in ("api_key", "apiKey", "FROM-SYNC-MUST-VANISH", "FROM-REST-MUST-VANISH"):
        assert needle not in surfaces_blob, f"{needle!r} leaked onto a read surface"

    # 3) The shape itself round-tripped intact (parity is real, not achieved by dropping data).
    assert got_x["base_url"] == "https://api.anthropic.com/v1" and got_x["context_limit"] == 200000
    assert got_y["model"] == "anthropic/claude-sonnet-4" and got_y["requires_key"] is True


# ── HSM-22-04: the travelling graph — SYNCED in, RUN on the hub ──────────────

def test_ipad_synced_graph_workflow_runs_on_the_hub(env, monkeypatch) -> None:
    """The whole Phase-22 loop over the real app: the SWIFT-ENCODED golden
    fixture (`blueprint-linear-sample.json`, the iPad Blueprint encoder's exact
    bytes) rides `/api/sync/push` as a workflow's `graph_json`, then
    `/api/workflows/{id}/run` executes the synced graph — threaded node order,
    the per-node provenance surfaced in the steps, the run-born artifact minted.
    Authored on one surface, synced, run on the hub: the graph travels."""
    db, client = env

    fixtures = (Path(__file__).resolve().parents[2]
                / "pm" / "roadmap" / "holdspeak-mobile" / "contracts" / "fixtures")
    graph = json.loads((fixtures / "blueprint-linear-sample.json").read_text(encoding="utf-8"))

    lm = "2030-06-26T12:00:00Z"
    push = client.post("/api/sync/push", json={"workflows": [{
        "meta": {"id": "wf-golden", "kind": "workflow", "last_modified": lm, "deleted": False},
        "value": {"name": graph["name"], "prompt": "fallback: {input}", "graph_json": graph},
    }]})
    assert push.status_code == 200
    assert push.json()["received"]["workflows"] == 1

    calls = []

    class _FakeIntel:
        active_provider = "local"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            calls.append(user_prompt)
            return f"risk: finding {len(calls)}\nnoise line"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _FakeIntel()
    )

    resp = client.post("/api/workflows/wf-golden/run", json={"input": "the standup"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # The graph ran (never the prompt fallback): llm → extract → keep_if in the
    # fixture's exec order, with the iPad-authored provenance on the steps.
    assert "warning" not in body
    assert [s["node_id"] for s in body["steps"]] == ["ask", "dec", "keep"]
    assert [s["kind"] for s in body["steps"]] == ["llm", "extract", "keep_if"]
    by_id = {s["node_id"]: s for s in body["steps"]}
    assert by_id["ask"]["failure_policy"] == "fallbackOnDevice"
    assert by_id["ask"]["runs_on"] == "endpoint"
    assert by_id["dec"]["failure_policy"] == "skip"
    assert by_id["dec"]["runs_on"] == "onDevice"

    # Two model ops fired; keep_if (pure) kept only the risk line of the last output.
    assert len(calls) == 2
    assert body["output"] == "risk: finding 2"

    # The run persisted as a run-born artifact with the workflow as its lineage.
    assert body["artifact_id"]
    assert body["sources"] == [{"source_type": "workflow", "source_ref": "wf-golden"}]
