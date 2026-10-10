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
        # ORDER RULING (Astra r1, 2): merge, (sent update), opened PR,
        # confirmed decision, done action, launch, then the rest.
        kinds = [item.text.split(": ", 1)[0] for item in brief.sections["changed"]]
        assert kinds[:5] == ["PR merged", "PR opened", "Decision confirmed", "Action done",
                             "Agent launched"], kinds
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


def test_a_corrupt_launch_file_is_a_not_read_row(tmp_path, db, monkeypatch) -> None:
    """Astra r1 (1): the REAL ledger over a REAL corrupt file, through the
    real service's default ledger: NOT READ · Agents with the reason."""
    from holdspeak.delivery.factory_launch import LaunchLedger, LaunchLedgerNotRead

    bad = tmp_path / "agent_launches.json"
    bad.write_text('{"launches_schema": 1, "launches": [', encoding="utf-8")
    monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", bad)
    assert LaunchLedger().list() == [], "the old read still answers empty"
    with pytest.raises(LaunchLedgerNotRead):
        LaunchLedger().read_all()

    brief = MondayBriefService(db).generate(OWNER)
    waiting = {item.text: item for item in brief.sections["waiting"]}
    assert "NOT READ · Agents" in waiting, sorted(waiting)
    assert waiting["NOT READ · Agents"].detail == "the launch file is not valid JSON"
    assert "source not read" in brief.headline

    # An absent file is no launches, not a NOT READ row.
    bad.unlink()
    brief = MondayBriefService(db).generate(OWNER)
    assert not any(i.text == "NOT READ · Agents" for i in brief.sections["waiting"])


def test_a_corrupt_room_merge_record_is_a_not_read_row(tmp_path, db) -> None:
    """Astra r1 (1): a Room merge record that cannot be read, written through
    the real observation repository, is a NOT READ row, never a silent zero."""
    from holdspeak.delivery.follow_through import MERGED_OBSERVATION

    db.project_observations.insert_observation(
        observation_id="pobs-corrupt-19", project_id=PROJECT, source_id="github:acme/railsproj",
        observation_kind=MERGED_OBSERVATION, subject_ref="https://github.com/acme/railsproj/pull/9",
        source_version="v1", observed_at=_z(BRIEF_NOW - timedelta(minutes=5)),
        fact_json='{"event": "pr_merged", "pr_url": ', content_hash="x",
    )
    brief = MondayBriefService(db, launch_ledger=_NoLaunches()).generate(OWNER, now=BRIEF_NOW)
    waiting = {item.text: item for item in brief.sections["waiting"]}
    assert "NOT READ · Room merges" in waiting, sorted(waiting)
    assert waiting["NOT READ · Room merges"].detail == "1 merge record cannot be read"


# ── Astra r1 (3, 4): the opened stamp backfills; discovery retires ──


def test_a_pr_kept_before_the_stamp_gains_gh_created_at(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        rig.gh.prs = [_pr(rig.branch, rig.head, "OPEN")]
        assert rig.observer.poll_open_prs(OWNER)["found"]
        # The upgrade state: a launch record written before this change kept
        # its PR and has no opened stamp.
        state = dict(rig.launches.get(launch_id)["follow_through"])
        state.pop("pr_opened_at")
        rig.launches.update(launch_id, follow_through=state)
        receipt = rig.observer.poll_open_prs(OWNER)
        assert receipt["polled"] and receipt["discovered"] == []
        assert rig.launches.get(launch_id)["follow_through"]["pr_opened_at"] == _z(OPENED)
    finally:
        rig.tmux.ended = True


def test_discovery_retires_when_the_branch_is_gone(tmp_path, db, monkeypatch) -> None:
    import subprocess

    rig = _rig(tmp_path, db, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        subprocess.run(["git", "-C", str(rig.repo), "worktree", "remove", "--force", str(rig.worktree)],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", str(rig.repo), "branch", "-D", rig.branch],
                       check=True, capture_output=True)
        receipt = rig.observer.poll_open_prs(OWNER)
        assert receipt["retired"] == [launch_id]
        follow = rig.launches.get(launch_id)["follow_through"]
        assert (follow["discovery"], follow["discovery_reason"]) == ("retired", "branch_gone")
        calls = len(rig.gh.calls)
        assert rig.observer.poll_open_prs(OWNER)["discovered"] == []
        assert len(rig.gh.calls) == calls, "a retired launch reads no gh"
    finally:
        rig.tmux.ended = True


def test_a_working_agent_with_no_pr_is_not_retired(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    try:
        for _ in range(3):
            assert "retired" not in rig.observer.poll_open_prs(OWNER)
        assert len(rig.gh.calls) == 3, "one branch list per poll while the branch exists"
    finally:
        rig.tmux.ended = True


def test_a_stopped_or_done_launch_is_not_discovered(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    try:
        launch_id = rig.result["launch_id"]
        rig.launches.update(launch_id, stopped={"at": "2026-10-07T23:00:00Z"})
        assert rig.observer.poll_open_prs(OWNER)["discovered"] == []
        rig.launches.update(launch_id, stopped=None, follow_through={"done": True})
        assert rig.observer.poll_open_prs(OWNER)["discovered"] == []
        assert rig.gh.calls == []
    finally:
        rig.tmux.ended = True


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
    # Astra r1 (2, 6): the sent update leads the recorded/added rows; the
    # project row carries its time.
    changed = [i["text"] for i in brief["sections"]["changed"]]
    assert changed.index("Update sent: Rehearsal repo hygiene") < changed.index(
        "Project added: Rehearsal repo hygiene"), changed
    assert re.fullmatch(r"\d{2}:\d{2}", rows["Project added: Rehearsal repo hygiene"]["detail"])


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


# ── Astra r1 (5): the REAL next-morning transition, through the cadence ──


@pytest.fixture
def denver(monkeypatch):
    """The hub's zone, pinned: the rehearsal's machine (America/Denver)."""
    import time

    monkeypatch.setenv("TZ", "America/Denver")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_the_next_mornings_scheduled_brief_carries_last_evening(tmp_path, db, monkeypatch, denver) -> None:
    """The cadence path untouched (regenerate=False, key-free): Wednesday's
    Brief exists; the evening's decision and done action land after it; the
    clock passes midnight (no Brief before its hour) and 07:10 Thursday makes
    Thursday's Brief, which covers Wednesday 00:00 (PHILO-17) through 07:10."""
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", tmp_path / "none.json")
    wed = datetime(2026, 10, 7)

    def at(hour: int, minute: int, days: int = 0) -> datetime:
        return wed + timedelta(days=days, hours=hour, minutes=minute)

    runtime = _runtime()

    def tick(moment: datetime) -> None:
        with patch("holdspeak.db.get_database", return_value=db), patch(
            "holdspeak.runtime.cadence.local_now", return_value=moment
        ):
            runtime._cadence_tick_body()

    tick(at(7, 10))  # Wednesday's scheduled Brief
    assert _briefs(db) == 1

    decided = at(21, 14).astimezone()
    monkeypatch.setattr("holdspeak.db.proposals.utc_now_iso", lambda: _z(decided))
    monkeypatch.setattr("holdspeak.services.follow_through_service.utc_now_iso",
                        lambda: _z(at(21, 40).astimezone()))
    proposal = db.proposals.create_proposal(
        meeting_id="m1", project_id=PROJECT, kind="decision",
        text="Squash merges only on the rehearsal repository", source_plugin="rehearsal")
    ProposalBridgeService(db).confirm_proposal(OWNER, proposal.id)
    FollowThroughService(db).complete(OWNER, "ai_1", "done", {})

    tick(at(23, 59))
    tick(at(0, 30, days=1))  # past midnight, before the Brief's hour
    assert _briefs(db) == 1
    tick(at(7, 10, days=1))
    assert _briefs(db) == 2

    latest = MondayBriefService(db).get_latest(OWNER)
    assert latest.period_end.startswith("2026-10-08T07:10")
    assert latest.period_start.startswith("2026-10-07T00:00")
    rows = _rows(latest)
    assert rows["Decision confirmed: Squash merges only on the rehearsal repository"].detail == "Wed 21:14"
    assert rows["Action done: Fix the login timeout"].detail == "Wed 21:40"
    _assert_plain(latest)


# ── Astra r2: the never-delete law on the launch file ────────────────

CORRUPT = b'{"launches_schema": 1, "launches": [{"launch_id": "lost-'


def _parked(path: Path) -> list[Path]:
    return sorted(path.parent.glob(f"{path.name}.not-read-*"))


def test_a_real_launch_parks_a_corrupt_ledger_byte_for_byte(tmp_path, db, monkeypatch) -> None:
    """Astra's producer probe: corrupt file -> a real launch -> the parked
    copy is byte-identical and the new file holds the launch."""
    import json

    from tests.unit.test_agent_hand import _rig as hand_rig

    rig = hand_rig(tmp_path, db, monkeypatch)
    path = rig.launches._path
    path.write_bytes(CORRUPT)
    try:
        result = rig.hand.hand(OWNER, "action", "ai_1")
        assert result["status"] == "launched", result
        parked = _parked(path)
        assert len(parked) == 1 and parked[0].read_bytes() == CORRUPT
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert [r["launch_id"] for r in doc["launches"]] == [result["launch_id"]]
    finally:
        rig.tmux.ended = True


def test_a_poll_on_a_loaded_ledger_parks_a_corrupt_file(tmp_path, db, monkeypatch) -> None:
    """The poll's polled_ns save on an instance that read the file before."""
    rig = _rig(tmp_path, db, monkeypatch)
    try:
        path = rig.launches._path
        path.write_bytes(CORRUPT)
        rig.observer.poll_open_prs(OWNER)
        parked = _parked(path)
        assert len(parked) == 1 and parked[0].read_bytes() == CORRUPT
        assert rig.launches.read_all(), "the file is readable again"
    finally:
        rig.tmux.ended = True


def test_no_park_no_overwrite(tmp_path) -> None:
    import os
    import stat

    from holdspeak.delivery.factory_launch import LaunchLedger, LaunchLedgerNotRead

    folder = tmp_path / "ledger"
    folder.mkdir()
    path = folder / "agent_launches.json"
    path.write_bytes(CORRUPT)
    ledger = LaunchLedger(path)
    os.chmod(folder, stat.S_IRUSR | stat.S_IXUSR)
    try:
        with pytest.raises(LaunchLedgerNotRead, match="could not be parked"):
            ledger.record({"launch_id": "launch-new"})
    finally:
        os.chmod(folder, stat.S_IRWXU)
    assert path.read_bytes() == CORRUPT and _parked(path) == []
    with pytest.raises(LaunchLedgerNotRead):
        ledger.read_all()


def test_a_removed_file_clears_the_cached_launches(tmp_path) -> None:
    from holdspeak.delivery.factory_launch import LaunchLedger

    path = tmp_path / "agent_launches.json"
    ledger = LaunchLedger(path)
    ledger.record({"launch_id": "launch-a"})
    assert [r["launch_id"] for r in ledger.list()] == ["launch-a"]
    path.unlink()
    assert ledger.list() == [] and ledger.read_all() == []
