"""Journey J2 "The dreaming program" on the hub (PG-LANG LANG12, JRN3, JRN4; 2026-11-01).

PROGRAM-JOURNEYS-2026-10-31.md J2, PROGRAM-LANGUAGE-2026-10-31.md §5.5. What
#1687 deferred: the Dreaming template; the backlog read by rule at the
window's start (Door tasks with the word "dream"), planned by the cheap
planner (REAL replies of qwen3.8-27b, tests/fixtures/program_night_reply.json
case ``backlog``, scripts/record_program_night_reply.py --only backlog); the
red-main hold (JRN3); the stop after two red steps in a row; a working step
parked at the window's end with its commit; and the night's line as the
morning's one Reach message at the digest hour with a briefing page link
(JRN4). The clock is frozen.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from holdspeak.services import program_night
from tests.integration.program_night_seed import BACKLOG_ITEMS, door_task, make_dreaming
from tests.integration.program_plan_seed import seed_files
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git, local_noon
from tests.unit.test_program_shaper import wire_engine

RECORDED = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "program_night_reply.json")
                      .read_text(encoding="utf-8"))["cases"]["backlog"]
REPLIES = [row["exchanges"][0]["reply_text"] for row in RECORDED["items"]]
RED = {"status": "completed", "conclusion": "failure", "name": "Nightly", "headSha": "1a2b3c4d5e6f"}
GREEN = {"status": "completed", "conclusion": "success", "name": "Nightly", "headSha": "9f8e7d6c5b4a"}


def at(day_offset: int, hour: int, minute: int = 0) -> datetime:
    """A local wall time relative to today's noon (``local_noon``)."""
    base = local_noon().replace(tzinfo=None) + timedelta(days=day_offset)
    return base.replace(hour=hour, minute=minute).astimezone()


class Clock:
    def __init__(self, moment: datetime) -> None:
        self.now = moment

    def iso(self) -> str:
        return self.now.astimezone(timezone.utc).isoformat()


def dream_desk(tmp_path: Path, monkeypatch, moment: datetime) -> tuple[Rig, Clock]:
    clock = Clock(moment)
    rig = Rig(tmp_path, clock=clock.iso, idle=lambda _engine: (True, "qwen"))
    rig.runner._now = lambda: clock.now
    rig.runner._reach = lambda: _NoReach()
    seed_files(rig, RECORDED["file_bytes"])  # the recorded files, so `within` keeps its folders
    rig.engine = wire_engine(rig, monkeypatch)
    rig.engine.replies = list(REPLIES)
    monkeypatch.setattr(program_night, "RED_READ_SECONDS", 0)
    program_night._RED_CACHE.clear()
    return rig, clock


class _NoReach:
    def night_line(self, ref: str, text: str, *, items: Any = None) -> dict[str, Any]:
        return {"ref": ref, "sent": False}


def lines(rig: Rig, pid: str) -> list[str]:
    return [row["line"] for row in rig.service.store.list_checkpoints(pid)]


# ── (a) the Dreaming template ────────────────────────────────────────

def test_the_dreaming_template_is_the_designs_night(tmp_path, monkeypatch) -> None:
    rig, _clock = dream_desk(tmp_path, monkeypatch, at(0, 14))
    pid = make_dreaming(rig)
    program = rig.program(pid)
    assert program["template"] == "dreaming" and program["control"] == "yolo"
    assert program["night"]["line"] == "23:30–07:00 · at most 8 steps"
    assert program["budget_tokens"] == 65536 and program["review_depth"] == "glance"
    assert program["default"]["profile"] == "pi-default" and program["prefer_idle"] is True
    # Within keeps the design's folders this repository has (the seed has two).
    assert program["within"] == ["web/src/desk/", "tests/unit/"]
    assert program["state"] != "drafting"  # a night Program starts empty; its backlog fills it


# ── (b) the backlog by rule, at the window's start ───────────────────

def test_at_the_window_start_the_backlog_becomes_tonights_steps(tmp_path, monkeypatch) -> None:
    rig, clock = dream_desk(tmp_path, monkeypatch, at(0, 14))
    door_task(rig, "Buy milk")  # no "dream": not the night's
    pid = make_dreaming(rig)
    rig.tick()
    assert rig.program(pid)["steps"] == []  # asleep: the backlog is read at the window's start
    clock.now = at(0, 23, 31)
    rig.tick()
    steps = rig.program(pid)["steps"]
    assert [step["title"] for step in steps] == [row["fields"]["title"] for row in RECORDED["items"]]
    assert [step["owns"] for step in steps] == [row["fields"]["owns"] for row in RECORDED["items"]]
    assert len(rig.engine.prompts) == 2  # one planning call per item
    assert "THE ITEM (the owner's words)\n" + BACKLOG_ITEMS[0] in rig.engine.prompts[0]["user_prompt"]
    assert "Read the backlog for tonight: 2 items added" in lines(rig, pid)
    decided = [row for row in rig.program(pid)["decided_for_you"] if row["kind"] == "add_step"]
    assert len(decided) == 2 and all(row["overturnable"] for row in decided)
    assert rig.hand.calls  # handed on the idle engine
    # Once a night.
    rig.tick()
    assert len(rig.program(pid)["steps"]) == 2 and lines(rig, pid).count("Read the backlog for tonight: 2 items added") == 1


# ── (c) JRN3: a red main holds the night until a step makes it green ─

def test_a_red_main_plans_one_green_step_first_and_holds_the_rest(tmp_path, monkeypatch) -> None:
    rig, clock = dream_desk(tmp_path, monkeypatch, at(0, 14))
    pid = make_dreaming(rig)
    rig.gh.runs = [RED]
    clock.now = at(0, 23, 31)
    rig.tick(2)
    steps = rig.program(pid)["steps"]
    assert steps[0]["title"] == "Make main green" and "Nightly failed on 1a2b3c4d" in steps[0]["brief"]
    assert [step["state_word"] for step in steps[1:]] == ["Ready · waits: main is red"] * 2
    assert [kind for kind, _item, _kw in rig.hand.calls] == ["program_step"]
    assert rig.hand.calls[0][1] == steps[0]["id"]
    assert "Main is red (Nightly failed on 1a2b3c4d): step 1 makes it green first; the rest wait" in lines(rig, pid)
    # The green step merges; main's next run is green; the night goes on.
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"fix.py": "1\n"})
    rig.tick(3)
    rig.gh.runs = [GREEN, RED]
    clock.now = at(1, 1, 0)
    rig.tick()
    assert "Main is green again; the night goes on" in lines(rig, pid)
    # One pi step at a time on the one engine: the next backlog step is handed.
    assert len([kind for kind, _item, _kw in rig.hand.calls if kind == "program_step"]) == 2
    assert not any("main is red" in step["state_word"] for step in rig.program(pid)["steps"])
    # The digest says how long the night waited.
    clock.now = at(1, 7, 20)
    rig.tick(2)
    digest = program_night.last_digest(rig.service, pid)
    assert digest is not None and "for a green main" in digest["line"], digest


def test_two_red_steps_in_a_row_stop_the_night_and_the_digest_says_so(tmp_path, monkeypatch) -> None:
    clock = Clock(at(0, 23, 31))
    rig = Rig(tmp_path, clock=clock.iso)
    rig.runner._now = lambda: clock.now
    rig.runner._reach = lambda: _NoReach()
    pid = rig.service.create(OWNER, title="Dreaming", repository=str(rig.repo), template="fast-cycle",
                             control="normal", check_command=f"FAKE_CHECK_RED=1 sh {FAKE_CHECK}")["id"]
    rig.service.update(OWNER, pid, night="23:30–07:00 · at most 8 steps")
    rig.service.start(OWNER, pid)
    for ordinal in (1, 2):  # one at a time, as the night's one engine runs them
        rig.service.plan(OWNER, pid, steps=[{"title": f"Fix {ordinal}", "brief": "x"}])
        rig.tick()
        for round_ in (1, 2):
            step = rig.step(pid, ordinal)
            rig.agent.finish(step["launch_id"], {f"f{ordinal}.txt": f"{round_}\n"})
            rig.tick()
            if round_ == 1:
                rig.agent.start_turn(step["launch_id"])
                rig.tick()
        assert rig.step(pid, ordinal)["state"] == "parked"
    rig.service.plan(OWNER, pid, steps=[{"title": "Fix 3", "brief": "x"}])
    rig.tick(2)
    three = rig.step(pid, 3)
    assert three["state"] == "ready" and three["state_word"] == "Ready · the night stopped after 2 red steps"
    assert "The night stopped after 2 red steps in a row" in lines(rig, pid)
    clock.now = at(1, 7, 5)
    rig.tick()
    digest = program_night.last_digest(rig.service, pid)
    assert digest is not None and digest["line"].endswith("stopped after 2 red steps"), digest


# ── (d) the window's end: a working step commits what it has and parks ─

def test_at_the_window_end_a_working_step_parks_with_its_commit_and_goes_on_the_next_night(tmp_path, monkeypatch) -> None:
    rig, clock = dream_desk(tmp_path, monkeypatch, at(0, 14))
    pid = make_dreaming(rig)
    clock.now = at(0, 23, 31)
    rig.tick()
    step = rig.step(pid, 1)
    worktree = Path(rig.ledger.get(step["launch_id"])["worktree_path"])
    (worktree / "half.txt").write_text("half done\n", encoding="utf-8")  # work, not committed
    clock.now = at(1, 7, 1)
    rig.tick()
    assert "The night ended: asked the agent to commit what it has" in lines(rig, pid)
    rig.agent.end_turn(step["launch_id"])  # the agent ended its turn without a commit
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "parked" and step["parked_reason"] == "Night ended; parked with a commit"
    assert "half.txt" in git(worktree, "show", "--name-only", "HEAD")
    assert not any(item["step_id"] == step["id"] for item in rig.program(pid)["your_turn_items"])  # the night's, not his
    # The next night it goes on from where the night ended, in its own worktree.
    clock.now = at(1, 23, 31)
    rig.tick()
    assert "Goes on tonight from where the night ended" in lines(rig, pid)
    step = rig.step(pid, 1)
    assert step["state"] in ("briefed", "working") and Path(rig.ledger.get(step["launch_id"])["worktree_path"]) == worktree


# ── (e) JRN4: the night's line is the morning's one Reach message ────

def test_the_nights_line_goes_at_the_digest_hour_with_a_page_link_and_no_second_digest(tmp_path, monkeypatch) -> None:
    from tests.unit.test_reach_telegram import Desk

    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "on")
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "home" / "channel-keys.json"))
    desk = Desk(tmp_path)
    desk.pair()
    pid, item = desk.core()
    morning = local_noon().replace(hour=7, minute=5)
    desk.reach._clock = lambda: morning.isoformat()
    desk.reach.quiet = lambda: (22, 7)
    desk.reach.save_settings(OWNER, {"digest": 8, "telegram": "digest"})
    desk.bot.calls.clear()
    ref = f"program:{pid}:{item['id']}"
    held = desk.reach.night_line(f"program:{pid}:night:tonight", "Dreaming · HoldSpeak\nSince last night: 1 step done",
                                 items=[ref])
    assert held["queued"] is True and desk.bot.of("sendMessage") == []  # before the digest hour
    eight = morning.replace(hour=8, minute=1)
    desk.reach._clock = lambda: eight.isoformat()
    desk.reach.tick()
    [message] = desk.bot.of("sendMessage")
    assert message["text"].startswith("Dreaming · HoldSpeak\nSince last night: 1 step done\n1 waits on you.")
    assert "Open the page: https://hub.tail.ts.net/b/" in message["text"]
    desk.reach.tick()
    assert len(desk.bot.of("sendMessage")) == 1  # one morning message: no second digest that day


def test_a_morning_with_two_held_items_links_one_page_for_both(tmp_path, monkeypatch) -> None:
    """DIR9: the morning message links ONE page that carries the night's held items in order."""
    from holdspeak.db.briefing import BriefingStore
    from tests.unit.test_reach_telegram import Desk

    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "on")
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "home" / "channel-keys.json"))
    desk = Desk(tmp_path)
    desk.pair()
    pid, item = desk.core()
    pid2, item2 = desk.merge()
    morning = local_noon().replace(hour=9)
    desk.reach._clock = lambda: morning.isoformat()
    desk.reach.quiet = lambda: (22, 7)
    desk.reach.save_settings(OWNER, {"digest": 8, "telegram": "digest"})
    desk.bot.calls.clear()
    refs = [f"program:{pid}:{item['id']}", f"program:{pid2}:{item2['id']}"]
    desk.reach.night_line(f"program:{pid}:night:tonight", "Dreaming · HoldSpeak\nSince last night: 2 steps done",
                          items=refs)
    [message] = desk.bot.of("sendMessage")
    assert "\n2 wait on you.\nOpen the page: https://hub.tail.ts.net/b/" in message["text"]
    [package] = [row for row in BriefingStore(desk.rig.db).open_like(f"program:{pid}:", morning.isoformat())
                 if row["kind"] == "digest"]
    assert package["refs"] == refs and package["body"]["head"] == "Since last night: 2 steps done"
