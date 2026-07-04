"""Mission-control bridge tests (HS-82-02).

The bridge relays the three Delivery Workbench documents byte-honest
from the dw CLI, with schema checks at the door. Everything here
runs against a fake runner and a temp project map — no real rails
repo, no real CLI, per the design's injection seams
(docs/MISSION_CONTROL_DESK.md §1).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.missioncontrol_bridge import (
    FEED_SCHEMA_PROVEN,
    load_project_map,
    state_payload,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_missioncontrol_router

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

SESSIONS_DOC = {
    "sessions_schema": 1,
    "registry": "ok",
    "sessions": [
        {
            "key": "claude:s1",
            "agent": "claude",
            "correlation": "on_story",
            "stories": [{"story_id": "DM-1-02"}],
            "awaiting_response": True,
            "stale": False,
            "tmux": {"session": "desk"},
        }
    ],
}

EVENTS_DOC = [
    {"ts": "2026-07-04T12:00:00Z", "event": "gate_refusal",
     "story": "DM-1-02", "detail": {"rule": "story-evidence"}},
]


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
    app.include_router(
        build_missioncontrol_router(
            WebContext(get_state=lambda: {}), runner=runner, map_path=map_path
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
            load_project_map(_make_map(tmp_path)), hangs
        )["repos"][0]
        assert entry["status"] == "unavailable"


class TestSessionsRoute:
    def test_sessions_relayed_once_desk_global(self, tmp_path):
        client = _client(
            _make_map(tmp_path), _runner_for({"sessions": SESSIONS_DOC})
        )
        payload = client.get("/api/missioncontrol/sessions").json()
        assert payload["status"] == "live"
        assert payload["sessions"] == SESSIONS_DOC

    def test_unproven_sessions_schema_refused(self, tmp_path):
        drifted = {**SESSIONS_DOC, "sessions_schema": 99}
        client = _client(
            _make_map(tmp_path), _runner_for({"sessions": drifted})
        )
        payload = client.get("/api/missioncontrol/sessions").json()
        assert payload["status"] == "compatibility"

    def test_no_map_is_unavailable(self, tmp_path):
        client = _client(
            tmp_path / "absent.json", _runner_for({"sessions": SESSIONS_DOC})
        )
        payload = client.get("/api/missioncontrol/sessions").json()
        assert payload["status"] == "unavailable"


class TestEventsRoute:
    def test_events_relayed_with_tail_clamped(self, tmp_path):
        calls = []

        def runner(argv, cwd=None):
            calls.append(list(argv))
            return SimpleNamespace(
                returncode=0, stdout=json.dumps(EVENTS_DOC), stderr=""
            )

        client = _client(_make_map(tmp_path), runner)
        payload = client.get(
            "/api/missioncontrol/events", params={"tail": 999}
        ).json()
        assert payload["repos"][0]["status"] == "live"
        assert payload["repos"][0]["events"] == EVENTS_DOC
        assert "100" in calls[0]  # clamped to the design's ceiling

    def test_non_list_events_is_compatibility(self, tmp_path):
        client = _client(
            _make_map(tmp_path), _runner_for({"events": {"not": "a list"}})
        )
        entry = client.get("/api/missioncontrol/events").json()["repos"][0]
        assert entry["status"] == "compatibility"
