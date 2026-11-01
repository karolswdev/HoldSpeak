"""PG-LANG LANG12 and JRN2 (2026-10-31): the dreaming program.

PROGRAM-LANGUAGE-2026-10-31.md §5.5, PROGRAM-JOURNEYS-2026-10-31.md J2. A
Program with ``night 23:30–07:00 · at most 8 steps`` hands steps only
inside its window; Add to tonight marks a Door task, a note line or a step
for it; at the window's start the planner cuts each marked item into one
tiny step inside ``within``; after the window ONE digest line ("Since last
night: …") is written on top of the note and goes through Reach. The clock
is frozen (the service's clock and the runner's ``_now``). The planner's
answers are REAL replies of qwen3.8-27b (tests/fixtures/
program_night_reply.json, scripts/record_program_night_reply.py), replayed
through the runner's engine seam.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import program_night
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_night_seed import NIGHT_ITEMS, WITHIN, door_task, make_night
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig
from tests.unit.test_program_shaper import wire_engine

RECORDED = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "program_night_reply.json")
                      .read_text(encoding="utf-8"))
ITEMS = RECORDED["cases"]["night"]["items"]
REPLIES = [row["exchanges"][0]["reply_text"] for row in ITEMS]
AGENT = Principal(PrincipalKind.AGENT, "agent:orchestrator")


def at(day: int, hour: int, minute: int = 0) -> datetime:
    """A local wall-clock moment (aware), Monday 2 November 2026 is day 2."""
    return datetime(2026, 11, day, hour, minute).astimezone()


class Clock:
    def __init__(self, moment: datetime) -> None:
        self.now = moment

    def iso(self) -> str:
        return self.now.astimezone(timezone.utc).isoformat()


class Reach:
    """Where the digest line goes (``ReachService.night_line``'s seam)."""

    def __init__(self) -> None:
        self.lines: list[tuple[str, str]] = []

    def night_line(self, ref: str, text: str) -> dict[str, Any]:
        self.lines.append((ref, text))
        return {"ref": ref, "sent": True}


def desk(tmp_path: Path, monkeypatch, moment: datetime, *, engine: bool = True) -> tuple[Rig, Clock, Reach]:
    clock = Clock(moment)
    rig = Rig(tmp_path, clock=clock.iso)
    rig.runner._now = lambda: clock.now
    reach = Reach()
    rig.runner._reach = lambda: reach
    rig.engine = wire_engine(rig, monkeypatch) if engine else None
    if engine:
        rig.engine.replies = list(REPLIES)
    return rig, clock, reach


def handed(rig: Rig) -> list[str]:
    return [item_id for kind, item_id, _kw in rig.hand.calls if kind == "program_step"]


# ── the window ───────────────────────────────────────────────────────

def test_the_window_wraps_midnight_and_names_its_night() -> None:
    night = {"start": "23:30", "end": "07:00"}
    assert program_night.inside(night, at(2, 23, 45)) and program_night.inside(night, at(3, 6, 59))
    assert not program_night.inside(night, at(3, 7, 0)) and not program_night.inside(night, at(2, 14, 0))
    start, end = program_night.window(night, at(3, 3, 0))
    assert (start, end) == (at(2, 23, 30), at(3, 7, 0)) and program_night.night_key(start) == "2026-11-02"
    day = {"start": "09:00", "end": "17:00"}
    assert program_night.inside(day, at(2, 12, 0)) and not program_night.inside(day, at(2, 18, 0))


def test_outside_its_window_the_program_sleeps_and_nothing_is_planned(tmp_path, monkeypatch) -> None:
    rig, clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, sids = make_night(rig)
    rig.tick(2)

    steps = rig.program(pid)["steps"]
    assert [step["state_word"] for step in steps] == ["Ready · sleeps until 23:30"] * 3
    assert [step["title"] for step in steps] == list(NIGHT_ITEMS)
    assert handed(rig) == [] and rig.engine.prompts == []


def test_at_the_window_start_each_item_is_planned_into_one_tiny_step_and_handed(tmp_path, monkeypatch) -> None:
    rig, clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, sids = make_night(rig)
    clock.now = at(2, 23, 31)
    rig.tick()

    # ONE planning call per item, with the bounds and the size.
    assert len(rig.engine.prompts) == 3
    prompt = rig.engine.prompts[0]
    assert prompt["response_format"]["json_schema"]["name"] == "program_night_item"
    assert "BOUNDS\n" + "\n".join(f"- {bound}" for bound in WITHIN) in prompt["system_prompt"]
    assert "the step must fit in 32k tokens" in prompt["system_prompt"]
    assert "THE ITEM (the owner's words)\n" + NIGHT_ITEMS[0] in prompt["user_prompt"]
    assert "WHERE IT IS FROM\nA task on the Door" in prompt["user_prompt"]
    steps = rig.program(pid)["steps"]
    assert [step["title"] for step in steps] == [row["fields"]["title"] for row in ITEMS]
    assert [step["owns"] for step in steps] == [row["fields"]["owns"] for row in ITEMS]
    assert all(path.startswith("web/src/desk/") for step in steps for path in step["owns"])
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid)]
    assert f"Planned for tonight: step 1 · {ITEMS[0]['fields']['title']}" in lines
    assert handed(rig) == sids
    # Each step's merge closes its Door task.
    assert all(str(step["origin_ref"]).startswith("action:ai_") for step in steps)


def test_at_most_n_steps_a_night(tmp_path, monkeypatch) -> None:
    rig, clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, sids = make_night(rig)
    rig.service.update(OWNER, pid, night="23:30–07:00 · at most 2 steps")
    clock.now = at(2, 23, 40)
    rig.tick(2)

    assert handed(rig) == sids[:2]
    assert rig.step(pid, 3)["state_word"] == "Ready · the night's 2 steps ran"


def test_with_no_planner_an_item_runs_as_written(tmp_path, monkeypatch) -> None:
    rig, clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0), engine=False)
    pid, sids = make_night(rig)
    clock.now = at(2, 23, 31)
    rig.tick()
    assert [step["title"] for step in rig.program(pid)["steps"]] == list(NIGHT_ITEMS)
    assert handed(rig) == sids
    assert any(row["line"].startswith("Runs as written tonight: the planner could not plan it")
               for row in rig.service.store.list_checkpoints(pid))


# ── the morning digest ───────────────────────────────────────────────

def _merge_first(rig: Rig, pid: str) -> None:
    one = rig.step(pid, 1)
    rig.agent.finish(one["launch_id"], {one["owns"][0]: "export {};\n"})
    rig.tick(4)


def test_after_the_window_one_digest_line_on_top_of_the_note_and_through_reach(tmp_path, monkeypatch) -> None:
    rig, clock, reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, sids = make_night(rig)
    clock.now = at(2, 23, 31)
    rig.tick()
    clock.now = at(3, 1, 0)
    _merge_first(rig, pid)
    assert rig.step(pid, 1)["state"] in ("merged", "done")
    clock.now = at(3, 6, 0)
    rig.tick()
    assert [row for row in rig.service.store.list_checkpoints(pid) if row.get("kind") == "night_digest"] == []

    clock.now = at(3, 7, 5)
    rig.tick()
    (row,) = [row for row in rig.service.store.list_checkpoints(pid) if row.get("kind") == "night_digest"]
    assert row["line"].startswith("Since last night: 1 step done")
    pr = rig.step(pid, 1)["pr"]["number"]
    assert row["undo"] == {"night": "2026-11-02", "lines": [row["line"], f"Merged: #{pr}"]}
    assert reach.lines == [(f"program:{pid}:night:2026-11-02", f"Dreaming · HoldSpeak\n{row['line']}")]
    note = rig.note(pid)
    assert "## Since last night\n" + row["line"].split(": ", 1)[1] + f"\nMerged: #{pr}\n" in note
    assert note.index("## Since last night") < note.index("## Your turn")
    # Once a night.
    clock.now = at(3, 8, 0)
    rig.tick()
    assert len(reach.lines) == 1
    assert len([row for row in rig.service.store.list_checkpoints(pid) if row.get("kind") == "night_digest"]) == 1


def test_a_night_that_did_nothing_writes_no_digest(tmp_path, monkeypatch) -> None:
    rig, clock, reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid = rig.service.create(OWNER, title="Quiet", goal="Nothing.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control="yolo")["id"]
    rig.service.update(OWNER, pid, night="23:30–07:00")
    clock.now = at(3, 7, 30)
    rig.tick()
    assert reach.lines == [] and "## Since last night" not in rig.note(pid)


def test_the_digest_counts_a_split_and_what_waits(tmp_path, monkeypatch) -> None:
    rig, clock, _reach = desk(tmp_path, monkeypatch, at(3, 7, 30))
    pid, _sids = make_night(rig)
    start, end = at(2, 23, 30), at(3, 7, 0)
    rig.service.store.add_checkpoint(step_id="", program_id=pid, at=at(3, 1, 0).astimezone(timezone.utc).isoformat(),
                                     by="engine", line="Split step 3", kind="step_too_big", choice="split",
                                     rule="YOLO: the planner splits a step too big for its budget and says so")
    lines = program_night.digest_lines(rig.service, rig.service.store.get_program(pid), start, end)
    assert lines == ["Since last night: 1 split"]


# ── Add to tonight ───────────────────────────────────────────────────

def test_the_same_item_twice_is_one_step(tmp_path, monkeypatch) -> None:
    rig, _clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, _sids = make_night(rig)
    task = door_task(rig, "The Notes toolbar wraps at 520.")
    first = rig.service.add_to_night(OWNER, kind="action", item_id=task)
    again = rig.service.add_to_night(OWNER, kind="action", item_id=task)
    assert first["added"] is True and first["say"] == "Added to tonight: step 4 · The Notes toolbar wraps at 520."
    assert again["added"] is False and again["step_id"] == first["step_id"]
    assert again["say"] == "It is in tonight already: step 4"


def test_a_note_line_and_a_step_of_another_program(tmp_path, monkeypatch) -> None:
    rig, _clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, _sids = make_night(rig)
    rig.db.notes.upsert(note_id="note-loop", title="The loop budget", body_markdown="- Engines rows clip at 393\n")
    noted = rig.service.add_to_night(OWNER, kind="note", item_id="note-loop", line="Engines rows clip at 393")
    step = rig.service.store.get_step(noted["step_id"])
    assert step["title"] == "Engines rows clip at 393" and step["origin_ref"] is None
    assert step["facts"]["night_item"]["from"] == "A line of the note The loop budget"
    with pytest.raises(ProgramRefused) as refused:
        rig.service.add_to_night(OWNER, kind="note", item_id="note-loop")
    assert refused.value.code == "night_line_required"
    other = rig.service.create(OWNER, title="Day work", goal="Day.", repository=str(rig.repo),
                               check_command=f"sh {FAKE_CHECK}", template="fast-cycle")["id"]
    rig.service.plan(OWNER, other, steps=[{"title": "Tidy the dock", "brief": "Tidy it.", "owns": ["web/src/desk/dock.ts"]}])
    source = rig.service.store.list_steps(other)[0]
    copied = rig.service.add_to_night(OWNER, kind="program_step", item_id=source["id"])
    made = rig.service.store.get_step(copied["step_id"])
    assert (made["title"], made["owns"], made["program_id"]) == ("Tidy the dock", ["web/src/desk/dock.ts"], pid)


def test_refusals_by_name(tmp_path, monkeypatch) -> None:
    rig, _clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    with pytest.raises(ProgramRefused) as none:
        rig.service.add_to_night(OWNER, kind="action", item_id="ai_x")
    assert none.value.code == "no_night_program"
    pid, _sids = make_night(rig)
    with pytest.raises(ProgramRefused) as unknown:
        rig.service.add_to_night(OWNER, kind="action", item_id="ai_missing")
    assert unknown.value.code == "night_item_unknown"
    with pytest.raises(ProgramRefused) as kind:
        rig.service.add_to_night(OWNER, kind="meeting", item_id="m1")
    assert kind.value.code == "night_kind_invalid"
    second = rig.service.create(OWNER, title="Dreaming two", goal="Two.", repository=str(rig.repo),
                                check_command=f"sh {FAKE_CHECK}", template="fast-cycle")["id"]
    rig.service.update(OWNER, second, night="23:30–07:00")
    with pytest.raises(ProgramRefused) as two:
        rig.service.add_to_night(OWNER, kind="action", item_id=door_task(rig, "x"))
    assert two.value.code == "night_program_ambiguous"


def test_an_agent_adds_to_tonight_only_at_yolo_and_it_says_so(tmp_path, monkeypatch) -> None:
    rig, _clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, _sids = make_night(rig, control="normal")
    with pytest.raises(ProgramRefused) as refused:
        rig.service.add_to_night(AGENT, kind="action", item_id=door_task(rig, "A"))
    assert refused.value.code == "owner_required"
    rig.service.update(OWNER, pid, control="yolo")
    added = rig.service.add_to_night(AGENT, kind="action", item_id=door_task(rig, "B"))
    (row,) = [row for row in rig.service.decided_for_you(pid) if row["kind"] == "add_step"]
    assert row["line"] == "Added to tonight: step 4 · B" and row["overturnable"]
    rig.service.overturn(OWNER, pid, row["id"])
    assert rig.service.store.get_step(added["step_id"]) is None


def test_a_done_night_program_opens_again_for_tonight(tmp_path, monkeypatch) -> None:
    rig, _clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, _sids = make_night(rig)
    program = rig.service.store.get_program(pid)
    program["closed_at"] = (at(2, 7, 0)).astimezone(timezone.utc).isoformat()
    rig.service.store.save_program(program)
    rig.service.add_to_night(OWNER, kind="action", item_id=door_task(rig, "Again"))
    assert rig.service.store.get_program(pid)["closed_at"] is None
    assert "Opened again for tonight" in [row["line"] for row in rig.service.store.list_checkpoints(pid)]


# ── Reach: the one line on the ladder ────────────────────────────────

def test_the_night_line_goes_to_telegram_once_and_waits_out_quiet_hours(tmp_path, monkeypatch) -> None:
    from tests.unit.test_reach_telegram import Desk

    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "home" / "channel-keys.json"))
    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "on")
    telegram_desk = Desk(tmp_path)
    telegram_desk.pair()
    reach = telegram_desk.reach
    telegram_desk.bot.calls.clear()
    hour = datetime.now().astimezone().hour
    reach.quiet = lambda: (hour, (hour + 2) % 24)  # quiet now
    held = reach.night_line("program:p1:night:2026-11-02", "Dreaming · HoldSpeak\nSince last night: 1 step done")
    assert held == {"ref": "program:p1:night:2026-11-02", "queued": True, "sent": False}
    assert telegram_desk.bot.of("sendMessage") == []
    reach.quiet = lambda: (0, 0)  # quiet hours over: the ladder's tick sends it
    assert reach.tick()["night"] == ["program:p1:night:2026-11-02"]
    (sent,) = telegram_desk.bot.of("sendMessage")
    assert "Since last night: 1 step done" in sent["text"] and "reply_markup" not in sent
    again = reach.night_line("program:p1:night:2026-11-02", "Dreaming · HoldSpeak\nSince last night: 1 step done")
    assert again["again"] is True and reach.tick()["night"] == [] and len(telegram_desk.bot.of("sendMessage")) == 1
    # Telegram Off: never sent.
    reach.save_settings(OWNER, {"telegram": "off"})
    reach.night_line("program:p1:night:2026-11-03", "x")
    assert len(telegram_desk.bot.of("sendMessage")) == 1


def test_the_hours_after_the_window_are_bounded(tmp_path, monkeypatch) -> None:
    rig, clock, reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, _sids = make_night(rig)
    clock.now = at(2, 23, 31)
    rig.tick()
    clock.now = at(3, 1, 0)
    _merge_first(rig, pid)
    clock.now = at(3, 7, 0) + timedelta(hours=program_night.DIGEST_HOURS, minutes=1)
    rig.tick()
    assert reach.lines == []
