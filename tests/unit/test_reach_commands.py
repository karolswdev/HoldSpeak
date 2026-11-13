"""The bot answers what the owner asks, and what waits on him travels.

``/waiting``, ``/today``, ``/quiet``, ``/status`` and ``/help`` from the
owner chat; the command menu; a held tool call with what it will write and
Deny first; a notice for a Send that waits; the chat's budget; the morning
brief; "Back at". Needs you and Today are a RECORDED real hub answer
(``web/src/desk/__tests__/fixtures/daily-week/today.json``); Telegram is a
fake transport; the clock is a value. Nothing here calls Telegram.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import reach_commands
from holdspeak.services.held_tool_details import held_call_details
from holdspeak.services.reach_service import ReachService
from holdspeak.services.telegram_reach import TelegramReach
from holdspeak.services.thread_service import ThreadService
from holdspeak.services.thread_tools import ToolCallHandle
from holdspeak.services.thread_turns import _ToolExecutorAggregator
from tests.unit.test_reach_telegram import OWNER_CHAT, keystore  # noqa: F401
from tests.unit.test_reach_telegram_setup import OWNER, TOKEN, Bot, Clock, update

RECORDED = Path(__file__).resolve().parents[2] / "web/src/desk/__tests__/fixtures/daily-week/today.json"
DAY = "2026-11-13T19:00:00+00:00"       # midday in the Americas and the evening in Europe: not quiet, not the digest hour


def _recorded_today() -> dict[str, Any]:
    def find(value: Any) -> Any:
        if isinstance(value, dict):
            if "since_yesterday" in value and "needs_you" in value:
                return value
            for inner in value.values():
                found = find(inner)
                if found:
                    return found
        if isinstance(value, list):
            for inner in value:
                found = find(inner)
                if found:
                    return found
        return None

    return copy.deepcopy(find(json.loads(RECORDED.read_text(encoding="utf-8"))))


class Reads:
    """The hub's reads, replayed from the recorded answer."""

    def __init__(self) -> None:
        self.answer = _recorded_today()
        self.calls: list[Any] = []
        self.fails = False

    @property
    def needs(self) -> dict[str, Any]:
        return self.answer["needs_you"]

    def needs_you(self, principal: Any) -> dict[str, Any]:
        assert principal.kind is PrincipalKind.OWNER
        if self.fails:
            raise RuntimeError("not read")
        return copy.deepcopy(self.needs)

    def today(self, principal: Any) -> dict[str, Any]:
        return copy.deepcopy(self.answer)

    def held_calls(self) -> list[Any]:
        return list(self.calls)

    def desk_name(self) -> str:
        return "Karol's Mac"

    def keep(self, count: int) -> None:
        """Keep ``count`` waiting things (the recorded rows, repeated with their own refs)."""
        rows = [row for row in self.needs["items"] if isinstance(row, dict)]
        made = []
        for index in range(count):
            row = copy.deepcopy(rows[index % len(rows)])
            row["ref"] = f"{row.get('ref')}#{index}"
            row["id"] = row["ref"]
            made.append(row)
        self.needs["items"] = made
        self.needs["members"] = [{"ref": row["ref"], "kind": "attention"} for row in made]
        self.needs["count"] = count
        self.needs["failedMeetings"] = []


class Programs:
    def needs_you_items(self) -> list[dict[str, Any]]:
        return []

    def notice_lost(self, *args: Any) -> None:
        pass


def desk(tmp_path: Path, clock: Clock | None = None) -> SimpleNamespace:
    from holdspeak.db import Database

    clock = clock or Clock()
    clock.at = DAY
    db = Database(tmp_path / "reach.db")
    bot = Bot()
    box: dict[str, Any] = {}
    reach = ReachService(db, programs=lambda: Programs(), telegram=lambda: box["tg"], clock=clock)
    tg = TelegramReach(db, caller=bot, reach=reach, clock=clock, programs=lambda: Programs())
    box["tg"] = tg
    tg.reads = Reads()
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    assert tg.handle_update(update("pair", code=code))["ok"] is True
    return SimpleNamespace(tg=tg, bot=bot, db=db, reach=reach, reads=tg.reads, clock=clock)


def say(text: str, chat: Any = OWNER_CHAT) -> dict[str, Any]:
    return {"update_id": 900, "message": {"message_id": 5, "chat": {"id": chat}, "text": text,
                                          "date": 1794581000, "from": {"first_name": "K"}}}


def press(data: str, message_id: int = 7, text: str = "") -> dict[str, Any]:
    return {"update_id": 901, "callback_query": {"id": "cb1", "data": data, "message": {
        "message_id": message_id, "chat": {"id": OWNER_CHAT}, "text": text}}}


def texts(bot: Bot, since: int = 0) -> list[str]:
    return [row["text"] for row in bot.of("sendMessage")[since:]]


def held(monkeypatch, args: dict[str, Any] | None = None) -> tuple[Any, list[Any]]:
    owner = Principal(PrincipalKind.OWNER, "ask")
    handle = ToolCallHandle("call-1", "thread-1", "turn-1", "door.add_item",
                            args or {"task": "Email Dana about the cutover date"},
                            "effect_proposal", False, "awaiting_decision", principal=owner)
    answers: list[Any] = []
    executor = SimpleNamespace(_handles={"call-1": handle},
                               decide=lambda h, decision, answer=None: answers.append((h.call_id, decision)))
    aggregator = _ToolExecutorAggregator()
    aggregator.register("turn-1", executor)
    monkeypatch.setattr(ThreadService, "_tool_executor", aggregator)
    return handle, answers


# ── 1. the command menu ──────────────────────────────────────────────

def test_the_menu_is_set_one_time_and_again_only_when_it_differs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("holdspeak.services.reach_service.carries_cadence", lambda db: False)
    d = desk(tmp_path)
    assert d.tg.ensure_menu() is True
    assert d.tg.ensure_menu() is False
    menus = d.bot.of("setMyCommands")
    assert len(menus) == 1
    assert [row["command"] for row in menus[0]["commands"]] == ["waiting", "today", "quiet", "status", "help"]
    assert all(row["description"] for row in menus[0]["commands"])
    # Cadence carries loops: its commands join the menu, and the menu is set again one time.
    monkeypatch.setattr("holdspeak.services.reach_service.carries_cadence", lambda db: True)
    assert d.tg.ensure_menu() is True and d.tg.ensure_menu() is False
    assert [row["command"] for row in d.bot.of("setMyCommands")[-1]["commands"]][-3:] == ["brief", "loops", "closeout"]


def test_the_thread_port_gives_every_call_that_waits(monkeypatch) -> None:
    handle, _answers = held(monkeypatch)
    assert ThreadService.waiting_tool_calls() == [handle]
    handle.state = "admitted"
    assert ThreadService.waiting_tool_calls() == []


# ── 2. /waiting ──────────────────────────────────────────────────────

def test_waiting_with_nothing_says_so(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting")) == {"action": "waiting", "shown": 0, "more": 0}
    assert texts(d.bot, before) == ["Nothing waits on you."]


def test_waiting_with_three_gives_the_count_then_each_thing(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(3)
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting")) == {"action": "waiting", "shown": 3, "more": 0}
    sent = texts(d.bot, before)
    assert len(sent) == 4 and sent[0] == "<b>3 things wait on you</b>"
    first = d.reads.needs["items"][0]
    assert sent[1].startswith(f"<b>{first['title']}</b>\n")
    assert first["projectName"] in sent[1], "who or what it is from"
    assert "Due today" in sent[1] and "DUE TODAY" not in sent[1], "the reason, in sentence case"
    assert "Waits " in sent[1], "since when"


def test_waiting_with_twelve_shows_eight_and_one_line_for_the_rest(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(12)
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting")) == {"action": "waiting", "shown": 8, "more": 4}
    sent = texts(d.bot, before)
    assert len(sent) == 10
    assert sent[0] == "<b>12 things wait on you</b>" and sent[-1].startswith("and 4 more on your desk.")


def test_a_command_says_so_when_needs_you_cannot_be_read(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.fails = True
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting")) == {"action": "waiting", "read": False}
    assert texts(d.bot, before) == [reach_commands.NOT_READ_WORDS]


def test_a_command_from_another_chat_gets_only_the_refusal(tmp_path) -> None:
    d = desk(tmp_path)
    before = len(d.bot.of("sendMessage"))
    for text in ("/waiting", "/today", "/status", "/quiet 2h", "/help"):
        assert d.tg.handle_update(say(text, chat=424242)) == {"action": "rejected"}
    sent = d.bot.of("sendMessage")[before:]
    assert [row["text"] for row in sent] == ["This chat is not paired."] * 5
    assert d.reach.quiet_until() is None, "another chat changes nothing"


# ── 8. a held tool call: what it will write, Deny first, the guarded path ──

def test_a_held_tool_call_shows_its_facts_with_deny_first_and_a_press_answers(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    handle, answers = held(monkeypatch)
    d.reads.calls = [handle]
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting"))["shown"] == 1
    count, call = d.bot.of("sendMessage")[before:]
    assert count["text"] == "<b>1 thing waits on you</b>"
    assert "Email Dana about the cutover date" in call["text"], "what it will write"
    assert "It runs one time." in call["text"]
    row = call["reply_markup"]["inline_keyboard"][0]
    assert [button["text"] for button in row] == ["Deny", "Allow once"], "Allow is never the first button"
    assert all(len(button["callback_data"].encode("utf-8")) <= 64 for button in row)
    done = d.tg.handle_update(press(row[1]["callback_data"]))
    assert done == {"action": "held", "decision": "approve"}
    assert answers == [("call-1", "approve")], "through the one guarded answer path"
    edit = d.bot.of("editMessageText")[-1]
    assert "Allowed one time" in edit["text"] and "reply_markup" not in edit


def test_a_stale_press_on_a_held_call_is_refused_and_the_message_says_it_changed(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    handle, answers = held(monkeypatch)
    d.reads.calls = [handle]
    before = len(d.bot.of("sendMessage"))
    d.tg.handle_update(say("/waiting"))
    row = d.bot.of("sendMessage")[before:][1]["reply_markup"]["inline_keyboard"][0]
    seen = held_call_details(handle, OWNER)["binding"]
    handle.args = {"task": "Email everyone the cutover date"}   # the call changed after he read it
    handle.resolved_args = None
    assert held_call_details(handle, OWNER)["binding"] != seen
    refused = d.tg.handle_update(press(row[1]["callback_data"]))
    assert refused["action"] == "held_refused" and refused["code"] == "answer_stale"
    assert answers == [], "nothing was decided"
    assert reach_commands.HELD_CHANGED_WORDS in d.bot.of("editMessageText")[-1]["text"]


def test_a_press_on_a_call_that_is_gone_decides_nothing(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    _handle, answers = held(monkeypatch)
    assert d.tg.handle_update(press("r1|held|nokey00000|a"))["action"] == "held_gone"
    assert answers == []


def test_a_new_held_call_travels_one_time_with_its_facts(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    handle, _answers = held(monkeypatch)
    d.reads.calls = [handle]
    before = len(d.bot.of("sendMessage"))
    assert d.reach.tick()["noticed"] == ["held:call-1"]
    assert d.reach.tick()["noticed"] == [], "one key for one call and its details: not a second time"
    sent = d.bot.of("sendMessage")[before:]
    assert len(sent) == 1 and "Email Dana about the cutover date" in sent[0]["text"]
    # The row at rest holds the call's identity and revision, never its words.
    kept = json.dumps(d.tg._policy("reach_telegram_outbox"))
    assert "Email Dana" not in kept and str(OWNER_CHAT) not in kept


# ── 3. /today ────────────────────────────────────────────────────────

def test_today_gives_the_day_in_six_lines_at_most(tmp_path) -> None:
    d = desk(tmp_path)
    event = d.reads.answer["day"]["upcoming"][0]
    event["starts_at"] = "2026-11-13T21:30:00+00:00"
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/today")) == {"action": "today"}
    (sent,) = d.bot.of("sendMessage")[before:]
    lines = sent["text"].split("\n")
    assert lines[0].startswith("<b>Today · ") and len(lines) <= 8
    assert any(event["title"] in line for line in lines), "the meeting ahead, with its time"
    assert any("wait on you" in line or "waits on you" in line for line in lines)
    assert any("due today" in line for line in lines)
    assert sent["reply_markup"]["inline_keyboard"][0][0] == {"text": "What waits", "callback_data": "r1|cmd|waiting"}
    # The button asks what /waiting asks.
    assert d.tg.handle_update(press("r1|cmd|waiting"))["action"] == "waiting"


# ── 4. /quiet ────────────────────────────────────────────────────────

def test_quiet_holds_a_send_and_releases_it_after(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    send = {"ref": "send:1", "id": "send:1", "source": "send", "kind": "send",
            "title": "Weekly report waits for your press", "why": "PREPARED", "since": DAY}
    d.reads.needs["items"] = [send]
    d.reads.needs["members"] = [{"ref": "send:1", "kind": "attention"}]
    d.reads.needs["count"] = 1
    before = len(d.bot.of("sendMessage"))
    made = d.tg.handle_update(say("/quiet 2h"))
    assert made["action"] == "quiet" and made["until"].startswith("2026-11-13T21:00")
    answer = texts(d.bot, before)
    assert len(answer) == 1 and answer[0].startswith("<b>Quiet until "), "the answer says until when, and goes now"
    assert d.reach.status(OWNER)["quiet_hours"]["now"] is True
    assert d.reach.status(OWNER)["quiet_hours"]["until"].startswith("2026-11-13T21:00")
    # The Send waits: nothing comes until then.
    assert d.reach.tick().get("noticed") in (None, [])
    assert len(texts(d.bot, before)) == 1, "no message until then"
    d.clock.at = "2026-11-13T21:00:30+00:00"
    d.reach.tick()
    sent = texts(d.bot, before)
    assert len(sent) == 2 and sent[1].startswith("<b>Weekly report waits for your press</b>")


def test_quiet_off_ends_it_and_words_that_are_not_understood_change_nothing(tmp_path) -> None:
    d = desk(tmp_path)
    d.tg.handle_update(say("/quiet 90m"))
    assert d.reach.quiet_until() is not None
    assert d.tg.handle_update(say("/quiet off"))["until"] is None
    assert d.reach.quiet_until() is None and d.reach.is_quiet(d.reach.now()) is False
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/quiet for ever")) == {"action": "quiet", "understood": False}
    assert texts(d.bot, before) == [reach_commands.QUIET_HELP] and d.reach.quiet_until() is None


def test_quiet_alone_is_until_the_end_of_quiet_hours(tmp_path) -> None:
    d = desk(tmp_path)
    from holdspeak.services.reach_service import quiet_end_after

    made = d.tg.handle_update(say("/quiet"))
    assert d.reach.quiet_until() == quiet_end_after(d.reach.now(), d.reach.quiet())
    assert made["until"] is not None


# ── 5. /status ───────────────────────────────────────────────────────

def test_status_says_the_desk_the_health_the_count_the_mode_and_quiet(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(2)
    d.tg.handle_update(say("/quiet 2h"))
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/status")) == {"action": "status"}
    (sent,) = texts(d.bot, before)
    assert sent.startswith("<b>Your desk on Karol's Mac</b>\n")
    assert "Telegram answers." in sent and "2 things wait on you." in sent
    assert "Messages: At once." in sent and "Quiet until " in sent and "Last message here: " in sent


def test_help_lists_the_menu_and_cadences_commands(tmp_path) -> None:
    d = desk(tmp_path)
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/help")) == {"action": "help"}
    (sent,) = texts(d.bot, before)
    for name in ("/waiting", "/today", "/quiet", "/status", "/help", "/brief", "/loops", "/closeout"):
        assert name in sent
    assert "Only this chat can answer." in sent


# ── 6. what travels ──────────────────────────────────────────────────

def _sends(reads: Reads, count: int) -> None:
    rows = [{"ref": f"send:{index}", "id": f"send:{index}", "source": "send", "kind": "send",
             "title": f"Report {index} waits for your press", "why": "PREPARED", "since": DAY}
            for index in range(count)]
    reads.needs["items"] = rows
    reads.needs["members"] = [{"ref": row["ref"], "kind": "attention"} for row in rows]
    reads.needs["count"] = count
    reads.needs["failedMeetings"] = []


def test_a_new_waiting_send_makes_one_notice_and_no_second_one(tmp_path) -> None:
    d = desk(tmp_path)
    _sends(d.reads, 1)
    before = len(d.bot.of("sendMessage"))
    assert d.reach.tick()["noticed"] == ["send:0"]
    assert d.reach.tick()["noticed"] == []
    sent = d.bot.of("sendMessage")[before:]
    assert len(sent) == 1 and sent[0]["text"].startswith("<b>Report 0 waits for your press</b>")
    assert "reply_markup" not in sent[0], "a send is pressed on the desk: the notice has the way there, no answer button"
    # It says another thing: it is new, and it travels again.
    d.reads.needs["items"][0]["title"] = "Report 0 was changed and waits for your press"
    assert d.reach.tick()["noticed"] == ["send:0"]
    assert len(d.bot.of("sendMessage")[before:]) == 2


def test_a_thing_that_is_due_does_not_travel_one_by_one(tmp_path) -> None:
    d = desk(tmp_path)
    sources = {str(row.get("source")) for row in d.reads.needs["items"]}
    assert sources and not sources & set(reach_commands.NOTICE_SOURCES), "the recorded rows are due things"
    d.reads.needs["failedMeetings"] = []
    before = len(d.bot.of("sendMessage"))
    assert d.reach.tick()["noticed"] == []
    assert texts(d.bot, before) == []


def test_the_chat_gets_at_most_six_messages_in_ten_minutes_and_the_rest_is_in_the_digest(tmp_path) -> None:
    d = desk(tmp_path)
    _sends(d.reads, 9)
    before = len(d.bot.of("sendMessage"))
    assert len(d.reach.tick()["noticed"]) == 6
    assert len(d.reach.tick()["noticed"]) == 0, "the rest is not sent one by one later"
    assert len(d.bot.of("sendMessage")[before:]) == 6
    assert len(d.reach._held_back(d.reach.now())) == 3
    made = d.tg.digest([], day_lines=["No meetings ahead today."], more=3)
    assert "and 3 more on your desk." in made["text"]


# ── 7. the morning brief, and "Back at" ──────────────────────────────

def test_the_morning_brief_is_the_day_and_what_waits_in_one_message(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.answer["day"]["upcoming"][0]["starts_at"] = "2026-11-13T21:30:00+00:00"
    lines = d.reach._day_lines(d.tg, d.reach.now())
    assert lines and len(lines) <= 6
    before = len(d.bot.of("sendMessage"))
    item = {"kind": "core_question", "program_title": "Payments ledger cutover", "ordinal": 4}
    d.tg.digest([item], day_lines=lines)
    (sent,) = texts(d.bot, before)
    assert sent.startswith("<b>1 waits on you</b>\n")
    assert d.reads.answer["day"]["upcoming"][0]["title"] in sent and "Payments ledger cutover" in sent


def test_back_at_is_said_one_time_after_the_desk_was_down_and_things_waited(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(3)
    d.reach.tick()                       # the desk runs: it notes that it is alive
    before = len(d.bot.of("sendMessage"))
    d.clock.at = "2026-11-13T19:05:00+00:00"
    again = ReachService(d.db, programs=lambda: Programs(), telegram=lambda: d.tg, clock=d.clock)
    again.tick()
    assert texts(d.bot, before) == [], "five minutes is not down"
    d.clock.at = "2026-11-13T20:00:00+00:00"
    later = ReachService(d.db, programs=lambda: Programs(), telegram=lambda: d.tg, clock=d.clock)
    later.tick()
    later.tick()
    sent = d.bot.of("sendMessage")[before:]
    assert len(sent) == 1, "one time"
    assert sent[0]["text"].startswith("Back at ") and "3 things waited." in sent[0]["text"]
    assert sent[0]["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == "r1|cmd|waiting"


def test_nothing_is_said_when_the_desk_comes_back_and_nothing_waits(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    d.reach.tick()
    before = len(d.bot.of("sendMessage"))
    d.clock.at = "2026-11-13T20:00:00+00:00"
    ReachService(d.db, programs=lambda: Programs(), telegram=lambda: d.tg, clock=d.clock).tick()
    assert texts(d.bot, before) == []
