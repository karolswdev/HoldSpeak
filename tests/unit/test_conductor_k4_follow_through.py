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
5. GitHub Watches carry the branch; Room PR watches stay open-only (open
   coverage is never derived from a bounded all-state list). Merges of
   agent PRs are observed by the per-launch PR lookup (1-2).

Astra's round-1 reproducers on #900 are ported below as fences.

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
        "isCrossRepository": False,
        "headRepositoryOwner": {"login": "acme"}, "headRepository": {"name": "railsproj"},
    }


def _launch(tmp_path, db, monkeypatch, *, item=("action", "ai_1"), mode="yolo", gh_available=True):
    """K2's real hand-to-agent launch, then the agent's commit on its branch."""
    rig = _rig(tmp_path, db, monkeypatch, item=item)
    _git(rig.repo, "remote", "add", "origin", "https://github.com/acme/railsproj.git")
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
        "attempts": "reconciled",
    }
    assert record["follow_through"]["pr"]["number"] == 7 and record["follow_through"]["pr"]["url"] == PR_URL
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
    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["pr_state"] == "no_pr"
    rig.tmux.ended = True


# ── Astra round 1, finding 1: PR identity ───────────────────────────


@pytest.mark.parametrize("case", ["other_branch_same_sha", "fork_same_branch", "reused_branch"])
def test_unrelated_merge_must_not_close(tmp_path, db, monkeypatch, case) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    if case == "other_branch_same_sha":
        row = _pr("another-branch", rig.head)
    elif case == "fork_same_branch":
        row = _pr(rig.branch, "0" * 40)
        row.update(isCrossRepository=True, headRepositoryOwner={"login": "another-owner"},
                   headRepository={"name": "railsproj"})
    else:  # a merge on this branch name from before the launch
        row = _pr(rig.branch, rig.head)
        row["mergedAt"] = "2026-07-15T12:00:00Z"
    rig.gh.prs = [row, dict(_pr(rig.branch, rig.head, "OPEN"), number=8)]
    _sweep(rig)
    record = rig.launches.get(rig.result["launch_id"])
    assert _status(db, "ai_1") == "open", f"{case} closed the action"
    # The launch's own open PR is the one selected, and kept by identity.
    assert record["follow_through"]["pr"]["number"] == 8
    assert record["follow_through"]["pr_state"] == "pr_open"
    rig.tmux.ended = True


def test_selected_pr_is_kept_by_number_and_url(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
    _sweep(rig)
    # A second PR on the same branch later: the kept PR still decides.
    rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN"), dict(_pr(rig.branch, rig.head), number=9, url=PR_URL[:-1] + "9")]
    _sweep(rig)
    assert _status(db, "ai_1") == "open"
    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["pr"]["number"] == 7
    rig.tmux.ended = True


def test_several_candidates_are_ambiguous_by_name(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head), dict(_pr(rig.branch, rig.head, "OPEN"), number=8)]
    _sweep(rig)
    record = rig.launches.get(rig.result["launch_id"])
    assert record["follow_through"]["pr_state"] == "pr_ambiguous"
    assert "pr" not in record["follow_through"]
    assert _status(db, "ai_1") == "open"
    rig.tmux.ended = True


def test_no_github_origin_is_named(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    _git(rig.repo, "remote", "remove", "origin")
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["pr_state"] == "repository_unknown"
    assert _status(db, "ai_1") == "open"
    rig.tmux.ended = True


def test_pr_closed_without_merge_ends_follow_through(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
    _sweep(rig)
    rig.gh.prs = [_pr(rig.branch, rig.head, "CLOSED")]
    _sweep(rig)
    record = rig.launches.get(rig.result["launch_id"])
    assert record["follow_through"]["pr_state"] == "pr_closed_unmerged"
    assert record["follow_through"]["done"] is True
    assert _status(db, "ai_1") == "open" and rig.worktree.exists()
    calls = len(rig.gh.calls)
    _sweep(rig)
    assert len(rig.gh.calls) == calls, "an ended follow-through is not polled"
    rig.tmux.ended = True


# ── Astra round 1, finding 2: only the launch's own worktree goes ────


def test_manual_worktree_must_survive(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    _git(rig.repo, "remote", "add", "origin", "https://github.com/acme/railsproj.git")
    manual = tmp_path / "my-handmade-worktree"
    _git(rig.repo, "worktree", "add", "-b", "my-handmade-branch", str(manual))
    (manual / "change.txt").write_text("user change")
    _git(manual, "add", "change.txt")
    _git(manual, "commit", "-m", "my change")
    source, wt = rig.registry.register(str(manual))
    record = rig.service.launch({
        "agent_profile_id": "claude-default", "source_id": source.source_id,
        "worktree": {"mode": "existing", "worktree_id": wt.worktree_id},
        "story_ref": {"project": PROJECT, "story_id": "action-ai_1"},
        "origin_ref": {"kind": "action", "id": "ai_1"}, "session_label": "handmade-probe",
    })
    assert record["state"] == "launched" and record["commands"]["worktree_create"] is None
    gh = FakeGh()
    gh.prs = [_pr(wt.branch, _git(manual, "rev-parse", "HEAD"))]
    observer = FollowThroughObserver(
        db, ledger=rig.launches, registry=rig.registry,
        receipts=PrReceiptsService(rig.registry, runner=gh, gh_available=lambda: True, gate_matcher=lambda p: False),
        attempts=WorkAttemptService(db.work_attempts), control_mode=lambda: "yolo", tmux_runner=rig.tmux,
        gate_path=rig.gate_path, audit=lambda **kw: 1, clock=lambda: T0,
    )
    _sweep(rig, observer)
    assert manual.exists(), "the user-created worktree was removed"
    follow = rig.launches.get(record["launch_id"])["follow_through"]
    assert follow["close"] == "closed", "the merge still closes the origin"
    assert follow["cleanup"]["worktree"] == "worktree_kept_not_ours"
    rig.tmux.ended = True


def test_two_sweeps_one_close(tmp_path, db, monkeypatch) -> None:
    from concurrent.futures import ThreadPoolExecutor

    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in [pool.submit(_sweep, rig) for _ in range(2)]:
            future.result()
    assert len(_completed(db)) == 1
    assert sum(1 for c in rig.tmux.calls if c[1] == "kill-session") == 1


# ── Astra round 1, finding 3: an exited agent is still followed ─────


def test_agent_exit_before_merge_is_still_followed(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    launch_id = rig.result["launch_id"]
    rig.tmux(["tmux", "kill-session", "-t", rig.launches.get(launch_id)["session"]])
    _wait_for(lambda: rig.launches.get(launch_id), "state", "complete")
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    assert rig.gh.calls, "the completed launch still polls its PR"
    assert _status(db, "ai_1") == "done"
    follow = rig.launches.get(launch_id)["follow_through"]
    assert follow["cleanup"]["session"] == "session_gone" and follow["done"] is True


# ── Astra round 1, finding 7: the attempt is reconciled after a crash ─


def _crash_then_restart(rig, monkeypatch) -> None:
    def crash_after_remove(worktree_id):
        assert not rig.worktree.exists()
        raise RuntimeError("crash after physical removal, before attempt marker")

    monkeypatch.setattr(rig.observer._attempts, "mark_worktree_removed", crash_after_remove)
    first = _sweep(rig)
    assert first["follow_through"].get("errors")
    assert not rig.worktree.exists()
    restarted = FollowThroughObserver(
        rig.db, ledger=type(rig.launches)(rig.launches._path), registry=rig.registry,
        receipts=rig.receipts, attempts=WorkAttemptService(rig.db.work_attempts),
        control_mode=lambda: "yolo", tmux_runner=rig.tmux, gate_path=rig.gate_path,
        audit=lambda **kw: 1, clock=lambda: T0,
    )
    _sweep(rig, restarted)
    attempt = rig.db.work_attempts.get(rig.result["attempt_id"])
    follow = rig.launches.get(rig.result["launch_id"])["follow_through"]
    assert attempt.state == "abandoned", "finished launch left its Work attempt live"
    assert follow["cleanup"]["worktree"] == "worktree_absent"
    assert follow["cleanup"]["attempts"] == "reconciled" and follow["done"] is True


def test_restart_after_remove_finishes_attempt(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _crash_then_restart(rig, monkeypatch)


def test_retry_absent_worktree_finishes_attempt(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch)
    rig.service.first_message.close(timeout=1.0)
    _wait_for(lambda: {"stopped": not rig.service.first_message._watched}, "stopped", True)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _crash_then_restart(rig, monkeypatch)


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


def test_secure_dismiss_survives_mode_change(tmp_path, db, monkeypatch) -> None:
    """Astra round 1, finding 4: a dismissal is final for the launch."""
    rig = _launch(tmp_path, db, monkeypatch, mode="safe")
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    with db._connection() as conn:
        confirm_id = conn.execute(
            "SELECT id FROM action_items WHERE source_ref = ?",
            (f"agent_launch:{rig.result['launch_id']}",),
        ).fetchone()[0]
    FollowThroughService(db).complete(OWNER, confirm_id, "dismiss")
    rig.observer._control_mode = lambda: "yolo"
    _sweep(rig)
    _sweep(rig)
    assert _status(db, "ai_1") == "open", "the explicit dismissal was ignored"
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


# ── 3. The weekly update reports merges as closed ───────────────────


def _watch_merge(db) -> dict[str, Any]:
    """A real WatchService github.pr.merged observation (GitHubWatchSource,
    gh faked at its process boundary) on an explicit merged-state watch."""
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

    def gh(argv, **_kw):
        row = dict(_pr("hs/action-ai_1", "a" * 40, phase["state"]), number=42,
                   url="https://github.com/acme/railsproj/pull/42", reviewRequests=[],
                   createdAt="2026-10-05T10:00:00Z", updatedAt="2026-10-06T10:00:00Z")
        return SimpleNamespace(returncode=0, stdout=json.dumps([row]), stderr="")

    watches = WatchService(
        db, snapshot_fetcher=lambda principal, **kw: fetch_watch_snapshot(principal, github_runner=gh, **kw),
    )
    watches.baseline_watch(OWNER, watch_id)
    phase["state"] = "MERGED"
    evaluated = watches.evaluate_once(OWNER, watch_id)
    assert evaluated["state"] == "completed" and evaluated["observation_ids"]
    return evaluated


def _updates(db):
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_update_service import ProjectUpdateService

    delta = ProjectDeltaService(db, ProjectEvidenceCollector(db))
    return delta, ProjectUpdateService(db, project_service=ProjectService(db, delta_service=delta), delta_service=delta)


def _progress(body: str) -> str:
    return body.split("## Progress", 1)[1].split("## Decisions", 1)[0]


def test_watch_merge_is_closed_in_the_draft_whatever_the_review(db) -> None:
    """Astra round 1, finding 6: before a review opens, while it is open,
    and after it is accepted, the period's merge is reported as closed."""
    _watch_merge(db)
    delta, updates = _updates(db)
    line = "Closed: Fix the login timeout (#42) -- merged"

    before = updates.draft_update(OWNER, PROJECT)["body_md"]
    review = delta.open_review(OWNER, PROJECT)
    during = updates.draft_update(OWNER, PROJECT)
    delta.accept_review(OWNER, PROJECT, review["review_id"])
    after = updates.draft_update(OWNER, PROJECT)["body_md"]

    for body in (before, during["body_md"], after):
        assert line in _progress(body)
        assert body.count(line) == 1
    decisions = during["body_md"].split("## Decisions", 1)[1].split("## Risks", 1)[0]
    assert "Fix the login timeout" not in decisions, "a closed proposal is not repeated in Decisions"
    # The delta keeps the class on the stored proposal (persisted, not dropped).
    stored = db.project_observations.list_proposals(PROJECT, review_window_key=review["review_id"])
    assert [p["change_class"] for p in stored if "github.pr.merged" in p["patch_json"]] == ["closed"]
    claims = json.loads(during["claims_json"])
    closed = [c for c in claims if c["text"] == line]
    assert closed and closed[0]["section"] == "progress" and closed[0]["refs"][0].startswith("pobs:")


def test_published_update_starts_the_next_period(db) -> None:
    _watch_merge(db)
    _delta, updates = _updates(db)
    draft = updates.draft_update(OWNER, PROJECT)
    with db._connection() as conn:
        conn.execute(
            "UPDATE project_updates SET lifecycle='published', published_at=? WHERE id=?",
            ("2099-01-01T00:00:00+00:00", draft["id"]),
        )
    assert "Closed:" not in updates.draft_update(OWNER, PROJECT)["body_md"]


def test_agent_merge_is_closed_in_the_draft(tmp_path, db, monkeypatch) -> None:
    """The per-launch PR lookup is the agent PR's merge observation: its
    commitment.completed evidence is reported, with no Watch at all."""
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    _delta, updates = _updates(db)
    draft = updates.draft_update(OWNER, PROJECT)
    assert "Closed: Fix the login timeout (PR #7) -- merged" in _progress(draft["body_md"])
    claims = json.loads(draft["claims_json"])
    assert any(c["refs"] == ["action_item:ai_1"] and c["text"].startswith("Closed: ") for c in claims)


# ── 5. GitHub Watch fields; open coverage stays open-only ───────────


def test_watch_carries_the_branch_and_room_prs_stay_open(tmp_path) -> None:
    from holdspeak import github_templates
    from holdspeak.services.watch_sources import GH_WATCH_FIELDS, GitHubWatchSource

    assert "headRefName" in GH_WATCH_FIELDS.split(",")
    assert github_templates.compile("watch.github.review_queue", "acme/app")["subject"]["query"]["state"] == "open"

    def gh(command, **_kw):
        rows = [{"number": 1, "state": "OPEN", "headRefName": "hs/a", "title": "a", "url": "u1"}]
        return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")

    entities = GitHubWatchSource(runner=gh).snapshot(
        OWNER, query_kind="pull_requests", query={"repository": "acme/app", "state": "open"},
    )
    assert entities[0]["headRefName"] == "hs/a"
    from holdspeak.services.reaction_service import normalize_snapshot

    assert normalize_snapshot("gh", entities)["entities"]["1"]["head_ref"] == "hs/a"


def test_open_pr_count_survives_more_than_50_merged_prs() -> None:
    """Astra round 1, finding 5: a busy repository's old open PR counts."""
    from holdspeak.services.project_door_service import ProjectDoorService

    rows = [dict(_pr(f"closed-{n}", "a" * 40), number=n) for n in range(52, 1, -1)]
    rows.append(dict(_pr("old-but-open", "b" * 40, "OPEN"), number=1))

    def gh(argv, **_kw):
        state = argv[argv.index("--state") + 1]
        limit = int(argv[argv.index("--limit") + 1])
        eligible = [r for r in rows if state == "all" or r["state"].lower() == state]
        return SimpleNamespace(returncode=0, stdout=json.dumps(eligible[:limit]), stderr="")

    result = ProjectDoorService(gh_runner=gh).count(OWNER, "github", "acme/railsproj", ["open_prs"])
    assert result["tokens"][0]["count"] == 1


# ── Astra round 2, finding 6: publication boundaries keep progress ──


def test_merge_observed_after_draft_before_publish_is_not_lost(db) -> None:
    """A draft frozen before the merge is published later: the merge is
    reported in the next draft (no time cutoff at publication)."""
    _delta, updates = _updates(db)
    previous = updates.draft_update(OWNER, PROJECT)
    assert "Closed:" not in _progress(previous["body_md"])
    _watch_merge(db)
    updates.publish_update(OWNER, previous["id"])
    current = updates.draft_update(OWNER, PROJECT)
    assert "Closed: Fix the login timeout (#42) -- merged" in _progress(current["body_md"])
    # Once a draft that reports it is published, it is not reported again.
    updates.publish_update(OWNER, current["id"])
    assert "Closed:" not in _progress(updates.draft_update(OWNER, PROJECT)["body_md"])


def test_secure_close_after_publication_is_reported(tmp_path, db, monkeypatch) -> None:
    """Secure: an update is published while the confirmation is pending;
    the commitment completed later is reported in the next draft."""
    rig = _launch(tmp_path, db, monkeypatch, mode="safe")
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    try:
        _sweep(rig)
        assert _status(db, "ai_1") == "open"
        _delta, updates = _updates(db)
        previous = updates.draft_update(OWNER, PROJECT)
        assert "Closed:" not in _progress(previous["body_md"])
        updates.publish_update(OWNER, previous["id"])
        with db._connection() as conn:
            confirm_id = conn.execute(
                "SELECT id FROM action_items WHERE source_ref = ?",
                (f"agent_launch:{rig.result['launch_id']}",),
            ).fetchone()[0]
        FollowThroughService(db).complete(OWNER, confirm_id, "done")
        _sweep(rig)
        assert _status(db, "ai_1") == "done"
        current = updates.draft_update(OWNER, PROJECT)
        assert "Closed: Fix the login timeout (PR #7) -- merged" in _progress(current["body_md"])
        assert json.loads(current["source_manifest_json"])["closure_keys"] == [PR_URL]
    finally:
        rig.tmux.ended = True
