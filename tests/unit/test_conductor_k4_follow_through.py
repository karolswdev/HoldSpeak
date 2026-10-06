"""Conductor K4: follow through (docs/internal/CONDUCTOR.md, step 6).

1. The Heartbeat sweep refreshes the PR receipts of a source with a live
   agent launch; gh missing or unauthenticated is a named state.
2. A merged PR with exact attribution closes the launch's origin with the
   PR as evidence (Normal/YOLO), or asks the owner through one Door item
   (Secure). One close per launch, across sweeps and restarts.
3. The weekly update reports a merged PR as closed: a real WatchService
   ``github.pr.merged`` observation -> delta -> stored proposal (with its
   change class) -> drafted update text.
4. Cleanup: the agent's tmux session ends, a clean merged worktree goes,
   its Work attempt abandons, the launch's gate path is released.
5. New Room GitHub Watches read every PR state and carry the branch.

Real producers throughout: real git repos, the real launch engine with a
real kernel broker and receipts (K2's rig), real WatchService observations.
Only ``gh`` and ``tmux`` are faked, at their process boundary.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.delivery.attempts import WorkAttemptService
from holdspeak.delivery.factory_launch import execute_worktree_remove
from holdspeak.delivery.follow_through import FollowThroughObserver
from holdspeak.delivery.pr_receipts import GH_FIELDS, PrReceiptsService
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.heartbeat_service import HeartbeatService
from holdspeak.services.service_event_ledger import ServiceEventLedger
from tests.unit.test_agent_hand import OWNER, PROJECT, _rig, _seed, _wait_for
from tests.unit.test_factory_launch import T0

SWEEPER = Principal(PrincipalKind.OWNER, "heartbeat-conductor")
NOON = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
PR_URL = "https://github.com/acme/railsproj/pull/7"
MERGE_COMMIT = "f" * 40


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "hub.db")
    _seed(database)
    return database


def _git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


class FakeGh:
    """``gh`` at its process boundary: canned ``gh pr list`` JSON. git
    passes through to the real git (the receipts read worktree HEADs)."""

    def __init__(self) -> None:
        self.prs: list[dict[str, Any]] = []
        self.calls: list[list[str]] = []
        self.fail: tuple[int, str] | None = None

    def __call__(self, argv, cwd=None):
        if argv[0] == "git":
            return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=60)
        self.calls.append(list(argv))
        if self.fail is not None:
            return SimpleNamespace(returncode=self.fail[0], stdout="", stderr=self.fail[1])
        return SimpleNamespace(returncode=0, stdout=json.dumps(self.prs), stderr="")


def _pr(head_ref: str, head_sha: str, state: str = "MERGED") -> dict[str, Any]:
    merged = state == "MERGED"
    return {
        "number": 7, "title": "Fix the login timeout", "url": PR_URL,
        "headRefName": head_ref, "baseRefName": "main",
        "headRefOid": head_sha, "baseRefOid": "",
        "state": state, "isDraft": False, "statusCheckRollup": [],
        "author": {"login": "agent"}, "reviewDecision": "APPROVED" if merged else "",
        "mergedAt": "2026-10-06T11:00:00Z" if merged else None,
        "mergeCommit": {"oid": MERGE_COMMIT} if merged else None,
    }


def _launch(tmp_path, db, monkeypatch, *, item=("action", "ai_1"), mode="yolo", gh_available=True):
    """K2's real hand-to-agent launch, then the agent's commit on its branch."""
    rig = _rig(tmp_path, db, monkeypatch, item=item)
    result = rig.hand.hand(OWNER, *item)
    assert result["status"] == "launched", result
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    (rig.worktree / "fix.txt").write_text("timeout = 30\n", encoding="utf-8")
    _git(rig.worktree, "add", "-A")
    _git(rig.worktree, "commit", "-m", "Fix the login timeout")
    gh = FakeGh()
    receipts = PrReceiptsService(
        rig.registry, runner=gh, gh_available=lambda: gh_available,
        gate_matcher=lambda _path: False,
    )
    observer = FollowThroughObserver(
        db, ledger=rig.launches, registry=rig.registry, receipts=receipts,
        attempts=WorkAttemptService(db.work_attempts), control_mode=lambda: mode,
        tmux_runner=rig.tmux, gate_path=rig.gate_path, audit=lambda **_kw: 1,
        clock=lambda: T0,  # the rig launches at T0
    )
    rig.result, rig.gh, rig.receipts, rig.observer = result, gh, receipts, observer
    rig.branch = result["worktree"]["branch"]
    rig.head = _git(rig.worktree, "rev-parse", "HEAD")
    return rig


def _sweep(rig, observer=None) -> dict[str, Any]:
    heartbeat = HeartbeatService(
        rig.db, follow_through=observer or rig.observer,
        notifier=lambda *_a, **_k: True, clock=lambda: NOON, local_zone=timezone.utc,
    )
    return heartbeat.run_sweep(SWEEPER, owner_hand=True)


def _completed(db) -> list[dict[str, Any]]:
    return ServiceEventLedger(db).list(OWNER, event_type="commitment.completed")


def _status(db, item_id: str) -> str:
    with db._connection() as conn:
        return str(conn.execute("SELECT status FROM action_items WHERE id=?", (item_id,)).fetchone()[0])


# ── 1. PR refresh on the Heartbeat ──────────────────────────────────


def test_gh_fields_carry_review_decision_and_merge() -> None:
    fields = GH_FIELDS.split(",")
    assert {"reviewDecision", "mergedAt", "headRefName", "headRefOid"} <= set(fields)


def test_sweep_refreshes_the_pr_of_a_live_launch(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head, state="OPEN")]

    receipt = _sweep(rig)

    assert len(rig.gh.calls) == 1, "one batched gh pr list per followed source"
    argv = rig.gh.calls[0]
    assert argv[:3] == ["gh", "pr", "list"] and GH_FIELDS in argv
    ft = receipt["follow_through"]
    assert ft["launches"] == 1
    assert ft["sources"] == [{"source_id": rig.source.source_id, "gh_state": "live", "detail": ""}]
    record = rig.launches.get(rig.result["launch_id"])
    assert record["follow_through"]["pr"] == {
        "url": PR_URL, "number": 7, "state": "open", "review_decision": "",
    }
    # The shared receipts cache shows the sweep's rows to the next read.
    rows = rig.receipts.rows_view()["sources"][0]["prs"]
    assert rows[0]["attribution"] == "exact"
    assert rows[0]["worktree_id"] == record["worktree_id"]
    assert rig.receipts.rows_view()["sources"][0]["gh_state"] == "live"
    assert _status(db, "ai_1") == "open", "an open PR closes nothing"
    rig.tmux.ended = True


def test_no_live_launch_makes_no_gh_call(tmp_path, db) -> None:
    gh = FakeGh()
    from holdspeak.delivery import DeliveryRegistry
    from holdspeak.delivery.factory_launch import LaunchLedger

    registry = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
    observer = FollowThroughObserver(
        db, ledger=LaunchLedger(tmp_path / "launches.json"), registry=registry,
        receipts=PrReceiptsService(registry, runner=gh, gh_available=lambda: True),
        attempts=WorkAttemptService(db.work_attempts),
    )
    receipt = HeartbeatService(
        db, follow_through=observer, notifier=lambda *_a, **_k: True,
        clock=lambda: NOON, local_zone=timezone.utc,
    ).run_sweep(SWEEPER, owner_hand=True)
    assert receipt["follow_through"]["launches"] == 0
    assert gh.calls == []


def test_gh_missing_is_a_named_state(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch, gh_available=False)
    receipt = _sweep(rig)
    assert receipt["follow_through"]["sources"][0]["gh_state"] == "gh_missing"
    assert rig.gh.calls == []
    assert _status(db, "ai_1") == "open"
    rig.tmux.ended = True


def test_gh_unauthenticated_is_a_named_state(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.fail = (1, "To get started with GitHub CLI, please run:  gh auth login")
    receipt = _sweep(rig)
    assert receipt["follow_through"]["sources"][0]["gh_state"] == "gh_unauthenticated"
    assert _status(db, "ai_1") == "open"
    rig.tmux.ended = True


# ── 2 + 4. Close the origin on merge, then clean up ─────────────────


def test_merge_closes_the_action_with_evidence_and_cleans_up(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    launch_id = rig.result["launch_id"]
    session = rig.launches.get(launch_id)["session"]
    key = str(rig.worktree.resolve())
    assert key in json.loads(rig.gate_path.read_text())["armed_paths"]

    receipt = _sweep(rig)

    # The origin closed, receipted, with the PR as evidence.
    assert _status(db, "ai_1") == "done"
    events = _completed(db)
    assert len(events) == 1
    assert events[0]["facts"]["evidence"] == {
        "pr_url": PR_URL, "merged_sha": MERGE_COMMIT, "merged_at": "2026-10-06T11:00:00Z",
        "attempt_id": rig.result["attempt_id"], "launch_id": launch_id,
    }
    assert receipt["follow_through"]["closed"] == [{"launch_id": launch_id, "close": "closed"}]

    # Cleanup: session ended, clean merged worktree removed, attempt
    # abandoned, the launch's gate path released.
    assert session not in rig.tmux.sessions
    assert any(c[1] == "kill-session" for c in rig.tmux.calls)
    assert not rig.worktree.exists()
    assert rig.branch in _git(rig.repo, "branch", "--list", rig.branch), "the branch is kept"
    attempt = db.work_attempts.get(rig.result["attempt_id"])
    assert attempt.state == "abandoned"
    gate = json.loads(rig.gate_path.read_text())
    assert key not in gate.get("armed_paths", []) and key not in gate["repos"]
    record = rig.launches.get(launch_id)
    assert record["follow_through"]["close"] == "closed"
    assert record["follow_through"]["cleanup"] == {
        "session": "killed", "worktree": "worktree_removed", "gate": "released",
    }
    assert record["follow_through"]["done"] is True


def test_one_close_per_launch_across_sweeps_and_restarts(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    kills = sum(1 for c in rig.tmux.calls if c[1] == "kill-session")

    # A restart: a new observer over the same durable ledger.
    restarted = FollowThroughObserver(
        db, ledger=type(rig.launches)(rig.launches._path), registry=rig.registry,
        receipts=rig.receipts, attempts=WorkAttemptService(db.work_attempts),
        control_mode=lambda: "yolo", tmux_runner=rig.tmux, gate_path=rig.gate_path,
        audit=lambda **_kw: 1, clock=lambda: T0,
    )
    receipt = _sweep(rig, restarted)
    _sweep(rig)

    assert len(_completed(db)) == 1
    assert sum(1 for c in rig.tmux.calls if c[1] == "kill-session") == kills
    assert receipt["follow_through"]["launches"] == 0, "a finished launch is not followed"


def test_reopened_close_replays_without_a_second_receipt(tmp_path, db, monkeypatch) -> None:
    """A crash between the close and the ledger write: the next sweep's
    close is a replay (no second commitment.completed)."""
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    FollowThroughService(db).complete(OWNER, "ai_1", "done")
    _sweep(rig)
    assert len(_completed(db)) == 1
    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["close"] == "already_closed"


def test_heuristic_or_unrelated_pr_closes_nothing(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr("feature/action-ai_1-other", "0" * 40)]
    _sweep(rig)
    assert _status(db, "ai_1") == "open"
    assert rig.worktree.exists()
    rig.tmux.ended = True


def test_secure_asks_through_one_door_item_then_closes_on_confirm(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch, mode="safe")
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    launch_id = rig.result["launch_id"]

    receipt = _sweep(rig)
    _sweep(rig)

    assert _status(db, "ai_1") == "open", "Secure does not close"
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT id, task, owner FROM action_items WHERE source_ref = ?",
            (f"agent_launch:{launch_id}",),
        ).fetchall()
    assert len(rows) == 1, "one confirm item across sweeps"
    confirm_id, task, owner = rows[0]
    assert task == "Merged: confirm close: Fix the login timeout (PR #7)"
    assert owner is None
    board = FollowThroughService(db).board(OWNER)
    assert confirm_id in [card.id for card in board.unassigned], "the item is on the Door (Needs you R1)"
    assert receipt["follow_through"]["confirm"] == [{"launch_id": launch_id}]
    assert rig.worktree.exists(), "cleanup waits for the close"

    # The owner confirms: the next sweep closes the origin with the evidence.
    FollowThroughService(db).complete(OWNER, confirm_id, "done")
    _sweep(rig)
    assert _status(db, "ai_1") == "done"
    origin_events = [e for e in _completed(db) if e["facts"]["action_item_id"] == "ai_1"]
    assert origin_events[0]["facts"]["evidence"]["pr_url"] == PR_URL
    assert not rig.worktree.exists()


def test_secure_dismissed_confirm_keeps_the_origin_open(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch, mode="safe")
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    with db._connection() as conn:
        confirm_id = conn.execute(
            "SELECT id FROM action_items WHERE source_ref = ?",
            (f"agent_launch:{rig.result['launch_id']}",),
        ).fetchone()[0]
    FollowThroughService(db).complete(OWNER, confirm_id, "dismiss")
    _sweep(rig)
    assert _status(db, "ai_1") == "open"
    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["close"] == "close_declined"


def test_decision_record_origin_links_the_pr(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch, item=("decision_record", "dr1"))
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    with db._connection() as conn:
        work = conn.execute(
            "SELECT work_type, work_ref FROM decision_record_work WHERE record_id='dr1'"
        ).fetchall()
    assert [tuple(row) for row in work] == [("pr", PR_URL)]
    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["close"] == "linked"


def test_decision_origin_links_the_pr_on_its_record(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch, item=("decision", "d1"))
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT w.work_ref FROM decision_record_work w JOIN decision_records r ON r.id = w.record_id "
            "WHERE r.source_type='meeting' AND r.source_id='d1' AND w.work_type='pr'"
        ).fetchall()
    assert [row[0] for row in rows] == [PR_URL]


def test_dirty_worktree_is_kept_by_name(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    (rig.worktree / "scratch.txt").write_text("not committed\n", encoding="utf-8")
    _sweep(rig)
    cleanup = rig.launches.get(rig.result["launch_id"])["follow_through"]["cleanup"]
    assert cleanup["worktree"] == "worktree_dirty"
    assert cleanup["session"] == "killed" and cleanup["gate"] == "released"
    assert rig.worktree.exists()


def test_unmerged_commit_keeps_the_worktree_by_name(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    (rig.worktree / "later.txt").write_text("after the merge\n", encoding="utf-8")
    _git(rig.worktree, "add", "-A")
    _git(rig.worktree, "commit", "-m", "later work")
    _sweep(rig)
    cleanup = rig.launches.get(rig.result["launch_id"])["follow_through"]["cleanup"]
    assert cleanup["worktree"] == "worktree_unmerged"
    assert rig.worktree.exists()


def test_worktree_remove_refuses_by_name(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    audit: list[str] = []

    def record(**kw):
        audit.append(kw["outcome"])
        return 1

    assert execute_worktree_remove(
        {"name": "../x", "repo_path": str(repo), "path": str(tmp_path / "x")}, audit=record,
    )["status"] == "bad_name"
    assert execute_worktree_remove(
        {"name": "x", "repo_path": str(repo), "path": str(tmp_path / "deep" / "x")}, audit=record,
    )["status"] == "out_of_root"
    assert execute_worktree_remove(
        {"name": "gone", "repo_path": str(repo), "path": str(tmp_path / "gone")}, audit=record,
    )["status"] == "worktree_absent"
    assert audit == ["bad_name", "out_of_root", "worktree_absent"], "every refusal is audited"


# ── 3. The weekly update reports a merged PR as closed ──────────────


def test_merged_pr_is_closed_in_the_drafted_update(tmp_path, db) -> None:
    """Producer to draft: a real WatchService github.pr.merged observation
    (GitHubWatchSource with gh faked at its process boundary) -> delta ->
    the stored proposal keeps change_class -> the drafted update text
    reports the PR under Progress as closed."""
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_update_service import ProjectUpdateService
    from holdspeak.services.reaction_service import ReactionService
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import fetch_watch_snapshot

    watch_id = "watch-k4-merge"
    ReactionService(db).create_watch(
        OWNER, connector_id="gh", query_kind="pull_requests", name="PR watch",
        query={"repository": "acme/railsproj", "state": "all"}, watch_id=watch_id,
    )
    db.automations.update_watch_spec(watch_id, project_id=PROJECT, revision=1)
    db.automations.create_project_source(
        source_id="psrc_k4", project_id=PROJECT, source_ref=f"watch:{watch_id}",
        label="PR watch", semantic_role="watch",
    )
    phase = {"state": "OPEN"}
    gh_argv: list[list[str]] = []

    def gh(argv, **_kw):
        gh_argv.append(list(argv))
        row = {
            "number": 42, "title": "Fix the login timeout",
            "url": "https://github.com/acme/railsproj/pull/42", "state": phase["state"],
            "isDraft": False, "reviewRequests": [], "reviewDecision": "",
            "statusCheckRollup": [], "headRefOid": "abc123", "headRefName": "hs/action-ai_1",
            "updatedAt": "2026-10-06T10:00:00Z", "createdAt": "2026-10-05T10:00:00Z",
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps([row]), stderr="")

    watches = WatchService(
        db, snapshot_fetcher=lambda principal, **kw: fetch_watch_snapshot(principal, github_runner=gh, **kw),
    )
    watches.baseline_watch(OWNER, watch_id)
    phase["state"] = "MERGED"
    evaluated = watches.evaluate_once(OWNER, watch_id)
    assert evaluated["state"] == "completed" and evaluated["observation_ids"]
    assert "--state" in gh_argv[-1] and gh_argv[-1][gh_argv[-1].index("--state") + 1] == "all"

    delta = ProjectDeltaService(db, ProjectEvidenceCollector(db))
    review = delta.open_review(OWNER, PROJECT)
    stored = db.project_observations.list_proposals(PROJECT, review_window_key=review["review_id"])
    merged = [p for p in stored if "github.pr.merged" in p["patch_json"]]
    assert merged and merged[0]["change_class"] == "closed"

    projects = ProjectService(db, delta_service=delta)
    draft = ProjectUpdateService(db, project_service=projects, delta_service=delta).draft_update(OWNER, PROJECT)
    body = draft["body_md"]
    progress = body.split("## Progress", 1)[1].split("## Decisions", 1)[0]
    decisions = body.split("## Decisions", 1)[1].split("## Risks", 1)[0]
    assert "Closed: Fix the login timeout (#42) -- merged" in progress
    assert "Fix the login timeout" not in decisions
    claims = json.loads(draft["claims_json"])
    closed = [c for c in claims if c["text"].startswith("Closed: ")]
    assert closed and closed[0]["section"] == "progress"


# ── 5. Room GitHub Watch defaults ───────────────────────────────────


def test_new_room_pr_watch_reads_every_state_and_the_branch(tmp_path) -> None:
    from holdspeak import github_templates
    from holdspeak.services.project_door_service import ProjectDoorService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.watch_sources import GH_WATCH_FIELDS, GitHubWatchSource
    from holdspeak.services.watch_service import WatchService

    assert "headRefName" in GH_WATCH_FIELDS.split(",")
    assert github_templates.compile("watch.github.review_queue", "acme/app")["subject"]["query"]["state"] == "all"
    assert github_templates.compile("watch.github.merge_flow", "acme/app")["subject"]["query"]["state"] == "all"

    database = Database(tmp_path / "door.db")
    door = ProjectDoorService(
        project_service=ProjectService(database),
        watch_service=WatchService(database, snapshot_fetcher=lambda _p, **_k: []),
    )
    door.create(OWNER, "Ship the release", [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}])
    pr_watch = next(w for w in database.automations.list_watches() if w["query_kind"] == "pull_requests")
    query = pr_watch["query"] if isinstance(pr_watch["query"], dict) else json.loads(pr_watch["query_json"])
    assert query["state"] == "all"

    argv: list[list[str]] = []

    def gh(command, **_kw):
        argv.append(list(command))
        rows = [
            {"number": 1, "state": "OPEN", "headRefName": "hs/a", "title": "a", "url": "u1"},
            {"number": 2, "state": "MERGED", "headRefName": "hs/b", "title": "b", "url": "u2"},
        ]
        return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")

    entities = GitHubWatchSource(runner=gh).snapshot(OWNER, query_kind="pull_requests", query=query)
    assert argv[0][argv[0].index("--state") + 1] == "all"
    assert [e["headRefName"] for e in entities] == ["hs/a", "hs/b"]
    # An existing watch with no state keeps its open-only read.
    GitHubWatchSource(runner=gh).snapshot(OWNER, query_kind="pull_requests", query={"repository": "acme/app"})
    assert argv[1][argv[1].index("--state") + 1] == "open"
    # The Door's OPEN PRS token still counts open PRs only.
    counted = ProjectDoorService(gh_runner=gh).count(OWNER, "github", "acme/app", ["open_prs"])
    assert counted["tokens"][0]["count"] == 1
