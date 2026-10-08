"""PHILO-15 lane 17: a merged PR reaches the PUBLISHED update once, within
two minutes, by its own title (rehearsal 1 part B: B50, B51, B52, B53).

B52 ruling: a merged PR is reported in the update that is actually
published, once, as ``Merged: <PR title> (PR #n) <link>``. A draft that is
discarded or superseded does not consume the watermark, and neither does a
published update whose body does not carry the row.

B51 ruling: while a launch has an open PR, the hub reads that PR every 2
minutes (one ``gh pr view`` per PR); a merge closes the item at once.

Producer-backed: K2's real hand-to-agent launch, the real K4 follow-through,
the real ``commitment.completed`` receipt and the real update service. Only
``gh`` and ``tmux`` are faked, at their process boundary. The PR is the
rehearsal's real PR #1, as ``gh pr view`` read it on 2026-10-07 (below).
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.delivery import follow_through
from holdspeak.services.agent_flights import agent_flights
from holdspeak.services.channel_contract import render_update
from tests.unit.test_agent_hand import OWNER, PROJECT
from tests.unit.test_conductor_k4_follow_through import (
    FakeGh,
    _completed,
    _git,
    _launch,
    _progress,
    _status,
    _sweep,
    _updates,
    db,  # noqa: F401  (the fixture)
)

#: ``gh pr view https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/1
#: --json number,title,url,state,mergedAt,headRefName``, read once on
#: 2026-10-07 (and docs/internal/philo/phase-15/rehearsal-1b/pr1.json).
REAL_PR1 = {
    "headRefName": "hs/action-action_1ff5227ebc101ddbe1d827ba",
    "mergedAt": "2026-10-07T22:48:40Z",
    "number": 1,
    "state": "MERGED",
    "title": "Add CONTRIBUTING.md with the three pull request rules",
    "url": "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/1",
}
REPO = "karolswdev/holdspeak-dayone-rehearsal-1558"
ROW = (
    "Merged: Add CONTRIBUTING.md with the three pull request rules (PR #1) "
    "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/1"
)


class ViewGh(FakeGh):
    """``gh pr list`` as K4's fake; ``gh pr view <url>`` answers that PR."""

    def __call__(self, argv, cwd=None):
        if argv[:3] == ["gh", "pr", "view"]:
            self.calls.append(list(argv))
            row = next((p for p in self.prs if p["url"] == argv[3]), None)
            if row is None:
                return SimpleNamespace(returncode=1, stdout="", stderr="no pull requests found")
            return SimpleNamespace(returncode=0, stdout=json.dumps(row), stderr="")
        return super().__call__(argv, cwd)


def _real_pr(branch: str, head: str, state: str) -> dict[str, Any]:
    """The real PR #1, on the rig's branch (the agent's worktree here)."""
    merged = state == "MERGED"
    return {
        "number": REAL_PR1["number"], "title": REAL_PR1["title"], "url": REAL_PR1["url"],
        "headRefName": branch, "baseRefName": "main", "headRefOid": head, "baseRefOid": "",
        "state": state, "isDraft": False, "statusCheckRollup": [], "author": {"login": "agent"},
        "reviewDecision": "", "mergedAt": REAL_PR1["mergedAt"] if merged else None,
        "mergeCommit": {"oid": "f" * 40} if merged else None, "isCrossRepository": False,
        "headRepositoryOwner": {"login": "karolswdev"},
        "headRepository": {"name": "holdspeak-dayone-rehearsal-1558"},
    }


def _rehearsal_launch(tmp_path, db, monkeypatch):
    rig = _launch(tmp_path, db, monkeypatch)
    _git(rig.repo, "remote", "set-url", "origin", f"https://github.com/{REPO}.git")
    gh = ViewGh()
    rig.gh = gh
    rig.receipts._runner = gh
    return rig


def _merged(tmp_path, db, monkeypatch):
    """The agent's PR opens (one sweep keeps it), then merges and is read."""
    rig = _rehearsal_launch(tmp_path, db, monkeypatch)
    rig.gh.prs = [_real_pr(rig.branch, rig.head, "OPEN")]
    _sweep(rig)
    rig.gh.prs = [_real_pr(rig.branch, rig.head, "MERGED")]
    receipt = rig.observer.poll_open_prs(OWNER)
    assert receipt["closed"], receipt
    return rig


def _fake_model(monkeypatch) -> None:
    """The model at its boundary: the rehearsal's prose, which named the
    merge in its own words and dropped the row (B52)."""
    from holdspeak.services.project_update_service import ProjectUpdateService

    prose = (
        "## Progress\n\n- The contributing file with the three rules was merged into the "
        "rehearsal repository.\n\n## Decisions\n\nNo decisions.\n"
    )

    def model(self, principal, det_claims, det_sections, det_body_md, known_names=(), memory=None):
        return prose, "[]", "model:ia_69187bba560b4ce1", "192.168.1.43:8080", "qwen3.8-27b"

    monkeypatch.setattr(ProjectUpdateService, "_draft_with_model", model)


# ── B52: the row, by the PR's own title, with its link ──────────────


def test_the_receipt_carries_the_prs_title_and_number(tmp_path, db, monkeypatch) -> None:
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        evidence = _completed(db)[0]["facts"]["evidence"]
        assert evidence["pr_title"] == REAL_PR1["title"]
        assert evidence["pr_number"] == "1"
        assert evidence["pr_url"] == REAL_PR1["url"]
        # B50: the flight (the lane's card, the drawer, the Room receipt)
        # names the PR by its own title from the same gh row.
        flight = agent_flights(db, [], ledger=rig.launches)[0]
        assert flight["state"] == "merged"
        assert flight["pr"]["title"] == REAL_PR1["title"]
        assert flight["title"] == "Fix the login timeout", "the item keeps its own title"
    finally:
        rig.tmux.ended = True


def test_model_draft_discarded_deterministic_published_reports_once(tmp_path, db, monkeypatch) -> None:
    """The rehearsal's order: merge -> a model draft -> a deterministic
    draft supersedes it -> publish. The row is in what was published; the
    next update does not repeat it."""
    _fake_model(monkeypatch)
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        model = updates.draft_update(OWNER, PROJECT, generator="model")
        assert model["generator"].startswith("model:")
        published = updates.draft_update(OWNER, PROJECT)  # supersedes the model draft
        assert db.project_updates.get_update(model["id"])["lifecycle"] == "superseded"
        assert published["id"] != model["id"]
        updates.publish_update(OWNER, published["id"])
        row = db.project_updates.get_update(published["id"])
        assert _progress(row["body_md"]).count(ROW) == 1
        nxt = updates.draft_update(OWNER, PROJECT)
        assert "Merged:" not in nxt["body_md"], "a published row is not repeated"
    finally:
        rig.tmux.ended = True


def test_a_model_draft_carries_the_row_word_for_word(tmp_path, db, monkeypatch) -> None:
    """B52: the model's prose dropped the row; the draft carries it, with
    its claim, so publishing the model draft reports the merge."""
    _fake_model(monkeypatch)
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        draft = updates.draft_update(OWNER, PROJECT, generator="model")
        assert draft["generator"].startswith("model:")
        assert ROW in _progress(draft["body_md"])
        assert "was merged into the rehearsal repository" in draft["body_md"], "the prose stays"
        claims = json.loads(draft["claims_json"])
        assert [c["text"] for c in claims] == [ROW]
        updates.publish_update(OWNER, draft["id"])
        assert "Merged:" not in updates.draft_update(OWNER, PROJECT)["body_md"]
    finally:
        rig.tmux.ended = True


def test_a_published_update_without_the_row_does_not_consume_it(tmp_path, db, monkeypatch) -> None:
    """The owner cut the row before he published: that update did not
    report the merge, so the next one does (once)."""
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        draft = updates.draft_update(OWNER, PROJECT)
        cut = draft["body_md"].replace(f"- {ROW}\n", "")
        assert ROW not in cut
        updates.save_update(OWNER, draft["id"], body_md=cut)
        updates.publish_update(OWNER, draft["id"])
        second = updates.draft_update(OWNER, PROJECT)
        assert _progress(second["body_md"]).count(ROW) == 1
        updates.publish_update(OWNER, second["id"])
        assert "Merged:" not in updates.draft_update(OWNER, PROJECT)["body_md"]
    finally:
        rig.tmux.ended = True


def test_a_draft_never_published_consumes_nothing(tmp_path, db, monkeypatch) -> None:
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        for _ in range(3):
            assert ROW in _progress(updates.draft_update(OWNER, PROJECT)["body_md"])
    finally:
        rig.tmux.ended = True


# ── B53: the sent text carries no desk mark ─────────────────────────


def test_the_sent_document_drops_the_unverified_mark(db) -> None:
    from holdspeak.services.project_update_service import UNVERIFIED_MARKER

    _delta, updates = _updates(db)
    draft = updates.draft_update(OWNER, PROJECT)
    body = draft["body_md"].replace(
        "## Dependencies\n\n", f"## Dependencies\n\n- {UNVERIFIED_MARKER} No dependencies tracked.\n",
    )
    updates.save_update(OWNER, draft["id"], body_md=body)
    updates.publish_update(OWNER, draft["id"])
    sent = render_update(db, draft["id"])
    assert "UNVERIFIED" not in sent.body_md
    assert "- No dependencies tracked." in sent.body_md
    assert sent.title.startswith("Railsproj"), "the document is named by the Project's name"
    # The desk keeps the fact: the stored body still has the mark.
    assert UNVERIFIED_MARKER in db.project_updates.get_update(draft["id"])["body_md"]


# ── B51: the open-PR poll ───────────────────────────────────────────


def test_the_poll_reads_each_open_pr_once_and_closes_on_merge(tmp_path, db, monkeypatch) -> None:
    rig = _rehearsal_launch(tmp_path, db, monkeypatch)
    try:
        rig.gh.prs = [_real_pr(rig.branch, rig.head, "OPEN")]
        _sweep(rig)
        rig.gh.calls.clear()

        open_poll = rig.observer.poll_open_prs(OWNER)
        assert [c[:4] for c in rig.gh.calls] == [["gh", "pr", "view", REAL_PR1["url"]]]
        assert open_poll["polled"][0]["state"] == "open" and not open_poll["closed"]
        assert _status(db, "ai_1") == "open"

        rig.gh.prs = [_real_pr(rig.branch, rig.head, "MERGED")]
        rig.gh.calls.clear()
        merged_poll = rig.observer.poll_open_prs(OWNER)
        assert len(rig.gh.calls) == 1, "one gh pr view per open PR"
        assert merged_poll["closed"] == [{"launch_id": rig.result["launch_id"], "close": "closed"}]
        assert _status(db, "ai_1") == "done"

        rig.gh.calls.clear()
        assert rig.observer.poll_open_prs(OWNER)["polled"] == []
        assert rig.gh.calls == [], "a merged PR is not polled again"
    finally:
        rig.tmux.ended = True


def test_no_open_pr_no_gh(tmp_path, db, monkeypatch) -> None:
    rig = _rehearsal_launch(tmp_path, db, monkeypatch)
    try:
        assert rig.observer.poll_open_prs(OWNER)["polled"] == []  # no PR yet
        assert rig.gh.calls == []
    finally:
        rig.tmux.ended = True


def test_a_stopped_launch_is_not_polled(tmp_path, db, monkeypatch) -> None:
    rig = _rehearsal_launch(tmp_path, db, monkeypatch)
    try:
        rig.gh.prs = [_real_pr(rig.branch, rig.head, "OPEN")]
        _sweep(rig)
        rig.launches.update(rig.result["launch_id"], stopped={"at": "2026-10-07T23:00:00Z"})
        rig.gh.calls.clear()
        assert rig.observer.poll_open_prs(OWNER)["polled"] == []
        assert rig.gh.calls == []
    finally:
        rig.tmux.ended = True


def test_the_poll_is_bounded_and_every_two_minutes() -> None:
    assert follow_through.POLL_SECONDS == 120
    assert follow_through.POLL_MAX_PRS == 10


def test_the_heartbeat_poll_refreshes_needs_you_on_a_close(tmp_path, db, monkeypatch) -> None:
    from holdspeak.services.heartbeat_service import HeartbeatService

    rig = _rehearsal_launch(tmp_path, db, monkeypatch)
    try:
        rig.gh.prs = [_real_pr(rig.branch, rig.head, "OPEN")]
        _sweep(rig)
        rig.gh.prs = [_real_pr(rig.branch, rig.head, "MERGED")]
        refreshed: list = []
        heartbeat = HeartbeatService(db, follow_through=rig.observer)
        monkeypatch.setattr(heartbeat, "refresh_aggregate", lambda *a, **k: refreshed.append(1) or {})
        receipt = heartbeat.poll_open_prs(OWNER)
        assert receipt["kind"] == "pr_poll" and receipt["closed"]
        assert refreshed == [1]
    finally:
        rig.tmux.ended = True


@pytest.mark.parametrize("state", ["CLOSED"])
def test_a_pr_closed_unmerged_ends_the_poll(tmp_path, db, monkeypatch, state) -> None:
    rig = _rehearsal_launch(tmp_path, db, monkeypatch)
    try:
        rig.gh.prs = [_real_pr(rig.branch, rig.head, "OPEN")]
        _sweep(rig)
        rig.gh.prs = [_real_pr(rig.branch, rig.head, state)]
        rig.observer.poll_open_prs(OWNER)
        assert _status(db, "ai_1") == "open", "a closed PR closes nothing"
        rig.gh.calls.clear()
        assert rig.observer.poll_open_prs(OWNER)["polled"] == []
        assert rig.gh.calls == []
    finally:
        rig.tmux.ended = True
