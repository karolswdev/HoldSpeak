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


# ── The approval leg (HS-82-05): propose → approve → execute ────────
# The dw CLI is a fake runner; the db is real (temp file); the gate's
# refusal banner is proven to ride back verbatim on the crown case.

import holdspeak.db as db_module
import holdspeak.web.routes.missioncontrol as mc_routes
from holdspeak.db.core import Database


def _propose_client(tmp_path, monkeypatch, dw_runner):
    db = Database(tmp_path / "mc.db")
    monkeypatch.setattr(db_module, "get_database", lambda db_path=None: db)
    monkeypatch.setattr(mc_routes, "_DW_RUNNER", dw_runner)
    broadcasts = []
    app = FastAPI()
    app.include_router(
        build_missioncontrol_router(
            WebContext(
                get_state=lambda: {},
                broadcast=lambda kind, data: broadcasts.append((kind, data)),
            ),
            runner=dw_runner,
            map_path=_make_map(tmp_path),
        )
    )
    return TestClient(app), db, broadcasts


def _flip_body(story="DM-1-02", status="in-progress"):
    return {
        "repo": "demo", "verb": "status", "project": "demo",
        "story": story, "status": status,
    }


FEED_WITH_STORIES = {
    **FEED_DOC,
    "projects": [
        {
            **FEED_DOC["projects"][0],
            "phases": [
                {"number": 1, "title": "Alpha", "status": "open",
                 "stories_done": 1, "stories_total": 2},
            ],
            "stories": [
                {"story_id": "DM-1-01", "title": "First", "status": "done",
                 "phase": 1, "evidence_exists": True},
                {"story_id": "DM-1-02", "title": "Second", "status": "in-progress",
                 "phase": 1, "evidence_exists": False},
            ],
        }
    ],
}


class TestApprovalLeg:
    def test_propose_validates_against_the_live_feed(self, tmp_path, monkeypatch):
        client, _db, _b = _propose_client(
            tmp_path, monkeypatch, _runner_for({"state": FEED_WITH_STORIES})
        )
        for bad, why in [
            ({**_flip_body(), "repo": "ghost"}, "project map"),
            ({**_flip_body(), "project": "ghost"}, "not on the roadmap"),
            ({**_flip_body(story="DM-9-99")}, "not on the demo roadmap"),
            ({**_flip_body(status="shipped-it")}, "is not one of"),
            ({**_flip_body(), "verb": "delete"}, "not an allow-listed"),
        ]:
            resp = client.post("/api/missioncontrol/story/propose", json=bad)
            assert resp.status_code == 400, bad
            assert why in resp.json()["error"]

    def test_propose_then_approve_executes_the_allowed_argv(
        self, tmp_path, monkeypatch
    ):
        argv_log = []

        def runner(argv, cwd=None, **kwargs):
            argv_log.append(list(argv))
            if "state" in argv:
                return SimpleNamespace(
                    returncode=0, stdout=json.dumps(FEED_WITH_STORIES), stderr=""
                )
            return SimpleNamespace(returncode=0, stdout="DM-1-02\tblocked", stderr="")

        client, _db, broadcasts = _propose_client(tmp_path, monkeypatch, runner)
        resp = client.post(
            "/api/missioncontrol/story/propose",
            json=_flip_body(status="blocked"),
        )
        assert resp.status_code == 200
        proposal = resp.json()["proposal"]
        assert "The dw gate still applies" in proposal["preview"]
        assert proposal["status"] == "proposed"

        decided = client.post(
            f"/api/missioncontrol/proposals/{proposal['id']}/decision",
            json={"decision": "approved", "actor": "the-owner"},
        )
        assert decided.status_code == 200
        final = decided.json()["proposal"]
        assert final["status"] == "executed", final["error"]
        story_argv = [a for a in argv_log if "story" in a]
        assert story_argv and story_argv[-1][-4:] == ["demo", "1", "DM-1-02", "blocked"]

    def test_crown_case_refusal_banner_rides_back_verbatim(
        self, tmp_path, monkeypatch
    ):
        def runner(argv, cwd=None, **kwargs):
            if "state" in argv:
                return SimpleNamespace(
                    returncode=0, stdout=json.dumps(FEED_WITH_STORIES), stderr=""
                )
            return SimpleNamespace(
                returncode=1, stdout="",
                stderr="refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file",
            )

        client, _db, _b = _propose_client(tmp_path, monkeypatch, runner)
        proposal = client.post(
            "/api/missioncontrol/story/propose", json=_flip_body(status="done")
        ).json()["proposal"]
        final = client.post(
            f"/api/missioncontrol/proposals/{proposal['id']}/decision",
            json={"decision": "approved", "actor": "the-owner"},
        ).json()["proposal"]
        assert final["status"] == "failed"
        assert "refusing to mark story done without evidence" in final["error"]

    def test_reject_never_touches_the_cli(self, tmp_path, monkeypatch):
        argv_log = []

        def runner(argv, cwd=None, **kwargs):
            argv_log.append(list(argv))
            return SimpleNamespace(
                returncode=0, stdout=json.dumps(FEED_WITH_STORIES), stderr=""
            )

        client, _db, _b = _propose_client(tmp_path, monkeypatch, runner)
        proposal = client.post(
            "/api/missioncontrol/story/propose", json=_flip_body(status="done")
        ).json()["proposal"]
        argv_before = len(argv_log)
        final = client.post(
            f"/api/missioncontrol/proposals/{proposal['id']}/decision",
            json={"decision": "rejected", "actor": "the-owner"},
        ).json()["proposal"]
        assert final["status"] == "rejected"
        assert argv_log[argv_before:] == []

    def test_tampered_repo_fails_the_path_allow_list(self, tmp_path, monkeypatch):
        client, db, _b = _propose_client(
            tmp_path, monkeypatch, _runner_for({"state": FEED_WITH_STORIES})
        )
        rogue = db.actuators.record_proposal(
            meeting_id=None, origin="desk", window_id="desk:missioncontrol",
            plugin_id="missioncontrol_desk", plugin_version="0.1.0",
            idempotency_key="mc-story:tampered",
            target="delivery-workbench", action="dw_story_status",
            preview="tampered", reversible=True,
            payload={
                "repo": "/somewhere/else", "verb": "status", "project": "demo",
                "phase": "1", "story": "DM-1-02", "status": "done",
            },
        )
        final = client.post(
            f"/api/missioncontrol/proposals/{rogue.id}/decision",
            json={"decision": "approved", "actor": "the-owner"},
        ).json()["proposal"]
        assert final["status"] == "failed"
        assert "not in the operator's project map" in final["error"]


# ── HS-86-03: receipts + belt frames ─────────────────────────────────

RECEIPTS_DOC = [
    {
        "number": 7,
        "title": "Phase 16: the flagship tree",
        "url": "https://example.test/pr/7",
        "headRefName": "flagship-tree",
        "statusCheckRollup": [
            {"name": "verify-history", "conclusion": "SUCCESS"},
        ],
    }
]


def _gh_runner(doc, returncode=0):
    def runner(argv, cwd=None):
        if argv and argv[0] == "gh":
            if returncode != 0:
                return SimpleNamespace(returncode=returncode, stdout="", stderr="gh: not logged in")
            return SimpleNamespace(returncode=0, stdout=json.dumps(doc), stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="unknown verb")

    return runner


class TestReceipts:
    def test_receipts_relayed_live(self, tmp_path):
        client = _client(_make_map(tmp_path), _gh_runner(RECEIPTS_DOC))
        body = client.get("/api/missioncontrol/receipts").json()
        assert body["repos"][0]["status"] == "live"
        assert body["repos"][0]["prs"] == RECEIPTS_DOC

    def test_gh_failure_is_typed_unavailable_in_a_200(self, tmp_path):
        client = _client(_make_map(tmp_path), _gh_runner(RECEIPTS_DOC, returncode=4))
        resp = client.get("/api/missioncontrol/receipts")
        assert resp.status_code == 200
        entry = resp.json()["repos"][0]
        assert entry["status"] == "unavailable"
        assert "gh exited 4" in entry["detail"]

    def test_non_json_gh_is_unavailable(self, tmp_path):
        def runner(argv, cwd=None):
            return SimpleNamespace(returncode=0, stdout="not json", stderr="")

        client = _client(_make_map(tmp_path), runner)
        entry = client.get("/api/missioncontrol/receipts").json()["repos"][0]
        assert entry["status"] == "unavailable"

    def test_receipts_route_is_get_only(self, tmp_path):
        """The belt addition registers no write path (RFC B1)."""
        from holdspeak.web.routes import missioncontrol as mc_module

        app = FastAPI()
        app.include_router(
            build_missioncontrol_router(
                WebContext(get_state=lambda: {}),
                runner=_gh_runner(RECEIPTS_DOC),
                map_path=_make_map(tmp_path),
            )
        )
        for route in app.routes:
            path = getattr(route, "path", "")
            if "receipts" in path:
                assert set(route.methods) == {"GET"}
        assert not hasattr(mc_module, "_belt_write")


class TestBeltFrames:
    def _framed_client(self, tmp_path, tree_sequence):
        """A client whose fake feed advances through tree_sequence."""
        from holdspeak.web.routes import missioncontrol as mc_module

        mc_module._BELT_TREES.clear()
        trees = list(tree_sequence)
        frames: list = []

        def runner(argv, cwd=None):
            if "state" in argv:
                doc = dict(FEED_DOC)
                doc["generated_at_tree"] = trees[0] if len(trees) == 1 else trees.pop(0)
                return SimpleNamespace(returncode=0, stdout=json.dumps(doc), stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="unknown verb")

        app = FastAPI()
        app.include_router(
            build_missioncontrol_router(
                WebContext(
                    get_state=lambda: {},
                    broadcast=lambda kind, payload: frames.append((kind, payload)),
                ),
                runner=runner,
                map_path=_make_map(tmp_path),
            )
        )
        return TestClient(app), frames

    def test_unchanged_tree_emits_no_frame(self, tmp_path):
        client, frames = self._framed_client(tmp_path, ["t1"])
        client.get("/api/missioncontrol/state")
        client.get("/api/missioncontrol/state")
        assert frames == []

    def test_changed_tree_emits_one_belt_frame(self, tmp_path):
        client, frames = self._framed_client(tmp_path, ["t1", "t2"])
        client.get("/api/missioncontrol/state")
        assert frames == []  # first observation is a baseline
        client.get("/api/missioncontrol/state")
        assert len(frames) == 1
        kind, payload = frames[0]
        assert kind == "intel_status"
        assert payload["scope"] == "belt"
        assert payload["state"] == "ready"
        assert payload["capability"] == {"kind": "belt", "id": "demo", "name": "demo"}


# ── HS-86-04: evidence in place (CLI-resolved, path-contained) ───────

def _context_doc(evidence_rel):
    return {
        "kind": "delivery-workbench-roadmap-context",
        "projects": [{
            "slug": "demo",
            "phases": [{
                "number": 1,
                "stories": [{
                    "story_id": "DM-1-01",
                    "evidence_path": evidence_rel,
                }],
            }],
        }],
    }


def _evidence_client(tmp_path, evidence_rel, write=True):
    map_path = _make_map(tmp_path)
    repo = tmp_path / "rails-repo"
    if write:
        target = repo / "pm" / "roadmap" / "demo" / "phase-1-a"
        target.mkdir(parents=True, exist_ok=True)
        (target / "evidence-story-01.md").write_text("# Evidence\n\n- real proof\n")
    runner = _runner_for({"context": _context_doc(evidence_rel)})
    return _client(map_path, runner)


class TestEvidenceInPlace:
    REL = "pm/roadmap/demo/phase-1-a/evidence-story-01.md"

    def _get(self, client, repo="demo"):
        return client.get(
            f"/api/missioncontrol/evidence?repo={repo}&project=demo&story=DM-1-01"
        ).json()

    def test_happy_path_reads_the_contained_file(self, tmp_path):
        body = self._get(_evidence_client(tmp_path, self.REL))
        assert body["status"] == "live"
        assert body["path"] == self.REL
        assert "real proof" in body["text"]

    def test_traversal_is_refused(self, tmp_path):
        body = self._get(_evidence_client(tmp_path, "pm/roadmap/../../secrets.md"))
        assert body["status"] == "refused"

    def test_absolute_path_is_refused(self, tmp_path):
        body = self._get(_evidence_client(tmp_path, "/etc/hosts"))
        assert body["status"] == "refused"

    def test_non_markdown_is_refused(self, tmp_path):
        body = self._get(_evidence_client(tmp_path, "pm/roadmap/demo/notes.txt"))
        assert body["status"] == "refused"

    def test_unknown_repo_is_refused(self, tmp_path):
        body = self._get(_evidence_client(tmp_path, self.REL), repo="nope")
        assert body["status"] == "refused"

    def test_missing_file_is_absent(self, tmp_path):
        body = self._get(_evidence_client(tmp_path, self.REL, write=False))
        assert body["status"] == "absent"

    def test_route_is_get_only(self, tmp_path):
        app = FastAPI()
        app.include_router(
            build_missioncontrol_router(
                WebContext(get_state=lambda: {}),
                runner=_runner_for({}),
                map_path=_make_map(tmp_path),
            )
        )
        for route in app.routes:
            if "evidence" in getattr(route, "path", ""):
                assert set(route.methods) == {"GET"}


class TestRailsSize:
    """The grounding gauge's honest number (HS-88-02): sizes only, a
    receipt (the dw-named file), never the content."""

    def _repo_with_story(self, tmp_path: Path):
        repo = tmp_path / "rails-repo"
        (repo / ".githooks").mkdir(parents=True)
        dw = repo / ".githooks" / "dw"
        dw.write_text("#!/usr/bin/env python3\n")
        dw.chmod(0o755)
        story_rel = "pm/roadmap/demo/phase-1/story-01.md"
        (repo / "pm" / "roadmap" / "demo" / "phase-1").mkdir(parents=True)
        (repo / story_rel).write_text("z" * 640, encoding="utf-8")
        map_path = tmp_path / "delivery_workbench.json"
        map_path.write_text(
            json.dumps({"projects": {"demo": str(repo)}, "default": str(repo)})
        )
        context_doc = {
            "kind": "delivery-workbench-roadmap-context",
            "projects": [
                {
                    "slug": "demo",
                    "readme": "pm/roadmap/demo/README.md",
                    "phases": [
                        {
                            "number": 1,
                            "slug": "demo-phase",
                            "status_file": "pm/roadmap/demo/phase-1/current-phase-status.md",
                            "stories": [
                                {
                                    "story_id": "DEMO-1-01",
                                    "title": "First",
                                    "trace": {"story": story_rel, "evidence": "x"},
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        return map_path, _runner_for({"context": context_doc})

    def test_rails_size_returns_hydrated_char_counts(self, tmp_path):
        map_path, runner = self._repo_with_story(tmp_path)
        client = _client(map_path, runner)
        res = client.post(
            "/api/missioncontrol/rails/size",
            json={"rails": [{"repo": "demo", "project": "demo", "kind": "story", "id": "DEMO-1-01"}]},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["sizes"] == [
            {"kind": "story", "id": "DEMO-1-01", "title": "DEMO-1-01 First", "chars": 640}
        ]
        assert body["unknown"] == []

    def test_rails_size_reports_unknown_refs(self, tmp_path):
        map_path, runner = self._repo_with_story(tmp_path)
        client = _client(map_path, runner)
        res = client.post(
            "/api/missioncontrol/rails/size",
            json={"rails": [{"repo": "demo", "project": "demo", "kind": "story", "id": "GHOST"}]},
        )
        assert res.json()["unknown"] == ["story:GHOST"]

    def test_rails_size_never_returns_the_content(self, tmp_path):
        map_path, runner = self._repo_with_story(tmp_path)
        client = _client(map_path, runner)
        body = client.post(
            "/api/missioncontrol/rails/size",
            json={"rails": [{"repo": "demo", "project": "demo", "kind": "story", "id": "DEMO-1-01"}]},
        ).json()
        assert "text" not in body["sizes"][0]
        assert "zzz" not in json.dumps(body)  # the file body never crosses
