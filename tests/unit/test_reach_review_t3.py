"""The review of the Telegram commands (#2304), fixed forward.

Who can answer (a private chat and the connected user only; a button key is
random, of one pairing, one message and one call); People content never
travels (a count and a kind); a message that does not show the whole call
has no Allow; a message over the chat's budget waits and goes later, and the
budget is kept in the outbox store; a held tool call is a member of the one
Needs you membership; an Open button carries no token.

Telegram is a fake transport, the hub's reads are the recorded answer, the
clock is a value. Nothing here calls Telegram.
"""
from __future__ import annotations

import copy
import json
from types import SimpleNamespace
from typing import Any

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import needs_you_membership, reach_commands, telegram_reach
from holdspeak.services.reach_service import ReachService
from holdspeak.services.telegram_reach import PAIR_PRIVATE_WORDS, TelegramReach
from holdspeak.services.telegram_writer import Message, payload, safe_open_url
from holdspeak.services.thread_service import ThreadService
from holdspeak.services.thread_tools import ToolCallHandle
from holdspeak.services.thread_turns import _ToolExecutorAggregator
from tests.unit.test_reach_commands import DAY, Programs, Reads, _sends, desk, held, press, say, texts
from tests.unit.test_reach_telegram import OWNER_CHAT, keystore, update  # noqa: F401
from tests.unit.test_reach_telegram_setup import OWNER, TOKEN, Bot, Clock

DESK = "https://desk.tail0000.ts.net"
OTHER_USER = 777000111


def unpaired(tmp_path) -> SimpleNamespace:
    from holdspeak.db import Database

    clock = Clock()
    clock.at = DAY
    db = Database(tmp_path / "reach.db")
    bot = Bot()
    box: dict[str, Any] = {}
    reach = ReachService(db, programs=lambda: Programs(), telegram=lambda: box["tg"], clock=clock)
    tg = TelegramReach(db, caller=bot, reach=reach, clock=clock, programs=lambda: Programs())
    box["tg"] = tg
    tg.reads = Reads()
    tg.save_token(OWNER, TOKEN)
    return SimpleNamespace(tg=tg, bot=bot, db=db, reach=reach, reads=tg.reads, clock=clock)


def held_buttons(d: SimpleNamespace, since: int) -> tuple[dict[str, Any], int]:
    """The held call's message of the sends after ``since``, and its message id."""
    sends = d.bot.of("sendMessage")
    index = next(i for i in range(since, len(sends)) if "A tool call waits for you" in sends[i]["text"])
    return sends[index], d.bot.next_id - (len(sends) - 1 - index)


# ── 1. who can answer ────────────────────────────────────────────────

def test_a_pair_command_in_a_group_is_refused_and_pairs_nothing(tmp_path) -> None:
    d = unpaired(tmp_path)
    for kind in ("group", "supergroup", "channel"):
        code = d.tg.start_pairing(OWNER)["code"]
        for text in (f"/pair {code}", f"/start {code}"):
            asked = update("pair", code=code)
            asked["message"]["text"] = text
            asked["message"]["chat"] = {"id": -1001234567890, "title": "The team", "type": kind}
            before = len(d.bot.of("sendMessage"))
            made = d.tg.handle_update(asked)
            assert made["ok"] is False and made["refused"] == "not_private", (kind, text)
            assert texts(d.bot, before) == [PAIR_PRIVATE_WORDS], "one line"
            assert telegram_reach.paired_chat() is None and d.tg.status()["paired"] is None
        d.tg.cancel_pairing(OWNER) if hasattr(d.tg, "cancel_pairing") else None
    # The same code still connects the private chat: the group did not use it up.
    code = (d.tg.status()["pairing"] or {}).get("code") or d.tg.start_pairing(OWNER)["code"]
    assert d.tg.handle_update(update("pair", code=code))["ok"] is True
    stored = json.loads(telegram_reach._read(telegram_reach.CHAT_SLOT))
    assert stored["type"] == "private" and stored["user"] == str(OWNER_CHAT)


def test_a_pairing_that_is_not_a_private_chat_is_not_connected(tmp_path) -> None:
    d = unpaired(tmp_path)
    telegram_reach._write(telegram_reach.CHAT_SLOT, json.dumps({"id": "-1001234567890", "name": "The team"}))
    assert telegram_reach.paired_chat() is None and d.tg.status()["paired"] is None
    telegram_reach._write(telegram_reach.CHAT_SLOT, json.dumps(
        {"id": "-1001234567890", "name": "The team", "type": "supergroup", "user": str(OWNER_CHAT)}))
    assert telegram_reach.paired_chat() is None
    # A pairing made before this fix has no type: a private chat's id is the user's id.
    telegram_reach._write(telegram_reach.CHAT_SLOT, json.dumps({"id": str(OWNER_CHAT), "name": "Karol"}))
    assert telegram_reach.paired_chat()["id"] == str(OWNER_CHAT)
    assert telegram_reach.paired_user() == str(OWNER_CHAT)


def test_a_press_from_another_user_in_the_paired_chat_is_refused(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    handle, answers = held(monkeypatch)
    d.reads.hold(handle)
    before = len(d.bot.of("sendMessage"))
    d.tg.handle_update(say("/waiting"))
    call, message_id = held_buttons(d, before)
    allow = call["reply_markup"]["inline_keyboard"][0][1]["callback_data"]
    other = press(allow, message_id=message_id)
    other["callback_query"]["from"] = {"id": OTHER_USER, "first_name": "Mallory"}
    assert d.tg.handle_update(other) == {"action": "rejected"}
    assert answers == [] and handle.state == "awaiting_decision", "nothing was decided"
    # A command from another user in the same chat is refused too.
    words = say("/quiet 2h")
    words["message"]["from"] = {"id": OTHER_USER, "first_name": "Mallory"}
    assert d.tg.handle_update(words) == {"action": "rejected"}
    assert d.reach.quiet_until() is None
    # A press with no sender at all is not his.
    nobody = press(allow, message_id=message_id)
    del nobody["callback_query"]["from"]
    assert d.tg.handle_update(nobody) == {"action": "rejected"} and answers == []
    # His own press answers.
    assert d.tg.handle_update(press(allow, message_id=message_id)) == {"action": "held", "decision": "approve"}
    assert answers == [("call-1", "approve")]


def test_a_key_of_an_old_generation_is_refused(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    handle, answers = held(monkeypatch)
    d.reads.hold(handle)
    before = len(d.bot.of("sendMessage"))
    d.tg.handle_update(say("/waiting"))
    call, message_id = held_buttons(d, before)
    allow = call["reply_markup"]["inline_keyboard"][0][1]["callback_data"]
    key = allow.split("|")[2]
    assert len(key) >= 16 and "call-1" not in allow, "random: 96 bits, not made from the call"
    kept = copy.deepcopy(d.tg._held_keys[key])
    # He disconnects and connects again: every key is forgotten.
    d.tg.unpair(OWNER)
    assert d.tg._held_keys == {}
    code = d.tg.start_pairing(OWNER)["code"]
    assert d.tg.handle_update(update("pair", code=code))["ok"] is True
    assert d.tg.handle_update(press(allow, message_id=message_id))["action"] == "held_gone"
    # Even a key that was kept from the old pairing answers nothing.
    d.tg._held_keys[key] = kept
    assert kept["gen"] != d.tg._generation()
    refused = d.tg.handle_update(press(allow, message_id=message_id))
    assert refused == {"action": "held_gone", "refused": "another_message"}
    assert answers == [] and handle.state == "awaiting_decision"


def test_a_key_pressed_on_another_message_is_refused(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    handle, answers = held(monkeypatch)
    d.reads.hold(handle)
    before = len(d.bot.of("sendMessage"))
    d.tg.handle_update(say("/waiting"))
    call, message_id = held_buttons(d, before)
    allow = call["reply_markup"]["inline_keyboard"][0][1]["callback_data"]
    refused = d.tg.handle_update(press(allow, message_id=message_id + 50))
    assert refused == {"action": "held_gone", "refused": "another_message"} and answers == []


def test_two_calls_never_share_a_key(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    owner = Principal(PrincipalKind.OWNER, "ask")
    # Two calls whose ids start with the same eighteen characters: a key cut
    # from the id would be the same key.
    ids = ("call-0123456789abcdef-one", "call-0123456789abcdef-two")
    handles = {call_id: ToolCallHandle(call_id, "thread-1", "turn-1", "door.add_item", {"task": f"Task of {call_id}"},
                                       "effect_proposal", False, "awaiting_decision", principal=owner)
               for call_id in ids}
    answers: list[Any] = []
    executor = SimpleNamespace(_handles=handles,
                               decide=lambda h, decision, answer=None: answers.append((h.call_id, decision)))
    aggregator = _ToolExecutorAggregator()
    aggregator.register("turn-1", executor)
    monkeypatch.setattr(ThreadService, "_tool_executor", aggregator)
    for handle in handles.values():
        d.reads.hold(handle)
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting"))["shown"] == 2
    sends = d.bot.of("sendMessage")[before:]
    calls = [row for row in sends if "A tool call waits for you" in row["text"]]
    keys = [row["reply_markup"]["inline_keyboard"][0][0]["callback_data"].split("|")[2] for row in calls]
    assert len(keys) == 2 and keys[0] != keys[1]
    assert {d.tg._held_keys[key]["call_id"] for key in keys} == set(ids), "one key, one call"
    # Asked again, the same call gets a new key for its new message: never the old one.
    d.tg.handle_update(say("/waiting"))
    assert len({key for key in d.tg._held_keys}) == 4
    # Deny on the second message denies the second call, not the first.
    second = next(row for row in calls if ids[1] in row["text"] or "one" not in row["text"])
    data = second["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    target = d.tg._held_keys[data.split("|")[2]]
    done = d.tg.handle_update(press(data, message_id=target["message_id"]))
    assert done == {"action": "held", "decision": "deny"} and answers == [(target["call_id"], "deny")]


# ── 2. People content does not travel ────────────────────────────────

NAME = "Dana Whitfield"
WORDS = "Tell Dana about the reorganisation before Friday"


def _people_row() -> dict[str, Any]:
    """A People commitment as the OWNER's web shape holds it: the words and the person."""
    return {"id": "door:people:c-9", "ref": "people:c-9", "source": "people_commitment", "kind": "commitment",
            "title": WORDS, "why": "DUE TODAY", "projectId": "", "projectName": NAME, "personId": "p-1",
            "group": NAME, "since": DAY, "dueAt": DAY[:10], "dueWord": "today", "severity": "warning",
            "openRef": "people:p-1", "_doorCard": {"source": "people_commitment", "title": WORDS, "owner": NAME}}


def test_a_people_commitment_sends_no_word_and_no_name(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    # The reader gives the owner's full shape (the mistake the review found).
    d.reads.needs["items"] = [_people_row()]
    d.reads.needs["members"] = [{"ref": "people:c-9", "kind": "attention"}]
    d.reads.needs["count"] = 1
    d.reads.needs.pop("peopleWithheld", None)
    before = len(d.bot.calls)
    assert d.tg.handle_update(say("/waiting"))["shown"] == 1
    assert d.tg.handle_update(say("/today")) == {"action": "today"}
    assert d.tg.handle_update(say("/status")) == {"action": "status"}
    d.reach.tick()
    lines = d.reach._day_lines(d.tg, d.reach.now())
    d.tg.digest([], day_lines=lines)
    d.clock.at = "2026-11-13T20:00:00+00:00"        # the desk was down: "Back at"
    ReachService(d.db, programs=lambda: Programs(), telegram=lambda: d.tg, clock=d.clock).tick()
    sent = json.dumps(d.bot.calls[before:])
    for secret in (WORDS, NAME, "Dana", "reorganisation", "c-9", "p-1"):
        assert secret not in sent, secret
    assert secret not in json.dumps(d.tg._policy("reach_telegram_outbox"))
    said = [row["text"] for row in d.bot.of("sendMessage")]
    assert any(text.startswith("<b>1 commitment is due today</b>") for text in said), "a count and a kind"
    assert "Open it on your desk." in "\n".join(said)


def test_two_people_commitments_are_one_message_with_a_count(tmp_path) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    first, second = _people_row(), {**_people_row(), "id": "door:people:c-10", "ref": "people:c-10", "why": "WAITS"}
    d.reads.needs["items"] = [first, second]
    d.reads.needs["members"] = [{"ref": row["ref"], "kind": "attention"} for row in (first, second)]
    d.reads.needs["count"] = 2
    before = len(d.bot.of("sendMessage"))
    d.tg.handle_update(say("/waiting"))
    sent = texts(d.bot, before)
    assert sent[0] == "<b>2 things wait on you</b>"
    assert sent[1].startswith("<b>2 commitments wait on you</b>") and "Open them on your desk." in sent[1]
    assert len(sent) == 2 and NAME not in json.dumps(sent) and "Tell Dana" not in json.dumps(sent)


def test_the_hub_reads_ask_for_the_withheld_shape(monkeypatch) -> None:
    asked: list[tuple[str, str]] = []

    def invoke(principal, name, args, held=None, shape="web"):
        asked.append((name, shape))
        if name == "desk.needs_you":
            answer = {"items": [_people_row()], "members": [{"ref": "people:c-9", "kind": "attention"}], "count": 1}
            return needs_you_membership.withhold_people_content(answer) if shape == "call" else answer
        return {"needs_you": {"items": []}, "day": {}}

    root = SimpleNamespace(operations=SimpleNamespace(invoke=invoke), door_service=SimpleNamespace())
    monkeypatch.setattr("holdspeak.runtime.composition.current", lambda: root)
    reads = reach_commands.Reads()
    needs = reads.needs_you(OWNER)
    reads.today(OWNER)
    assert asked == [("desk.needs_you", "call"), ("today.get", "call")], "never the owner's web shape"
    assert needs["peopleWithheld"] is True and NAME not in json.dumps(needs) and WORDS not in json.dumps(needs)
    assert needs["count"] == 1, "it is still counted"


# ── 3. no Allow for a call he cannot read whole ──────────────────────

def test_a_held_call_whose_facts_do_not_fit_has_no_allow(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    long = "Email every customer the cutover date and the new price list. " * 120
    handle, answers = held(monkeypatch, {"task": long})
    d.reads.hold(handle)
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting"))["shown"] == 1
    call, message_id = held_buttons(d, before)
    assert len(call["text"]) <= 4096
    assert reach_commands.HELD_CUT_WORDS in call["text"], "the message says that it does not show all of it"
    labels = [button["text"] for row in call["reply_markup"]["inline_keyboard"] for button in row]
    assert "Allow once" not in labels and labels[0] == "Deny"
    # A call with many facts that are each short enough, and together too long, is cut by the writer: the same rule.
    many = {"call_id": "c", "words": "Add an item", "binding": {}, "facts": [
        {"label": f"Part {index}", "value": "Many words in this fact. " * 20} for index in range(12)]}
    assert reach_commands.held_facts_whole(many) is True
    cut, key = d.tg._held_message(many)
    assert d.tg._held_keys.pop(key)["allow"] is False and [b.text for row in cut.buttons for b in row] == ["Deny"]
    # A made-up Allow press with this message's key is refused: nothing runs.
    deny = call["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    forged = deny[:-1] + "a"
    assert d.tg.handle_update(press(forged, message_id=message_id)) == {"action": "held_refused", "code": "not_whole"}
    assert answers == [] and handle.state == "awaiting_decision"
    # Deny still works here.
    assert d.tg.handle_update(press(deny, message_id=message_id)) == {"action": "held", "decision": "deny"}


def test_a_held_call_that_travels_by_itself_and_does_not_fit_has_no_allow(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(0)
    handle, _answers = held(monkeypatch, {"task": "Email every customer the new price list. " * 120})
    d.reads.hold(handle)
    before = len(d.bot.of("sendMessage"))
    assert d.reach.tick()["noticed"] == ["held:call-1"]
    (pushed,) = d.bot.of("sendMessage")[before:]
    assert "Allow once" not in json.dumps(pushed.get("reply_markup")) and reach_commands.HELD_CUT_WORDS in pushed["text"]
    assert pushed["reply_markup"]["inline_keyboard"][0][0]["text"] == "Deny"


def test_the_writer_says_when_a_message_was_cut_and_drops_its_deciding_buttons() -> None:
    from holdspeak.services.telegram_reach import fence
    from holdspeak.services.telegram_writer import Button, was_cut

    decides = ((Button("Deny", "r1|x|d"), Button("Allow once", "r1|x|a", whole=True)),)
    short = Message(head="A question", lines=("One line.",), buttons=decides)
    assert was_cut(short, fenced=fence) is False
    params, _text = payload("1", short, fenced=fence)
    assert [b["text"] for b in params["reply_markup"]["inline_keyboard"][0]] == ["Deny", "Allow once"]
    long = Message(head="A question", lines=("Many words in this line. " * 400,), buttons=decides)
    assert was_cut(long, fenced=fence) is True
    params, _text = payload("1", long, fenced=fence)
    assert [b["text"] for b in params["reply_markup"]["inline_keyboard"][0]] == ["Deny"]


# ── 4. the budget ────────────────────────────────────────────────────

def test_the_seventh_message_waits_and_goes_after_ten_minutes(tmp_path) -> None:
    d = desk(tmp_path)
    _sends(d.reads, 7)
    before = len(d.bot.of("sendMessage"))
    assert len(d.reach.tick()["noticed"]) == 7
    assert len(d.bot.of("sendMessage")[before:]) == 6
    d.clock.at = "2026-11-13T19:09:00+00:00"
    d.reach.tick()
    d.tg.flush()
    assert len(d.bot.of("sendMessage")[before:]) == 6, "nine minutes: it still waits"
    d.clock.at = "2026-11-13T19:10:30+00:00"
    d.tg.flush()
    sent = d.bot.of("sendMessage")[before:]
    assert len(sent) == 7 and sent[6]["text"].startswith("<b>Report 6 waits for your press</b>")
    d.tg.flush()
    assert len(d.bot.of("sendMessage")[before:]) == 7, "one time"


def test_a_question_goes_before_a_notice_when_the_budget_returns(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    _sends(d.reads, 8)
    before = len(d.bot.of("sendMessage"))
    d.reach.tick()
    assert len(d.bot.of("sendMessage")[before:]) == 6
    handle, _answers = held(monkeypatch)
    d.reads.hold(handle)
    d.reach.tick()
    assert len(d.bot.of("sendMessage")[before:]) == 6, "the question waits too: six is six"
    d.clock.at = "2026-11-13T19:10:30+00:00"
    d.tg.flush()
    sent = d.bot.of("sendMessage")[before:]
    assert len(sent) == 9 and "A tool call waits for you" in sent[6]["text"], "the question first"


def test_the_budget_holds_across_a_new_service_object(tmp_path) -> None:
    d = desk(tmp_path)
    _sends(d.reads, 9)
    before = len(d.bot.of("sendMessage"))
    d.reach.tick()
    assert len(d.bot.of("sendMessage")[before:]) == 6
    # The hub starts again: new objects, the same store.
    box: dict[str, Any] = {}
    reach = ReachService(d.db, programs=lambda: Programs(), telegram=lambda: box["tg"], clock=d.clock)
    again = TelegramReach(d.db, caller=d.bot, reach=reach, clock=d.clock, programs=lambda: Programs())
    box["tg"] = again
    again.reads = d.reads
    assert again.budget_left() == 0
    again.flush()
    reach.tick()
    assert len(d.bot.of("sendMessage")[before:]) == 6, "a restart is not a new budget"
    d.clock.at = "2026-11-13T19:10:30+00:00"
    again.flush()
    assert len(d.bot.of("sendMessage")[before:]) == 9


# ── 5. a held call is a member of Needs you ──────────────────────────

def test_a_held_ask_call_is_in_the_needs_you_membership(monkeypatch) -> None:
    handle, _answers = held(monkeypatch)
    rows = needs_you_membership._read_tool_calls(OWNER)
    assert rows == [{"call_id": "call-1", "thread_id": "thread-1", "words": rows[0]["words"]}]
    answer = needs_you_membership.compute_needs_you(door={}, tool_calls=rows)
    (row,) = [item for item in answer["unmutedItems"] if item.get("source") == needs_you_membership.TOOL_CALL_SOURCE]
    assert row["ref"] == "tool_call:call-1" and row["why"] == "TO APPROVE" and row["openRef"] == "thread:thread-1"
    assert answer["count"] == 1 and [m["ref"] for m in answer["members"]] == ["tool_call:call-1"], "it is counted"
    assert "Email Dana" not in json.dumps(answer), "what it will write is read where he answers, not in the row"
    handle.state = "admitted"
    assert needs_you_membership._read_tool_calls(OWNER) == []


def test_waiting_shows_a_held_call_one_time_and_only_from_the_membership(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    d.reads.keep(2)
    handle, _answers = held(monkeypatch)
    # It waits in the thread port, and Needs you does not hold it: the chat has no second list.
    assert ThreadService.waiting_tool_calls() == [handle]
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting")) == {"action": "waiting", "shown": 2, "more": 0}
    assert not any("A tool call waits" in text for text in texts(d.bot, before))
    # It is a member: it is shown one time, and the number is the membership's number.
    d.reads.hold(handle)
    before = len(d.bot.of("sendMessage"))
    assert d.tg.handle_update(say("/waiting")) == {"action": "waiting", "shown": 3, "more": 0}
    sent = texts(d.bot, before)
    assert sent[0] == "<b>3 things wait on you</b>" and len(sent) == 4
    assert sum("A tool call waits for you" in text for text in sent) == 1
    assert d.tg.waiting_call_ids() == ["call-1"]


# ── 6. Open is a button, and it carries no token ─────────────────────

def test_an_open_button_carries_no_token(tmp_path) -> None:
    d = desk(tmp_path)
    d.tg._link = lambda path: f"{DESK}{path}"
    _sends(d.reads, 1)
    before = len(d.bot.of("sendMessage"))
    d.reach.tick()
    (sent,) = d.bot.of("sendMessage")[before:]
    rows = sent["reply_markup"]["inline_keyboard"]
    assert rows[-1] == [{"text": "Open", "url": f"{DESK}/"}], "the hub's own address and nothing after it"
    assert "Open it on your desk." not in sent["text"] and DESK not in sent["text"], "the button says it"
    assert TOKEN not in json.dumps(sent)
    # A link that could hold a token, or is not the desk's own page, is never a button.
    for unsafe in (f"{DESK}/b/abc123token", f"{DESK}/?t=abc", f"{DESK}/#t=abc", "http://desk.tail0000.ts.net/",
                   f"https://user:pw@desk.tail0000.ts.net/", "tg://resolve?domain=x", "", None):
        assert safe_open_url(unsafe, lambda text: text) is None, unsafe
        params, _text = payload("1", Message(head="A thing waits", desk_words="Open it on your desk.",
                                              open_url=unsafe), fenced=lambda text: text)
        assert "reply_markup" not in params and "Open it on your desk." in params["text"]


def test_with_no_address_the_line_stays_and_there_is_no_button(tmp_path) -> None:
    d = desk(tmp_path)
    d.tg._link = lambda path: None
    _sends(d.reads, 1)
    before = len(d.bot.of("sendMessage"))
    d.reach.tick()
    (sent,) = d.bot.of("sendMessage")[before:]
    assert "reply_markup" not in sent and "Open it on your desk." in sent["text"]
