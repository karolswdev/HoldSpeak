"""The iPad belt's two reads and the project map (HS-82-02, HS-88-03).

The state feed is relayed byte-honest from the dw CLI, with schema checks at
the door; the rails journal lists the observer's notes. The rest of Mission
control is parked; its tests are in
tests/_parked/unit/test_web_routes_missioncontrol_20261109.py. Everything here
runs against a fake runner and a temp project map: no real rails repo, no real
CLI.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.missioncontrol_bridge import (
    FEED_SCHEMA_PROVEN,
    load_project_map,
    state_payload,
)
from holdspeak.principals import Principal, PrincipalKind, UNAUTHENTICATED
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_missioncontrol_router

OWNER = Principal(PrincipalKind.OWNER, "owner-session")


def _authenticate_owner(app: FastAPI) -> None:
    @app.middleware("http")
    async def owner_principal(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)


FEED_DOC = {
    "feed_schema": 1,
    "generated_at_tree": "abc123",
    "projects": [
        {
            "slug": "demo",
            "prefix": "DM",
            "current_phase": {
                "number": 1,
                "title": "Alpha",
                "status": "open",
                "stories_done": 1,
                "stories_total": 2,
            },
            "next_story": {
                "story_id": "DM-1-02",
                "title": "Second thing",
                "status": "ready",
            },
            "phases": [],
            "stories": [],
            "warnings": 0,
        }
    ],
}


def _runner_for(documents: dict[str, object]):
    """A fake dw CLI: keyed by the dw verb in the argv tail."""

    def runner(argv, cwd=None):
        for verb, doc in documents.items():
            if verb in argv:
                return SimpleNamespace(
                    returncode=0, stdout=json.dumps(doc), stderr=""
                )
        return SimpleNamespace(returncode=1, stdout="", stderr="unknown verb")

    return runner


def _make_map(tmp_path: Path) -> Path:
    repo = tmp_path / "rails-repo"
    (repo / ".githooks").mkdir(parents=True)
    dw = repo / ".githooks" / "dw"
    dw.write_text("#!/usr/bin/env python3\n")
    dw.chmod(0o755)
    map_path = tmp_path / "delivery_workbench.json"
    map_path.write_text(
        json.dumps({"projects": {"demo": str(repo)}, "default": str(repo)})
    )
    return map_path


def _client(map_path: Path, runner) -> TestClient:
    app = FastAPI()
    _authenticate_owner(app)
    app.include_router(
        build_missioncontrol_router(
            WebContext(get_state=lambda: {}),
            runner=runner,
            map_path=map_path,
        )
    )
    return TestClient(app)


class TestProjectMap:
    def test_missing_map_is_empty_not_an_error(self, tmp_path):
        loaded = load_project_map(tmp_path / "absent.json")
        assert loaded == {"projects": {}, "default": None}

    def test_dead_paths_are_dropped(self, tmp_path):
        map_path = tmp_path / "m.json"
        map_path.write_text(
            json.dumps({"projects": {"gone": str(tmp_path / "gone")}})
        )
        loaded = load_project_map(map_path)
        assert loaded["projects"] == {}
        assert loaded["default"] is None


class TestStateRoute:
    def test_feed_is_relayed_byte_honest(self, tmp_path):
        client = _client(
            _make_map(tmp_path), _runner_for({"state": FEED_DOC})
        )
        payload = client.get("/api/missioncontrol/state").json()
        assert payload["repos"][0]["status"] == "live"
        # Byte-honest: the document is the dw document, unreshaped.
        assert payload["repos"][0]["feed"] == FEED_DOC

    def test_schema_drift_is_a_typed_compatibility_error(self, tmp_path):
        drifted = {**FEED_DOC, "feed_schema": FEED_SCHEMA_PROVEN + 1}
        client = _client(
            _make_map(tmp_path), _runner_for({"state": drifted})
        )
        entry = client.get("/api/missioncontrol/state").json()["repos"][0]
        assert entry["status"] == "compatibility"
        assert "proven against" in entry["detail"]
        assert "feed" not in entry

    def test_dead_cli_is_unavailable_with_stderr_tail(self, tmp_path):
        def dead(argv, cwd=None):
            return SimpleNamespace(
                returncode=2, stdout="", stderr="boom line 1\nfinal boom"
            )

        client = _client(_make_map(tmp_path), dead)
        entry = client.get("/api/missioncontrol/state").json()["repos"][0]
        assert entry["status"] == "unavailable"
        assert "final boom" in entry["detail"]

    def test_timeout_is_unavailable(self, tmp_path):
        def hangs(argv, cwd=None):
            raise subprocess.TimeoutExpired(cmd=argv, timeout=30)

        entry = state_payload(
            load_project_map(_make_map(tmp_path)), hangs, principal=OWNER
        )["repos"][0]
        assert entry["status"] == "unavailable"

    def test_unauthenticated_read_refuses_before_dw(self, tmp_path):
        from holdspeak.connector_runtime import ReadSubprocessDenied

        called = False

        def forbidden_runner(*_args, **_kwargs):
            nonlocal called
            called = True

        with pytest.raises(ReadSubprocessDenied):
            state_payload(
                load_project_map(_make_map(tmp_path)),
                forbidden_runner,
                principal=UNAUTHENTICATED,
            )
        assert called is False


class TestRailsJournal:
    """The observer's journal read (HS-88-03) — notes tagged
    rails-journal, newest first, read-only."""

    def test_journal_lists_tagged_notes(self, tmp_path, monkeypatch):
        from holdspeak.db.core import Database, reset_database
        from holdspeak import rails_observer

        reset_database()
        db = Database(tmp_path / "hs.db")
        monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
        batch = rails_observer.summarize_batch(
            [{"ts": "t1", "event": "story_status", "story": "HS-1", "repo": "code"}],
            summarize_fn=lambda s, u: "HS-1 shipped.",
        )
        rails_observer.record_journal_entry(db, batch, title="Rails journal")

        client = _client(_make_map(tmp_path), _runner_for({}))
        res = client.get("/api/missioncontrol/rails/journal")
        assert res.status_code == 200
        entries = res.json()["entries"]
        assert len(entries) == 1
        assert "HS-1 shipped." in entries[0]["body_markdown"]
        reset_database()
