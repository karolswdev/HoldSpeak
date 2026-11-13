"""Telegram setup, the guards the review of #2298 asked for (review T1).

1. The pairing link holds the code. Only the owner's read returns it
   (``ReachService.status`` → ``TelegramReach.status``). Every other reader
   gets ``TelegramReach.summary``: ``ReachService.summary`` forwards it into
   ``phone.status``, which an agent reads over MCP. An agent that read the
   link could send ``/start <code>`` from its own chat and become the owner
   chat.
2. The wrong-try limit of a pairing code holds when the store cannot be
   written: the code is void, in this process too.
3. A halt (the token is revoked, another desk reads the bot) is cleared by an
   owner act only. While halted nothing polls and nothing is sent, so no
   operation is recorded.
4. The new operations refuse an agent at the registry (the door the HTTP
   route calls) and at MCP dispatch; a 404 from ``getMe`` refuses the token;
   a refused token leaves the saved one in place.

Fake Bot API only; nothing leaves the machine.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock

import pytest

from holdspeak import operations
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import telegram_reach
from holdspeak.services.reach_service import ReachService
from holdspeak.services.telegram_reach import HALTED, PAIR_NOT_SAVED_WORDS, PAIR_WRONG_MAX, TelegramReach, TelegramRefused
from tests.unit.test_reach_telegram import OWNER_CHAT, TOKEN, keystore, update  # noqa: F401
from tests.unit.test_reach_telegram_setup import BOT, Bot, Clock, _Reach, desk, paired

OWNER = Principal(PrincipalKind.OWNER, "owner")
AGENT = Principal(PrincipalKind.AGENT, "agent-1")
OTHER_TOKEN = "987654321:" + "B" * 35


def _secrets_in(answer: Any, code: str) -> list[str]:
    text = json.dumps(answer)
    found = [name for name, value in (("code", code), ("link", "start="), ("t.me", "t.me/"), ("token", TOKEN),
                                      ("chat id", str(OWNER_CHAT)), ("username", BOT["username"])) if value in text]
    return found


# ── 1. the link is the owner's ───────────────────────────────────────

def test_the_summary_view_never_carries_the_code_the_link_the_bot_or_the_chat(tmp_path) -> None:
    tg, _bot, _db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    assert f"start={code}" in json.dumps(tg.status()), "the owner's view holds the link"
    assert _secrets_in(tg.summary(), code) == []
    assert tg.summary()["pairing"] == {"expires_at": tg.status()["pairing"]["expires_at"]}
    tg.handle_update(update("pair", code=code))
    assert _secrets_in(tg.summary(), code) == []
    assert tg.summary()["health"]["state"] == tg.status()["health"]["state"]


def test_the_reach_summary_that_phone_status_forwards_is_the_summary_view(tmp_path) -> None:
    tg, _bot, db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    reach = ReachService(db, telegram=lambda: tg)
    assert _secrets_in(reach.summary(), code) == []
    # The owner's read still holds the link for his own face.
    assert f"start={code}" in json.dumps(reach.status(OWNER))
    with pytest.raises(Exception):
        reach.status(AGENT)


def test_an_agent_reading_phone_status_over_mcp_gets_no_pairing_credential(tmp_path, monkeypatch) -> None:
    from holdspeak.mcp.families import phone as phone_family
    from holdspeak.phone import service as phone_service
    from holdspeak.services import reach_service

    tg, _bot, db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    reach = ReachService(db, telegram=lambda: tg)
    monkeypatch.setenv("HOLDSPEAK_PHONE", "on")
    monkeypatch.setattr(reach_service, "default_reach_service", lambda db=None: reach)
    monkeypatch.setattr(phone_service, "default_phone_service", lambda db=None: Mock(status=lambda principal: {"devices": []}))
    answer = phone_family.dispatch("phone.status", {}, AGENT)
    assert "telegram" in answer, "the reach part is in the answer"
    assert _secrets_in(answer, code) == []


def test_every_forwarder_of_the_telegram_state_calls_the_summary_view() -> None:
    """Derived from the tree: outside the Telegram service itself, the only
    call of the owner's view is in ``ReachService.status`` (owner only)."""
    import ast
    import inspect
    from pathlib import Path

    import holdspeak

    root = Path(inspect.getfile(holdspeak)).parent
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "_parked" in path.parts or path.name == "telegram_reach.py":
            continue
        source = path.read_text(encoding="utf-8")
        if "telegram" not in source:
            continue
        tree = ast.parse(source)
        for func in [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for call in [node for node in ast.walk(func) if isinstance(node, ast.Call)]:
                target = call.func
                if not (isinstance(target, ast.Attribute) and target.attr == "status" and not call.args):
                    continue
                inner = target.value
                # ``self.telegram().status()`` / ``default_telegram_reach(...).status()``
                name = getattr(getattr(inner, "func", None), "attr", None) or getattr(getattr(inner, "func", None), "id", None)
                if name in ("telegram", "default_telegram_reach"):
                    where = f"{path.relative_to(root.parent)}::{func.name}"
                    if where != "holdspeak/services/reach_service.py::status":
                        offenders.append(where)
    assert offenders == [], offenders


# ── 2. the wrong-try limit holds when the store fails ────────────────

class _FailingWrites:
    """The cadence repository, with writes that raise when ``broken``."""

    def __init__(self, inner: Any) -> None:
        self._inner, self.broken = inner, False

    def upsert_policy(self, policy: Any) -> Any:
        if self.broken:
            raise OSError("disk full")
        return self._inner.upsert_policy(policy)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def _with_failing_store(tg: TelegramReach, db: Any) -> _FailingWrites:
    store = _FailingWrites(db.cadence)
    tg.db = Mock(wraps=db)
    tg.db.cadence = store
    return store


def test_a_wrong_code_voids_the_code_when_the_try_cannot_be_written(tmp_path) -> None:
    tg, bot, db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    store = _with_failing_store(tg, db)
    store.broken = True
    wrong = "000000" if code != "000000" else "111111"
    assert tg.handle_update(update("pair", code=wrong))["ok"] is False
    # The count could not move, so the code is no longer good: not for more
    # guesses and not for the right code either.
    assert tg.pairing_open() is False
    store.broken = False
    assert tg.handle_update(update("pair", code=code))["ok"] is False
    assert telegram_reach.paired_chat() is None
    assert tg.status()["pairing"] is None and "start=" not in json.dumps(tg.status())


def test_many_wrong_codes_never_get_more_than_the_limit_when_the_store_fails(tmp_path) -> None:
    tg, _bot, db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    store = _with_failing_store(tg, db)
    store.broken = True
    for guess in range(PAIR_WRONG_MAX * 4):
        text = f"{guess:06d}"
        if text == code:
            continue
        tg.handle_update(update("pair", code=text))
    tried_good = tg.handle_update(update("pair", code=code))["ok"]
    assert tried_good is False and telegram_reach.paired_chat() is None


def test_the_right_code_pairs_nothing_when_its_use_cannot_be_written(tmp_path) -> None:
    tg, bot, db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    code = tg.start_pairing(OWNER)["code"]
    store = _with_failing_store(tg, db)
    store.broken = True
    result = tg.handle_update(update("pair", code=code))
    assert result["ok"] is False and result.get("refused") == "not_saved"
    assert telegram_reach.paired_chat() is None
    assert any(params.get("text") == PAIR_NOT_SAVED_WORDS for name, params in bot.calls if name == "sendMessage")
    # The code is void in this process: the store comes back, the code does not.
    store.broken = False
    assert tg.handle_update(update("pair", code=code))["ok"] is False
    assert telegram_reach.paired_chat() is None


def test_no_code_is_handed_out_when_it_cannot_be_stored(tmp_path) -> None:
    tg, _bot, db = desk(tmp_path)
    tg.save_token(OWNER, TOKEN)
    _with_failing_store(tg, db).broken = True
    with pytest.raises(TelegramRefused) as refused:
        tg.start_pairing(OWNER)
    assert refused.value.code == "pairing_not_saved"
    assert tg.pairing_open() is False


# ── 3. only the owner clears a halt ──────────────────────────────────

def _calls(bot: Bot) -> list[str]:
    return [name for name, _ in bot.calls]


def test_another_desk_stays_until_the_owner_acts_and_nothing_is_called_meanwhile(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["getUpdates"] = {"ok": False, "error_code": 409, "description": "Conflict"}
    tg.poll_once(None)
    assert tg.status()["health"]["state"] == "another_desk"
    del bot.instead["getUpdates"]
    before = len(bot.calls)
    # Automatic traffic: a line to the chat, more polls. None is made, so no
    # operation is recorded, and the state does not move.
    tg.line("A line to the chat.")
    for _ in range(5):
        tg.poll_once(None)
        assert tg.last_poll_ok is False
    assert len(bot.calls) == before, _calls(bot)[before:]
    assert tg.live() is False and tg.should_poll() is False
    assert tg.status()["health"]["state"] == "another_desk"
    # The owner's act starts it again.
    tg.use_here(OWNER)
    assert tg.should_poll() is True
    tg.poll_once(None)
    assert _calls(bot)[before:] != [] and tg.status()["health"]["state"] == "connected"


def test_a_revoked_token_stays_revoked_through_answers_and_timeouts(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["getUpdates"] = {"ok": False, "error_code": 401, "description": "Unauthorized"}
    tg.poll_once(None)
    assert tg.status()["health"]["state"] == "token_revoked"
    # An answer and a timeout that arrive for this token change nothing.
    tg._note("sendMessage", {"ok": True})
    assert tg.status()["health"]["state"] == "token_revoked"
    tg._note("getUpdates", {"ok": False, "description": "timed out"})
    assert tg.status()["health"]["state"] == "token_revoked"
    before = len(bot.calls)
    tg.line("A line to the chat.")
    assert len(bot.calls) == before, "no send with a revoked token"
    # A new token that Telegram knows is the owner's act.
    del bot.instead["getUpdates"]
    tg.save_token(OWNER, TOKEN)
    assert tg.status()["health"]["state"] == "connected" and tg.should_poll() is True


def test_the_test_message_says_the_halt_and_sends_nothing(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["getUpdates"] = {"ok": False, "error_code": 409, "description": "Conflict"}
    tg.poll_once(None)
    before = len(bot.calls)
    with pytest.raises(TelegramRefused) as refused:
        tg.send_test(OWNER)
    assert refused.value.detail == telegram_reach.HEALTH_WORDS["another_desk"]
    assert len(bot.calls) == before


def test_unreachable_and_blocked_clear_themselves_when_a_call_answers(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    bot.instead["getUpdates"] = {"ok": False, "description": "The read operation timed out"}
    tg.poll_once(None)
    assert tg.status()["health"]["state"] == "unreachable"
    del bot.instead["getUpdates"]
    tg.poll_once(None)
    assert tg.status()["health"]["state"] == "connected"
    assert set(HALTED) == {"token_revoked", "another_desk"}


# ── 4. the coverage the review asked for ─────────────────────────────

def _rows() -> dict[str, Any]:
    import holdspeak.operations  # noqa: F401
    from holdspeak.settings_operations import SETTINGS_OPERATIONS

    return {row.name: row for row in SETTINGS_OPERATIONS}


@pytest.mark.parametrize("name", ["reach.telegram.test", "settings.secret.telegram.remove",
                                  "settings.secret.telegram.use_here", "settings.secret.telegram.pair",
                                  "settings.secret.telegram.token", "reach.status"])
def test_an_agent_is_refused_at_the_registry_before_the_service_is_called(name: str) -> None:
    """The HTTP route of each row calls this registry: its refusal is the route's."""
    row = _rows()[name]
    target = Mock()
    registry = operations.bind({row.service: target}, (row,))
    with pytest.raises(operations.OperationOwnerRequired):
        registry.invoke(AGENT, name, {"username": BOT["username"], "token": TOKEN})
    assert target.mock_calls == []


@pytest.mark.parametrize("name", [name for name, row in _rows().items()
                                  if name.startswith(("reach.telegram.", "settings.secret.telegram.")) and row.tool_schema])
def test_an_agent_is_refused_at_mcp_dispatch(name: str, monkeypatch) -> None:
    from holdspeak.mcp import tools
    from holdspeak.mcp.families import declared

    row = _rows()[name]
    target = Mock()
    registry = operations.bind({row.service: target}, (row,))
    monkeypatch.setattr(tools, "runtime_registry", lambda: registry)
    with pytest.raises(operations.OperationOwnerRequired):
        declared.dispatch(name, {}, AGENT)
    assert target.mock_calls == []


def test_the_secret_rows_have_no_mcp_projection() -> None:
    rows = _rows()
    for name in ("settings.secret.telegram.remove", "settings.secret.telegram.use_here",
                 "settings.secret.telegram.pair", "settings.secret.telegram.token"):
        assert not any(part.startswith("mcp:") for part in rows[name].exposure), name


def test_the_service_refuses_an_agent_too(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    before = len(bot.calls)
    for act in (lambda: tg.send_test(AGENT), lambda: tg.remove_bot(AGENT, BOT["username"]),
                lambda: tg.use_here(AGENT), lambda: tg.start_pairing(AGENT), lambda: tg.save_token(AGENT, TOKEN)):
        with pytest.raises(TelegramRefused) as refused:
            act()
        assert refused.value.code == "owner_only"
    assert len(bot.calls) == before and telegram_reach.token_where() == "keystore"


def test_a_404_from_get_me_refuses_the_token(tmp_path) -> None:
    tg, bot, _db = desk(tmp_path)
    bot.instead["getMe"] = {"ok": False, "error_code": 404, "description": "Not Found"}
    with pytest.raises(TelegramRefused) as refused:
        tg.save_token(OWNER, TOKEN)
    assert refused.value.code == "token_unknown"
    assert telegram_reach.token_where() == "missing" and tg.status()["bot"] is None


def test_a_refused_token_leaves_the_saved_token_and_its_bot_in_place(tmp_path) -> None:
    tg, bot, _db = paired(tmp_path)
    saved_bot = tg.status()["bot"]
    bot.instead["getMe"] = {"ok": False, "error_code": 401, "description": "Unauthorized"}
    with pytest.raises(TelegramRefused):
        tg.save_token(OWNER, OTHER_TOKEN)
    assert telegram_reach.bot_token() == TOKEN
    assert tg.status()["bot"] == saved_bot and telegram_reach.paired_chat() is not None
    assert tg.status()["health"]["state"] == "connected", "a refused token is not this desk's token: its 401 is not a halt"
