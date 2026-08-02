"""HS-111-06 — the duplicate-attempts data fix (audit §1f/§4.5).

The owner's PR-387 defect, pinned in units:

1. a rider claim ADOPTS its session-unbound ``kind='launch'`` attempt
   even when the claim's cwd resolves to a DIFFERENT worktree — one
   attempt, one row, never a ``rider_claim`` sibling;
2. a worktree-resolution change on a bound session heartbeats the
   existing attempt (the idempotence key is (session, story, source),
   never the worktree);
3. the attempts READ path runs the launch sweep (bind + expire) —
   state advancement no longer waits for someone to open the Delivery
   board and fire ``/api/delivery/factory/discover``.

No deletion, no invented states: only WHEN the existing transitions
run and WHICH attempt a claim binds to.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.delivery.attempts import WorkAttemptService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_attempts import build_delivery_attempts_router


@pytest.fixture
def repo(tmp_path):
    return Database(tmp_path / "attempts.db").work_attempts


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
        "tmux_pane": "%9",
        "story_claim": {
            "project": project,
            "story_id": story_id,
            "claimed_by": f"rider:{agent}",
            "claimed_at": "2026-07-15T10:00:00Z",
        },
    }


class TestClaimAdoptsLaunchAttempt:
    def test_worktree_mismatch_binds_the_launch_attempt_not_a_sibling(
        self, repo
    ):
        # The launch minted its attempt in the launch worktree…
        launch = repo.create(
            kind="launch",
            exact=True,
            source_id="src_a",
            worktree_id="wt_launch",
            project="demo",
            story_id="DM-1-01",
        )
        assert launch.session_id is None and launch.state == "starting"
        # …but the rider's cwd resolves to a DIFFERENT worktree.
        service = WorkAttemptService(
            repo,
            resolver=_resolver(
                {"/work/tree": {"source_id": "src_a", "worktree_id": "wt_other", "node_id": None}}
            ),
        )
        summary = service.sync_rider_claims([_claim_row()])
        assert summary == {"created": 0, "updated": 1, "ended": 0, "skipped": 0}
        # ONE attempt total: the launch attempt, session-bound, advanced.
        rows = repo.list()
        assert len(rows) == 1
        (bound,) = rows
        assert bound.attempt_id == launch.attempt_id
        assert bound.kind == "launch"
        assert bound.session_id == "claude:s1"
        assert bound.state == "working"
        assert any(
            e["reason"] == "rider_registered"
            for e in repo.events(bound.attempt_id)
        )

    def test_one_live_exact_attempt_per_session_survives_adoption(self, repo):
        # The session was exactly bound elsewhere; a new claim first
        # supersedes that binding (existing sweep semantics), THEN
        # adopts the launch attempt — never two live exact attempts.
        old = repo.create(
            kind="rider_claim",
            exact=True,
            session_id="claude:s1",
            source_id="src_b",
            worktree_id="wt_b",
            project="other",
            story_id="OT-1-01",
        )
        launch = repo.create(
            kind="launch",
            exact=True,
            source_id="src_a",
            worktree_id="wt_a",
            project="demo",
            story_id="DM-1-01",
        )
        service = WorkAttemptService(
            repo,
            resolver=_resolver(
                {"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}
            ),
        )
        service.sync_rider_claims([_claim_row()])
        live = repo.find_active(session_id="claude:s1")
        assert [a.attempt_id for a in live] == [launch.attempt_id]
        assert repo.get(old.attempt_id).state == "ended"
        assert any(
            e["reason"] == "superseded_by_new_claim"
            for e in repo.events(old.attempt_id)
        )


class TestWorktreeIsNotTheIdempotenceKey:
    def test_a_worktree_change_heartbeats_the_same_attempt(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver(
                {
                    "/work/a": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None},
                    "/work/b": {"source_id": "src_a", "worktree_id": "wt_b", "node_id": None},
                }
            ),
        )
        service.sync_rider_claims([_claim_row(repo_root="/work/a")])
        (before,) = repo.find_active(session_id="claude:s1")
        # Same session, same story, same source — different worktree
        # resolution. Yesterday this ended+minted a sibling; now it is
        # a plain heartbeat on the same attempt_id.
        summary = service.sync_rider_claims(
            [_claim_row(repo_root="/work/b", lifecycle="waiting")]
        )
        assert summary == {"created": 0, "updated": 1, "ended": 0, "skipped": 0}
        (after,) = repo.find_active(session_id="claude:s1")
        assert after.attempt_id == before.attempt_id
        assert after.state == "waiting"
        assert len(repo.list()) == 1

    def test_a_new_story_still_mints_a_fresh_attempt(self, repo):
        service = WorkAttemptService(
            repo,
            resolver=_resolver(
                {"/work/tree": {"source_id": "src_a", "worktree_id": "wt_a", "node_id": None}}
            ),
        )
        service.sync_rider_claims([_claim_row(story_id="DM-1-01")])
        (first,) = repo.find_active(session_id="claude:s1")
        service.sync_rider_claims([_claim_row(story_id="DM-1-02")])
        (second,) = repo.find_active(session_id="claude:s1")
        assert second.attempt_id != first.attempt_id
        assert repo.get(first.attempt_id).state == "ended"


class TestSweepOnAttemptsRead:
    def _client(self, repo, sweep, *, sync_on_read=True):
        app = FastAPI()
        app.include_router(
            build_delivery_attempts_router(
                WebContext(get_state=lambda: {}),
                service=WorkAttemptService(repo),
                launch_sweep=sweep,
                sync_on_read=sync_on_read,
            )
        )
        return TestClient(app)

    def test_get_attempts_runs_the_launch_sweep(self, repo):
        calls: list[str] = []
        client = self._client(repo, lambda: calls.append("sweep"))
        assert client.get("/api/delivery/attempts").status_code == 200
        assert calls == ["sweep"]

    def test_a_failing_sweep_never_loses_the_read(self, repo):
        def broken() -> None:
            raise RuntimeError("registry offline")

        repo.create(
            kind="manual",
            exact=True,
            source_id="src_a",
            worktree_id="wt_a",
            project="demo",
            story_id="DM-1-01",
        )
        client = self._client(repo, broken)
        body = client.get("/api/delivery/attempts").json()
        assert len(body["attempts"]) == 1

    def test_sync_off_skips_the_sweep(self, repo):
        calls: list[str] = []
        client = self._client(
            repo, lambda: calls.append("sweep"), sync_on_read=False
        )
        assert client.get("/api/delivery/attempts").status_code == 200
        assert calls == []
