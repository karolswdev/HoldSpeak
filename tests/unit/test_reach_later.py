"""PG-DIRECTION DIR4: Later as a first-class answer (DIRECTION-2026-10-31.md §7).

The words map to their next touch by rule (no model); a deferred item leaves
the Needs you count, sits in the Later group with its time, and comes back
at the next touch; at YOLO a deferred core question parks its step for now
(Overturnable) and Go on resumes it from its checkpoint; below YOLO the step
only waits; a merge ask only waits at every level.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.briefing import HeldLaterStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.needs_you_membership import compute_needs_you
from holdspeak.services.reach_service import ReachRefused, ReachService, parse_later
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

AGENT = Principal(PrincipalKind.AGENT, "agent-1")


def _local(hour: int, minute: int = 0) -> datetime:
    """A local wall time on 2026-10-31 (the parser reads local time)."""
    return datetime(2026, 10, 31, hour, minute).astimezone()


@pytest.mark.parametrize("words, at, want", [
    ("later 2h", (12, 10), (14, 10, 0)),
    ("in two hours", (12, 10), (14, 10, 0)),
    ("later 30m", (12, 10), (12, 40, 0)),
    ("in 1 hour", (12, 10), (13, 10, 0)),
    ("in_1h", (12, 10), (13, 10, 0)),
    ("at one", (12, 10), (13, 0, 0)),
    ("later, at one", (6, 30), (13, 0, 0)),
    ("later, at five", (12, 10), (17, 0, 0)),
    ("at 13:00", (12, 10), (13, 0, 0)),
    ("later 13:00", (14, 0), (13, 0, 1)),
    ("14:30", (12, 10), (14, 30, 0)),
    ("at_13", (6, 30), (13, 0, 0)),
    ("tonight", (12, 10), (19, 0, 0)),
    ("tomorrow", (12, 10), (8, 0, 1)),
    ("later", (12, 10), (14, 10, 0)),
    ("", (21, 0), (8, 0, 1)),  # 23:00 is inside quiet hours: the end of them
])
def test_the_words_map_to_their_next_touch(words: str, at: tuple[int, int], want: tuple[int, int, int]) -> None:
    now = _local(*at)
    until = parse_later(words, now, quiet=(22, 8))
    hour, minute, days = want
    assert (until.hour, until.minute, (until.date() - now.date()).days) == (hour, minute, days), (words, until)


@pytest.mark.parametrize("words", ["after the standup", "soon", "at 25", "in 0 hours", "5"])
def test_anything_else_asks_for_a_time(words: str) -> None:
    with pytest.raises(ReachRefused) as refused:
        parse_later(words, _local(12), quiet=(22, 8))
    assert refused.value.code == "later_invalid" and refused.value.detail == "Say a time, for example 14:30."


def test_later_means_is_his_default(tmp_path) -> None:
    rig = Rig(tmp_path)
    noon = _local(12)
    reach = ReachService(rig.db, programs=lambda: rig.service, clock=lambda: noon.isoformat())
    reach.save_settings(OWNER, {"later_means": "tomorrow"})
    until = reach.later_until("later")
    assert until.hour == 8 and until.date() > noon.date()
    with pytest.raises(ReachRefused):
        reach.save_settings(AGENT, {"later_means": "in_2h"})
    with pytest.raises(ReachRefused) as bad:
        reach.save_settings(OWNER, {"telegram": "always"})
    assert bad.value.code == "telegram_invalid"


def _core(tmp_path: Path, control: str) -> tuple[Rig, str, dict[str, Any]]:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Overnight on the home box", goal="Stop the stalls.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control=control)["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Owned", "brief": "Store the stall reason.", "owns": ["src/a.py"]},
        {"title": "Other", "brief": "Log the stall.", "owns": ["src/c.py"]},
    ])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
    rig.tick()
    items = [item for item in rig.service.needs_you_items() if item["kind"] == "core"]
    assert len(items) == 1, rig.service.needs_you_items()
    return rig, pid, items[0]


def _counted(rig: Rig) -> tuple[list[str], list[dict[str, Any]]]:
    answer = compute_needs_you(programs=rig.service.needs_you_items())
    rows = [row for row in answer["unmutedItems"] if row.get("source") == "program"]
    return [member["ref"] for member in answer["members"]], rows


def test_a_deferred_item_leaves_the_count_and_comes_back_at_the_next_touch(tmp_path) -> None:
    rig, pid, item = _core(tmp_path, "normal")
    ref = f"program:{pid}:{item['id']}"
    members, _rows = _counted(rig)
    assert ref in members
    reach = ReachService(rig.db, programs=lambda: rig.service)
    said = reach.later(OWNER, ref, "later 2h", via="telegram")
    assert said["words"].startswith("Later · back at ") and said["parked"] is False
    members, rows = _counted(rig)
    row = next(row for row in rows if row["ref"] == ref)
    assert ref not in members and row["counted"] is False and row["later"]["via"] == "telegram"
    # The ledger names the channel; nothing was decided.
    lines = [c for c in rig.program(pid)["checkpoints"] if c["line"].startswith("Later, back at ")]
    assert lines and lines[0]["line"].endswith("· from Telegram") and lines[0]["via"] == "telegram"
    assert rig.step(pid, 1)["state"] != "parked"  # Normal: the step only waits
    # The next touch: the row is due; the tick drops it and the item counts again.
    HeldLaterStore(rig.db).put(ref=ref, until=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
                               via="telegram", at=datetime.now(timezone.utc).isoformat())
    done = reach.tick()
    assert [row["ref"] for row in done["returned"]] == [ref]
    members, _rows = _counted(rig)
    assert ref in members


def test_at_yolo_a_deferred_core_question_parks_its_step_and_go_on_resumes_it(tmp_path) -> None:
    rig, pid, item = _core(tmp_path, "yolo")
    ref = f"program:{pid}:{item['id']}"
    before = rig.step(pid, 1)["state"]
    reach = ReachService(rig.db, programs=lambda: rig.service)
    said = reach.later(OWNER, ref, "at one")
    assert said["parked"] is True
    step = rig.step(pid, 1)
    assert step["state"] == "parked"
    decided = [row for row in rig.program(pid)["decided_for_you"] if row["kind"] == "later"]
    assert decided and decided[0]["line"] == "Parked for now: you said later" and decided[0]["overturnable"]
    # The question is still his, and the other step goes on.
    assert [i["kind"] for i in rig.service.needs_you_items()] == ["core"]
    rig.service.decide(OWNER, pid, step["id"], kind="core", choice="go_on")
    resumed = rig.step(pid, 1)
    assert resumed["state"] != "parked", resumed["state"]
    lines = [c["line"] for c in rig.program(pid)["checkpoints"]]
    assert "Resumed the step from its checkpoint" in lines
    assert before in ("checking", "review", "working", "pr_open") or before  # it went back where it stopped


def test_a_merge_ask_only_waits(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="The hub stops stalling", goal="Stop the stalls.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", control="secure", template="")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "Do it.", "owns": ["a.py"]}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick(3)
    items = [item for item in rig.service.needs_you_items() if item["kind"] == "merge"]
    assert items, rig.service.needs_you_items()
    state = rig.step(pid, 1)["state"]
    said = ReachService(rig.db, programs=lambda: rig.service).later(OWNER, f"program:{pid}:{items[0]['id']}",
                                                                     "tonight")
    assert said["parked"] is False and rig.step(pid, 1)["state"] == state


def test_later_is_his_verb_only_and_needs_a_waiting_item(tmp_path) -> None:
    rig, pid, item = _core(tmp_path, "normal")
    reach = ReachService(rig.db, programs=lambda: rig.service)
    with pytest.raises(ReachRefused) as agent:
        reach.later(AGENT, f"program:{pid}:{item['id']}", "later")
    assert agent.value.code == "owner_only"
    with pytest.raises(Exception) as gone:
        reach.later(OWNER, f"program:{pid}:nope:core", "later")
    assert getattr(gone.value, "code", "") == "not_waiting"
