"""Telegram setup, from the hub's side (the owner, 2026-11-13: "so unfriendly
to configure").

What the setup pane needs and did not have: the token is checked with
Telegram when it is saved (a wrong one is refused and not kept; the bot's
name comes back); health is a state with one sentence (a revoked token, a
blocked bot, another desk on the same bot, no answer), and the poll waits
for the owner when the token is revoked or another desk reads the bot; the
pairing code is stored (a restart keeps it) and ``/start <code>`` pairs, so
that one link in Telegram connects the chat; a test message whose button
press is the proof; the bot can be removed, bound to its username; a
keystore that is not open says so.

Every call goes to a fake Bot API (no network); the keystore is the rig's
key file in the test's own folder.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import telegram_reach
from holdspeak.services.telegram_reach import HEALTH_WORDS, TelegramReach, TelegramRefused
from tests.unit.test_reach_telegram import FIXTURE, OWNER_CHAT, TOKEN, FakeBot, keystore, update  # noqa: F401

OWNER = Principal(PrincipalKind.OWNER, "owner")
AGENT = Principal(PrincipalKind.AGENT, "agent-1")
BOT = FIXTURE["answers"]["getMe"]["result"]


class Bot(FakeBot):
    """The fake Bot API, with an answer that a test can put in for one method."""

    def __init__(self) -> None:
        super().__init__()
        self.instead: dict[str, dict[str, Any]] = {}

    def __call__(self, token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method in self.instead:
            self.tokens.append(token)
            self.calls.append((method, json.loads(json.dumps(params))))
            return copy.deepcopy(self.instead[method])
        return super().__call__(token, method, params)


class _Reach:
    """The reach service, as far as the Telegram service asks it: quiet
    hours (none here unless a test sets them) and the items that wait."""

    def __init__(self) -> None:
        self.quiet_hours: tuple[int, int] = (0, 0)
        self.open: set[str] = set()
        self.unread = False

    def wake(self) -> None:
        pass

    def settings(self) -> dict[str, Any]:
        return {"telegram": "at_once", "brief": "on", "hour_cycle": "h23"}

    def hour_cycle(self) -> str:
        return "h23"

    def quiet(self) -> tuple[int, int]:
        return self.quiet_hours

    def is_quiet(self, moment) -> bool:
        from holdspeak.services.reach_service import in_quiet

        return in_quiet(moment, self.quiet())

    def open_refs(self) -> set[str]:
        if self.unread:
            raise RuntimeError("the items were not read")
        return set(self.open)


class Clock:
    def __init__(self) -> None:
        self.at = "2026-11-13T09:00:00+00:00"

    def __call__(self) -> str:
        return self.at


def desk(tmp_path: Path, bot: Bot | None = None, clock: Clock | None = None,
         db: Database | None = None) -> tuple[TelegramReach, Bot, Database]:
    bot = bot or Bot()
    db = db or Database(tmp_path / "reach.db")
    return TelegramReach(db, caller=bot, reach=_Reach(), clock=clock or Clock()), bot, db


def paired(tmp_path: Path) -> tuple[TelegramReach, Bot, Database]:
    tg, bot, db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    assert tg.handle_update(update("pair", code=code))["ok"] is True
    return tg, bot, db


# ── the token is checked when it is saved ────────────────────────────

def test_a_token_telegram_does_not_know_is_refused_and_not_kept(tmp_path) -> None:
    tg, bot, _db = desk(tmp_path)
    bot.instead["getMe"] = {"ok": False, "error_code": 401, "description": "Unauthorized"}
    with pytest.raises(TelegramRefused) as refused:
        tg.save_token(OWNER, TOKEN)
    assert refused.value.code == "token_unknown" and "Nothing was saved" in str(refused.value.detail)
    assert telegram_reach.token_where() == "missing"
    assert tg.status()["bot"] is None and tg.status()["health"]["state"] == "no_token"
    assert bot.tokens == [TOKEN] and [name for name, _ in bot.calls] == ["getMe"]


def test_a_good_token_is_kept_and_the_status_names_the_bot(tmp_path) -> None:
    tg, _bot, _db = desk(tmp_path)
    made = tg.save_token(OWNER, TOKEN)
    assert made["token"] == "keystore"
    assert made["bot"] == {"name": BOT["first_name"], "username": BOT["username"], "checked": True}
    status = tg.status()
    assert status["bot"] == made["bot"]
    assert status["health"] == {"state": "connected", "since": status["health"]["since"],
                                "words": HEALTH_WORDS["connected"]}


def test_a_token_is_kept_unchecked_when_telegram_does_not_answer_and_is_checked_at_the_next_poll(tmp_path) -> None:
    tg, bot, _db = desk(tmp_path)
    bot.instead["getMe"] = {"ok": False, "description": "The read operation timed out"}
    made = tg.save_token(OWNER, TOKEN)
    assert made == {"token": "keystore", "bot": {"name": "", "username": "", "checked": False}}
    assert tg.status()["health"]["state"] == "not_checked"
    del bot.instead["getMe"]
    code = tg.start_pairing(OWNER)["code"]
    tg.handle_update(update("pair", code=code))
    tg.poll_once(None)
    assert tg.status()["bot"] == {"name": BOT["first_name"], "username": BOT["username"], "checked": True}
    assert tg.status()["health"]["state"] == "connected"


# ── health is a state ────────────────────────────────────────────────

def test_a_revoked_token_is_a_state_and_the_poll_waits_for_the_owner(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    assert tg.should_poll() is True
    bot.instead["getUpdates"] = {"ok": False, "error_code": 401, "description": "Unauthorized"}
    tg.poll_once(None)
    health = tg.status()["health"]
    assert health["state"] == "token_revoked" and health["words"] == HEALTH_WORDS["token_revoked"] and health["since"]
    assert tg.should_poll() is False
    # A new token starts the poll again.
    del bot.instead["getUpdates"]
    tg.save_token(OWNER, TOKEN)
    assert tg.status()["health"]["state"] == "connected" and tg.should_poll() is True


def test_another_desk_on_the_same_bot_is_a_state_and_use_here_starts_the_poll_again(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["getUpdates"] = {"ok": False, "error_code": 409, "description": "Conflict"}
    tg.poll_once(None)
    assert tg.status()["health"]["state"] == "another_desk" and tg.should_poll() is False
    with pytest.raises(TelegramRefused):
        tg.use_here(AGENT)
    assert tg.use_here(OWNER)["health"]["state"] == "not_checked"
    assert tg.should_poll() is True


def test_a_blocked_bot_is_a_state_that_only_a_send_that_arrives_clears(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["sendMessage"] = {"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}
    tg.line("A line to the chat.")
    assert tg.status()["health"]["state"] == "bot_blocked"
    tg.poll_once(None)  # the poll answers; the chat still takes no message
    assert tg.status()["health"]["state"] == "bot_blocked" and tg.should_poll() is True
    del bot.instead["sendMessage"]
    # Review T2: a 403 on that message will never succeed: it ends (one line
    # for the owner) and does not come back each round.
    view = tg.status()["outbox"]
    assert view["waiting"] == 0 and view["last_error_words"] == telegram_reach.DROPPED_WORDS
    tg._clock = lambda: "2026-11-13T09:05:00+00:00"
    assert tg.line("A second line to the chat.")["ok"] is True
    assert tg.status()["health"]["state"] == "connected" and tg.status()["outbox"]["waiting"] == 0


def test_no_answer_is_unreachable_with_the_time_it_began(tmp_path) -> None:
    clock = Clock()
    tg, bot, db = desk(tmp_path, clock=clock)
    tg.save_token(OWNER, TOKEN)
    tg.handle_update(update("pair", code=tg.start_pairing(OWNER)["code"]))
    bot.instead["getUpdates"] = {"ok": False, "description": "The read operation timed out"}
    clock.at = "2026-11-13T09:10:00+00:00"
    tg.poll_once(None)
    clock.at = "2026-11-13T09:20:00+00:00"
    tg.poll_once(None)
    health = tg.status()["health"]
    assert health["state"] == "unreachable" and health["since"] == "2026-11-13T09:10:00+00:00"
    assert tg.should_poll() is True and tg.last_poll_ok is False
    del bot.instead["getUpdates"]
    tg.poll_once(None)
    assert tg.status()["health"]["state"] == "connected"


# ── pairing survives a restart; the link pairs ───────────────────────

def test_a_pairing_code_survives_a_restart_and_start_with_the_code_pairs(tmp_path) -> None:
    first, bot, db = desk(tmp_path)
    first.save_token(OWNER, TOKEN)
    made = first.start_pairing(OWNER)
    link = f"https://t.me/{BOT['username']}?start={made['code']}"
    assert made["link"] == link and first.status()["pairing"]["link"] == link
    # A new service object over the same store: the hub came up again.
    second, _bot, _db = desk(tmp_path, bot=bot, db=db)
    assert second.pairing_open() is True and second.should_poll() is True
    assert second.status()["pairing"] == {"expires_at": made["expires_at"]}  # the code is not stored: no link
    started = update("pair", code=made["code"])
    started["message"]["text"] = f"/start {made['code']}"
    assert second.handle_update(started) == {"action": "pair", "ok": True}
    assert telegram_reach.paired_chat()["id"] == str(OWNER_CHAT)
    assert second.status()["pairing"] is None and second.pairing_open() is False


def test_the_count_of_wrong_codes_survives_a_restart(tmp_path) -> None:
    first, bot, db = desk(tmp_path)
    first.save_token(OWNER, TOKEN)
    first.start_pairing(OWNER)
    for _ in range(telegram_reach.PAIR_WRONG_MAX - 1):
        assert first.handle_update(update("pair_other", code="000000"))["ok"] is False
    second, _bot, _db = desk(tmp_path, bot=bot, db=db)
    assert second.pairing_open() is True
    assert second.handle_update(update("pair_other", code="000000"))["ok"] is False
    assert second.pairing_open() is False


def test_a_pairing_code_ends_at_its_time(tmp_path) -> None:
    clock = Clock()
    tg, _bot, _db = desk(tmp_path, clock=clock)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    clock.at = "2026-11-13T09:11:00+00:00"  # ten minutes and one
    assert tg.pairing_open() is False and tg.status()["pairing"] is None
    assert tg.handle_update(update("pair", code=code))["ok"] is False


# ── the test message ─────────────────────────────────────────────────

def test_the_test_message_is_recorded_and_its_press_is_the_proof(tmp_path) -> None:
    clock = Clock()
    tg, bot, db = desk(tmp_path, clock=clock)
    tg.save_token(OWNER, TOKEN)
    tg.handle_update(update("pair", code=tg.start_pairing(OWNER)["code"]))
    with pytest.raises(TelegramRefused):
        tg.send_test(AGENT)
    made = tg.send_test(OWNER)
    assert made == {"last_test": {"sent_at": "2026-11-13T09:00:00+00:00", "answered_at": None}}
    sent = bot.of("sendMessage")[-1]
    assert sent["text"].startswith("Test from your desk · ")
    assert sent["reply_markup"]["inline_keyboard"] == [[{"text": "It works", "callback_data": "r1|test|ok"}]]
    assert tg.status()["last_test"] == made["last_test"]
    clock.at = "2026-11-13T09:01:00+00:00"
    tapped = tg.handle_update(update("tap", message_id=bot.next_id, text=sent["text"], data="r1|test|ok"))
    assert tapped["action"] == "test"
    assert tg.status()["last_test"] == {"sent_at": "2026-11-13T09:00:00+00:00",
                                        "answered_at": "2026-11-13T09:01:00+00:00"}
    edited = bot.of("editMessageText")[-1]
    assert edited["text"].splitlines()[0] == f"<b>{sent['text']}</b>"
    assert edited["text"].splitlines()[1].startswith("It works · ")
    assert "reply_markup" not in edited  # the button is gone


def test_the_test_refuses_with_words_when_no_chat_is_connected(tmp_path) -> None:
    tg, bot, _db = desk(tmp_path)
    with pytest.raises(TelegramRefused) as no_token:
        tg.send_test(OWNER)
    assert no_token.value.code == "telegram_not_connected" and no_token.value.detail == HEALTH_WORDS["no_token"]
    tg.save_token(OWNER, TOKEN)
    with pytest.raises(TelegramRefused) as no_chat:
        tg.send_test(OWNER)
    assert no_chat.value.detail == telegram_reach.NOT_CONNECTED_WORDS
    assert bot.of("sendMessage") == []


# ── remove the bot ───────────────────────────────────────────────────

def test_remove_needs_the_username_of_the_bot_that_is_saved(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    with pytest.raises(TelegramRefused):
        tg.remove_bot(AGENT, BOT["username"])
    with pytest.raises(TelegramRefused) as stale:
        tg.remove_bot(OWNER, "another_bot")
    assert stale.value.code == "answer_stale"
    assert telegram_reach.token_where() == "keystore" and telegram_reach.paired_chat() is not None
    assert tg.remove_bot(OWNER, "@" + BOT["username"].upper()) == {"token": "missing", "paired": None, "bot": None}
    assert telegram_reach.bot_token() == "" and telegram_reach.paired_chat() is None
    status = tg.status()
    assert status["bot"] is None and status["pairing"] is None and status["last_test"] is None
    assert status["health"]["state"] == "no_token" and tg.should_poll() is False


# ── a keystore that is not open ──────────────────────────────────────

def test_a_keystore_that_is_not_open_is_said(tmp_path, monkeypatch) -> None:
    tg, _bot, _db = paired(tmp_path)
    assert tg.status()["keystore"] == "open" and "keystore_words" not in tg.status()
    monkeypatch.setattr(telegram_reach, "_store", lambda: None)
    status = tg.status()
    assert status["keystore"] == "locked" and status["keystore_words"] == HEALTH_WORDS["keystore_locked"]
    assert status["health"]["state"] == "keystore_locked" and status["token"] == "missing"


# ── what the status never carries; who may call ──────────────────────

def test_the_status_never_carries_the_token_or_the_chat_id_and_the_code_only_in_the_link(tmp_path) -> None:
    tg, _bot, _db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    text = json.dumps(tg.status())
    assert TOKEN not in text and text.count(code) == 1 and f"start={code}" in text
    tg.handle_update(update("pair", code=code))
    text = json.dumps(tg.status())
    assert TOKEN not in text and str(OWNER_CHAT) not in text and code not in text


def test_the_new_operations_are_the_owners(tmp_path) -> None:
    import holdspeak.operations  # noqa: F401  (the registry imports the settings rows; alone they import in a circle)
    from holdspeak.settings_operations import SETTINGS_OPERATIONS

    rows = {row.name: row for row in SETTINGS_OPERATIONS}
    for name in ("reach.status", "reach.telegram.test", "settings.secret.telegram.remove",
                 "settings.secret.telegram.use_here", "settings.secret.telegram.token"):
        assert rows[name].owner_only is True, name
    assert "mcp:reach.telegram.test" in rows["reach.telegram.test"].exposure
    assert not any(part.startswith("mcp:") for part in rows["settings.secret.telegram.remove"].exposure)
