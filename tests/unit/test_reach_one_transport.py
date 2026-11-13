"""Telegram: one transport, one writer, and sends that survive a failure.

1. One transport. Cadence's slash commands and buttons are handlers that the
   one reach poll calls (``reach_cadence``); they answer through the one
   writer. The second transport, sender, pairing and poll loop are parked.
2. One writer (``telegram_writer``): HTML escaped in one place, a message
   over Telegram's limit cut at a line with the way to the desk, button data
   over 64 bytes refused.
3. The outbox: a failed send is retried and sent one time; a 429 waits what
   Telegram says; a 400 is dropped and said; one key is sent one time;
   nothing is sent while the poll waits for the owner; a question answered on
   the desk while it waited is not sent.

Fake Bot API only; nothing leaves the machine.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import holdspeak
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import reach_cadence, telegram_writer
from holdspeak.services.telegram_reach import DROPPED_WORDS, TelegramReach
from holdspeak.services.telegram_writer import MAX_BUTTON_DATA, MAX_TEXT, MORE_WORDS, Button, Message, WriterRefused
from tests.unit.test_reach_telegram import OWNER_CHAT, keystore, update  # noqa: F401
from tests.unit.test_reach_telegram_setup import Bot, Clock, desk, paired

OWNER = Principal(PrincipalKind.OWNER, "owner")
FAILED = {"ok": False, "description": "The read operation timed out"}


def _command(text: str) -> dict[str, Any]:
    return {"update_id": 900, "message": {"message_id": 5, "chat": {"id": OWNER_CHAT}, "text": text,
                                          "from": {"first_name": "K"}}}


def _at(tg: TelegramReach, stamp: str) -> None:
    tg._clock = lambda: stamp


# ── 1. one transport ─────────────────────────────────────────────────

def test_nothing_live_imports_the_parked_second_transport() -> None:
    root = Path(inspect.getfile(holdspeak)).parent
    assert not (root / "cadence_telegram.py").exists()
    assert (root / "_parked" / "cadence_telegram_20261113.py").exists()
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "_parked" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [alias.name for alias in node.names] if isinstance(node, (ast.Import, ast.ImportFrom)) else []
            module = getattr(node, "module", "") or ""
            if "cadence_telegram" in module or any("cadence_telegram" in name for name in names):
                offenders.append(str(path.relative_to(root)))
    assert offenders == []


def test_only_the_reach_module_joins_a_token_into_the_bot_api_address() -> None:
    """One transport: one live module names the Bot API."""
    root = Path(inspect.getfile(holdspeak)).parent
    users = [str(path.relative_to(root)) for path in sorted(root.rglob("*.py"))
             if "_parked" not in path.parts and "api.telegram.org" in path.read_text(encoding="utf-8")]
    assert users == ["services/telegram_reach.py"]


def test_cadences_status_and_brief_answer_through_the_one_writer_in_html(tmp_path) -> None:
    tg, bot, db = paired(tmp_path)
    before = len(bot.of("sendMessage"))
    assert tg.handle_update(_command("/status"))["result"] == {"action": "status"}
    assert tg.handle_update(_command("/brief"))["result"] == {"action": "brief"}
    sent = bot.of("sendMessage")[before:]
    assert len(sent) == 2
    assert all(row["parse_mode"] == "HTML" for row in sent)
    assert sent[0]["text"].startswith("<b>Cadence status</b>\nLoops: ")
    assert "*" not in sent[0]["text"] and "🧷" not in sent[0]["text"], "no Markdown, no second style"
    assert all(str(row["chat_id"]) == str(OWNER_CHAT) for row in sent)


def test_an_unknown_command_gets_the_commands_line(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    assert tg.handle_update(_command("/what"))["result"] == {"action": "help"}
    assert bot.of("sendMessage")[-1]["text"] == reach_cadence.HELP_WORDS


def test_a_cadence_kill_asks_one_time_more_with_cancel_first(tmp_path) -> None:
    loop = SimpleNamespace(id="loop-1", title="Reply to <Ana>", needs_review=False)
    statuses: list[tuple[str, str]] = []
    db = SimpleNamespace(cadence=SimpleNamespace(get_loop=lambda ident: loop if ident == "loop-1" else None,
                                                 set_status=lambda ident, status: statuses.append((ident, status))))
    pending: set[str] = set()
    action, _words, message = reach_cadence.button(db, "kill:loop-1", pending)
    assert action == "kill_confirm" and [b.text for b in message.buttons[0]] == ["Cancel", "Yes, kill it"]
    assert reach_cadence.button(db, "killyes:loop-1", pending)[0] == "killyes" and statuses == [("loop-1", "killed")]
    assert reach_cadence.button(db, "killyes:loop-1", pending)[0] == "kill_expired"


# ── 2. one writer ────────────────────────────────────────────────────

def test_the_writer_escapes_a_title_in_one_place() -> None:
    params, plain = telegram_writer.payload(7, Message(head="Merge <main> & ship", lines=("a < b",),
                                                       facts=(("Task", "Fix <it>"),), question="Now?"))
    assert params["parse_mode"] == "HTML"
    assert params["text"] == ("<b>Merge &lt;main&gt; &amp; ship</b>\na &lt; b\n<b>Task:</b> Fix &lt;it&gt;\n<b>Now?</b>")
    assert plain == "Merge <main> & ship\na < b\nTask: Fix <it>\nNow?"


def test_a_long_body_is_cut_at_a_line_with_the_way_to_the_desk() -> None:
    lines = tuple(f"line {index} " + "word " * 12 for index in range(80))  # about 5,000 characters
    assert sum(len(line) + 1 for line in lines) > 5000
    params, _plain = telegram_writer.payload(7, Message(head="Head", lines=lines, link="https://desk/b/1"))
    text = params["text"]
    assert len(text) <= MAX_TEXT
    rows = text.split("\n")
    assert rows[-1] == f"{MORE_WORDS}: https://desk/b/1"
    assert all(row in lines for row in rows[1:-1]), "every kept line is whole"
    assert text.count("https://desk/b/1") == 1


def test_the_writer_refuses_button_data_over_telegrams_limit() -> None:
    telegram_writer.keyboard(((Button("Ok", "x" * MAX_BUTTON_DATA),),))
    with pytest.raises(WriterRefused):
        telegram_writer.keyboard(((Button("Ok", "x" * (MAX_BUTTON_DATA + 1)),),))


def test_every_send_of_the_reach_module_goes_through_the_writer(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    tg.line("One line.")
    tg.digest([{"kind": "core", "program_title": "A <b> program", "ordinal": 1}])
    sends = bot.of("sendMessage")
    assert all(row.get("parse_mode") == "HTML" for row in sends), "one parse mode"
    assert "A &lt;b&gt; program" in sends[-1]["text"]


# ── 3. the outbox ────────────────────────────────────────────────────

def test_a_failed_send_waits_and_is_sent_one_time(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    before = len(bot.of("sendMessage"))
    bot.instead["sendMessage"] = dict(FAILED)
    out = tg.line("The night's line.")
    assert out["ok"] is True and out.get("queued") is True
    assert tg.status()["outbox"]["waiting"] == 1 and tg.status()["outbox"]["oldest_since"]
    assert tg.flush()["sent"] == 0, "its wait has not ended"
    del bot.instead["sendMessage"]
    _at(tg, "2026-11-13T09:00:06+00:00")
    assert tg.flush()["sent"] == 1
    assert tg.flush()["sent"] == 0 and tg.status()["outbox"]["waiting"] == 0
    arrived = [row for row in bot.of("sendMessage")[before:] if row["text"] == "The night's line."]
    assert len(arrived) == 2, "one failed try and one that arrived; never a second arrival"


def test_two_sends_of_one_key_send_once(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    before = len(bot.of("sendMessage"))
    tg.digest([{"kind": "core", "program_title": "P", "ordinal": 1}])
    tg.digest([{"kind": "core", "program_title": "P", "ordinal": 1}])
    assert len(bot.of("sendMessage")) - before == 1, "one digest for the day"


def test_a_429_waits_what_telegram_says(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = {"ok": False, "error_code": 429, "description": "Too Many Requests",
                                  "parameters": {"retry_after": 40}}
    tg.line("Held by the limit.")
    del bot.instead["sendMessage"]
    _at(tg, "2026-11-13T09:00:39+00:00")
    assert tg.flush()["sent"] == 0
    _at(tg, "2026-11-13T09:00:41+00:00")
    assert tg.flush()["sent"] == 1


def test_a_400_is_dropped_and_said(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = {"ok": False, "error_code": 400, "description": "Bad Request: can't parse"}
    out = tg.line("A message Telegram refuses.")
    assert out["ok"] is False
    view = tg.status()["outbox"]
    assert view["waiting"] == 0 and view["last_error_words"] == DROPPED_WORDS


def test_nothing_is_sent_while_the_poll_waits_for_the_owner_and_it_goes_after_use_here(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["getUpdates"] = {"ok": False, "error_code": 409, "description": "Conflict"}
    tg.poll_once(None)
    assert tg.status()["health"]["state"] == "another_desk"
    before = len(bot.of("sendMessage"))
    out = tg.line("It waits for the owner.")
    assert out.get("queued") is True and len(bot.of("sendMessage")) == before, "no call while halted"
    assert tg.flush()["sent"] == 0 and len(bot.of("sendMessage")) == before
    del bot.instead["getUpdates"]
    tg.use_here(OWNER)
    assert len(bot.of("sendMessage")) == before + 1
    assert tg.status()["outbox"]["waiting"] == 0


def test_a_question_answered_on_the_desk_while_it_waited_is_not_sent(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    before = len(bot.of("sendMessage"))
    bot.instead["sendMessage"] = dict(FAILED)
    chat = {"chat_id": OWNER_CHAT, "text": "A question", "parse_mode": "HTML"}
    assert tg._deliver("package:p1", "sendMessage", chat, ref="program:p:s:core")["state"] == "queued"
    del bot.instead["sendMessage"]
    _at(tg, "2026-11-13T09:01:00+00:00")
    tries = len(bot.of("sendMessage"))
    assert tg.flush(open_refs=set())["sent"] == 0, "the item waits no more: it is not sent"
    assert len(bot.of("sendMessage")) == tries and tg.status()["outbox"]["waiting"] == 0
    assert tries == before + 1


def test_in_quiet_hours_a_waiting_message_stays_and_an_edit_goes(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(FAILED)
    bot.instead["editMessageText"] = dict(FAILED)
    tg.line("A line for the morning.")
    tg._deliver("edit:p:1:x", "editMessageText", {"chat_id": OWNER_CHAT, "message_id": 1, "text": "Decided"},
                quiet=False)
    del bot.instead["sendMessage"], bot.instead["editMessageText"]
    _at(tg, "2026-11-13T09:10:00+00:00")
    sends = len(bot.of("sendMessage"))
    assert tg.flush(quiet=True)["sent"] == 1, "the edit does not notify: it goes"
    assert len(bot.of("sendMessage")) == sends and tg.status()["outbox"]["waiting"] == 1
    assert tg.flush(quiet=False)["sent"] == 1


def test_the_outbox_survives_a_restart(tmp_path) -> None:
    tg, bot, db = paired(tmp_path)
    bot.instead["sendMessage"] = dict(FAILED)
    tg.line("It waits across a restart.")
    del bot.instead["sendMessage"]
    clock = Clock()
    clock.at = "2026-11-13T09:02:00+00:00"
    again, _bot, _db = desk(tmp_path, bot=bot, clock=clock, db=db)
    assert again.status()["outbox"]["waiting"] == 1
    assert again.flush()["sent"] == 1
