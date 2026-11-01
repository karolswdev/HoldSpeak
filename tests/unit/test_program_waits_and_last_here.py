"""PG-IMPORT IMP3 (BROCREW-IMPORT-2026-11-01): wait sentences and "Since you
were last here".

BroCrew's rule: each wait "says what the LEDGER holds and never who must
move". The engine writes a closed cause (``facts.wait``) or the hub derives
it; ``brief_words.WAIT_SENTENCES`` is the one place that words it. The step's
row and the Programs list line read the sentence.

"Since you were last here": the desk's presence reports keep the edge of his
visits on disk; Today reads the Programs ledger and Reach after it, one line
per Program, with the two honest lines when the read was not whole, and no
section at all when nothing happened.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from holdspeak.services import last_here
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


def _program(rig: Rig, steps: list[dict[str, Any]], control: str = "normal") -> str:
    pid = rig.service.create(OWNER, title="Atlas", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", control=control)["id"]
    rig.service.plan(OWNER, pid, steps=steps)
    rig.service.start(OWNER, pid)
    rig.tick()
    return pid


def test_a_step_after_one_that_ended_waits_on_something_that_has_ended(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, [{"title": "Anchors", "brief": "x"}, {"title": "Index", "brief": "y", "after": [1]}])
    rig.states[rig.step(pid, 1)["launch_id"]] = {"state": "ended", "turn_id": None}  # cut off: parked by the engine
    rig.tick()
    second = rig.step(pid, 2)
    assert second["state"] == "planned"
    assert second["wait"]["cause"] == "target_ended"
    assert second["wait"]["line"] == "Step 2 with Claude Code is waiting on something that has ended."


def test_a_lane_the_hub_cannot_find_and_a_recovery(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, [{"title": "Anchors", "brief": "x"}])
    launch = rig.step(pid, 1)["launch_id"]
    rig.states.pop(launch)  # the hub has no record of the lane
    rig.tick()
    step = rig.step(pid, 1)
    assert step["wait"]["line"] == "Step 1 with Claude Code is waiting on something HoldSpeak can no longer find."
    line = next(row for row in rig.service.list(OWNER)["programs"] if row["id"] == pid)["line"]
    assert line == step["wait"]["line"]
    rig.states[launch] = {"state": "resuming", "turn_id": None}  # the hub restarted; the agent resumes
    rig.tick()
    assert rig.step(pid, 1)["wait"]["line"] == "Step 1 with Claude Code picks up again after the hub restart."
    rig.states[launch] = {"state": "working", "turn_id": None}
    rig.tick()
    assert rig.step(pid, 1)["wait"] is None


def test_a_hold_that_ended_with_no_answer(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, [{"title": "Anchors", "brief": "x"}])
    launch = rig.step(pid, 1)["launch_id"]
    rig.gate.hold_commit(launch)
    rig.tick()
    assert rig.step(pid, 1)["wait"] is None
    rig.gate.expire(launch)
    rig.tick()
    assert rig.step(pid, 1)["wait"]["cause"] == "hold_expired"


def test_a_message_that_did_not_arrive(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, [{"title": "Anchors", "brief": "x"}])
    step = rig.step(pid, 1)
    rig.service.notice_lost(pid, step["id"], "Telegram")
    assert rig.step(pid, 1)["wait"]["line"] == ("Step 1 with Claude Code waits on you, and the message to you did "
                                                "not arrive.")


def test_the_edge_of_his_visits_is_kept(tmp_path) -> None:
    rig = Rig(tmp_path)
    t0 = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
    stamp = lambda minutes: (t0 + timedelta(minutes=minutes)).isoformat()  # noqa: E731
    last_here.touch(rig.db, stamp(0))
    last_here.touch(rig.db, stamp(5))
    assert last_here.last_here(rig.db) is None  # one visit so far
    last_here.touch(rig.db, stamp(50))  # away 45 min: a new visit
    assert last_here.last_here(rig.db) == stamp(5)


def test_since_last_here_reads_the_ledger_one_line_per_program(tmp_path) -> None:
    rig = Rig(tmp_path)
    since = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    assert last_here.since_last_here(rig.db, rig.service, since) is None  # nothing happened: no section
    pid = _program(rig, [{"title": "Anchors", "brief": "x"}])
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"docs/a.md": "x\n"})
    rig.tick(3)
    read = last_here.since_last_here(rig.db, rig.service, since)
    assert read is not None and not read["partial"] and not read["capped"]
    [row] = read["lines"]
    assert row["program_id"] == pid and row["title"] == "Atlas"
    assert row["line"].startswith("1 step merged"), row["line"]
    capped = last_here.since_last_here(rig.db, rig.service, since, limit=2)
    assert capped["capped"] and capped["capped_words"] == "Only the newest 2 were read; older ones may be missing."


def test_a_record_that_could_not_be_read_says_so(tmp_path) -> None:
    rig = Rig(tmp_path)
    since = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    _program(rig, [{"title": "Anchors", "brief": "x"}])

    class Broken:
        class store:
            @staticmethod
            def get_program(_pid: str) -> Any:
                raise OSError("disk I/O error")

    read = last_here.since_last_here(rig.db, Broken(), since)
    assert read is not None and read["partial"]
    assert read["partial_words"] == "Part of the record could not be read, so some lines may be missing."
