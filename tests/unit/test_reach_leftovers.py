"""The Telegram leftovers (2026-11-13): times in his clock form, a kept note
in Inbox, a task with all of its words, the evening digest, words that wait
in memory only, and a ``/help`` and a first message that say what works.

Telegram is the fake transport of the rigs; the note, the task and the zone
are the REAL operations on this rig's database.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import pytest

from holdspeak.services import needs_you_membership, reach_commands, reach_inbound
from holdspeak.services.reach_service import ReachRefused, ReachService
from holdspeak.services.telegram_reach import TelegramReach
from holdspeak.services.telegram_writer import clock_text, hour_text
from tests.unit.test_reach_commands import DAY, Programs, _sends, desk, say, texts
from tests.unit.test_reach_inbound import HEARD, buttons, d, notes, press, sent_id, tasks, voice  # noqa: F401
from tests.unit.test_reach_telegram import keystore  # noqa: F401
from tests.unit.test_reach_telegram_setup import OWNER, TOKEN, update

H12 = re.compile(r"\b(1[0-2]|[1-9]):[0-5]\d (AM|PM)\b")
H23 = re.compile(r"\b([01]\d|2[0-3]):[0-5]\d\b")


# ── 1. one clock, in his form ────────────────────────────────────────

def test_the_writer_has_one_clock_in_both_forms() -> None:
    afternoon = datetime(2026, 11, 13, 13, 5).astimezone()
    midnight = datetime(2026, 11, 13, 0, 7).astimezone()
    assert clock_text(afternoon) == "13:05" and clock_text(afternoon, "h23") == "13:05"
    assert clock_text(afternoon, "h12") == "1:05 PM"
    assert clock_text(midnight, "h23") == "00:07" and clock_text(midnight, "h12") == "12:07 AM"
    assert clock_text(afternoon.isoformat(), "h12") == "1:05 PM", "a stamp is read too"
    assert clock_text("not a time", "h12") == ""
    assert hour_text(18) == "18:00" and hour_text(18, "h12") == "6:00 PM" and hour_text(0, "h12") == "12:00 AM"


def test_the_clock_form_is_one_reach_setting(tmp_path) -> None:
    made = desk(tmp_path)
    assert made.reach.settings()["hour_cycle"] == "h23" and made.reach.status(OWNER)["hour_cycle"] == "h23"
    made.reach.save_settings(OWNER, {"hour_cycle": "h12"})
    assert made.reach.status(OWNER)["hour_cycle"] == "h12"
    with pytest.raises(ReachRefused):
        made.reach.save_settings(OWNER, {"hour_cycle": "h24"})
    assert made.reach.settings()["hour_cycle"] == "h12"


@pytest.mark.parametrize("cycle,has,has_not", [("h12", H12, None), ("h23", H23, re.compile(r" (AM|PM)\b"))])
def test_every_time_the_bot_says_is_in_his_form(tmp_path, cycle, has, has_not) -> None:
    made = desk(tmp_path)
    made.reach.save_settings(OWNER, {"hour_cycle": cycle})
    made.reads.answer["day"]["upcoming"][0]["starts_at"] = "2026-11-13T21:30:00+00:00"
    said: list[str] = []
    before = len(made.bot.of("sendMessage"))
    made.tg.handle_update(say("/today"))
    made.tg.handle_update(say("/quiet 2h"))
    made.tg.handle_update(say("/status"))
    said += texts(made.bot, before)
    assert len(said) == 3
    said.append(reach_commands.back_message(made.reach.now(), 2, cycle=made.reach.hour_cycle()).lines[0])
    said.append(made.tg.clock_of(DAY))
    said.append(made.reach.clock(made.reach.now()))
    for text in said:
        assert has.search(text), (cycle, text)
        if has_not is not None:
            assert not has_not.search(text), (cycle, text)
    if cycle == "h12":
        for text in said:
            assert not re.search(r"\b\d\d:\d\d(?! (AM|PM))", text.replace("10:", "x:").replace("11:", "x:")
                                 .replace("12:", "x:")), text


def test_the_decided_line_and_the_kept_line_are_in_his_form(d) -> None:  # noqa: F811
    d.reach.save_settings(OWNER, {"hour_cycle": "h12"})
    d.tg.handle_update(voice())
    d.tg.handle_update(press(dict(buttons(d.bot))["Keep as a note"], sent_id(d.bot)))
    assert H12.search(d.bot.of("editMessageText")[-1]["text"])


# ── 3. a kept note is in Inbox; a task has all of its words ──────────

def _inbox_members(db: Any) -> list[str]:
    from holdspeak.mcp.tools import dispatch
    from holdspeak.services.automation_runs import inbox_directory_id

    rows = dispatch("zone.list_members", {"directory_id": inbox_directory_id(db)}, OWNER)
    rows = rows.get("members", rows) if isinstance(rows, dict) else rows
    return [str(row.get("primitive_id")) for row in rows if not row.get("deleted")]


def test_a_kept_note_is_filed_in_inbox_and_the_bot_says_so(d) -> None:  # noqa: F811
    d.tg.handle_update(voice())
    out = d.tg.handle_update(press(dict(buttons(d.bot))["Keep as a note"], sent_id(d.bot)))
    assert out["action"] == "noted"
    (note,) = notes(d.db)
    assert _inbox_members(d.db) == [f"note:{note['id']}"]
    assert "Kept in Inbox" in d.bot.of("editMessageText")[-1]["text"]
    assert d.bot.of("answerCallbackQuery")[-1]["text"] == "Kept in Inbox."


def test_a_desk_with_no_inbox_keeps_the_note_and_does_not_say_inbox(d) -> None:  # noqa: F811
    from holdspeak.services.automation_runs import INBOX_DIRECTORY_ID, inbox_directory_id

    inbox_directory_id(d.db)
    d.db.directories.delete(INBOX_DIRECTORY_ID)
    d.tg.handle_update(voice())
    d.tg.handle_update(press(dict(buttons(d.bot))["Keep as a note"], sent_id(d.bot)))
    assert len(notes(d.db)) == 1
    last = d.bot.of("editMessageText")[-1]["text"]
    assert "Kept as a note on your desk" in last and "Inbox" not in last


def test_a_task_has_all_of_the_words_because_it_has_no_detail_field(d) -> None:  # noqa: F811
    d.tg.handle_update(voice())
    out = d.tg.handle_update(press(dict(buttons(d.bot))["Make it a task"], sent_id(d.bot)))
    assert out["action"] == "tasked"
    assert tasks(d.db) == [HEARD.rstrip(".")], "the second sentence is not lost"
    assert "Added as a task: Ask Dana for the cutover window" in d.bot.of("editMessageText")[-1]["text"]


# ── 4. the evening digest ────────────────────────────────────────────

def _evening(tmp_path) -> Any:
    made = desk(tmp_path)
    made.reach.quiet = lambda: (0, 0)
    _sends(made.reads, 3)                         # three things that came in today (``since`` is DAY)
    return made


def _tick_at(made: Any, stamp: str) -> list[dict[str, Any]]:
    made.clock.at = stamp
    before = len(made.bot.of("sendMessage"))
    made.reach.tick()
    return [row for row in made.bot.of("sendMessage")[before:] if "came in today" in row["text"]]


def test_the_evening_digest_is_off_until_he_turns_it_on(tmp_path) -> None:
    made = _evening(tmp_path)
    digest = made.reach.status(OWNER)["digest"]
    assert (digest["evening"], digest["evening_words"], digest["evening_hour"]) == ("off", "Off", 18)
    hour = made.reach.now().astimezone().hour
    made.reach.save_settings(OWNER, {"evening_hour": hour})
    assert _tick_at(made, DAY) == []
    for bad in ({"evening": "yes"}, {"evening_hour": 24}, {"evening_hour": "18"}, {"evening_hour": True}):
        with pytest.raises(ReachRefused):
            made.reach.save_settings(OWNER, bad)


def test_the_evening_digest_goes_one_time_at_his_hour_with_the_count_first(tmp_path) -> None:
    made = _evening(tmp_path)
    hour = made.reach.now().astimezone().hour
    made.reach.save_settings(OWNER, {"evening": "on", "evening_hour": (hour + 1) % 24})
    assert _tick_at(made, DAY) == [], "not his hour"
    made.reach.save_settings(OWNER, {"evening_hour": hour})
    (sent,) = _tick_at(made, DAY)
    lines = sent["text"].split("\n")
    assert lines[0] == "<b>3 things came in today and still wait</b>"
    assert "Report 0 waits for your press" in sent["text"]
    assert sent["reply_markup"]["inline_keyboard"][-1][0]["callback_data"] == "r1|cmd|waiting"
    assert _tick_at(made, "2026-11-13T19:20:00+00:00") == [], "one a day"
    # Through the outbox: the key of the day is marked as sent there.
    from holdspeak.services.telegram_reach import OUTBOX_POLICY

    assert any(str(key).startswith("evening:") for key in made.tg._policy(OUTBOX_POLICY).get("sent") or {})


def test_the_evening_digest_says_nothing_when_nothing_came_in_or_in_quiet(tmp_path) -> None:
    made = _evening(tmp_path)
    hour = made.reach.now().astimezone().hour
    made.reach.save_settings(OWNER, {"evening": "on", "evening_hour": hour})
    for row in made.reads.needs["items"]:
        row["since"] = "2026-11-11T10:00:00+00:00"     # it waits from another day
    assert _tick_at(made, DAY) == []
    for row in made.reads.needs["items"]:
        row["since"] = DAY
    made.tg.handle_update(say("/quiet 2h"))
    assert _tick_at(made, DAY) == [], "quiet"
    made.tg.handle_update(say("/quiet off"))
    made.reach.save_settings(OWNER, {"telegram": "off"})
    assert _tick_at(made, DAY) == [], "Telegram is Off"


def test_people_are_a_count_in_the_evening_digest(tmp_path) -> None:
    made = _evening(tmp_path)
    rows = made.reads.needs["items"]
    # The reader gives the OWNER's shape by mistake: the door to the chat withholds it.
    rows[0].update({"source": needs_you_membership.PEOPLE_SOURCE, "kind": "people_commitment",
                    "title": "Tell Dana her review moved", "personName": "Dana Whitfield"})
    made.reads.needs.pop("peopleWithheld", None)
    hour = made.reach.now().astimezone().hour
    made.reach.save_settings(OWNER, {"evening": "on", "evening_hour": hour})
    (sent,) = _tick_at(made, DAY)
    text = sent["text"]
    lines = text.split("\n")
    assert lines[0] == "<b>2 things came in today and still wait</b>" and "1 commitment waits on you." in lines
    assert "Dana" not in text and "review moved" not in text


# ── 5. words that wait are in memory only ────────────────────────────

def _row(tg: Any) -> dict[str, Any]:
    return dict(tg._policy(reach_inbound.INBOUND_POLICY).get("pending") or {})


def test_no_word_he_sent_is_written_to_the_store(d) -> None:  # noqa: F811
    d.tg.handle_update(voice())
    d.tg.handle_update(say("The vendor wants the contract by the 20th"))
    rows = _row(d.tg)
    assert len(rows) == 2
    for row in rows.values():
        assert set(row) <= {"kind", "gen", "message_id", "at", "used"}
    at_rest = json.dumps(d.tg._policy(reach_inbound.INBOUND_POLICY))
    assert "Dana" not in at_rest and "vendor" not in at_rest
    with d.db._connection() as conn:
        dump = " ".join(str(value) for row in conn.execute("SELECT * FROM cadence_policies").fetchall() for value in row)
    assert "cutover window" not in dump and "vendor" not in dump


def test_after_a_restart_the_press_says_it_was_too_long_ago_and_writes_nothing(d) -> None:  # noqa: F811
    d.tg.handle_update(voice())
    key_data = dict(buttons(d.bot))["Keep as a note"]
    again = TelegramReach(d.db, caller=d.bot, reach=d.reach, clock=d.clock, programs=lambda: Programs())
    again.reads = d.reads
    out = again.handle_update(press(key_data, sent_id(d.bot)))
    assert out["action"] == "inbound_gone"
    assert d.bot.of("answerCallbackQuery")[-1]["text"] == "That was too long ago. Send it again."
    assert notes(d.db) == [] and tasks(d.db) == [] and _row(again) == {}


def test_words_a_hub_before_this_one_wrote_leave_the_row_on_the_tick(d) -> None:  # noqa: F811
    d.tg._save_policy(reach_inbound.INBOUND_POLICY, {"pending": {"k1": {
        "words": "Old plain words", "kind": "text", "gen": d.tg._generation(), "message_id": 4,
        "at": __import__("time").time()}}})
    reach_inbound.tick(d.tg)
    assert "Old plain words" not in json.dumps(d.tg._policy(reach_inbound.INBOUND_POLICY))


# ── 6. the first message and /help say what works now ────────────────

def test_the_pairing_message_says_what_this_chat_can_do(tmp_path) -> None:
    made = desk(tmp_path)
    first = texts(made.bot)[-1]
    assert first == ("This chat is now connected to your desk on Karol's Mac.\n\nYou can:\n"
                     "• Answer what waits on you\n• Get your day each morning\n"
                     "• Send a voice note or a thought\n\nOnly this chat can answer.")


def test_the_first_message_has_no_morning_line_when_the_brief_is_off(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("holdspeak.services.reach_service.carries_cadence", lambda db: True)
    made = desk(tmp_path)
    made.reach.save_settings(OWNER, {"brief": "off"})
    before = len(made.bot.of("sendMessage"))
    made.tg.handle_update(say("/start"))
    (sent,) = texts(made.bot, before)
    assert sent.startswith("This chat is connected to your desk on Karol's Mac.")
    assert "each morning" not in sent and "• Send a voice note or a thought" in sent


def test_help_names_each_thing_that_works_and_no_other(tmp_path) -> None:
    made = desk(tmp_path)
    before = len(made.bot.of("sendMessage"))
    made.tg.handle_update(say("/help"))
    (sent,) = texts(made.bot, before)
    for line in ("/waiting · What waits on you", "/today · Your day", "/quiet · No messages for a time",
                 "/status · Your desk and this chat", "/help · What you can send",
                 "A voice note: I write the words I hear. You keep them in Inbox, or as a task.",
                 "Words with no question: you keep them in Inbox, or ask your desk.",
                 "To answer a question: press its button, or reply to its message.",
                 "Only this chat can answer."):
        assert line in sent, line


# ── review T5 ────────────────────────────────────────────────────────

def test_an_evening_digest_that_waits_is_not_sent_after_he_turns_it_off(tmp_path) -> None:
    made = _evening(tmp_path)
    hour = made.reach.now().astimezone().hour
    made.reach.save_settings(OWNER, {"evening": "on", "evening_hour": hour})
    made.bot.instead["sendMessage"] = {"ok": False, "error_code": 429, "description": "Too Many Requests",
                                       "parameters": {"retry_after": 40}}
    _tick_at(made, DAY)                          # Telegram refuses it: the digest waits in the outbox
    del made.bot.instead["sendMessage"]
    made.reach.save_settings(OWNER, {"evening": "off"})
    made.clock.at = "2026-11-13T19:01:00+00:00"
    before = len(made.bot.of("sendMessage"))
    made.tg.flush()
    assert [row for row in made.bot.of("sendMessage")[before:] if "came in today" in row["text"]] == []


def test_words_too_large_for_the_memory_are_not_kept(d) -> None:  # noqa: F811
    assert reach_inbound._keep(d.tg, "é" * reach_inbound.WORDS_MAX_BYTES, "voice") is None
    assert reach_inbound._memory(d.tg) == {} and _row(d.tg) == {}
    assert reach_inbound._keep(d.tg, "Call Dana tomorrow", "voice")
