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
from holdspeak.services.channel_contract import render_update, stored_claims
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


PR10_URL = "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/10"
ROW10 = f"Merged: Add the release checklist (PR #10) {PR10_URL}"


def _merge_pr10(rig) -> None:
    """A second merge in the Room's repository, through the Heartbeat's own
    producer (R4's merged-only read)."""
    assert rig.observer._record_merge(PROJECT, REPO, {
        "url": PR10_URL, "number": 10, "title": "Add the release checklist",
        "state": "MERGED", "mergedAt": "2026-10-07T23:10:00Z", "headRefName": "release-checklist",
    })


def _cut(body: str, row: str) -> str:
    out = body.replace(f"- {row}\n", "")
    assert row not in out
    return out


def test_a_row_the_owner_cut_and_published_stays_excluded(tmp_path, db, monkeypatch) -> None:
    """Astra r1 ruling: a row the owner cut from a draft he then published is
    an intentional exclusion. Repeated: a second merge cut again stays out too."""
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        draft = updates.draft_update(OWNER, PROJECT)
        updates.save_update(OWNER, draft["id"], body_md=_cut(draft["body_md"], ROW))
        updates.publish_update(OWNER, draft["id"])
        second = updates.draft_update(OWNER, PROJECT)
        assert "Merged:" not in second["body_md"], "the owner's exclusion holds"

        _merge_pr10(rig)
        third = updates.draft_update(OWNER, PROJECT)
        assert _progress(third["body_md"]).count(ROW10) == 1 and ROW not in third["body_md"]
        updates.save_update(OWNER, third["id"], body_md=_cut(third["body_md"], ROW10))
        updates.publish_update(OWNER, third["id"])
        assert "Merged:" not in updates.draft_update(OWNER, PROJECT)["body_md"]
    finally:
        rig.tmux.ended = True


def test_pr_1_and_pr_10_are_two_rows(tmp_path, db, monkeypatch) -> None:
    """A model draft that wrote only PR #10's row still gets PR #1's: the
    row is matched whole, so ``/pull/1`` is never found inside ``/pull/10``."""
    from holdspeak.services.project_update_service import ProjectUpdateService

    def model(self, principal, det_claims, det_sections, det_body_md, known_names=(), memory=None):
        return (f"## Progress\n\n- {ROW10}\n\n## Decisions\n\nNo decisions.\n", "[]",
                "model:ia_1", "192.168.1.43:8080", "qwen3.8-27b")

    monkeypatch.setattr(ProjectUpdateService, "_draft_with_model", model)
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _merge_pr10(rig)
        _delta, updates = _updates(db)
        draft = updates.draft_update(OWNER, PROJECT, generator="model")
        progress = _progress(draft["body_md"])
        assert progress.count(ROW) == 1 and progress.count(ROW10) == 1
        updates.publish_update(OWNER, draft["id"])
        assert "Merged:" not in updates.draft_update(OWNER, PROJECT)["body_md"]
    finally:
        rig.tmux.ended = True


def test_a_manifest_from_before_the_fix_consumes_nothing(tmp_path, db, monkeypatch) -> None:
    """Astra r1 MISSED: the rehearsal's published model draft froze PR #1's
    key with no row in its body. After the upgrade that manifest (no
    ``closure_lines``) is read as unpublished, so the merge is reported once."""
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        legacy = updates.draft_update(OWNER, PROJECT)
        manifest = json.loads(legacy["source_manifest_json"])
        manifest.pop("closure_lines")
        body = _cut(legacy["body_md"], ROW)
        with db._connection() as conn:
            conn.execute(
                "UPDATE project_updates SET source_manifest_json=?, body_md=? WHERE id=?",
                (json.dumps(manifest), body, legacy["id"]),
            )
        updates.publish_update(OWNER, legacy["id"])
        current = updates.draft_update(OWNER, PROJECT)
        assert _progress(current["body_md"]).count(ROW) == 1
        updates.publish_update(OWNER, current["id"])
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


#: The rehearsal's model answer, as the model returns it (the parser's
#: input): a cited sentence, and three uncited fillers it marks [UNVERIFIED].
MODEL_RAW = json.dumps({"sections": [
    {"key": "progress", "sentences": [
        {"text": "The contributing file was merged into the rehearsal repository.",
         "cited_refs": ["action_item:ai_1"]}]},
    {"key": "risks_blockers", "sentences": [
        {"text": "No risks or blockers in this window.", "cited_refs": []}]},
    {"key": "dependencies", "sentences": [
        {"text": "No dependencies tracked.", "cited_refs": []}]},
    {"key": "next_actions", "sentences": [
        {"text": "Carol ships the ledger cutover on Friday.", "cited_refs": ["action_item:nope"]}]},
]})


def test_unchecked_model_claims_never_leave_the_desk(tmp_path, db, monkeypatch) -> None:
    """Astra r1 ruling (P1): a claim the model could not tie to evidence is
    OMITTED from the sent text, not sent as a fact; an emptied section says
    "Not checked."; the footer counts what stayed on the desk. Real model
    output through the real parser, the publication, Send and Copy."""
    from holdspeak.services import project_update_service as pus
    from holdspeak.services.channel_contract import without_desk_marks

    def model(self, principal, det_claims, det_sections, det_body_md, known_names=(), memory=None):
        refs = frozenset(r for c in det_claims for r in c.refs)
        sections, claims = pus._parse_model_output(MODEL_RAW, refs)
        return (pus._assemble_body(sections), json.dumps([c.to_dict() for c in claims]),
                "model:ia_1", "192.168.1.43:8080", "qwen3.8-27b")

    monkeypatch.setattr(pus.ProjectUpdateService, "_draft_with_model", model)
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        draft = updates.draft_update(OWNER, PROJECT, generator="model")
        assert draft["body_md"].count(pus.UNVERIFIED_MARKER) == 3, draft["body_md"]
        updates.publish_update(OWNER, draft["id"])
        sent = render_update(db, draft["id"]).body_md
        assert sent.startswith("# Railsproj · Update · "), sent
        assert "UNVERIFIED" not in sent
        assert "Carol ships the ledger cutover" not in sent, "an unchecked claim is not sent as fact"
        assert "No dependencies tracked." not in sent
        assert sent.count("Not checked.") == 3
        # PHILO-15 B64 ruling: a cited model sentence is an INFERENCE the
        # owner did not review; it stays on the desk like an unverified one.
        assert sent.rstrip().endswith("4 claims not checked, kept on the desk.")
        assert "The contributing file was merged into the rehearsal repository." not in sent
        assert ROW in sent, "the merge row is a record, not a claim"
        assert "_" not in sent.split("## Source Coverage", 1)[1], "plain words, never a raw code"
        # Copy leaves the desk the same way; the desk keeps every claim.
        stored = db.project_updates.get_update(draft["id"])
        # The Copy route's own call (PHILO-15 B64: with the stored claims).
        copied = without_desk_marks(stored["body_md"], claims=stored_claims(stored))
        assert "UNVERIFIED" not in copied and "Carol ships" not in copied
        assert "Carol ships" in db.project_updates.get_update(draft["id"])["body_md"]
    finally:
        rig.tmux.ended = True


def _model_from(monkeypatch, raw: str) -> None:
    """The model at its boundary: ``raw`` through the REAL parser and assembler."""
    from holdspeak.services import project_update_service as pus

    def model(self, principal, det_claims, det_sections, det_body_md, known_names=(), memory=None):
        refs = frozenset(r for c in det_claims for r in c.refs)
        sections, claims = pus._parse_model_output(raw, refs)
        return (pus._assemble_body(sections), json.dumps([c.to_dict() for c in claims]),
                "model:ia_1", "192.168.1.43:8080", "qwen3.8-27b")

    monkeypatch.setattr(pus.ProjectUpdateService, "_draft_with_model", model)


def test_a_multiline_unchecked_claim_is_omitted_whole(tmp_path, db, monkeypatch) -> None:
    """Astra r2 (P1): an uncited claim with an embedded newline leaves the
    desk with NONE of its lines, through the real parser, Send and Copy."""
    from holdspeak.services.channel_contract import without_desk_marks

    _model_from(monkeypatch, json.dumps({"sections": [
        {"key": "progress", "sentences": [
            {"text": "The contributing file was merged.", "cited_refs": ["action_item:ai_1"]},
            {"text": "Unverified.\nThe rollout is complete.", "cited_refs": []},
        ]},
    ]}))
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        draft = updates.draft_update(OWNER, PROJECT, generator="model")
        assert "The rollout is complete." in draft["body_md"], "the desk keeps the claim"
        updates.publish_update(OWNER, draft["id"])
        sent = render_update(db, draft["id"]).body_md
        stored = db.project_updates.get_update(draft["id"])
        # The Copy route's own call (PHILO-15 B64: with the stored claims).
        copied = without_desk_marks(stored["body_md"], claims=stored_claims(stored))
        for out in (sent, copied):
            assert "The rollout is complete." not in out and "Unverified." not in out, out
            # PHILO-15 B64: the cited sentence is an unreviewed inference.
            assert "The contributing file was merged." not in out
            assert "2 claims not checked, kept on the desk." in out
        # A legacy body (the mark on the first line only) is omitted whole too.
        legacy = "## Progress\n\n- **[UNVERIFIED]** Unverified.\nThe rollout is complete.\n- Kept.\n"
        assert without_desk_marks(legacy) == "## Progress\n\n- Kept.\n\n1 claim not checked, kept on the desk.\n"
    finally:
        rig.tmux.ended = True


ALL_UNCHECKED = json.dumps({"sections": [
    {"key": "progress", "sentences": [{"text": "The rollout is complete.", "cited_refs": []}]},
    {"key": "decisions", "sentences": [{"text": "We ship Friday.", "cited_refs": ["nope"]}]},
]})


def test_nothing_verified_refuses_the_send(db, monkeypatch) -> None:
    """Astra r2 ruling (P2): when omission leaves no substantive content,
    Send refuses NOTHING VERIFIED through the real export path; the stored
    claims are kept."""
    from holdspeak.services.channel_contract import ChannelRefused, render_document

    _model_from(monkeypatch, ALL_UNCHECKED)
    _delta, updates = _updates(db)
    draft = updates.draft_update(OWNER, PROJECT, generator="model")
    updates.publish_update(OWNER, draft["id"])
    with pytest.raises(ChannelRefused) as refused:
        render_document(db, f"project_update:{draft['id']}")
    assert refused.value.code == "nothing_verified"
    assert "NOTHING VERIFIED" in str(refused.value)
    stored = db.project_updates.get_update(draft["id"])["body_md"]
    assert "The rollout is complete." in stored and "We ship Friday." in stored


def test_a_verified_merge_row_keeps_it_sendable(tmp_path, db, monkeypatch) -> None:
    """The same all-unchecked model answer with a merge: the carried merge
    row is a record, so the update is sent (the claims omitted)."""
    _model_from(monkeypatch, ALL_UNCHECKED)
    rig = _merged(tmp_path, db, monkeypatch)
    try:
        _delta, updates = _updates(db)
        draft = updates.draft_update(OWNER, PROJECT, generator="model")
        updates.publish_update(OWNER, draft["id"])
        sent = render_update(db, draft["id"]).body_md
        assert ROW in sent and "The rollout is complete." not in sent
        assert "2 claims not checked, kept on the desk." in sent
    finally:
        rig.tmux.ended = True


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
    # The ceiling stated in the PR: 300 gh pr view an hour per hub.
    assert 3600 // follow_through.POLL_SECONDS * follow_through.POLL_MAX_PRS == 300


def test_more_than_ten_open_prs_are_read_in_round_robin(tmp_path, db) -> None:
    """Astra r1 (P1): with 13 open PRs, no launch waits for the sweep: the
    second poll reads the three the first did not, then the oldest seven."""
    from holdspeak.delivery.attempts import WorkAttemptService
    from holdspeak.delivery.factory_launch import LaunchLedger
    from holdspeak.delivery.follow_through import FollowThroughObserver

    ledger = LaunchLedger(tmp_path / "launches.json")
    for n in range(13):
        url = f"https://github.com/{REPO}/pull/{100 + n}"
        ledger.record({
            "launch_id": f"launch-{n:02d}", "state": "registered", "attempt_id": f"att-{n}",
            "worktree_id": f"wt-{n}", "source_id": "src", "origin_ref": {"kind": "action", "id": f"a{n}"},
            "follow_through": {"pr": {"url": url, "number": 100 + n, "state": "open"}},
        })
    read: list[str] = []

    class Receipts:
        def view_pr(self, source_id, url):
            read.append(url)
            number = int(url.rsplit("/", 1)[1])
            return {"url": url, "number": number, "state": "open", "title": f"PR {number}"}, "live"

    observer = FollowThroughObserver(
        db, ledger=ledger, registry=None, receipts=Receipts(),
        attempts=WorkAttemptService(db.work_attempts), control_mode=lambda: "yolo",
    )
    url = lambda n: f"https://github.com/{REPO}/pull/{n}"  # noqa: E731
    first = observer.poll_open_prs(OWNER)
    assert read == [url(100 + n) for n in range(10)]
    read.clear()
    second = observer.poll_open_prs(OWNER)
    assert len(first["polled"]) == len(second["polled"]) == 10
    assert read[:3] == [url(110), url(111), url(112)], "the three never read go first"
    assert read[3:] == [url(100 + n) for n in range(7)], "then the oldest reads"
    assert ledger.get("launch-12")["follow_through"]["polled_ns"] > 0


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
