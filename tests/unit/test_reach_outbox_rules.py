"""The Telegram outbox, after review T2 of #2300.

1. A message that waits never goes to the chat that was paired before.
2. A send whose arrival is not known is never sent again by itself.
3. Every flush looks at the object again: an answered, withdrawn or changed
   question, or a closed loop, is not sent.
4. The outbox reads quiet hours itself; only an edit goes in them.
5. The writer fences the link and bounds the whole message.
6. A message that can never go ends; it does not stop the others.
7. A chat named in a config file alone is not a pairing.
8. At rest the outbox holds no chat id, no page link and no question's words.

Fake Bot API only; nothing leaves the machine.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import telegram_reach, telegram_writer
from holdspeak.services.telegram_reach import (DROPPED_WORDS, OUTBOX_POLICY, OUTBOX_TRIES_MAX, UNCERTAIN_WORDS,
                                               WAITED_TOO_LONG_WORDS, TelegramReach, fence)
from holdspeak.services.telegram_writer import MAX_TEXT, MORE_WORDS, OPEN_DESK_WORDS, Message
from tests.unit.test_reach_telegram import OWNER_CHAT, TOKEN, keystore, update  # noqa: F401
from tests.unit.test_reach_telegram_setup import Bot, Clock, desk, paired

OWNER = Principal(PrincipalKind.OWNER, "owner")
NEVER_LEFT = {"ok": False, "description": "Connection refused", "undelivered": True}
TIMED_OUT = {"ok": False, "description": "The read operation timed out"}
REF = "program:p:s:core"
QUESTION = "Merge the cutover branch now?"
OTHER_CHAT = 424242


def _at(tg: TelegramReach, stamp: str) -> None:
    tg._clock = lambda: stamp


def _package(tg: TelegramReach, ident: str = "pkg1", question: str = QUESTION) -> None:
    tg.store.add(package_id=ident, kind="item", refs=[REF], token_hash=(ident * 64)[:64],
                 body={"head": "Payments ledger · step 4", "kind": "core", "question": question,
                       "choices": [{"id": "go_on", "label": "Go on", "consequence": "It goes on."}]},
                 created_at="2026-11-13T09:00:00+00:00", expires_at="2026-11-14T09:00:00+00:00")
    tg._reach.open = {REF}


def _row(tg: TelegramReach) -> str:
    """The outbox row as it is stored."""
    return json.dumps(tg._policy(OUTBOX_POLICY), ensure_ascii=False)


def _pair_message(chat_id: int, code: str) -> dict[str, Any]:
    return {"update_id": 7000 + chat_id % 100, "message": {"message_id": 9, "chat": {"id": chat_id, "type": "private"},
                                                           "text": f"/pair {code}",
                                                           "from": {"id": chat_id, "first_name": "B"}}}


def _texts(bot: Bot, start: int = 0) -> list[tuple[str, str]]:
    return [(str(row["chat_id"]), row["text"]) for row in bot.of("sendMessage")[start:]]


# ── 1. another pairing ───────────────────────────────────────────────

def test_a_message_that_waits_never_goes_to_the_chat_that_was_paired_before(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    _package(tg)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    assert tg.send_package("pkg1", "/b/page-token")["queued"] is True
    assert tg.line("A line for the first chat.").get("queued") is True
    del bot.instead["sendMessage"]
    tg.unpair(OWNER)
    assert tg.status()["outbox"]["waiting"] == 0, "what waited was for the chat before"
    assert tg.handle_update(_pair_message(OTHER_CHAT, tg.start_pairing(OWNER)["code"]))["ok"] is True
    before = len(bot.of("sendMessage"))
    _at(tg, "2026-11-13T09:30:00+00:00")
    assert tg.flush()["sent"] == 0
    assert _texts(bot, before) == [], "nothing of the first pairing reaches the second chat, or the first"
    assert tg.store.get("pkg1")["sent"] == [], "the question did not travel"


def test_an_entry_of_another_pairing_that_is_still_in_the_row_is_not_sent(tmp_path) -> None:
    """The store could not be emptied (it was written by another process, or
    the write failed): the entry is still there with the old generation."""
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.line("A line for the first chat.")
    del bot.instead["sendMessage"]
    kept = tg._policy(OUTBOX_POLICY)
    tg.unpair(OWNER)
    tg.handle_update(_pair_message(OTHER_CHAT, tg.start_pairing(OWNER)["code"]))
    tg._save_policy(OUTBOX_POLICY, kept)  # the old entry is back in the row
    before = len(bot.of("sendMessage"))
    _at(tg, "2026-11-13T09:30:00+00:00")
    assert tg.flush()["sent"] == 0 and _texts(bot, before) == []
    assert tg.status()["outbox"]["waiting"] == 0


def test_a_new_token_and_remove_empty_the_outbox(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.line("A line that waits.")
    assert tg.status()["outbox"]["waiting"] == 1
    tg.save_token(OWNER, TOKEN[:-1] + ("A" if TOKEN[-1] != "A" else "B"))
    assert tg.status()["outbox"]["waiting"] == 0
    tg.line("A second line that waits.")
    assert tg.status()["outbox"]["waiting"] == 1
    tg.remove_bot(OWNER, tg.status()["bot"]["username"])
    assert tg._policy(OUTBOX_POLICY).get("items") == []


# ── 2. never two times ───────────────────────────────────────────────

def test_a_timeout_after_the_request_left_is_never_sent_again_by_itself(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    _package(tg)
    before = len(bot.of("sendMessage"))
    bot.instead["sendMessage"] = dict(TIMED_OUT)
    out = tg.send_package("pkg1", "/b/page-token")
    assert out.get("uncertain") is True and "queued" not in out
    del bot.instead["sendMessage"]
    view = tg.status()["outbox"]
    assert view["waiting"] == 0 and view["uncertain"] == 1 and view["uncertain_words"] == UNCERTAIN_WORDS
    _at(tg, "2026-11-13T09:20:00+00:00")
    assert tg.flush()["sent"] == 0
    assert len(bot.of("sendMessage")) == before + 1, "one request left; no second one"
    assert tg._deliver("package:pkg1", {"kind": "package", "ident": "pkg1", "rev": "x", "ref": REF,
                                        "notifies": True})["state"] == "duplicate"
    (row,) = tg.store.get("pkg1")["sent"]
    assert row["uncertain"] is True and "queued" not in row, "the ladder counts it: it does not send the item again"


def test_a_try_that_a_crash_cut_off_is_uncertain_after_the_restart(tmp_path) -> None:
    tg, bot, db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.line("It was being sent when the hub stopped.")
    del bot.instead["sendMessage"]
    state = tg._policy(OUTBOX_POLICY)
    state["items"][0]["state"] = "sending"  # what the row holds while the request is out
    tg._save_policy(OUTBOX_POLICY, state)
    clock = Clock()
    clock.at = "2026-11-13T09:05:00+00:00"
    again, _bot, _db = desk(tmp_path, bot=bot, clock=clock, db=db)
    before = len(bot.of("sendMessage"))
    assert again.flush()["sent"] == 0 and len(bot.of("sendMessage")) == before
    view = again.status()["outbox"]
    assert view["waiting"] == 0 and view["uncertain"] == 1


def test_sending_is_written_on_the_row_before_the_request_leaves(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    seen: list[str] = []

    def spy(token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "sendMessage":
            seen.extend(str(item.get("state")) for item in tg._policy(OUTBOX_POLICY).get("items") or [])
        return bot(token, method, params)

    tg._call = spy
    tg.line("One line.")
    assert seen == ["sending"]


def test_a_sent_key_is_not_forgotten_because_many_keys_came_after_it(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    tg.line("The first line of the day.")
    for index in range(320):
        tg.line(f"Line {index}.")
    before = len(bot.of("sendMessage"))
    tg.line("The first line of the day.")
    assert len(bot.of("sendMessage")) == before, "the first key is still known: it is not sent a second time"


# ── 3. every flush looks at the object again ─────────────────────────

def test_use_here_does_not_send_a_question_that_was_answered_meanwhile(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    _package(tg)
    bot.instead["getUpdates"] = {"ok": False, "error_code": 409, "description": "Conflict"}
    tg.poll_once(None)
    assert tg.send_package("pkg1", "/b/page-token")["queued"] is True
    del bot.instead["getUpdates"]
    tg._reach.open = set()  # he answered it on the desk while Telegram waited
    before = len(bot.of("sendMessage"))
    tg.use_here(OWNER)
    assert len(bot.of("sendMessage")) == before and tg.status()["outbox"]["waiting"] == 0


def test_a_question_that_changed_is_not_sent_with_its_old_words(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    _package(tg)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.send_package("pkg1", "/b/page-token")
    del bot.instead["sendMessage"]
    with tg.db._connection() as conn:
        conn.execute("UPDATE briefing_packages SET body_json=? WHERE id='pkg1'",
                     (json.dumps({"head": "Payments ledger · step 4", "kind": "core", "question": "Hold it?"}),))
    before = len(bot.of("sendMessage"))
    _at(tg, "2026-11-13T09:10:00+00:00")
    assert tg.flush()["sent"] == 0 and len(bot.of("sendMessage")) == before
    assert tg.status()["outbox"]["waiting"] == 0 and tg.store.get("pkg1")["sent"] == []


def test_a_question_is_written_from_the_package_when_it_is_sent(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    _package(tg)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.send_package("pkg1", "/b/page-token")
    del bot.instead["sendMessage"]
    _at(tg, "2026-11-13T09:10:00+00:00")
    assert tg.flush()["sent"] == 1
    sent = bot.of("sendMessage")[-1]
    assert QUESTION in sent["text"] and str(sent["chat_id"]) == str(OWNER_CHAT)
    assert [button["text"] for button in sent["reply_markup"]["inline_keyboard"][0]] == ["Go on", "Later ▾"]


def test_when_the_open_items_cannot_be_read_a_question_waits(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    _package(tg)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.send_package("pkg1", "/b/page-token")
    del bot.instead["sendMessage"]
    tg._reach.unread = True
    before = len(bot.of("sendMessage"))
    _at(tg, "2026-11-13T09:10:00+00:00")
    assert tg.flush()["sent"] == 0 and len(bot.of("sendMessage")) == before
    assert tg.status()["outbox"]["waiting"] == 1, "not read is not 'nothing waits': it is not thrown away"
    tg._reach.unread = False
    assert tg.flush()["sent"] == 1


def test_a_nudge_of_a_loop_that_was_closed_or_snoozed_is_not_sent(tmp_path, monkeypatch) -> None:
    tg, bot, _db = paired(tmp_path)
    loops = {"l1": SimpleNamespace(id="l1", title="Reply to Ana", status="open", snoozed_until=None, stale_score=4.0),
             "l2": SimpleNamespace(id="l2", title="Send the plan", status="open", snoozed_until=None, stale_score=7.0),
             "l3": SimpleNamespace(id="l3", title="Call the bank", status="open", snoozed_until=None, stale_score=2.0)}
    monkeypatch.setattr(tg.db.cadence, "get_loop", lambda ident: loops.get(ident), raising=False)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    for loop in loops.values():
        out = tg.cadence_message(f"cadence-nudge:{loop.id}:2026-11-13", Message(head=loop.title), loop=loop)
        assert out["state"] == "queued"
    del bot.instead["sendMessage"]
    assert "Reply to Ana" not in _row(tg), "the row keeps the loop's identity, not its words"
    loops["l1"].status = "closed"
    loops["l2"].snoozed_until = "2026-11-14T09:00:00+00:00"
    before = len(bot.of("sendMessage"))
    _at(tg, "2026-11-13T09:10:00+00:00")
    assert tg.flush()["sent"] == 1, "only the loop that still stands open"
    (sent,) = bot.of("sendMessage")[before:]
    assert sent["text"].startswith("<b>Call the bank</b>")
    assert tg.status()["outbox"]["waiting"] == 0


def test_a_text_for_one_day_is_not_sent_the_next_day(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.digest([{"kind": "core", "program_title": "P", "ordinal": 1}])
    del bot.instead["sendMessage"]
    before = len(bot.of("sendMessage"))
    _at(tg, "2026-11-14T21:00:00+00:00")
    assert tg.flush()["sent"] == 0 and len(bot.of("sendMessage")) == before
    assert tg.status()["outbox"]["waiting"] == 0


# ── 4. quiet hours ───────────────────────────────────────────────────

def test_use_here_in_quiet_hours_releases_no_message_that_notifies(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["getUpdates"] = {"ok": False, "error_code": 409, "description": "Conflict"}
    tg.poll_once(None)
    tg.line("A line that waits for the owner.")
    del bot.instead["getUpdates"]
    hour = tg.now().astimezone().hour
    tg._reach.quiet_hours = (hour, (hour + 2) % 24)
    before = len(bot.of("sendMessage"))
    tg.use_here(OWNER)
    assert len(bot.of("sendMessage")) == before and tg.status()["outbox"]["waiting"] == 1
    tg._reach.quiet_hours = (0, 0)
    assert tg.flush()["sent"] == 1


def test_a_new_message_does_not_release_the_ones_that_wait_for_the_morning(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.line("A line that waits.")
    del bot.instead["sendMessage"]
    _at(tg, "2026-11-13T09:10:00+00:00")
    hour = tg.now().astimezone().hour
    tg._reach.quiet_hours = (hour, (hour + 2) % 24)
    before = len(bot.of("sendMessage"))
    assert tg.line("His own press: it goes now.")["ok"] is True
    assert [text for _chat, text in _texts(bot, before)] == ["His own press: it goes now."]
    assert tg.status()["outbox"]["waiting"] == 1


def test_when_quiet_hours_cannot_be_read_a_message_that_notifies_waits(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.line("A line that waits.")
    del bot.instead["sendMessage"]
    _at(tg, "2026-11-13T09:10:00+00:00")
    tg._reach.quiet = lambda: (_ for _ in ()).throw(RuntimeError("not read"))
    before = len(bot.of("sendMessage"))
    assert tg.flush()["sent"] == 0 and len(bot.of("sendMessage")) == before


# ── 5. the writer ────────────────────────────────────────────────────

def test_a_link_with_a_secret_in_it_is_not_sent_as_a_link() -> None:
    params, plain = telegram_writer.payload(7, Message(head="Open", link="https://x.example/?password=abc123",
                                                       desk_words="Open it on your desk."), fenced=fence)
    assert "abc123" not in params["text"] and "abc123" not in plain
    assert "x.example" not in params["text"] and params["text"].endswith("Open it on your desk.")
    bare, _ = telegram_writer.payload(7, Message(head="Open", link="https://x.example/?token=abcdefgh12345678"),
                                      fenced=fence)
    assert "abcdefgh12345678" not in bare["text"] and bare["text"].endswith(OPEN_DESK_WORDS)


def test_a_page_link_is_sent_as_it_is() -> None:
    link = "https://hub.example.ts.net/b/zSRsBieXR3oRph2bBp4bHwCIpyyEQZYdPkCV2Xijl4U"
    params, _plain = telegram_writer.payload(7, Message(head="Open", link=link), fenced=fence)
    assert params["text"].endswith(f"Open the page: {link}")


def test_the_whole_message_is_bounded_and_the_lines_after_the_link_too() -> None:
    long_closing = " ".join(["word"] * 1100)  # 5,499 characters in one closing line
    params, plain = telegram_writer.payload(7, Message(head="Head", lines=("One line.",), closing=(long_closing,)))
    assert len(params["text"]) <= MAX_TEXT and MORE_WORDS in params["text"]
    assert params["text"].splitlines()[0] == "<b>Head</b>" and "wordword" not in plain
    many = Message(head="Head", lines=tuple(f"Line {i} " + "x" * 80 for i in range(120)),
                   link="https://hub.example.ts.net/b/abc", closing=("Decided: Merge",) + ("y" * 3000,))
    text = telegram_writer.payload(7, many)[0]["text"]
    assert len(text) <= MAX_TEXT and all(len(line) < 3000 for line in text.splitlines())


# ── 6. a message that can never go ───────────────────────────────────

class _Picky(Bot):
    """Telegram refuses the messages that say "blocked"."""

    def __call__(self, token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "sendMessage" and method not in self.instead and "blocked" in str(params.get("text")):
            self.calls.append((method, json.loads(json.dumps(params))))
            return {"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}
        return super().__call__(token, method, params)


def test_a_403_ends_its_message_and_the_next_one_still_goes(tmp_path) -> None:
    tg, bot, _db = desk(tmp_path, bot=_Picky())
    tg.save_token(OWNER, TOKEN)
    assert tg.handle_update(update("pair", code=tg.start_pairing(OWNER)["code"]))["ok"] is True
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.line("This one is blocked.")
    tg.line("This one is good.")
    del bot.instead["sendMessage"]
    _at(tg, "2026-11-13T09:10:00+00:00")
    out = tg.flush()
    assert out["sent"] == 1 and out["waiting"] == 0, "the bad one ended; it did not stop the round"
    assert tg.status()["outbox"]["last_error_words"] == DROPPED_WORDS
    tries = len(bot.of("sendMessage"))
    _at(tg, "2026-11-13T10:10:00+00:00")
    tg.flush()
    assert len(bot.of("sendMessage")) == tries, "it does not come back each round"


def test_a_message_ends_after_its_tries(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    _package(tg)
    bot.instead["editMessageText"] = {"ok": False, "error_code": 502, "description": "Bad Gateway"}
    tg._deliver("edit:pkg1:1:x", {"kind": "edit", "ident": "pkg1", "message_id": 1, "words": "Decided",
                                  "data_class": "reach_package", "notifies": False})
    for round_ in range(1, OUTBOX_TRIES_MAX + 3):
        _at(tg, f"2026-11-13T{9 + (round_ * 6) // 60:02d}:{(round_ * 6) % 60:02d}:00+00:00")
        tg.flush()
    assert len(bot.of("editMessageText")) == OUTBOX_TRIES_MAX
    view = tg.status()["outbox"]
    assert view["waiting"] == 0 and view["last_error_words"] == WAITED_TOO_LONG_WORDS


def test_a_message_ends_after_a_day_of_waiting(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    _package(tg)
    bot.instead["editMessageText"] = dict(NEVER_LEFT)
    tg._deliver("edit:pkg1:1:x", {"kind": "edit", "ident": "pkg1", "message_id": 1, "words": "Decided",
                                  "data_class": "reach_package", "notifies": False})
    del bot.instead["editMessageText"]
    before = len(bot.of("editMessageText"))
    _at(tg, "2026-11-14T09:00:01+00:00")
    assert tg.flush()["sent"] == 0 and len(bot.of("editMessageText")) == before
    assert tg.status()["outbox"]["last_error_words"] == WAITED_TOO_LONG_WORDS


# ── 7. a config file is not a pairing ────────────────────────────────

def test_a_chat_named_in_the_config_file_alone_is_not_paired(tmp_path) -> None:
    class Section:
        bot_token = TOKEN
        pairing_code = ""
        allowed_chat_ids = ["999"]

    class Config:
        cadence_telegram = Section()

        def save(self) -> None:
            pass

    telegram_reach._repaired = False
    assert telegram_reach.repair_token(lambda: Config()) is True
    assert telegram_reach.bot_token() == TOKEN, "the token still moves into the keystore"
    assert telegram_reach.paired_chat() is None, "999 was never paired with a code on this desk"
    tg, bot, _db = desk(tmp_path)
    assert tg.handle_update({"update_id": 1, "message": {"message_id": 1, "chat": {"id": 999}, "text": "/status",
                                                         "from": {"first_name": "X"}}})["action"] == "rejected"


# ── 8. what the row holds ────────────────────────────────────────────

def test_the_outbox_keeps_no_chat_id_no_page_link_and_no_words_of_a_question(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    tg._link = lambda path: f"https://hub.example.ts.net{path}"
    _package(tg)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    bot.instead["editMessageText"] = dict(NEVER_LEFT)
    out = tg.send_package("pkg1", "/b/page-token-0123456789")
    assert "page-token-0123456789" in out["text"], "he gets the link in the message"
    tg._deliver("edit:pkg1:55:x", {"kind": "edit", "ident": "pkg1", "message_id": 55, "words": "Decided: Go on",
                                   "data_class": "reach_package", "notifies": False})
    row = _row(tg)
    assert str(OWNER_CHAT) not in row and "chat_id" not in row
    assert "page-token-0123456789" not in row and "hub.example" not in row
    assert QUESTION not in row and "Go on" not in row.replace("Decided: Go on", "")
    # A question goes before an edit of a sent message (review T3: questions first).
    items = tg._policy(OUTBOX_POLICY)["items"]
    (question,) = [item for item in items if item["kind"] != "edit"]
    (edit,) = [item for item in items if item["kind"] == "edit"]
    assert {key for key in question} == {"kind", "ident", "rev", "ref", "data_class", "notifies", "key", "gen",
                                         "queued_at", "tries", "next_at", "state"}
    assert edit["kind"] == "edit" and edit["words"] == "Decided: Go on"
    del bot.instead["sendMessage"], bot.instead["editMessageText"]
    _at(tg, "2026-11-13T09:10:00+00:00")
    assert tg.flush()["sent"] == 2
    assert "page-token-0123456789" in bot.of("sendMessage")[-1]["text"], "this process still held the link"


def test_after_a_restart_a_question_goes_with_the_way_to_the_desk_in_place_of_its_link(tmp_path) -> None:
    tg, bot, db = paired(tmp_path)
    tg._link = lambda path: f"https://hub.example.ts.net{path}"
    _package(tg)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.send_package("pkg1", "/b/page-token-0123456789")
    del bot.instead["sendMessage"]
    clock = Clock()
    clock.at = "2026-11-13T09:10:00+00:00"
    again, _bot, _db = desk(tmp_path, bot=bot, clock=clock, db=db)
    again._reach.open = {REF}
    assert again.flush()["sent"] == 1
    text = bot.of("sendMessage")[-1]["text"]
    assert QUESTION in text and "page-token" not in text and "Open it on your desk." in text


def test_a_one_time_text_is_kept_fenced(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(NEVER_LEFT)
    tg.line("The key is password=hunter2 for the night.")
    assert "hunter2" not in _row(tg)
