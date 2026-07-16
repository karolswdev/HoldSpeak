"""The exact-attempt fixture (HS-94-04 acceptance).

Two real scratch git worktrees of ONE rails clone, two synthetic agent
sessions whose hooks emit explicit rider claims, and the REAL vendored
``dw sessions`` correlation as the baseline:

- **before** (the old repo-wide guess): every session correlates
  ``ambiguous`` against the repo's two in-progress Stories — the live
  regression this story closes (29 ambiguous / zero exact on the real
  tree);
- **after** (rider claims through the hub): each session resolves to
  exactly ONE attempt with ``association.kind='rider_claim'`` and an
  exact Story + worktree binding.

Then the honesty invariants: heuristic ingest of the same dw document
performs zero exact→ambiguous downgrades, no session is pinned to two
attempts as exact, attempts survive a reopened database (hub restart),
worktree removal abandons with history, and a sequential-story claim
never reuses an attempt id.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from holdspeak.agent_context.sessions import ingest_agent_hook_event
from holdspeak.db import Database
from holdspeak.delivery import DeliveryRegistry
from holdspeak.delivery.attempts import WorkAttemptService, resolver_from_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
DW = REPO_ROOT / ".githooks" / "dw"

README = """# Demo

- **Story ID prefix:** DM

**Current phase:** [Phase 1](phase-1-alpha/current-phase-status.md)
"""

PHASE_TABLE = """# Phase 1 — Alpha

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| DM-1-01 | First thing | in-progress | [story-01-first.md](story-01-first.md) | [evidence-story-01.md](evidence-story-01.md) |
| DM-1-02 | Second thing | in-progress | [story-02-second.md](story-02-second.md) | [evidence-story-02.md](evidence-story-02.md) |
"""


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    )


def _story(story_id: str, title: str) -> str:
    return f"# {story_id} - {title}\n\n- **Status:** in-progress\n\nBody.\n"


def _evidence(story_id: str) -> str:
    return f"# Evidence — {story_id}\n\n- **Story:** {story_id}\n\nProof.\n"


def _make_rails_clone_with_two_worktrees(tmp_path: Path) -> tuple[Path, Path]:
    """One rails repo + one linked git worktree, both carrying the
    roadmap with TWO in-progress stories and a vendored-dw stub file
    (what `dw sessions` requires to call a repo 'on rails')."""
    repo = tmp_path / "rails"
    phase = repo / "pm" / "roadmap" / "demo" / "phase-1-alpha"
    phase.mkdir(parents=True)
    (repo / "pm" / "roadmap" / "demo" / "README.md").write_text(README, encoding="utf-8")
    (phase / "current-phase-status.md").write_text(PHASE_TABLE, encoding="utf-8")
    (phase / "story-01-first.md").write_text(_story("DM-1-01", "First thing"), encoding="utf-8")
    (phase / "story-02-second.md").write_text(_story("DM-1-02", "Second thing"), encoding="utf-8")
    (phase / "evidence-story-01.md").write_text(_evidence("DM-1-01"), encoding="utf-8")
    (phase / "evidence-story-02.md").write_text(_evidence("DM-1-02"), encoding="utf-8")
    hooks = repo / ".githooks"
    hooks.mkdir()
    (hooks / "dw").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.test")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed rails fixture")
    second = tmp_path / "rails-wt2"
    _git(repo, "worktree", "add", str(second), "-b", "second-story")
    return repo, second


def _emit_claim(state: Path, *, agent: str, session_id: str, cwd: Path, story: str) -> None:
    ingest_agent_hook_event(
        agent=agent,
        payload={
            "session_id": session_id,
            "hook_event_name": "SessionStart",
            "cwd": str(cwd),
        },
        state_path=state,
        env={"HOLDSPEAK_STORY_REF": f"demo/{story}"},
    )


def _dw_sessions(registry_file: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(DW), "--root", str(REPO_ROOT),
         "sessions", "--json", "--registry", str(registry_file)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.fixture
def rig(tmp_path):
    """The full fixture: two worktrees, a source registry over both,
    two claimed sessions, a durable attempt store, and the service."""
    wt1, wt2 = _make_rails_clone_with_two_worktrees(tmp_path)
    registry = DeliveryRegistry(
        tmp_path / "sources.json", map_path=tmp_path / "absent-map.json"
    )
    source1, tree1 = registry.register(str(wt1), label="rails")
    source2, tree2 = registry.register(str(wt2))
    assert source1.source_id == source2.source_id  # one clone, one source
    assert tree1.worktree_id != tree2.worktree_id  # two worktrees

    state = tmp_path / "agent_sessions.json"
    _emit_claim(state, agent="claude", session_id="s1", cwd=wt1, story="DM-1-01")
    _emit_claim(state, agent="codex", session_id="s2", cwd=wt2, story="DM-1-02")

    db_path = tmp_path / "attempts.db"
    repo = Database(db_path).work_attempts
    service = WorkAttemptService(repo, resolver=resolver_from_registry(registry))
    return {
        "wt1": wt1, "wt2": wt2,
        "source_id": source1.source_id,
        "wt1_id": tree1.worktree_id, "wt2_id": tree2.worktree_id,
        "state": state, "db_path": db_path, "repo": repo, "service": service,
        "tmp": tmp_path,
    }


class TestExactAttemptFixture:
    def test_exact_claims_close_the_zero_exact_baseline(self, rig, tmp_path):
        # BEFORE — the real vendored dw's repo-wide guess: both sessions
        # ambiguous across both in-progress stories, zero exact.
        baseline = _dw_sessions(rig["state"])
        assert baseline["registry"] == "ok"
        assert len(baseline["sessions"]) == 2
        assert {row["correlation"] for row in baseline["sessions"]} == {"ambiguous"}
        assert all(len(row["stories"]) == 2 for row in baseline["sessions"])
        exact_before = sum(
            1 for row in baseline["sessions"] if row["correlation"] == "on_story"
        )
        assert exact_before == 0  # the observed regression

        # AFTER — rider claims resolve to exact attempts through the hub.
        summary = rig["service"].sync_rider_claims(state_path=rig["state"])
        assert summary["created"] == 2
        attempts = rig["repo"].find_active()
        assert len(attempts) == 2
        by_session = {a.session_id: a for a in attempts}
        s1 = by_session["claude:s1"]
        s2 = by_session["codex:s2"]
        assert s1.kind == s2.kind == "rider_claim"
        assert s1.exact and s2.exact
        assert (s1.project, s1.story_id, s1.worktree_id) == (
            "demo", "DM-1-01", rig["wt1_id"],
        )
        assert (s2.project, s2.story_id, s2.worktree_id) == (
            "demo", "DM-1-02", rig["wt2_id"],
        )
        assert s1.source_id == s2.source_id == rig["source_id"]

        # The old guessing, ingested AFTER the claims, downgrades nothing:
        # both sessions already hold exact attempts, so every heuristic row
        # is skipped and the exact bindings stand untouched.
        heuristics = rig["service"].ingest_heuristic(baseline)
        assert heuristics["created"] == 0
        survivors = rig["repo"].find_active()
        assert len(survivors) == 2
        assert all(a.exact and a.kind == "rider_claim" for a in survivors)

        # No session is pinned to two attempts as exact.
        exact_by_session: dict[str, int] = {}
        for attempt in rig["repo"].list(exact=True, active_only=True):
            exact_by_session[attempt.session_id] = (
                exact_by_session.get(attempt.session_id, 0) + 1
            )
        assert exact_by_session and all(n == 1 for n in exact_by_session.values())

        # §13 on the projection: no filesystem path crosses to the wire.
        wire = rig["service"].list_attempts()
        assert str(tmp_path) not in json.dumps(wire)

    def test_attached_sessions_survive_a_hub_restart(self, rig):
        rig["service"].sync_rider_claims(state_path=rig["state"])
        reopened = Database(rig["db_path"]).work_attempts
        attempts = reopened.find_active()
        assert {a.session_id for a in attempts} == {"claude:s1", "codex:s2"}
        assert all(a.exact and a.kind == "rider_claim" for a in attempts)
        assert all(reopened.events(a.attempt_id) for a in attempts)

    def test_worktree_removal_abandons_without_deleting_history(self, rig):
        rig["service"].sync_rider_claims(state_path=rig["state"])
        (before,) = rig["repo"].find_active(worktree_id=rig["wt2_id"])
        shutil.rmtree(rig["wt2"])
        assert rig["service"].mark_worktree_removed(rig["wt2_id"]) == 1
        after = rig["repo"].get(before.attempt_id)
        assert after.state == "abandoned"
        assert after.ended_at is not None
        reasons = [e["reason"] for e in rig["repo"].events(after.attempt_id)]
        assert reasons == ["created:rider_claim", "worktree_removed"]
        # The other worktree's attempt is untouched.
        assert len(rig["repo"].find_active(worktree_id=rig["wt1_id"])) == 1

    def test_one_agent_across_sequential_stories_never_reuses_identity(self, rig):
        rig["service"].sync_rider_claims(state_path=rig["state"])
        (first,) = rig["repo"].find_active(session_id="claude:s1")

        # The same agent session moves on to the second Story.
        _emit_claim(
            rig["state"], agent="claude", session_id="s1",
            cwd=rig["wt1"], story="DM-1-02",
        )
        rig["service"].sync_rider_claims(state_path=rig["state"])

        finished = rig["repo"].get(first.attempt_id)
        assert finished.state == "ended"
        (second,) = rig["repo"].find_active(session_id="claude:s1")
        assert second.attempt_id != first.attempt_id
        assert second.story_id == "DM-1-02"
        assert second.exact and second.kind == "rider_claim"
        # Concurrency on one Story remains representable: the other agent's
        # attempt now shares DM-1-02, each with its own identity.
        story_rows = rig["repo"].find_active(project="demo", story_id="DM-1-02")
        assert len(story_rows) == 2
        assert len({a.attempt_id for a in story_rows}) == 2
