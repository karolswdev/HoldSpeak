"""Conductor R4: hand and close more kinds.

1. A Room issue row (a real Jira Watch snapshot) can be handed: the brief
   carries its title, body, labels, URL and the Room's context; the
   launch's origin_ref is the issue. On merge nothing is written to Jira or
   GitHub: the PR is linked to the issue in the Room, with evidence.
2. Every other origin K4 left ``not_closable`` gets a close: a Project
   item takes its done transition; a note, a meeting and an artifact get
   the PR linked in their Room.
3. The Secure "Merged: confirm close" Door item is the owner's.
4. A removed worktree leaves the Delivery registry, with a receipt.
5. The Heartbeat reads each Room repository's merged PRs (a setting, ON by
   default): the weekly update reports merges no agent made, one line per
   PR URL with K4's own closures.

Real producers: real git, K2's launch rig (a real kernel broker and
receipts), a real WatchService Jira snapshot, the real JiraProviderAdapter
and GitHubWatchSource. Only ``acli``, ``gh`` and ``tmux`` are faked, at
their process boundary.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.delivery import DeliveryRegistry
from holdspeak.delivery.attempts import WorkAttemptService
from holdspeak.delivery.follow_through import FollowThroughObserver
from holdspeak.delivery.pr_receipts import PrReceiptsService
from holdspeak.services.agent_brief import compose_agent_brief, parse_item_ref
from holdspeak.services.agent_issue import issue_body
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.heartbeat_service import HeartbeatService
from holdspeak.services.jira_provider import JiraProviderAdapter
from tests.unit.test_agent_hand import OWNER, PROJECT, _rig, _seed, _wait_for
from tests.unit.test_conductor_k4_follow_through import (
    MERGE_COMMIT,
    NOON,
    PR_URL,
    SWEEPER,
    FakeGh,
    _git,
    _pr,
    _progress,
    _updates,
)
from tests.unit.test_factory_launch import T0

WATCH = "watch-r4-jira"
ISSUE_ID = f"{WATCH}.PAY-418"
CONNECTION = "acme.atlassian.net|me@acme.dev"
BODY = "Month-end runs take 40 minutes. Batch the ledger reads."
DUE = (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat()


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "hub.db")
    _seed(database)
    return database


class FakeAcli:
    """``acli`` at its process boundary: the account switch, the status
    read-back, the search, and the work item view."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.resolved = False
        self.description: Any = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": BODY}]}],
        }

    def __call__(self, argv, **_kw):
        self.calls.append(list(argv))
        verb = argv[1:4]
        if verb == ["jira", "auth", "switch"]:
            return SimpleNamespace(returncode=0, stdout="switched", stderr="")
        if verb == ["jira", "auth", "status"]:
            return SimpleNamespace(
                returncode=0, stderr="",
                stdout="✓ Authenticated\n  Site: acme.atlassian.net\n  Email: me@acme.dev\n",
            )
        if verb == ["jira", "workitem", "search"]:
            if self.resolved:
                return SimpleNamespace(returncode=0, stdout="[]", stderr="")
            issues = [{
                "key": "PAY-418", "id": "10418",
                "fields": {
                    "summary": "Reconciliation job slow on month-end data",
                    "labels": ["ledger", "performance"],
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "issuetype": {"name": "Bug"},
                },
            }]
            return SimpleNamespace(returncode=0, stdout=json.dumps(issues), stderr="")
        if verb == ["jira", "workitem", "view"]:
            fields = argv[argv.index("--fields") + 1]
            if "description" in fields:
                return SimpleNamespace(
                    returncode=0, stderr="",
                    stdout=json.dumps({"fields": {"description": self.description, "labels": ["ledger"]}}),
                )
            return SimpleNamespace(
                returncode=0, stderr="",
                stdout=json.dumps({"fields": {"duedate": DUE, "project": {"key": "PAY"}}}),
            )
        return SimpleNamespace(returncode=1, stdout="", stderr=f"unexpected {argv}")


def _jira_watch(db) -> FakeAcli:
    """A real Room Jira Watch whose snapshot WatchService baselines through
    the real JiraWatchSource and JiraProviderAdapter (acli faked)."""
    from holdspeak.services.reaction_service import ReactionService
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import fetch_watch_snapshot

    acli = FakeAcli()
    ReactionService(db).create_watch(
        OWNER, connector_id="jira", query_kind="issues", name="Ledger issues",
        query={"connection_ref": CONNECTION, "projects": ["PAY"]}, watch_id=WATCH,
    )
    db.automations.update_watch_spec(WATCH, project_id=PROJECT, revision=1)
    adapter = JiraProviderAdapter(db=db, runner=acli)
    WatchService(
        db, snapshot_fetcher=lambda principal, **kw: fetch_watch_snapshot(principal, jira_adapter=adapter, **kw),
    ).baseline_watch(OWNER, WATCH)
    return acli


def _observer(rig, gh, *, mode="yolo", audit=None):
    receipts = PrReceiptsService(
        rig.registry, runner=gh, gh_available=lambda: True, gate_matcher=lambda _path: False,
    )
    return FollowThroughObserver(
        rig.db, ledger=rig.launches, registry=rig.registry, receipts=receipts,
        attempts=WorkAttemptService(rig.db.work_attempts), control_mode=lambda: mode,
        tmux_runner=rig.tmux, gate_path=rig.gate_path, audit=audit or (lambda **_kw: 1),
        clock=lambda: T0, gh_runner=lambda argv, **_kw: gh(argv),
    )


def _launch(tmp_path, db, monkeypatch, item, *, mode="yolo", acli=None, audit=None):
    """K2's real hand-to-agent launch of ``item``, then the agent's commit."""
    rig = _rig(tmp_path, db, monkeypatch, item=item)
    if acli is not None:
        rig.hand.issue_reads = {"jira_adapter": JiraProviderAdapter(db=db, runner=acli)}
    _git(rig.repo, "remote", "add", "origin", "https://github.com/acme/railsproj.git")
    result = rig.hand.hand(OWNER, *item)
    assert result["status"] == "launched", result
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    (rig.worktree / "fix.txt").write_text("timeout = 30\n", encoding="utf-8")
    _git(rig.worktree, "add", "-A")
    _git(rig.worktree, "commit", "-m", "Fix it")
    rig.gh = FakeGh()
    rig.observer = _observer(rig, rig.gh, mode=mode, audit=audit)
    rig.result = result
    rig.branch = result["worktree"]["branch"]
    rig.head = _git(rig.worktree, "rev-parse", "HEAD")
    return rig


def _sweep(rig, **heartbeat_kw) -> dict[str, Any]:
    return HeartbeatService(
        rig.db, follow_through=rig.observer, notifier=lambda *_a, **_k: True,
        clock=lambda: NOON, local_zone=timezone.utc, **heartbeat_kw,
    ).run_sweep(SWEEPER, owner_hand=True)


def _observations(db, kind: str) -> list[dict[str, Any]]:
    return [o for o in db.project_observations.list_observations(PROJECT, limit=500) if o["observation_kind"] == kind]


def _links(db) -> list[tuple[str, str, str]]:
    with db._connection() as conn:
        return [tuple(r) for r in conn.execute(
            "SELECT target_ref, evidence_ref, relation FROM project_evidence_links WHERE project_id=?", (PROJECT,)
        )]


# ── 1. A Room issue can be handed ────────────────────────────────────


def test_room_jira_row_names_its_watch_and_entity(db) -> None:
    from holdspeak.services.project_service import ProjectService

    _jira_watch(db)
    rows = [r for r in ProjectService(db)._read_room_needs_you(PROJECT)["items"] if r["source"] == "jira"]
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["title"] == "PAY-418 Reconciliation job slow on month-end data"
    assert (row["kind"], row["watchId"], row["entity_id"]) == ("issue", WATCH, "PAY-418")
    # The row's own ids are the item id agent.hand takes.
    assert parse_item_ref({"kind": "issue", "id": f"{row['watchId']}.{row['entity_id']}"}) == ("issue", ISSUE_ID)


def test_issue_brief_carries_title_body_labels_url_and_the_room(db) -> None:
    acli = _jira_watch(db)
    brief = compose_agent_brief(
        db, {"kind": "issue", "id": ISSUE_ID}, control_mode="yolo",
        principal=OWNER, issue_reads={"jira_adapter": JiraProviderAdapter(db=db, runner=acli)},
    )
    text = brief["text"]
    assert 'HoldSpeak hands you one item: issue:watch-r4-jira.PAY-418 "PAY-418 Reconciliation job slow' in text
    assert BODY in text
    assert "Labels: ledger, performance" in text
    assert "URL: https://acme.atlassian.net/browse/PAY-418" in text
    assert "Room watch: Ledger issues" in text
    assert brief["project_id"] == PROJECT, "the issue's Room is the Watch's Project"
    assert f"issue:{ISSUE_ID}" in brief["refs"]
    assert any("Do not write Closes" in line for line in brief["acceptance"])
    # Reads only: the account switch, its read-back, the search, the views.
    assert {tuple(c[1:4]) for c in acli.calls} <= {
        ("jira", "auth", "switch"), ("jira", "auth", "status"),
        ("jira", "workitem", "search"), ("jira", "workitem", "view"),
    }


def test_issue_brief_names_an_unread_body_and_still_composes(db) -> None:
    acli = _jira_watch(db)

    def broken(argv, **kw):
        if argv[1:4] == ["jira", "workitem", "view"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="boom")
        return acli(argv, **kw)

    brief = compose_agent_brief(
        db, {"kind": "issue", "id": ISSUE_ID}, control_mode="yolo",
        principal=OWNER, issue_reads={"jira_adapter": JiraProviderAdapter(db=db, runner=broken)},
    )
    assert "Body: not read" in brief["text"] and BODY not in brief["text"]


def test_github_issue_body_is_read_with_gh_issue_view() -> None:
    calls: list[list[str]] = []

    def gh(argv, **_kw):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout=json.dumps({"body": "Steps to reproduce"}), stderr="")

    body, state = issue_body(
        OWNER, {"connector": "gh", "repository": "acme/payments-ledger", "key": "418"}, gh_runner=gh,
    )
    assert (body, state) == ("Steps to reproduce", "read")
    assert calls == [["gh", "issue", "view", "418", "--repo", "acme/payments-ledger", "--json", "body,labels,title,url"]]


def test_hand_an_issue_launches_with_the_issue_as_origin(tmp_path, db, monkeypatch) -> None:
    acli = _jira_watch(db)
    rig = _launch(tmp_path, db, monkeypatch, ("issue", ISSUE_ID), acli=acli)
    try:
        assert rig.result["origin_ref"] == {"kind": "issue", "id": ISSUE_ID}
        assert rig.result["project_id"] == PROJECT
        assert rig.result["worktree"] == {"name": f"hs-issue-{ISSUE_ID}", "branch": f"hs/issue-{ISSUE_ID}"}
        record = rig.launches.get(rig.result["launch_id"])
        assert record["origin_ref"] == {"kind": "issue", "id": ISSUE_ID}
        typed = "\n".join(text for _pane, text in rig.typed)
        assert BODY in typed, "the brief the agent received carries the issue body"
    finally:
        rig.tmux.ended = True


def test_merged_issue_pr_is_linked_in_the_room_and_nothing_is_written_to_jira(tmp_path, db, monkeypatch) -> None:
    acli = _jira_watch(db)
    rig = _launch(tmp_path, db, monkeypatch, ("issue", ISSUE_ID), acli=acli)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    calls_before = len(acli.calls)

    _sweep(rig)

    state = rig.launches.get(rig.result["launch_id"])["follow_through"]
    assert state["close"] == "linked"
    assert state["evidence"]["pr_url"] == PR_URL
    linked = _observations(db, "conductor.pr_linked")
    assert len(linked) == 1 and linked[0]["subject_ref"] == f"issue:{ISSUE_ID}"
    fact = json.loads(linked[0]["fact_json"])
    assert fact["pr_url"] == PR_URL and fact["merged_sha"] == MERGE_COMMIT
    assert fact["title"] == "PAY-418 Reconciliation job slow on month-end data"
    assert _links(db) == [(f"issue:{ISSUE_ID}", PR_URL, "merged_pr")]
    # Nothing on the tracker: no acli call at all after the hand-off, and
    # every gh call was a read.
    assert acli.calls[calls_before:] == []
    assert all(c[:3] == ["gh", "pr", "list"] for c in rig.gh.calls), rig.gh.calls
    # A second sweep links nothing again.
    _sweep(rig)
    assert len(_observations(db, "conductor.pr_linked")) == 1 and len(_links(db)) == 1


def test_issue_that_left_its_watch_before_the_merge_is_still_linked(tmp_path, db, monkeypatch) -> None:
    """Resolved in Jira and out of the Watch's query before the PR merged:
    the Watch's next evaluation drops it; the PR is still linked by its id."""
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import fetch_watch_snapshot

    acli = _jira_watch(db)
    rig = _launch(tmp_path, db, monkeypatch, ("issue", ISSUE_ID), acli=acli)
    acli.resolved = True
    adapter = JiraProviderAdapter(db=db, runner=acli)
    WatchService(
        db, snapshot_fetcher=lambda principal, **kw: fetch_watch_snapshot(principal, jira_adapter=adapter, **kw),
    ).evaluate_once(OWNER, WATCH)
    from holdspeak.services.agent_issue import read_issue

    assert read_issue(db, ISSUE_ID) is None, "the snapshot no longer holds the issue"
    rig.gh.prs = [_pr(rig.branch, rig.head)]

    _sweep(rig)

    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["close"] == "linked"
    assert _links(db) == [(f"issue:{ISSUE_ID}", PR_URL, "merged_pr")]
    fact = json.loads(_observations(db, "conductor.pr_linked")[0]["fact_json"])
    assert fact["title"] == f"issue:{ISSUE_ID}"


def test_secure_issue_close_waits_for_the_owner_confirm(tmp_path, db, monkeypatch) -> None:
    acli = _jira_watch(db)
    rig = _launch(tmp_path, db, monkeypatch, ("issue", ISSUE_ID), mode="safe", acli=acli)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    try:
        _sweep(rig)
        assert _observations(db, "conductor.pr_linked") == [], "Secure links nothing before the owner confirms"
        with db._connection() as conn:
            confirm_id, task, owner = conn.execute(
                "SELECT id, task, owner FROM action_items WHERE source_ref = ?",
                (f"agent_launch:{rig.result['launch_id']}",),
            ).fetchone()
        assert task == "Merged: confirm close: PAY-418 Reconciliation job slow on month-end data (PR #7)"
        assert owner == "me"
        FollowThroughService(db).complete(OWNER, confirm_id, "done")
        _sweep(rig)
        assert rig.launches.get(rig.result["launch_id"])["follow_through"]["close"] == "linked"
        assert len(_observations(db, "conductor.pr_linked")) == 1
    finally:
        rig.tmux.ended = True


# ── 2. Every origin has a close ─────────────────────────────────────


@pytest.mark.parametrize("item,title", [
    (("note", "n1"), "Login notes"),
    (("meeting", "m1"), "Planning sync"),
    (("artifact", "art1"), "Sync summary"),
])
def test_note_meeting_and_artifact_get_the_pr_linked_in_their_room(tmp_path, db, monkeypatch, item, title) -> None:
    rig = _launch(tmp_path, db, monkeypatch, item)
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    state = rig.launches.get(rig.result["launch_id"])["follow_through"]
    assert state["close"] == "linked", state
    ref = f"{item[0]}:{item[1]}"
    assert _links(db) == [(ref, PR_URL, "merged_pr")]
    linked = _observations(db, "conductor.pr_linked")
    assert [o["subject_ref"] for o in linked] == [ref]
    _delta, updates = _updates(db)
    assert f"Merged: PR #7 for {title}" in _progress(updates.draft_update(OWNER, PROJECT)["body_md"])


def test_project_item_takes_its_done_transition(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch, ("project_item", "pi1"))
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["close"] == "closed"
    assert db.projects.get_project_item("pi1")["lifecycle"] == "mitigated", "a risk the PR fixed is mitigated"
    assert _links(db) == [("project_item:pi1", PR_URL, "merged_pr")]


def test_a_signal_is_linked_not_transitioned(tmp_path, db, monkeypatch) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO project_items (id, project_id, item_type, title, lifecycle) "
            "VALUES ('sig1', ?, 'signal', 'Login errors rise', 'active')", (PROJECT,),
        )
    rig = _launch(tmp_path, db, monkeypatch, ("project_item", "sig1"))
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    assert rig.launches.get(rig.result["launch_id"])["follow_through"]["close"] == "linked"
    assert db.projects.get_project_item("sig1")["lifecycle"] == "active"


# ── 3. The confirm item is the owner's ──────────────────────────────


def test_secure_confirm_item_is_owned_and_counted_in_needs_you(tmp_path, db, monkeypatch) -> None:
    from holdspeak.services.needs_you_membership import door_items, owner_names

    rig = _launch(tmp_path, db, monkeypatch, ("action", "ai_1"), mode="safe")
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    try:
        _sweep(rig)
        board = FollowThroughService(db).board(OWNER)
        card = next(c for c in board.now if c.text.startswith("Merged: confirm close"))
        rows = door_items({"now": [asdict(card)]}, set(), datetime.now().astimezone())
        assert rows[0]["why"] == "DUE TODAY" and rows[0]["owner"] == "me"
        assert "me" in owner_names(), "the owner name the needs-you rule reads as his own"
        assert not any(c.text.startswith("Merged: confirm close") for c in board.unassigned)
    finally:
        rig.tmux.ended = True


# ── 4. A removed worktree leaves the registry ──────────────────────


def test_removed_worktree_is_unregistered_with_a_receipt(tmp_path, db, monkeypatch) -> None:
    receipts: list[dict[str, Any]] = []
    rig = _launch(tmp_path, db, monkeypatch, ("action", "ai_1"), audit=lambda **kw: receipts.append(kw) or 1)
    worktree_id = rig.launches.get(rig.result["launch_id"])["worktree_id"]
    assert any(wt.worktree_id == worktree_id for wt in rig.registry.get(rig.source.source_id).worktrees)
    rig.gh.prs = [_pr(rig.branch, rig.head)]

    _sweep(rig)

    state = rig.launches.get(rig.result["launch_id"])["follow_through"]
    assert state["cleanup"]["worktree"] == "worktree_removed"
    assert state["cleanup"]["registry"] == "unregistered" and state["done"] is True
    fresh = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
    source = fresh.get(rig.source.source_id)
    assert [wt.worktree_id for wt in source.worktrees] == [source.worktrees[0].worktree_id], "only the clone stays"
    assert worktree_id not in [wt.worktree_id for wt in source.worktrees]
    assert any(r.get("outcome") == "worktree_unregistered" and worktree_id in r["text"] for r in receipts), receipts


def test_kept_worktree_stays_registered(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch, ("action", "ai_1"))
    (rig.worktree / "wip.txt").write_text("not committed\n", encoding="utf-8")
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    try:
        _sweep(rig)
        state = rig.launches.get(rig.result["launch_id"])["follow_through"]
        assert state["cleanup"]["worktree"] == "worktree_dirty"
        assert "registry" not in state["cleanup"]
        worktree_id = rig.launches.get(rig.result["launch_id"])["worktree_id"]
        fresh = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
        assert worktree_id in [wt.worktree_id for wt in fresh.get(rig.source.source_id).worktrees]
    finally:
        rig.tmux.ended = True


# ── 5. Every merge reaches the weekly update ───────────────────────


def _room_pr_watch(db) -> None:
    from holdspeak.services.reaction_service import ReactionService

    ReactionService(db).create_watch(
        OWNER, connector_id="gh", query_kind="pull_requests", name="PR watch",
        query={"repository": "acme/railsproj", "state": "open"}, watch_id="watch-r4-prs",
    )
    db.automations.update_watch_spec("watch-r4-prs", project_id=PROJECT, revision=1)


def _merged_only_rig(tmp_path, db):
    """No agent launch at all: a Room with an open-only PR Watch."""
    from holdspeak.delivery.factory_launch import LaunchLedger

    _room_pr_watch(db)
    gh = FakeGh()
    gh.prs = [dict(_pr("feature/bump", "c" * 40), number=51, title="Bump the ledger schema",
                   url="https://github.com/acme/railsproj/pull/51")]
    registry = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
    observer = FollowThroughObserver(
        db, ledger=LaunchLedger(tmp_path / "launches.json"), registry=registry,
        receipts=PrReceiptsService(registry, runner=gh, gh_available=lambda: True),
        attempts=WorkAttemptService(db.work_attempts), clock=lambda: NOON,
        gh_runner=lambda argv, **_kw: gh(argv),
    )
    return SimpleNamespace(db=db, gh=gh, observer=observer)


def test_merge_no_agent_made_is_in_the_weekly_update(tmp_path, db) -> None:
    rig = _merged_only_rig(tmp_path, db)

    receipt = _sweep(rig)

    assert receipt["merged_prs"]["repositories"] == [
        {"repository": "acme/railsproj", "state": "live", "merged": 1, "recorded": 1},
    ]
    call = rig.gh.calls[0]
    assert call[:3] == ["gh", "pr", "list"] and call[call.index("--state") + 1] == "merged"
    assert call[call.index("--search") + 1] == "merged:>=2026-09-28", "bounded to the last 8 days"
    assert int(call[call.index("--limit") + 1]) == 30
    _delta, updates = _updates(db)
    draft = updates.draft_update(OWNER, PROJECT)
    assert "Merged: Bump the ledger schema (PR #51)" in _progress(draft["body_md"])
    assert json.loads(draft["source_manifest_json"])["closure_keys"] == ["https://github.com/acme/railsproj/pull/51"]
    # Read again: nothing new is recorded; the update keeps one line.
    assert _sweep(rig)["merged_prs"]["recorded"] == 0
    assert updates.draft_update(OWNER, PROJECT)["body_md"].count("PR #51") == 1


def test_the_setting_turns_the_merged_read_off(tmp_path, db) -> None:
    rig = _merged_only_rig(tmp_path, db)
    heartbeat = HeartbeatService(db)
    assert heartbeat.get_settings()["report_merged_prs"] is True, "ON by default"
    heartbeat.update_settings({"report_merged_prs": False})
    assert HeartbeatService(db).get_settings()["report_merged_prs"] is False

    receipt = _sweep(rig)

    assert "merged_prs" not in receipt and rig.gh.calls == []


def test_agent_pr_merge_is_one_line_with_k4s_closure(tmp_path, db, monkeypatch) -> None:
    """The merged-only read sees the agent's own PR too: K4's closure and
    the merged observation share the key (the PR URL), so one line."""
    rig = _launch(tmp_path, db, monkeypatch, ("action", "ai_1"))
    _room_pr_watch(db)
    rig.gh.prs = [_pr(rig.branch, rig.head)]

    receipt = _sweep(rig)

    assert receipt["merged_prs"]["recorded"] == 1
    _delta, updates = _updates(db)
    body = updates.draft_update(OWNER, PROJECT)["body_md"]
    assert "Closed: Fix the login timeout (PR #7) -- merged" in _progress(body)
    assert body.count("PR #7") == 1, body


# ── R4 round 2: GitHub issue rows (a read-only GitHub issues Watch) ──

GH_WATCH = "watch-r4-gh-issues"
GH_ISSUE_ID = f"{GH_WATCH}.418"
GH_BODY = "Month-end reconciliation scans every row twice."


class FakeGhIssues:
    """``gh`` at its process boundary: `gh issue list` and `gh issue view`."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.issues = [{
            "number": 418, "title": "Reconciliation job slow on month-end data",
            "url": "https://github.com/acme/railsproj/issues/418", "state": "OPEN",
            "labels": [{"name": "ledger"}, {"name": "performance"}],
            "createdAt": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }]

    def __call__(self, argv, **_kw):
        self.calls.append(list(argv))
        if argv[1:3] == ["issue", "list"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.issues), stderr="")
        if argv[1:3] == ["issue", "view"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"body": GH_BODY}), stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr=f"unexpected {argv}")


def _gh_issue_watch(db) -> tuple[FakeGhIssues, Any]:
    """A real Room GitHub issues Watch, baselined by WatchService through the
    real GitHubWatchSource (gh faked at its process boundary)."""
    from holdspeak.services.reaction_service import ReactionService
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.watch_sources import fetch_watch_snapshot

    gh = FakeGhIssues()
    ReactionService(db).create_watch(
        OWNER, connector_id="gh", query_kind="issues", name="Open issues",
        query={"repository": "acme/railsproj", "state": "open"}, watch_id=GH_WATCH,
    )
    db.automations.update_watch_spec(GH_WATCH, project_id=PROJECT, revision=1)
    watches = WatchService(
        db, snapshot_fetcher=lambda principal, **kw: fetch_watch_snapshot(principal, github_runner=gh, **kw),
    )
    watches.baseline_watch(OWNER, GH_WATCH)
    return gh, watches


def test_github_issues_watch_reads_gh_issue_list_and_makes_room_issue_rows(db) -> None:
    from holdspeak.services.project_service import ProjectService

    gh, _watches = _gh_issue_watch(db)
    assert gh.calls[0][:3] == ["gh", "issue", "list"]
    assert gh.calls[0][gh.calls[0].index("--state") + 1] == "open"
    assert "assignees" not in gh.calls[0][gh.calls[0].index("--json") + 1], "no People data is read"
    rows = [r for r in ProjectService(db)._read_room_needs_you(PROJECT)["items"] if r.get("kind") == "issue"]
    assert len(rows) == 1, rows
    row = rows[0]
    assert (row["source"], row["title"], row["why"]) == (
        "github", "#418 Reconciliation job slow on month-end data", "ISSUE · OPEN 2 D",
    )
    assert (row["watchId"], row["entity_id"]) == (GH_WATCH, "418")
    assert parse_item_ref({"kind": "issue", "id": f"{row['watchId']}.{row['entity_id']}"}) == ("issue", GH_ISSUE_ID)


def test_github_issue_rows_stay_out_of_the_desk_needs_you_count(db) -> None:
    from holdspeak.services.needs_you_aggregate import LastKnownStore, build_aggregate
    from holdspeak.services.project_service import ProjectService

    _gh_issue_watch(db)
    service = ProjectService(db)
    aggregate = build_aggregate(
        list_projects=service.list_projects, room=service.room, principal=OWNER, last_known=LastKnownStore(),
    )
    assert not any(str(i.get("title", "")).startswith("#418") for i in aggregate.get("items", []))


def test_a_new_github_issue_is_an_issue_transition_not_a_pr(db) -> None:
    gh, watches = _gh_issue_watch(db)
    gh.issues.append(dict(gh.issues[0], number=421, title="Add the ledger freeze flag",
                          url="https://github.com/acme/railsproj/issues/421"))
    evaluated = watches.evaluate_once(OWNER, GH_WATCH)
    assert evaluated["state"] == "completed"
    facts = [json.loads(o["fact_json"]) for o in _observations(db, "watch.transition")]
    assert [f["event_type"] for f in facts] == ["github.issue.opened"]


def test_github_issue_brief_reads_its_body_with_gh_issue_view(db) -> None:
    gh, _watches = _gh_issue_watch(db)
    brief = compose_agent_brief(
        db, {"kind": "issue", "id": GH_ISSUE_ID}, control_mode="yolo",
        principal=OWNER, issue_reads={"gh_runner": gh},
    )
    assert 'issue:watch-r4-gh-issues.418 "#418 Reconciliation job slow on month-end data"' in brief["text"]
    assert GH_BODY in brief["text"] and "Labels: ledger, performance" in brief["text"]
    assert "URL: https://github.com/acme/railsproj/issues/418" in brief["text"]
    assert brief["project_id"] == PROJECT
    assert ["gh", "issue", "view", "418", "--repo", "acme/railsproj", "--json", "body,labels,title,url"] in gh.calls


def test_hand_a_github_issue_then_link_its_merged_pr(tmp_path, db, monkeypatch) -> None:
    gh_issues, _watches = _gh_issue_watch(db)
    rig = _rig(tmp_path, db, monkeypatch, item=("issue", GH_ISSUE_ID))
    rig.hand.issue_reads = {"gh_runner": gh_issues}
    _git(rig.repo, "remote", "add", "origin", "https://github.com/acme/railsproj.git")
    result = rig.hand.hand(OWNER, "issue", GH_ISSUE_ID)
    assert result["status"] == "launched", result
    assert result["origin_ref"] == {"kind": "issue", "id": GH_ISSUE_ID}
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    assert GH_BODY in "\n".join(text for _pane, text in rig.typed)
    (rig.worktree / "fix.txt").write_text("batch = 500\n", encoding="utf-8")
    _git(rig.worktree, "add", "-A")
    _git(rig.worktree, "commit", "-m", "Batch the reads")
    rig.gh = FakeGh()
    rig.observer = _observer(rig, rig.gh)
    rig.gh.prs = [_pr(result["worktree"]["branch"], _git(rig.worktree, "rev-parse", "HEAD"))]
    issue_calls = len(gh_issues.calls)

    _sweep(rig)

    assert rig.launches.get(result["launch_id"])["follow_through"]["close"] == "linked"
    assert _links(db) == [(f"issue:{GH_ISSUE_ID}", PR_URL, "merged_pr")]
    assert len(gh_issues.calls) == issue_calls, "nothing is asked of, or written to, the issue"
    assert all(c[:3] == ["gh", "pr", "list"] for c in rig.gh.calls), rig.gh.calls


def test_the_door_arms_the_open_issues_watch_with_the_pr_queue(db) -> None:
    from holdspeak.services.project_door_service import ProjectDoorService
    from holdspeak.services.project_service import ProjectService

    created = ProjectDoorService(project_service=ProjectService(db)).create(
        OWNER, "Ship the ledger", [{"provider": "github", "scope": "acme/ledger", "watches": ["open_prs"]}],
    )
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT connector_id, query_kind, query_json FROM connector_watches WHERE project_id=? ORDER BY query_kind",
            (created["projectId"],),
        ).fetchall()
    kinds = [(r[0], r[1]) for r in rows]
    assert kinds == [("gh", "issues"), ("gh", "pull_requests")], kinds
    issues_query = json.loads(rows[0][2])
    assert issues_query["repository"] == "acme/ledger" and issues_query["state"] == "open"


# ── R4 round 2: no test reaches the real gh/acli ────────────────────


def test_the_default_runner_refuses_a_real_gh_in_tests(tmp_path, monkeypatch) -> None:
    from holdspeak.cli_guard import RealCliRefusedInTests, refuse_real_cli_in_tests

    assert __import__("os").environ.get("HOLDSPEAK_TEST_NO_REAL_CLI") == "1", "tests/conftest.py sets it"
    monkeypatch.setattr("shutil.which", lambda name: f"/opt/owner/bin/{name}")
    with pytest.raises(RealCliRefusedInTests, match="real_cli_refused_in_tests"):
        refuse_real_cli_in_tests(["gh", "pr", "list"])
    with pytest.raises(RealCliRefusedInTests):
        refuse_real_cli_in_tests(["acli", "jira", "auth", "status"])
    refuse_real_cli_in_tests(["git", "status"])  # other programs are not guarded
    stub = tmp_path / "gh"
    stub.write_text("#!/bin/sh\nexit 0\n")
    refuse_real_cli_in_tests([str(stub), "pr", "list"])  # a test's own stub runs
    monkeypatch.setenv("HOLDSPEAK_TEST_NO_REAL_CLI", "0")
    refuse_real_cli_in_tests(["gh", "pr", "list"])  # production: no guard


def test_the_merged_read_without_a_runner_never_runs_the_real_gh(tmp_path, db, monkeypatch) -> None:
    from holdspeak.delivery.factory_launch import LaunchLedger

    _room_pr_watch(db)
    monkeypatch.setattr("shutil.which", lambda name: f"/opt/owner/bin/{name}")
    ran: list = []
    monkeypatch.setattr("subprocess.run", lambda *a, **k: ran.append(a) or SimpleNamespace(returncode=0, stdout="[]", stderr=""))
    registry = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
    observer = FollowThroughObserver(
        db, ledger=LaunchLedger(tmp_path / "launches.json"), registry=registry,
        receipts=PrReceiptsService(registry, gh_available=lambda: True),
        attempts=WorkAttemptService(db.work_attempts), clock=lambda: NOON,
    )
    receipt = observer.sweep_merged(SWEEPER)
    assert receipt["repositories"] == [{"repository": "acme/railsproj", "state": "real_cli_refused_in_tests"}]
    assert ran == []


# ── R1's real walk: hand -> merge -> cleanup -> hand again ──────────


def test_the_same_item_can_be_handed_again_after_cleanup(tmp_path, db, monkeypatch) -> None:
    rig = _launch(tmp_path, db, monkeypatch, ("action", "ai_1"))
    rig.gh.prs = [_pr(rig.branch, rig.head)]
    _sweep(rig)
    first = rig.launches.get(rig.result["launch_id"])["follow_through"]
    assert first["done"] is True and first["cleanup"]["worktree"] == "worktree_removed"
    assert first["cleanup"]["registry"] == "unregistered"
    assert not rig.worktree.exists()
    # The item is open again (the owner reopened it, or more work came).
    with db._connection() as conn:
        conn.execute("UPDATE action_items SET status='open' WHERE id='ai_1'")

    again = rig.hand.hand(OWNER, "action", "ai_1")

    assert again["status"] == "launched", again
    assert again["launch_id"] != rig.result["launch_id"]
    assert again["origin_ref"] == {"kind": "action", "id": "ai_1"}
    name, branch = again["worktree"]["name"], again["worktree"]["branch"]
    # K4 kept the merged branch hs/action-ai_1: the second hand-off takes round 2.
    assert (name, branch) == ("hs-action-ai_1-2", "hs/action-ai_1-2")
    assert (rig.repo.parent / name / ".git").exists(), "a real new worktree"
    assert _git(rig.repo.parent / name, "rev-parse", "--abbrev-ref", "HEAD") == branch
    rig.tmux.ended = True
