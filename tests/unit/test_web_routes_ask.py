"""The Ask AI atom's hub routes (HSM-16-04, the web parity of HSM-16-09).

/api/ask runs an instruction over lasso'd context and persists NOTHING —
keep/bin is the human's judgment. /api/ask/keep mints the kept artifact
wearing the SAME provenance wire shape the iPad's kept Ask wears
(DeskRecords.swift `provenanceJSON` / `provenanceSources`), locked here
byte-for-byte so 16-06's cross-surface proof has one shape to trust.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


class _FakeIntel:
    active_provider = "local"

    def __init__(self):
        self.captured = {}

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        self.captured["system_prompt"] = system_prompt
        self.captured["user_prompt"] = user_prompt
        return "PRINTED"


def test_ask_requires_prompt(env) -> None:
    _, client = env
    assert client.post("/api/ask", json={}).status_code == 400
    assert client.post("/api/ask", json={"prompt": "  "}).status_code == 400


def test_ask_grounds_in_the_canonical_store_and_persists_nothing(env, monkeypatch) -> None:
    """The Phase-53 lesson, asserted: the lasso'd cards' CONTENT reaches the
    model — grounding is loaded from the hub's store, never a client claim."""
    db, client = env
    nid = client.post(
        "/api/notes", json={"title": "Mesh sync owner", "body_markdown": "Karol owns the mesh."}
    ).json()["note"]["id"]
    db.plugins.record_artifact(
        artifact_id="artifact_ask1", meeting_id="", artifact_type="plugin_output",
        title="Q3 summary", body_markdown="Ship the manifest.",
    )

    fake = _FakeIntel()
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: fake
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.sync._hub_model_name", lambda ctx: "HubModel-9B"
    )

    before = len(db.plugins.list_run_artifacts())
    resp = client.post("/api/ask", json={
        "prompt": "Distill the state of play.",
        "lens": "Distill",
        "context": [
            {"id": nid, "kind": "note"},
            {"id": "artifact_ask1", "kind": "artifact"},
            {"id": "ghost", "kind": "meeting", "title": "Offline card"},
        ],
    })
    assert resp.status_code == 200
    body = resp.json()

    # The instruction leads; every card's stored content follows as material.
    up = fake.captured["user_prompt"]
    assert up.startswith("Distill the state of play.")
    assert "## Mesh sync owner\nKarol owns the mesh." in up
    assert "## Q3 summary\nShip the manifest." in up
    # A card the hub can't load contributes its title honestly.
    assert "## Offline card" in up

    assert body["output"] == "PRINTED"
    assert body["lens"] == "Distill"
    assert body["provider"] == "local"
    assert body["profile_id"] is None
    assert body["egress"] == {"scope": "local"}
    assert body["model"] == "HubModel-9B"
    # Titles resolve from the store (the note's real title, not a client hint).
    assert body["context_titles"] == ["Mesh sync owner", "Q3 summary", "Offline card"]

    # The run route persists NOTHING — keep/bin is the human's judgment.
    assert len(db.plugins.list_run_artifacts()) == before


def test_ask_runs_on_profile_and_names_honest_egress(env, monkeypatch) -> None:
    _, client = env
    pid = client.post("/api/profiles", json={
        "name": "LAN box", "kind": "openAICompatible",
        "base_url": "http://192.168.1.43:8080/v1", "model": "Qwen3.5-9B-Q6_K",
    }).json()["profile"]["id"]

    captured = {}

    def fake_for_profile(*, kind, base_url, model, profile_id):
        captured.update(kind=kind, base_url=base_url, model=model, profile_id=profile_id)
        intel = _FakeIntel()
        intel.active_provider = "cloud"
        return intel

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile", fake_for_profile
    )

    resp = client.post("/api/ask", json={"prompt": "Go", "profile_id": pid})
    assert resp.status_code == 200
    body = resp.json()
    assert captured["profile_id"] == pid
    # The badge names where THIS run went — the run's profile, never the app default.
    assert body["egress"] == {"scope": "cloud", "host": "192.168.1.43"}
    assert body["model"] == "Qwen3.5-9B-Q6_K"
    assert body["profile_id"] == pid


def test_ask_model_override_picks_the_matching_profile(env, monkeypatch) -> None:
    """HSM-15-11: `model` alone selects the hub profile that runs that model —
    the phone can say "think with Qwen3.5-9B" without knowing profile ids."""
    _, client = env
    pid = client.post("/api/profiles", json={
        "name": "LAN box", "kind": "openAICompatible",
        "base_url": "http://192.168.1.43:8080/v1", "model": "Qwen3.5-9B-Q6_K",
    }).json()["profile"]["id"]

    captured = {}

    def fake_for_profile(*, kind, base_url, model, profile_id):
        captured.update(model=model, profile_id=profile_id)
        intel = _FakeIntel()
        intel.active_provider = "cloud"
        return intel

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile", fake_for_profile
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.sync._hub_model_name", lambda ctx: "HubModel-9B"
    )

    resp = client.post("/api/ask", json={"prompt": "Go", "model": "Qwen3.5-9B-Q6_K"})
    assert resp.status_code == 200
    body = resp.json()
    assert captured == {"model": "Qwen3.5-9B-Q6_K", "profile_id": pid}
    assert body["model"] == "Qwen3.5-9B-Q6_K"     # the run record names what ran
    assert body["profile_id"] == pid
    assert body["egress"] == {"scope": "cloud", "host": "192.168.1.43"}


def test_ask_model_override_matching_the_hubs_own_model_runs_the_default_engine(env, monkeypatch) -> None:
    _, client = env
    fake = _FakeIntel()
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: fake
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.sync._hub_model_name", lambda ctx: "HubModel-9B"
    )
    resp = client.post("/api/ask", json={"prompt": "Go", "model": "HubModel-9B"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == "HubModel-9B"
    assert body["egress"] == {"scope": "local"}
    assert body["profile_id"] is None


def test_ask_model_override_refuses_a_model_the_hub_cannot_run(env, monkeypatch) -> None:
    """The manifest is the allow-list: a model some other node pushed (or a
    typo) refuses loudly with the runnable set — never a silent fallback."""
    _, client = env
    client.post("/api/profiles", json={
        "name": "LAN box", "kind": "openAICompatible",
        "base_url": "http://192.168.1.43:8080/v1", "model": "Qwen3.5-9B-Q6_K",
    })
    monkeypatch.setattr(
        "holdspeak.web.routes.sync._hub_model_name", lambda ctx: "HubModel-9B"
    )
    resp = client.post("/api/ask", json={"prompt": "Go", "model": "iphone-gemma4-2B"})
    assert resp.status_code == 400
    body = resp.json()
    assert "not runnable" in body["error"]
    assert body["allowed_models"] == ["HubModel-9B", "Qwen3.5-9B-Q6_K"]


def _seed_meeting(db, mid: str, title: str, *, segments=None, intel=None) -> None:
    from datetime import datetime

    from holdspeak.meeting_session import MeetingState

    db.meetings.save_meeting(MeetingState(
        id=mid, started_at=datetime(2026, 7, 1, 10, 0, 0),
        ended_at=datetime(2026, 7, 1, 11, 0, 0), title=title,
        segments=segments or [], intel=intel,
    ))


def test_ask_grounding_hydrates_references_from_the_hub_store(env, monkeypatch) -> None:
    """HSM-15-12: the envelope ships ids; the hub hydrates the bodies — the
    answer can know content the phone never shipped. Blocks wear the envelope's
    provenance headers, and the lineage folds into context_ids/titles."""
    from holdspeak.meeting_session import IntelSnapshot, TranscriptSegment

    db, client = env
    _seed_meeting(
        db, "m_env1", "Q3 kickoff",
        segments=[TranscriptSegment(text="We ship the manifest.", speaker="Karol",
                                    start_time=0.0, end_time=2.0)],
        intel=IntelSnapshot(timestamp=1.0, summary="Kickoff decided the manifest ships.",
                            action_items=[{"id": "ai_env1", "task": "Ship the manifest"}]),
    )
    db.plugins.record_artifact(
        artifact_id="artifact_env1", meeting_id="m_env1", artifact_type="decisions",
        title="Decisions", body_markdown="- The manifest ships this quarter.",
    )

    fake = _FakeIntel()
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: fake
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.sync._hub_model_name", lambda ctx: "HubModel-9B"
    )

    resp = client.post("/api/ask", json={
        "prompt": "What did we decide?",
        "grounding": {"meeting_ids": ["m_env1"], "artifact_ids": ["artifact_env1"]},
    })
    assert resp.status_code == 200
    body = resp.json()

    up = fake.captured["user_prompt"]
    assert up.startswith("What did we decide?")
    # Provenance-headed blocks — the ONE envelope shape (story 15-12).
    assert "[MEETING: Q3 kickoff — 2026-07-01]" in up
    assert "Kickoff decided the manifest ships." in up      # summary expand = intel digest
    assert "- Ship the manifest" in up
    assert "[ARTIFACT: Decisions — Q3 kickoff]" in up
    assert "- The manifest ships this quarter." in up

    # The lineage is one list: grounding rides context_ids/titles + the echo.
    assert body["context_ids"] == ["m_env1", "artifact_env1"]
    assert body["context_titles"] == ["Q3 kickoff", "Decisions"]
    assert body["grounding"] == {
        "meeting_ids": ["m_env1"], "artifact_ids": ["artifact_env1"],
        "expand": "summary", "titles": ["Q3 kickoff", "Decisions"],
    }


def test_ask_grounding_full_expand_hydrates_the_transcript_and_marks_a_cut(env, monkeypatch) -> None:
    """expand=full reads the real segments; a transcript past the bound is CUT
    WITH A MARKER in the block — never trimmed silently (the overflow rule)."""
    from holdspeak.meeting_session import TranscriptSegment

    db, client = env
    segs = [TranscriptSegment(text=f"Point {i} on the mesh roadmap, in detail.",
                              speaker="Karol", start_time=float(i), end_time=float(i) + 1)
            for i in range(400)]
    _seed_meeting(db, "m_env2", "Deep dive", segments=segs)

    fake = _FakeIntel()
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: fake
    )
    monkeypatch.setattr(
        "holdspeak.web.routes.sync._hub_model_name", lambda ctx: "HubModel-9B"
    )

    resp = client.post("/api/ask", json={
        "prompt": "Recap.",
        "grounding": {"meeting_ids": ["m_env2"], "expand": "full"},
    })
    assert resp.status_code == 200
    up = fake.captured["user_prompt"]
    assert "Karol: Point 0 on the mesh roadmap" in up
    assert "[transcript cut at 12000 chars]" in up


def test_ask_grounding_refuses_unknown_ids_loudly(env, monkeypatch) -> None:
    """Grounding is never a best-effort claim: an id the hub does not hold
    refuses the whole ask, naming the ids (unlike inline context's title-only
    honesty, which predates the envelope)."""
    from holdspeak.meeting_session import TranscriptSegment

    db, client = env
    _seed_meeting(db, "m_env3", "Real one",
                  segments=[TranscriptSegment(text="hi", speaker="Me",
                                              start_time=0.0, end_time=1.0)])
    resp = client.post("/api/ask", json={
        "prompt": "Go",
        "grounding": {"meeting_ids": ["m_env3", "ghost_m"], "artifact_ids": ["ghost_a"]},
    })
    assert resp.status_code == 400
    body = resp.json()
    assert "not on this hub" in body["error"]
    assert body["unknown_ids"] == ["ghost_m", "ghost_a"]


def test_ask_grounding_refuses_bad_shapes(env) -> None:
    _, client = env
    assert client.post("/api/ask", json={
        "prompt": "Go", "grounding": "meetings",
    }).status_code == 400
    assert client.post("/api/ask", json={
        "prompt": "Go", "grounding": {"meeting_ids": ["m1"], "expand": "everything"},
    }).status_code == 400
    too_many = {"meeting_ids": [f"m{i}" for i in range(17)]}
    resp = client.post("/api/ask", json={"prompt": "Go", "grounding": too_many})
    assert resp.status_code == 400
    assert "capped at 16" in resp.json()["error"]


def test_ask_surfaces_engine_error_as_502(env, monkeypatch) -> None:
    _, client = env
    from holdspeak.intel.models import MeetingIntelError

    class _Boom:
        active_provider = "local"

        def run_prompt(self, **kwargs):
            raise MeetingIntelError("no model")

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: _Boom()
    )
    resp = client.post("/api/ask", json={"prompt": "Go"})
    assert resp.status_code == 502
    assert "no model" in resp.json()["error"]


def test_ask_keep_mints_the_ipad_wire_shape(env) -> None:
    """The kept ask's provenance is byte-shaped like the iPad's — one shape,
    one renderer, every surface (the 16-06 cross-surface contract)."""
    db, client = env
    resp = client.post("/api/ask/keep", json={
        "lens": "Distill",
        "prompt": "Distill the state of play.",
        "output": "The mesh is real.",
        "context": [
            {"id": "m:askM", "title": "Q3 kickoff"},
            {"id": "note:askN", "title": "Mesh sync owner"},
            {"id": "out:askO", "title": "Q3 summary"},
        ],
    })
    assert resp.status_code == 201
    aid = resp.json()["artifact_id"]

    art = db.plugins.get_artifact(aid)
    assert art is not None
    assert art.artifact_type == "plugin_output"
    assert art.title == "Distill"
    assert art.body_markdown == "The mesh is real."
    assert art.status == "draft"

    # The structured provenance — EXACT key set and values (ask keys ride only
    # when present; the golden recipe/chain shape is untouched by design).
    assert art.structured_json["lens"] == "Distill"
    assert art.structured_json["source"] == "3 items"
    assert art.structured_json["provenance"] == {
        "source_card_id": "",
        "source_card_title": "3 items",
        "via_id": "",
        "via_name": "Distill",
        "via_kind": "ask",
        "context_ids": ["m:askM", "note:askN", "out:askO"],
        "context_titles": ["Q3 kickoff", "Mesh sync owner", "Q3 summary"],
        "prompt": "Distill the state of play.",
    }

    # The canonical sources rows: every card the ask read + its own via row.
    # (The store reads rows back ORDER BY source_type, source_ref — assert the
    # exact set; renderers resolve by type, not position.)
    assert sorted(art.sources, key=lambda s: (s["source_type"], s["source_ref"])) == [
        {"source_type": "ask", "source_ref": "Distill"},
        {"source_type": "card", "source_ref": "Mesh sync owner"},
        {"source_type": "card", "source_ref": "Q3 kickoff"},
        {"source_type": "card", "source_ref": "Q3 summary"},
    ]

    # Run-born: it rides the sync pull's run lane like the iPad's kept Ask.
    assert aid in {a.id for a in db.plugins.list_run_artifacts()}


def test_ask_keep_single_context_names_the_source_card(env) -> None:
    db, client = env
    aid = client.post("/api/ask/keep", json={
        "lens": "Summarize",
        "prompt": "Summarize.",
        "output": "Short.",
        "context": [{"id": "m:one", "title": "Q3 kickoff"}],
    }).json()["artifact_id"]
    prov = db.plugins.get_artifact(aid).structured_json["provenance"]
    assert prov["source_card_id"] == "m:one"
    assert prov["source_card_title"] == "Q3 kickoff"


def test_ask_keep_requires_output(env) -> None:
    _, client = env
    assert client.post("/api/ask/keep", json={"lens": "Ask", "prompt": "p"}).status_code == 400
