"""Work attempts: repository, service, rider-claim emission, routes (HS-94-04).

PLATFORM-CONTRACT §4.2 pinned in units:

- the honest state machine with replayable, timestamped history;
- opaque, never-reused attempt identity;
- one live exact attempt per session (DB-enforced);
- provenance that never masquerades (manual is manual, heuristic is
  never exact);
- resilience transitions (worktree removed, node offline, staleness);
- durable rows across a reopened database (hub restart);
- the additive rider-claim emission from the agent hook path;
- the locally-assembled router (no web_server involvement).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.agent_context.hooks import detect_story_claim
from holdspeak.agent_context.sessions import (
    ingest_agent_hook_event,
    list_agent_story_claims,
)
from holdspeak.db import Database
from holdspeak.db.delivery_attempts import (
    AttemptConflict,
    AttemptError,
    AttemptTransitionError,
)
from holdspeak.delivery.attempts import (
    WorkAttemptService,
    resolver_from_registry,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_attempts import build_delivery_attempts_router


@pytest.fixture
def repo(tmp_path):
    return Database(tmp_path / "attempts.db").work_attempts


def _identity(n: int = 1) -> dict[str, str]:
    return {
        "source_id": f"src_{n:04d}",
        "worktree_id": f"wt_{n:04d}",
        "project": "demo",
        "story_id": f"DM-1-{n:02d}",
    }


def _resolver(mapping: dict[str, dict]):
    return lambda path: mapping.get(str(path or ""))


def _claim_row(
    *,
    session_key: str = "claude:s1",
    repo_root: str = "/work/tree",
    lifecycle: str = "working",
    project: str = "demo",
    story_id: str = "DM-1-01",
) -> dict:
    agent, _, session_id = session_key.partition(":")
    return {
        "session_key": session_key,
        "agent": agent,
        "session_id": session_id,
        "cwd": repo_root,
        "repo_root": repo_root,
        "updated_at": "2026-07-15T10:00:00Z",
        "lifecycle": lifecycle,
        "tmux_pane": None,
        "story_claim": {
            "project": project,
            "story_id": story_id,
            "claimed_by": f"rider:{agent}",
            "claimed_at": "2026-07-15T10:00:00Z",
        },
    }


# ── the repository + state machine ───────────────────────────────────


class TestAttemptRepository:
    def test_create_mints_an_opaque_id_and_a_created_event(self, repo):
        attempt = repo.create(kind="manual", exact=True, **_identity())
        assert attempt.attempt_id.startswith("att_")
        assert attempt.state == "starting"
        assert attempt.exact is True
        history = repo.events(attempt.attempt_id)
        assert [(e["from"], e["to"], e["reason"]) for e in history] == [
            (None, "starting", "created:manual")
        ]
        assert history[0]["occurred_at"]

    def test_the_honest_lifecycle_records_every_transition(self, repo):
        attempt = repo.create(kind="manual", exact=True, **_identity())
        for state in ("working", "waiting", "working", "idle", "ended"):
            attempt = repo.transition(attempt.attempt_id, state, reason="test")
        assert attempt.state == "ended"
        assert attempt.ended_at is not None
        history = repo.events(attempt.attempt_id)
        assert [e["to"] for e in history] == [
            "starting", "working", "waiting", "working", "idle", "ended",
        ]
        assert all(e["occurred_at"] for e in history)

    def test_terminal_states_are_sticky(self, repo):
        ended = repo.create(kind="manual", exact=True, state="ended", **_identity(1))
        abandoned = repo.create(kind="manual", exact=False, **_identity(2))
        repo.transition(abandoned.attempt_id, "abandoned", reason="worktree_removed")
        for tombstone in (ended.attempt_id, abandoned.attempt_id):
            with pytest.raises(AttemptTransitionError):
                repo.transition(tombstone, "working")

    def test_same_state_is_a_quiet_noop(self, repo):
        attempt = repo.create(kind="manual", exact=True, **_identity())
        repo.transition(attempt.attempt_id, "working")
        before = repo.events(attempt.attempt_id)
        repo.transition(attempt.attempt_id, "working")
        assert repo.events(attempt.attempt_id) == before

    def test_unknown_recovers_when_the_node_returns(self, repo):
        attempt = repo.create(kind="manual", exact=True, **_identity())
        repo.transition(attempt.attempt_id, "working")
        repo.transition(attempt.attempt_id, "unknown", reason="node_offline")
        recovered = repo.transition(attempt.attempt_id, "working", reason="node_back")
        assert recovered.state == "working"

    def test_a_heuristic_association_is_never_exact(self, repo):
        with pytest.raises(AttemptError):
            repo.create(kind="heuristic", exact=True, **_identity())

    def test_unknown_kinds_and_states_refuse(self, repo):
        with pytest.raises(AttemptError):
            repo.create(kind="vibes", exact=False, **_identity())
        attempt = repo.create(kind="manual", exact=False, **_identity())
        with pytest.raises(AttemptError):
            repo.transition(attempt.attempt_id, "finished-ish")

    def test_one_session_holds_at_most_one_live_exact_attempt(self, repo):
        first = repo.create(
            kind="rider_claim", exact=True, session_id="claude:s1", **_identity(1)
        )
        with pytest.raises(AttemptConflict):
            repo.create(
                kind="manual", exact=True, session_id="claude:s1", **_identity(2)
            )
        # A non-exact heuristic row for the same session is allowed.
        repo.create(
            kind="heuristic", exact=False, session_id="claude:s1", **_identity(2)
        )
        # Ending the exact attempt frees the pin; the successor is a NEW id.
        repo.transition(first.attempt_id, "ended", reason="session_ended")
        second = repo.create(
            kind="rider_claim", exact=True, session_id="claude:s1", **_identity(2)
        )
        assert second.attempt_id != first.attempt_id

    def test_concurrent_attempts_on_one_story_are_allowed(self, repo):
        identity = _identity()
        one = repo.create(
            kind="rider_claim", exact=True, session_id="claude:s1", **identity
        )
        two = repo.create(
            kind="rider_claim", exact=True, session_id="codex:s2", **identity
        )
        assert one.attempt_id != two.attempt_id
        rows = repo.find_active(
            source_id=identity["source_id"],
            project=identity["project"],
            story_id=identity["story_id"],
        )
        assert len(rows) == 2

    def test_rows_survive_a_reopened_database(self, tmp_path):
        path = tmp_path / "restart.db"
        attempt = Database(path).work_attempts.create(
            kind="rider_claim", exact=True, session_id="claude:s1", **_identity()
        )
        reopened = Database(path).work_attempts
        found = reopened.get(attempt.attempt_id)
        assert found is not None
        assert found.session_id == "claude:s1"
        assert found.exact is True
        assert reopened.events(attempt.attempt_id)

    def test_list_filters_by_story_ref(self, repo):
        repo.create(kind="manual", exact=False, **_identity(1))
        repo.create(kind="manual", exact=False, **_identity(2))
        rows = repo.list(source_id="src_0001", project="demo", story_id="DM-1-01")
        assert [r.story_id for r in rows] == ["DM-1-01"]


# ── the service: creation paths + resilience ─────────────────────────


class TestWorkAttemptService:
    def test_manual_attach_is_manual_provenance(self, repo):
        service = WorkAttemptService(repo)
        wire = service.manual_attach(
            source_id="src_a", worktree_id="wt_a", project="demo",
            story_id="DM-1-01", session_id="claude:s1", actor="desk-owner",
        )
        assert wire["association"]["kind"] == "manual"
        assert wire["association"]["claimed_by"] == "desk-owner"
        assert wire["exact"] is True
        assert wire["story_ref"] == {
            "source_id": "src_a", "project": "demo", "story_id": "DM-1-01",
        }

    def test_rider_claims_become_exact_attempts(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver({"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}),
        )
        summary = service.sync_rider_claims([_claim_row()])
        assert summary["created"] == 1
        (attempt,) = repo.find_active(session_id="claude:s1")
        assert attempt.kind == "rider_claim"
        assert attempt.exact is True
        assert attempt.state == "working"
        assert attempt.claimed_by == "rider:claude"
        assert (attempt.project, attempt.story_id) == ("demo", "DM-1-01")

    def test_rider_heartbeats_update_state_not_identity(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver({"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}),
        )
        service.sync_rider_claims([_claim_row(lifecycle="working")])
        (before,) = repo.find_active(session_id="claude:s1")
        summary = service.sync_rider_claims([_claim_row(lifecycle="waiting")])
        assert summary == {"created": 0, "updated": 1, "ended": 0, "skipped": 0}
        (after,) = repo.find_active(session_id="claude:s1")
        assert after.attempt_id == before.attempt_id
        assert after.state == "waiting"
        assert any(e["reason"] == "rider_heartbeat" for e in repo.events(after.attempt_id))

    def test_sequential_stories_never_reuse_an_attempt_id(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver({"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}),
        )
        service.sync_rider_claims([_claim_row(story_id="DM-1-01")])
        (first,) = repo.find_active(session_id="claude:s1")
        service.sync_rider_claims([_claim_row(story_id="DM-1-02")])
        finished = repo.get(first.attempt_id)
        assert finished.state == "ended"
        assert any(
            e["reason"] == "superseded_by_new_claim"
            for e in repo.events(first.attempt_id)
        )
        (second,) = repo.find_active(session_id="claude:s1")
        assert second.attempt_id != first.attempt_id
        assert second.story_id == "DM-1-02"

    def test_session_end_tombstones_the_attempt(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver({"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}),
        )
        service.sync_rider_claims([_claim_row()])
        summary = service.sync_rider_claims([_claim_row(lifecycle="ended")])
        assert summary["ended"] == 1
        assert repo.find_active(session_id="claude:s1") == []
        rows = repo.list(session_id="claude:s1")
        assert rows and rows[0].state == "ended"

    def test_an_unresolvable_claim_is_skipped_not_guessed(self, repo):
        service = WorkAttemptService(repo, resolver=_resolver({}))
        summary = service.sync_rider_claims([_claim_row()])
        assert summary == {"created": 0, "updated": 0, "ended": 0, "skipped": 1}
        assert repo.list() == []

    def test_heuristic_ingest_is_labeled_ambiguous_and_never_exact(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver({"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}),
        )
        doc = {
            "sessions_schema": 1,
            "sessions": [{
                "key": "claude:s9",
                "repo_root": "/work/tree",
                "correlation": "ambiguous",
                "stale": False,
                "awaiting_response": False,
                "stories": [
                    {"project": "demo", "story_id": "DM-1-01"},
                    {"project": "demo", "story_id": "DM-1-02"},
                ],
            }],
        }
        summary = service.ingest_heuristic(doc)
        assert summary["created"] == 2
        rows = repo.find_active(session_id="claude:s9")
        assert {r.story_id for r in rows} == {"DM-1-01", "DM-1-02"}
        assert all(r.kind == "heuristic" and r.exact is False for r in rows)
        # Idempotent: re-ingest creates nothing new.
        assert service.ingest_heuristic(doc)["created"] == 0

    def test_the_old_exact_singleton_guess_stays_heuristic(self, repo):
        """`dw sessions` called a single in-progress story `on_story`
        (its exact). Ported rows stay labeled heuristic + non-exact."""
        service = WorkAttemptService(
            repo,
            resolver=_resolver({"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}),
        )
        doc = {"sessions": [{
            "key": "codex:s1", "repo_root": "/work/tree",
            "correlation": "on_story", "stale": False, "awaiting_response": True,
            "stories": [{"project": "demo", "story_id": "DM-1-01"}],
        }]}
        service.ingest_heuristic(doc)
        (row,) = repo.find_active(session_id="codex:s1")
        assert row.kind == "heuristic"
        assert row.exact is False
        assert row.state == "waiting"

    def test_heuristic_never_shadows_an_exact_binding(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver({"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}),
        )
        service.sync_rider_claims([_claim_row(session_key="claude:s1")])
        doc = {"sessions": [{
            "key": "claude:s1", "repo_root": "/work/tree",
            "correlation": "ambiguous", "stale": False,
            "stories": [
                {"project": "demo", "story_id": "DM-1-01"},
                {"project": "demo", "story_id": "DM-1-02"},
            ],
        }]}
        summary = service.ingest_heuristic(doc)
        assert summary == {"created": 0, "skipped": 1}
        rows = repo.find_active(session_id="claude:s1")
        assert len(rows) == 1 and rows[0].exact is True  # zero downgrades

    def test_heuristic_ingest_is_capped(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver({"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}),
        )
        doc = {"sessions": [{
            "key": f"claude:s{i}", "repo_root": "/work/tree",
            "correlation": "ambiguous", "stale": False,
            "stories": [
                {"project": "demo", "story_id": f"DM-1-{j:02d}"} for j in range(1, 5)
            ],
        } for i in range(10)]}
        summary = service.ingest_heuristic(doc, cap=3)
        assert summary["created"] == 3
        assert len(repo.list()) == 3

    def test_worktree_removal_abandons_with_history(self, repo):
        service = WorkAttemptService(repo)
        wire = service.manual_attach(
            source_id="src_a", worktree_id="wt_gone", project="demo",
            story_id="DM-1-01",
        )
        assert service.mark_worktree_removed("wt_gone") == 1
        row = repo.get(wire["attempt_id"])
        assert row.state == "abandoned"
        assert row.ended_at is not None
        assert [e["reason"] for e in repo.events(row.attempt_id)] == [
            "created:manual", "worktree_removed",
        ]

    def test_node_offline_moves_attempts_to_unknown(self, repo):
        service = WorkAttemptService(repo)
        wire = service.manual_attach(
            source_id="src_a", worktree_id="wt_a", project="demo",
            story_id="DM-1-01", node_id="node_x",
        )
        assert service.mark_node_offline("node_x") == 1
        assert repo.get(wire["attempt_id"]).state == "unknown"

    def test_stale_attempts_abandon_on_timeout(self, repo):
        service = WorkAttemptService(repo)
        stamp = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)
        wire = service.manual_attach(
            source_id="src_a", worktree_id="wt_a", project="demo",
            story_id="DM-1-01", now=stamp,
        )
        later = stamp + timedelta(hours=25)
        assert service.abandon_stale(now=later) == 1
        row = repo.get(wire["attempt_id"])
        assert row.state == "abandoned"
        assert any(e["reason"] == "stale_timeout" for e in repo.events(row.attempt_id))


# ── rider-claim emission from the hook path ──────────────────────────


class TestRiderClaimEmission:
    def test_detect_story_claim_sources_and_precedence(self):
        payload = {"story_ref": {"project": "demo", "story_id": "DM-1-01"}}
        env = {"HOLDSPEAK_STORY_REF": "other/DM-9-99"}
        assert detect_story_claim(payload, env=env) == {
            "project": "demo", "story_id": "DM-1-01",
        }
        assert detect_story_claim({}, env={"HOLDSPEAK_STORY_REF": "demo/DM-1-02"}) == {
            "project": "demo", "story_id": "DM-1-02",
        }
        assert detect_story_claim({}, env={"HOLDSPEAK_STORY_REF": "demo:DM-1-03"}) == {
            "project": "demo", "story_id": "DM-1-03",
        }
        assert detect_story_claim(
            {}, env={"HOLDSPEAK_STORY_PROJECT": "demo", "HOLDSPEAK_STORY_ID": "DM-1-04"}
        ) == {"project": "demo", "story_id": "DM-1-04"}
        # Half an identity is no identity.
        assert detect_story_claim({}, env={"HOLDSPEAK_STORY_PROJECT": "demo"}) == {}
        assert detect_story_claim({}, env={"HOLDSPEAK_STORY_REF": "demo"}) == {}
        assert detect_story_claim({}, env={}) == {}

    def test_ingest_emits_a_sticky_story_claim(self, tmp_path: Path):
        workdir = tmp_path / "repo"
        workdir.mkdir()
        (workdir / ".git").mkdir()
        state = tmp_path / "state.json"
        ingest_agent_hook_event(
            agent="claude",
            payload={"session_id": "s1", "hook_event_name": "SessionStart", "cwd": str(workdir)},
            state_path=state,
            env={"HOLDSPEAK_STORY_REF": "demo/DM-1-01"},
        )
        # The next heartbeat has NO env claim; the claim sticks.
        ingest_agent_hook_event(
            agent="claude",
            payload={"session_id": "s1", "hook_event_name": "PostToolUse", "cwd": str(workdir)},
            state_path=state,
            env={},
        )
        (row,) = list_agent_story_claims(state_path=state)
        assert row["session_key"] == "claude:s1"
        assert row["repo_root"] == str(workdir.resolve())
        assert row["lifecycle"] == "working"
        assert row["story_claim"]["project"] == "demo"
        assert row["story_claim"]["story_id"] == "DM-1-01"
        assert row["story_claim"]["claimed_by"] == "rider:claude"
        first_claimed_at = row["story_claim"]["claimed_at"]
        assert first_claimed_at

        # Re-claiming the SAME story keeps claimed_at; a NEW story moves it.
        ingest_agent_hook_event(
            agent="claude",
            payload={"session_id": "s1", "hook_event_name": "PostToolUse", "cwd": str(workdir)},
            state_path=state,
            env={"HOLDSPEAK_STORY_REF": "demo/DM-1-01"},
        )
        (row,) = list_agent_story_claims(state_path=state)
        assert row["story_claim"]["claimed_at"] == first_claimed_at
        ingest_agent_hook_event(
            agent="claude",
            payload={"session_id": "s1", "hook_event_name": "PostToolUse", "cwd": str(workdir)},
            state_path=state,
            env={"HOLDSPEAK_STORY_REF": "demo/DM-1-02"},
            now=datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc),
        )
        (row,) = list_agent_story_claims(state_path=state)
        assert row["story_claim"]["story_id"] == "DM-1-02"
        assert row["story_claim"]["claimed_at"] != first_claimed_at

    def test_sessions_without_claims_stay_out_of_the_claim_list(self, tmp_path: Path):
        workdir = tmp_path / "repo"
        workdir.mkdir()
        (workdir / ".git").mkdir()
        state = tmp_path / "state.json"
        ingest_agent_hook_event(
            agent="codex",
            payload={"session_id": "s2", "hook_event_name": "SessionStart", "cwd": str(workdir)},
            state_path=state,
            env={},
        )
        assert list_agent_story_claims(state_path=state) == []
        # The registry file itself stays a valid version-1 document.
        raw = json.loads(state.read_text(encoding="utf-8"))
        assert raw["version"] == 1
        assert "story_claim" not in raw["sessions"]["codex:s2"]


# ── the routes (locally assembled app) ───────────────────────────────


def _client(repo, *, resolver=None, claims_state_path=None, sync_on_read=False):
    service = WorkAttemptService(repo, resolver=resolver)
    app = FastAPI()
    app.include_router(
        build_delivery_attempts_router(
            WebContext(get_state=lambda: {}),
            service=service,
            claims_state_path=claims_state_path,
            sync_on_read=sync_on_read,
        )
    )
    return TestClient(app)


class TestDeliveryAttemptRoutes:
    def test_post_creates_a_manual_attempt_and_get_projects_it(self, repo, tmp_path):
        client = _client(repo)
        created = client.post("/api/delivery/attempts", json={
            "source_id": "src_a", "worktree_id": "wt_a",
            "project": "demo", "story_id": "DM-1-01",
            "session_id": "claude:s1",
        })
        assert created.status_code == 200
        body = created.json()
        assert body["success"] is True
        assert body["attempt"]["association"]["kind"] == "manual"

        listed = client.get(
            "/api/delivery/attempts",
            params={"project": "demo", "story_id": "DM-1-01"},
        ).json()
        assert listed["attempts_schema"] == 1
        (row,) = listed["attempts"]
        assert row["attempt_id"] == body["attempt"]["attempt_id"]
        assert row["state"] == "starting"
        assert row["history"][0]["reason"] == "created:manual"
        # §13: no filesystem truth on the wire.
        assert str(tmp_path) not in json.dumps(listed)

    def test_post_refusals_are_typed_and_bounded(self, repo):
        client = _client(repo)
        blank = client.post("/api/delivery/attempts", json={
            "source_id": "  ", "worktree_id": "wt_a",
            "project": "demo", "story_id": "DM-1-01",
        })
        assert blank.status_code == 400
        assert blank.json()["error"] == "source_id is required"

        first = client.post("/api/delivery/attempts", json={
            "source_id": "src_a", "worktree_id": "wt_a",
            "project": "demo", "story_id": "DM-1-01", "session_id": "claude:s1",
        })
        assert first.status_code == 200
        conflict = client.post("/api/delivery/attempts", json={
            "source_id": "src_a", "worktree_id": "wt_a",
            "project": "demo", "story_id": "DM-1-02", "session_id": "claude:s1",
        })
        assert conflict.status_code == 409
        assert "already" in conflict.json()["error"]

    def test_get_sweeps_emitted_rider_claims(self, repo, tmp_path):
        workdir = tmp_path / "tree"
        workdir.mkdir()
        (workdir / ".git").mkdir()
        state = tmp_path / "state.json"
        ingest_agent_hook_event(
            agent="claude",
            payload={"session_id": "s1", "hook_event_name": "SessionStart", "cwd": str(workdir)},
            state_path=state,
            env={"HOLDSPEAK_STORY_REF": "demo/DM-1-01"},
        )
        resolver = _resolver({
            str(workdir.resolve()): {
                "source_id": "src_a", "worktree_id": "wt_a", "node_id": None,
            }
        })
        client = _client(
            repo, resolver=resolver, claims_state_path=state, sync_on_read=True
        )
        listed = client.get("/api/delivery/attempts").json()
        (row,) = listed["attempts"]
        assert row["association"]["kind"] == "rider_claim"
        assert row["exact"] is True
        assert row["session_id"] == "claude:s1"
        assert row["story_ref"]["story_id"] == "DM-1-01"
        assert str(tmp_path) not in json.dumps(listed)

    def test_heuristic_rows_are_visually_distinguishable_data(self, repo):
        service_resolver = _resolver({
            "/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}
        })
        service = WorkAttemptService(repo, resolver=service_resolver)
        service.ingest_heuristic({"sessions": [{
            "key": "codex:s7", "repo_root": "/work/tree",
            "correlation": "ambiguous", "stale": False,
            "stories": [
                {"project": "demo", "story_id": "DM-1-01"},
                {"project": "demo", "story_id": "DM-1-02"},
            ],
        }]})
        client = _client(repo)
        listed = client.get("/api/delivery/attempts").json()
        assert len(listed["attempts"]) == 2
        for row in listed["attempts"]:
            assert row["association"]["kind"] == "heuristic"
            assert row["exact"] is False


def test_resolver_from_registry_maps_resolved_paths(tmp_path):
    worktree = tmp_path / "clone"
    worktree.mkdir()
    registry = SimpleNamespace(sources=lambda: [
        SimpleNamespace(
            source_id="src_a",
            node_id=None,
            worktrees=[SimpleNamespace(worktree_id="wt_a", path=str(worktree))],
        )
    ])
    resolve = resolver_from_registry(registry)
    assert resolve(str(worktree)) == {
        "source_id": "src_a", "worktree_id": "wt_a", "node_id": None,
    }
    assert resolve(str(tmp_path / "elsewhere")) is None
    assert resolve("") is None
