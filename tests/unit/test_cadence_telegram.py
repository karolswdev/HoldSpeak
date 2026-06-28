"""CAD-4 — the Cadence Telegram surface (hermetic; the network transport is mocked)."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.cadence.models import OpenLoop
from holdspeak.cadence_telegram import TelegramSurface
from holdspeak.config import TelegramConfig
from holdspeak.db import Database


class FakeCaller:
    """Records (method, params) instead of hitting the network."""

    def __init__(self):
        self.calls = []

    def __call__(self, token, method, params, *, timeout=10.0):
        self.calls.append((token, method, params))
        return {"ok": True, "result": []}

    def sent_texts(self):
        return [p.get("text", "") for (_, m, p) in self.calls if m == "sendMessage"]


@pytest.fixture
def db(tmp_path: Path) -> Database:
    d = Database(tmp_path / "tg.db")
    d.cadence.upsert_loop(OpenLoop(source_type="meeting_action", source_id="a1",
                                   title="File the watchdog issue", stale_score=12.0))
    return d


def _surface(db, **cfg):
    base = dict(enabled=True, bot_token="SECRET-TOKEN", pairing_code="hunter2")
    base.update(cfg)
    caller = FakeCaller()
    return TelegramSurface(db, TelegramConfig(**base), caller=caller), caller


def msg(chat_id, text):
    return {"message": {"chat": {"id": chat_id}, "text": text}}


def test_off_by_default():
    assert TelegramConfig().is_active is False  # disabled + no token
    assert TelegramConfig(enabled=True).is_active is False  # no token


def test_unpaired_chat_gets_no_data(db):
    s, caller = _surface(db)
    res = s.handle_update(msg("999", "/loops"))
    assert res["action"] == "rejected"
    assert all("watchdog" not in t for t in caller.sent_texts())  # no loop data leaked
    assert any("not paired" in t.lower() for t in caller.sent_texts())


def test_pairing_with_code(db):
    s, _ = _surface(db)
    assert s.handle_update(msg("42", "/pair hunter2"))["ok"] is True
    assert s.is_authorized("42")
    s2, _ = _surface(db)
    assert s2.handle_update(msg("42", "/pair wrong"))["ok"] is False


def test_paired_chat_can_read_brief(db):
    s, caller = _surface(db, allowed_chat_ids=["42"])
    assert s.handle_update(msg("42", "/brief"))["action"] == "brief"
    assert any("watchdog" in t for t in caller.sent_texts())


def test_token_never_appears_in_sent_text(db):
    s, caller = _surface(db, allowed_chat_ids=["42"])
    s.handle_update(msg("42", "/brief"))
    s.handle_update(msg("42", "/status"))
    assert all("SECRET-TOKEN" not in t for t in caller.sent_texts())


def test_snooze_and_done_decisions(db):
    s, _ = _surface(db, allowed_chat_ids=["42"])
    loop_id = db.cadence.list_loops()[0].id
    cb = lambda data: {"callback_query": {"id": "c", "data": data, "message": {"chat": {"id": "42"}}}}
    assert s.handle_update(cb(f"snooze:{loop_id}"))["action"] == "snooze"
    assert db.cadence.get_loop(loop_id).status == "snoozed"
    assert s.handle_update(cb(f"done:{loop_id}"))["action"] == "done"
    assert db.cadence.get_loop(loop_id).status == "closed"


def test_kill_requires_second_confirm(db):
    s, _ = _surface(db, allowed_chat_ids=["42"])
    loop_id = db.cadence.list_loops()[0].id
    cb = lambda data: {"callback_query": {"id": "c", "data": data, "message": {"chat": {"id": "42"}}}}
    # first tap only asks to confirm; the loop is NOT killed yet
    assert s.handle_update(cb(f"kill:{loop_id}"))["action"] == "kill_confirm"
    assert db.cadence.get_loop(loop_id).status != "killed"
    # the confirm kills it
    assert s.handle_update(cb(f"killyes:{loop_id}"))["action"] == "killyes"
    assert db.cadence.get_loop(loop_id).status == "killed"


def test_kill_cancel_keeps_loop(db):
    s, _ = _surface(db, allowed_chat_ids=["42"])
    loop_id = db.cadence.list_loops()[0].id
    cb = lambda data: {"callback_query": {"id": "c", "data": data, "message": {"chat": {"id": "42"}}}}
    s.handle_update(cb(f"kill:{loop_id}"))
    assert s.handle_update(cb(f"killno:{loop_id}"))["action"] == "kill_cancelled"
    assert db.cadence.get_loop(loop_id).status != "killed"


def test_unpaired_callback_rejected(db):
    s, _ = _surface(db)  # no paired chats
    loop_id = db.cadence.list_loops()[0].id
    cb = {"callback_query": {"id": "c", "data": f"kill:{loop_id}", "message": {"chat": {"id": "999"}}}}
    assert s.handle_update(cb)["action"] == "rejected"
    assert db.cadence.get_loop(loop_id).status != "killed"


def test_brief_command_renders_morning_push(db):
    s, caller = _surface(db, allowed_chat_ids=["42"])
    s.handle_update(msg("42", "/brief"))
    texts = caller.sent_texts()
    assert any("Morning Push" in t and "watchdog" in t for t in texts)


def test_push_due_nudges_sends_and_records(db):
    s, caller = _surface(db, allowed_chat_ids=["42", "43"])
    due = db.cadence.list_loops()
    sent = s.push_due_nudges(due)
    assert sent == 2  # one per paired chat
    assert db.cadence.get_loop(due[0].id).nudge_count == 1  # recorded
    sends = [p for (_, m, p) in caller.calls if m == "sendMessage"]
    assert {p["chat_id"] for p in sends} == {"42", "43"}


def test_push_is_noop_without_paired_chats(db):
    s, caller = _surface(db)  # no paired chats
    assert s.push_due_nudges(db.cadence.list_loops()) == 0
    assert caller.calls == []
