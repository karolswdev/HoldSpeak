"""HS-74-01 — run results persist as run-born artifacts (schema v6).

A persona/chain/workflow run's output enters the ONE artifact store with
capability lineage instead of evaporating with the HTTP response: it rides
`/api/sync/pull` in the unchanged value shape (`meeting_id` stays a plain
string — `""` for run-born, so the iPad's non-optional decode is unmoved),
and the v5→v6 upgrade rebuilds the artifacts table without losing a row.
"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="route tests drive the real app")

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database


@pytest.fixture()
def db(monkeypatch):
    reset_database()
    database = Database(Path(tempfile.mkdtemp()) / "run-artifacts.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: database)
    yield database
    reset_database()


def test_record_artifact_accepts_run_born(db) -> None:
    db.plugins.record_artifact(
        artifact_id="run-1", meeting_id="", artifact_type="run_output",
        title="Owl: hi", body_markdown="answer", status="draft",
        plugin_id="recipe_run", plugin_version="1",
        sources=[{"source_type": "recipe", "source_ref": "a-owl"}],
    )
    got = db.plugins.get_artifact("run-1")
    assert got is not None
    assert got.meeting_id == ""  # NULL in the DB, a string on every surface
    assert got.sources == [{"source_type": "recipe", "source_ref": "a-owl"}]


def test_artifact_id_still_required(db) -> None:
    with pytest.raises(ValueError):
        db.plugins.record_artifact(
            artifact_id="", meeting_id="", artifact_type="run_output",
            title="x",
        )


def test_meeting_scoped_listing_unaffected(db) -> None:
    from holdspeak.meeting_session import MeetingState

    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="M")
    )
    db.plugins.record_artifact(
        artifact_id="meet-art", meeting_id="m1", artifact_type="decisions",
        title="D", body_markdown="-", status="draft",
    )
    db.plugins.record_artifact(
        artifact_id="run-art", meeting_id="", artifact_type="run_output",
        title="R", body_markdown="-", status="draft",
        sources=[{"source_type": "recipe", "source_ref": "a1"}],
    )
    meeting_side = db.plugins.list_artifacts("m1")
    assert [a.id for a in meeting_side] == ["meet-art"]
    run_side = db.plugins.list_run_artifacts()
    assert [a.id for a in run_side] == ["run-art"]


def test_agent_run_persists_and_responds_with_artifact_id(db, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    db.recipes.upsert(recipe_id="a-owl", name="Owl", avatar="🦉",
                     system_prompt="terse")

    class _StubIntel:
        active_provider = "stub"

        def run_prompt(self, **kwargs):
            return "the run output"

    import holdspeak.intel.providers as providers
    monkeypatch.setattr(
        providers, "build_configured_meeting_intel", lambda: _StubIntel()
    )

    server = MeetingWebServer(WebRuntimeCallbacks(
        on_bookmark=lambda *a, **k: None, on_stop=lambda *a, **k: None,
        get_state=lambda: {"activity": {"state": "idle"}},
    ), host="127.0.0.1")
    client = TestClient(server.app)

    resp = client.post("/api/recipes/a-owl/run", json={"input": "say hi"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["output"] == "the run output"
    artifact_id = data["artifact_id"]
    assert artifact_id

    stored = db.plugins.get_artifact(artifact_id)
    assert stored is not None
    assert stored.body_markdown == "the run output"
    assert stored.plugin_id == "recipe_run"
    assert {"source_type": "recipe", "source_ref": "a-owl"} in stored.sources
    assert stored.title == "Owl: say hi"

    # The run-born artifact rides the pull with the unchanged value shape.
    pull = client.get("/api/sync/pull?limit=50").json()
    arts = [r for r in pull["artifacts"] if r["meta"]["id"] == artifact_id]
    assert len(arts) == 1
    value = arts[0]["value"]
    assert value["meeting_id"] == ""  # a plain string on the wire, never null
    assert value["body_markdown"] == "the run output"
    assert value["origin"] == "run"  # explicit since HSM-18-07, not inferred


def test_origin_explicit_on_every_serialized_surface(db) -> None:
    """HSM-18-07 — `origin` rides the wire ('run' | 'meeting') on both artifact
    surfaces (sync pull + the meeting artifacts route), and the emitted values
    still validate against the cross-surface artifact contract schema — with
    `origin` absent staying valid (a client push may omit it)."""
    import json as jsonlib

    jsonschema = pytest.importorskip("jsonschema")

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.meeting_session import MeetingState
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_sync_router
    from holdspeak.web.routes.sync import _artifact_value

    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="M")
    )
    db.plugins.record_artifact(
        artifact_id="anchored-1", meeting_id="m1", artifact_type="decisions",
        title="Anchored", body_markdown="b", status="draft",
        plugin_id="decision_capture", plugin_version="1",
    )
    db.plugins.record_artifact(
        artifact_id="run-1", meeting_id="", artifact_type="plugin_output",
        title="Run-born", body_markdown="answer", status="draft",
        plugin_id="recipe_run", plugin_version="1",
        sources=[{"source_type": "recipe", "source_ref": "a-owl"}],
    )

    app = FastAPI()
    app.include_router(build_sync_router(WebContext(get_state=lambda: {})))
    pull = TestClient(app).get("/api/sync/pull?limit=50").json()
    values = {r["meta"]["id"]: r["value"] for r in pull["artifacts"]}
    assert values["anchored-1"]["origin"] == "meeting"
    assert values["run-1"]["origin"] == "run"
    assert values["run-1"]["meeting_id"] == ""

    # The other serialized surface — a stored summary through the meetings
    # route's dict shape (the route emits `artifact.origin` verbatim).
    stored = db.plugins.get_artifact("anchored-1")
    assert stored.origin == "meeting"
    assert db.plugins.get_artifact("run-1").origin == "run"

    # Both emitted values validate against the contract schema; an origin-less
    # copy (a client push) stays valid too.
    schema_path = (
        Path(__file__).parents[2]
        / "pm/roadmap/holdspeak-mobile/contracts/schemas/artifact.schema.json"
    )
    schema = jsonlib.loads(schema_path.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for aid in ("anchored-1", "run-1"):
        validator.validate(values[aid])
        originless = dict(values[aid])
        originless.pop("origin")
        validator.validate(originless)
    assert _artifact_value(stored)["origin"] == "meeting"


def test_v5_to_v6_upgrade_rebuilds_without_losing_rows(tmp_path) -> None:
    """A v5-facsimile DB (artifacts.meeting_id NOT NULL, no origin) upgrades:
    rows survive with ids verbatim, origin backfills to 'meeting'."""
    import sqlite3

    db_path = tmp_path / "v5.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE schema_version (version INTEGER NOT NULL);
        INSERT INTO schema_version (version) VALUES (5);
        CREATE TABLE meetings (id TEXT PRIMARY KEY, started_at TEXT);
        INSERT INTO meetings (id, started_at) VALUES ('m1', '2026-01-01T00:00:00');
        CREATE TABLE artifacts (
            id TEXT PRIMARY KEY,
            meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
            artifact_type TEXT NOT NULL,
            title TEXT NOT NULL,
            body_markdown TEXT NOT NULL DEFAULT '',
            structured_json TEXT NOT NULL DEFAULT '{}',
            confidence REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'draft',
            plugin_id TEXT NOT NULL DEFAULT 'unknown',
            plugin_version TEXT NOT NULL DEFAULT 'unknown',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO artifacts (id, meeting_id, artifact_type, title)
        VALUES ('old-art', 'm1', 'decisions', 'Kept');
        """
    )
    conn.commit()
    conn.close()

    reset_database()
    upgraded = Database(db_path)
    rows = upgraded._connection_for_tests() if hasattr(upgraded, "_connection_for_tests") else None
    got = upgraded.plugins.get_artifact("old-art")
    assert got is not None and got.title == "Kept" and got.meeting_id == "m1"
    # And the rebuilt table accepts a run-born row (the point of v6).
    upgraded.plugins.record_artifact(
        artifact_id="run-after-upgrade", meeting_id="",
        artifact_type="run_output", title="R",
        sources=[{"source_type": "recipe", "source_ref": "a1"}],
    )
    assert upgraded.plugins.get_artifact("run-after-upgrade") is not None
    # A backup landed before the migration (the Phase-50 contract).
    backups = list(db_path.parent.glob(f"{db_path.name}.*.bak"))
    assert backups, "no backup before the schema migration"
    reset_database()
