"""The night ends on time and finishes (Astra's post-merge check, 2026-11-01; ruling the same day).

- the window is read again right before each hand;
- a step resumed from an earlier night is tonight's: ``at most`` counts it
  and the window's end parks it;
- a hub back after ``DIGEST_HOURS`` still writes that night's digest, once;
- the canon backlog's claim is written before any task is filed, so a read
  cut off in the middle never files a second set;
- the night's end never commits an audit's worktree.
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from holdspeak.services import program_night
from tests.integration.program_night_seed import make_night
from tests.integration.program_rig import FAKE_CHECK, OWNER, git
from tests.unit.test_program_dreaming import at as dream_at, dream_desk, lines
from tests.unit.test_program_night import _merge_first, at, desk


def test_the_window_is_read_again_right_before_each_hand(tmp_path, monkeypatch) -> None:
    rig, clock, _reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, sids = make_night(rig)
    clock.now = at(3, 6, 59)
    real_room = program_night.night_room

    def room_then_morning(runner, program, ready):
        room = real_room(runner, program, ready)
        clock.now = at(3, 7, 1)  # the morning comes while the hands run
        return room

    monkeypatch.setattr(program_night, "night_room", room_then_morning)
    rig.tick()
    assert [kind for kind, _id, _kw in rig.hand.calls if kind == "program_step"] == []
    assert rig.step(pid, 1)["state_word"].startswith("Ready · sleeps until")


def test_a_resumed_step_is_tonights_and_counts(tmp_path, monkeypatch) -> None:
    rig, clock = dream_desk(tmp_path, monkeypatch, dream_at(0, 14))
    pid = rig.service.create(OWNER, title="Night", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="dreaming")["id"]
    rig.service.update(OWNER, pid, night="23:30–07:00 · at most 1 step")
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x", "owns": ["web/src/desk/a.ts"]},
                                        {"title": "Two", "brief": "y", "owns": ["web/src/desk/b.ts"]}])
    rig.service.start(OWNER, pid)
    clock.now = dream_at(0, 23, 31)
    rig.tick()
    one = rig.step(pid, 1)
    assert one["state"] in ("briefed", "working")
    clock.now = dream_at(1, 7, 1)
    rig.tick()
    rig.agent.end_turn(one["launch_id"])
    rig.tick()
    assert rig.step(pid, 1)["state"] == "parked"
    # The next night: step 1 goes on (Resume's path); at most 1 means step 2 waits.
    clock.now = dream_at(1, 23, 31)
    rig.tick(2)
    assert rig.step(pid, 1)["state"] in ("briefed", "working")
    assert rig.step(pid, 2)["state"] == "ready", rig.step(pid, 2)["state_word"]
    # And the window's end parks the resumed step again.
    clock.now = dream_at(2, 7, 1)
    rig.tick()
    assert lines(rig, pid).count("The night ended: asked the agent to commit what it has") == 2


def test_a_hub_back_late_still_writes_the_nights_digest_once(tmp_path, monkeypatch) -> None:
    rig, clock, reach = desk(tmp_path, monkeypatch, at(2, 14, 0))
    pid, _sids = make_night(rig)
    clock.now = at(2, 23, 31)
    rig.tick()
    clock.now = at(3, 1, 0)
    _merge_first(rig, pid)
    clock.now = at(3, 7, 0) + timedelta(hours=program_night.DIGEST_HOURS, minutes=1)  # 19:01
    rig.tick()  # the steps the night left are asked to commit
    clock.now += timedelta(minutes=program_night.END_MINUTES + 1)
    rig.tick(3)
    assert program_night.last_digest(rig.service, pid) is not None
    assert len(reach.lines) == 1
    rig.tick()
    assert len(reach.lines) == 1


def test_the_backlog_claim_comes_first_so_a_cut_read_never_files_twice(tmp_path, monkeypatch) -> None:
    from holdspeak.services import program_canon

    rig, clock = dream_desk(tmp_path, monkeypatch, dream_at(0, 14))
    pid = rig.service.create(OWNER, title="Night", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="dreaming")["id"]
    rig.service.start(OWNER, pid)
    filed: list[int] = []
    monkeypatch.setattr(program_canon, "file_items", lambda runner, program, limit=5: filed.append(limit) or [])
    real_add = rig.service.store.add_checkpoint
    cut = {"done": False}

    def add(**kwargs):
        if kwargs.get("kind") == program_night.BACKLOG_KIND and not cut["done"]:
            cut["done"] = True
            raise RuntimeError("the hub stopped here")
        return real_add(**kwargs)

    monkeypatch.setattr(rig.service.store, "add_checkpoint", add)
    clock.now = dream_at(0, 23, 31)
    program = rig.service.store.get_program(pid)
    start, end = program_night.window(program["night"], clock.now)
    with pytest.raises(RuntimeError):
        program_night.read_backlog(rig.runner, program, start, end)
    program_night.read_backlog(rig.runner, program, start, end)
    program_night.read_backlog(rig.runner, program, start, end)
    assert len(filed) <= 1


def test_the_nights_end_never_commits_an_audit(tmp_path, monkeypatch) -> None:
    rig, clock = dream_desk(tmp_path, monkeypatch, dream_at(0, 14))
    pid = rig.service.create(OWNER, title="Night audit", repository=str(rig.repo), control="yolo",
                             template="audit")["id"]
    rig.service.update(OWNER, pid, night="23:30–07:00 · at most 1 step")
    rig.service.plan(OWNER, pid, steps=[{"title": "Read the Notes window", "brief": "Read it.",
                                        "owns": ["web/src/desk/"]}])
    rig.service.start(OWNER, pid)
    clock.now = dream_at(0, 23, 31)
    rig.tick()
    step = rig.step(pid, 1)
    worktree = Path(rig.ledger.get(step["launch_id"])["worktree_path"])
    before = git(worktree, "rev-parse", "HEAD")
    (worktree / "test-output.txt").write_text("output of an allowed test\n", encoding="utf-8")
    clock.now = dream_at(1, 7, 1)
    rig.tick()
    rig.agent.end_turn(step["launch_id"])
    rig.tick()
    assert rig.step(pid, 1)["state"] == "parked"
    assert git(worktree, "rev-parse", "HEAD") == before
