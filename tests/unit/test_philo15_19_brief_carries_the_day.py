"""PHILO-15 lane 19: the Brief carries the day (rehearsal 2: B58, B59, B65, B73).

B58: the morning Brief listed "meeting recorded / project added / summary
requested" and missed the day's confirmed decision, the agent launch, its PR,
the merge and the sent update. Each is now a Changed row in plain words, with
the title and the local time, and a ref the face opens.

B59: a hub started after the Brief's hour, with no Brief for the day, makes it
at start (it waited one tick interval, 5 minutes).

B65: a NEW PR of a launch is found by the 2-minute poll (one bounded
``gh pr list --head <branch>``), not only by the 15-minute sweep.

B73: a Brief row carries no JSON, no record id, no digest and no UTC stamp.

Producer-backed: K2's real hand-to-agent launch, the real K4 follow-through
(its poll), the real proposal confirm, the real FollowThroughService close,
the real update publish and the real folder Send through the hub. Only ``gh``
and ``tmux`` are faked, at their process boundary, and the producers' clocks
are set to the rig's launch day.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from holdspeak.delivery import follow_through
from holdspeak.runtime import composition
from holdspeak.services.monday_brief_service import MondayBriefService, _sanitize_detail
from holdspeak.timestamps import parse_stamp
from tests.unit.test_agent_hand import OWNER, PROJECT
from tests.unit.test_conductor_k4_follow_through import (
    _launch,
    _status,
    db,  # noqa: F401  (the fixture)
)
from tests.unit.test_factory_launch import T0
from tests.unit.test_philo15_17_merge_reaches_update import ViewGh

PR_URL = "https://github.com/acme/railsproj/pull/7"
OPENED = T0 + timedelta(minutes=10)
MERGED = T0 + timedelta(minutes=50)
DONE = T0 + timedelta(minutes=55)  # the producers' clock after the merge
BRIEF_NOW = (T0 + timedelta(hours=3)).astimezone()


def _z(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pr(branch: str, head: str, state: str) -> dict[str, Any]:
    merged = state == "MERGED"
    return {
        "number": 7, "title": "Fix the login timeout", "url": PR_URL,
        "headRefName": branch, "baseRefName": "main", "headRefOid": head, "baseRefOid": "",
        "state": state, "isDraft": False, "statusCheckRollup": [], "author": {"login": "agent"},
        "reviewDecision": "", "createdAt": _z(OPENED),
        "mergedAt": _z(MERGED) if merged else None,
        "mergeCommit": {"oid": "f" * 40} if merged else None, "isCrossRepository": False,
        "headRepositoryOwner": {"login": "acme"}, "headRepository": {"name": "railsproj"},
    }


def _rig(tmp_path, db, monkeypatch):
    rig = _launch(tmp_path, db, monkeypatch)
    rig.gh = ViewGh()
    rig.receipts._runner = rig.gh
    return rig


def _hm(stamp: Any) -> str:
    """The local clock time a person reads (the rig's day is the Brief's day)."""
    return parse_stamp(stamp).astimezone().strftime("%H:%M")


def _rows(brief) -> dict[str, Any]:
    return {item.text: item for items in brief.sections.values() for item in items}


_RAW = re.compile(r"[{}\[\]]|\d{4}-\d{2}-\d{2}T|sha256|launch-|prop-|brief-|ai_1|\bm1\b")


def _assert_plain(brief) -> None:
    for items in brief.sections.values():
        for item in items:
            for text in (item.text, item.detail or ""):
                assert not _RAW.search(text), (item.text, item.detail)


# ── B65: the poll finds a NEW PR ─────────────────────────────────────


def test_the_poll_finds_a_new_pr_by_its_branch(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        # No PR yet: the poll lists the branch, finds nothing, keeps nothing.
        receipt = rig.observer.poll_open_prs(OWNER)
        assert receipt["discovered"] == [{"launch_id": launch_id, "gh_state": "live", "prs": 0}]
        assert "found" not in receipt
        argv = rig.gh.calls[-1]
        assert argv[:3] == ["gh", "pr", "list"]
        assert argv[argv.index("--head") + 1] == rig.branch
        assert argv[argv.index("--limit") + 1] == "5"

        # The agent opens its PR: the next poll keeps it (it was the sweep's).
        rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
        receipt = rig.observer.poll_open_prs(OWNER)
        assert receipt["found"] == [launch_id]
        state = rig.launches.get(launch_id)["follow_through"]
        assert state["pr"]["number"] == 7 and state["pr"]["state"] == "open"
        assert state["pr_opened_at"] == _z(OPENED), "gh's own createdAt"

        # From now on it is a known PR: one `gh pr view`, no branch list.
        calls = len(rig.gh.calls)
        rig.gh.prs = [_pr(rig.branch, rig.head, "MERGED")]
        receipt = rig.observer.poll_open_prs(OWNER)
        assert rig.gh.calls[calls][:3] == ["gh", "pr", "view"]
        assert receipt["discovered"] == [] and receipt["closed"], receipt
        assert _status(db, "ai_1") == "done"
    finally:
        rig.tmux.ended = True


def test_the_discovery_is_inside_the_poll_ceiling(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    try:
        monkeypatch.setattr(follow_through, "POLL_MAX_PRS", 0)
        rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
        receipt = rig.observer.poll_open_prs(OWNER)
        assert receipt["discovered"] == [] and rig.gh.calls == []
    finally:
        rig.tmux.ended = True


def test_a_found_pr_announces_one_desk_change(tmp_path, db, monkeypatch) -> None:
    """The ledger is a file: the hub names the found PR itself, so the lane,
    the drawer and Needs re-read within the poll."""
    from holdspeak.services.heartbeat_service import HeartbeatService

    rig = _rig(tmp_path, db, monkeypatch)
    sent: list[Any] = []

    class _Sender:
        broadcast = True

        def _send_desk_changed(self, changes):
            sent.append(list(changes))

    monkeypatch.setattr(composition, "_installed", _Sender())
    try:
        rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
        heartbeat = HeartbeatService(db, follow_through=rig.observer, notifier=lambda *_a, **_k: True)
        receipt = heartbeat.poll_open_prs(OWNER)
        assert receipt["found"] == [rig.result["launch_id"]]
        assert len(sent) == 1, sent
    finally:
        rig.tmux.ended = True


# ── B58 + B73: the Brief carries the day ─────────────────────────────


def _the_day(tmp_path, db, monkeypatch):
    """The rehearsal's day on the rig: a decision confirmed, the agent
    launched on the action, its PR opened and merged, the action done."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    monkeypatch.setattr("holdspeak.db.proposals.utc_now_iso", lambda: _z(T0 + timedelta(minutes=5)))
    monkeypatch.setattr("holdspeak.services.follow_through_service.utc_now_iso", lambda: _z(DONE))
    proposal = db.proposals.create_proposal(
        meeting_id="m1", project_id=PROJECT, kind="decision",
        text="Squash merges only on the rehearsal repository", source_plugin="rehearsal",
    )
    assert ProposalBridgeService(db).confirm_proposal(OWNER, proposal.id)["decision_record_id"]
    rig = _rig(tmp_path, db, monkeypatch)
    rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
    assert rig.observer.poll_open_prs(OWNER)["found"]
    rig.gh.prs = [_pr(rig.branch, rig.head, "MERGED")]
    assert rig.observer.poll_open_prs(OWNER)["closed"]
    assert _status(db, "ai_1") == "done"
    return rig


def test_the_brief_carries_the_decision_the_agent_its_pr_the_merge_and_the_done_action(
    tmp_path, db, monkeypatch,
) -> None:
    rig = _the_day(tmp_path, db, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        brief = MondayBriefService(db, launch_ledger=rig.launches).generate(OWNER, now=BRIEF_NOW)
        rows = _rows(brief)
        wanted = {
            "Decision confirmed: Squash merges only on the rehearsal repository": (
                "meeting:m1", _hm(T0 + timedelta(minutes=5))),
            "Agent launched: Fix the login timeout": (f"launch:{launch_id}", _hm(T0)),
            "PR opened: Fix the login timeout (PR #7)": (f"launch:{launch_id}", _hm(OPENED)),
            "PR merged: Fix the login timeout (PR #7)": (f"launch:{launch_id}", _hm(MERGED)),
            "Action done: Fix the login timeout": ("action_item:ai_1", _hm(DONE)),
        }
        for text, (ref, clock) in wanted.items():
            assert text in rows, (text, sorted(rows))
            item = rows[text]
            assert item.section == "changed"
            assert item.source_ref == ref, (text, item.source_ref)
            assert item.detail and item.detail.endswith(clock), (text, item.detail)
        assert "Claude Code" in rows["Agent launched: Fix the login timeout"].detail
        # Said once: the merge and the close are one row each.
        assert sum(t.startswith("PR merged: ") for t in rows) == 1
        assert not any(t.startswith("Follow-up completed: Fix the login timeout") for t in rows)
        assert "things changed" in brief.headline
        _assert_plain(brief)

        # The owner's Generate later the same day gives the same rows.
        again = MondayBriefService(db, launch_ledger=rig.launches).generate(
            OWNER, now=BRIEF_NOW + timedelta(minutes=7))
        assert set(wanted) <= set(_rows(again))
        assert again.id == brief.id
    finally:
        rig.tmux.ended = True


def test_the_scheduled_brief_carries_the_day_key_free(tmp_path, db, monkeypatch) -> None:
    """The 07:10 Brief runs under the read-only brief-conductor principal
    with no People reads: it says the same day."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.runtime.cadence import BRIEF_PRINCIPAL_IDENTITY

    rig = _the_day(tmp_path, db, monkeypatch)
    try:
        principal = Principal(PrincipalKind.BRIEF_CONDUCTOR, BRIEF_PRINCIPAL_IDENTITY)
        brief = MondayBriefService(db, launch_ledger=rig.launches).generate(
            principal, now=BRIEF_NOW, regenerate=False, people_reads=False)
        texts = set(_rows(brief))
        assert {"Decision confirmed: Squash merges only on the rehearsal repository",
                "PR merged: Fix the login timeout (PR #7)",
                "Action done: Fix the login timeout"} <= texts, sorted(texts)
        _assert_plain(brief)
    finally:
        rig.tmux.ended = True


def test_an_unreadable_launch_ledger_is_a_not_read_row(tmp_path, db) -> None:
    class _Broken:
        def list(self):
            raise OSError("agent_launches.json: permission denied")

    brief = MondayBriefService(db, launch_ledger=_Broken()).generate(OWNER)
    waiting = {item.text: item for item in brief.sections["waiting"]}
    assert "NOT READ · Agents" in waiting, sorted(waiting)
    assert "permission denied" in (waiting["NOT READ · Agents"].detail or "")
    assert "source not read" in brief.headline


# ── B73: plain words ─────────────────────────────────────────────────


def test_a_recorded_call_detail_is_plain_words_never_json() -> None:
    assert _sanitize_detail('{"meeting_id":"23c66417","expected_selection_hash":"sha256:3e52aa"}') is None
    assert _sanitize_detail('{"path": "/Users/karol/.config/holdspeak/settings.json"}') is None
    assert _sanitize_detail("{}") is None
    assert _sanitize_detail('{"verb": "done", "card_id": "ai_1"}') == "verb done"


def test_a_summary_request_row_reads_its_title_and_local_time(tmp_path, db) -> None:
    import json
    import uuid

    stamp = BRIEF_NOW - timedelta(minutes=30)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events (event_id, timestamp, service, method, principal_kind,
               principal_identity, args_summary, result_summary, error, error_code, duration_ms,
               correlation_id, is_async) VALUES (?, ?, 'MeetingIntelService', 'run_intelligence',
               'owner', 'karol', ?, '{"state":"queued"}', NULL, NULL, 3, '', 0)""",
            (str(uuid.uuid4()), stamp.timestamp(),
             json.dumps({"meeting_id": "m1", "expected_selection_hash": "sha256:3e52aa"})),
        )
    brief = MondayBriefService(db, launch_ledger=_NoLaunches()).generate(OWNER, now=BRIEF_NOW)
    row = _rows(brief)["Summary requested: Planning sync"]
    assert row.detail == stamp.strftime("%H:%M")
    _assert_plain(brief)


class _NoLaunches:
    def list(self):
        return []


# ── B58: the update he sent, through the hub ─────────────────────────


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)
    monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", tmp_path / "launches.json")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _philo10_send import _boot

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_the_sent_update_is_a_brief_row_that_opens_its_room(hub) -> None:
    from _philo10_send import room, send, send_body

    pid, update = room(hub, name="Rehearsal repo hygiene")
    resp = send(hub, send_body(hub, "inline", update, "holdspeak-folder", "k-b58"))
    assert resp.status_code == 200, resp.text
    brief = hub.client.post("/api/brief/generate").json()
    rows = {i["text"]: i for items in brief["sections"].values() for i in items}
    row = rows.get("Update sent: Rehearsal repo hygiene")
    assert row is not None, sorted(rows)
    assert row["source_ref"] == f"project:{pid}"
    assert re.fullmatch(r"HoldSpeak folder · \d{2}:\d{2}", row["detail"]), row["detail"]
    # One row per update: sent, not also "published".
    assert "Update published: Rehearsal repo hygiene" not in rows


# ── B59: the first tick at start ─────────────────────────────────────


def _runtime(stop_after_start: bool = True):
    import threading

    from holdspeak.config import Config
    from holdspeak.runtime.cadence import CadenceMixin

    class Runtime(CadenceMixin):
        def __init__(self) -> None:
            self.config = Config()
            self.runtime_stop_event = threading.Event()
            self.ticks = 0

        def _cadence_tick_once(self) -> None:
            self.ticks += 1
            self._cadence_tick_body()

        def _cadence_service(self):  # the loop job is off by default
            raise AssertionError("the loop job is off")

    runtime = Runtime()
    if stop_after_start:
        runtime.runtime_stop_event.set()
    return runtime


def _briefs(db) -> int:
    with db._connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM monday_briefs").fetchone()[0]


def test_a_hub_started_at_0705_makes_the_days_brief_at_start(tmp_path) -> None:
    from holdspeak.db import Database

    db = Database(tmp_path / "hub.db")
    runtime = _runtime()
    with patch("holdspeak.db.get_database", return_value=db), patch(
        "holdspeak.runtime.cadence.local_now", return_value=datetime(2026, 10, 8, 7, 5)
    ):
        runtime._cadence_loop()  # the stop event is set: only the start runs
        assert runtime.ticks == 1 and _briefs(db) == 1
        # The day's Brief exists: the next start makes no tick.
        again = _runtime()
        again._cadence_loop()
        assert again.ticks == 0 and _briefs(db) == 1


def test_a_hub_started_before_the_briefs_hour_waits(tmp_path) -> None:
    from holdspeak.db import Database

    db = Database(tmp_path / "hub.db")
    runtime = _runtime()
    with patch("holdspeak.db.get_database", return_value=db), patch(
        "holdspeak.runtime.cadence.local_now", return_value=datetime(2026, 10, 8, 5, 30)
    ):
        runtime._cadence_loop()
    assert runtime.ticks == 0 and _briefs(db) == 0
