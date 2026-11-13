"""The Telegram long poll does not time itself out, and a failed poll waits.

On the owner's hub (2026-11-13) ``getUpdates`` asked Telegram for a 25 s long
poll through a client with a 10 s timeout. Every quiet poll ended as a client
timeout, was recorded as an ``indeterminate`` egress operation, and the reach
loop polled again at once: about 8,500 operations a day and 91,000 in ten
days, each with five kernel journal events.
"""
from __future__ import annotations

import threading
import time
from typing import Any

from holdspeak.services import telegram_reach
from holdspeak.services.reach_service import PollBackoff
from holdspeak.services.telegram_reach import TelegramReach
from tests.unit.test_reach_telegram import Desk, keystore  # noqa: F401  (the autouse keystore fixture)


def test_the_long_poll_gives_its_client_more_time_than_it_asks_telegram_for(tmp_path, monkeypatch) -> None:
    desk = Desk(tmp_path)
    desk.pair()
    seen: list[dict[str, Any]] = []

    def recorded(token: str, method: str, params: dict[str, Any], **more: Any) -> dict[str, Any]:
        seen.append({"method": method, "params": dict(params), **more})
        return {"ok": True, "result": []}

    monkeypatch.setattr(telegram_reach, "call_reach", recorded)
    production = TelegramReach(desk.rig.db)  # no injected caller: the real transport's seat

    production.poll_once(None)

    (poll,) = [call for call in seen if call["method"] == "getUpdates"]
    assert poll["timeout"] > poll["params"]["timeout"], poll
    assert poll["params"]["timeout"] == telegram_reach.LONG_POLL_SECONDS
    assert production.last_poll_ok is True


def test_only_the_long_poll_changes_its_client_timeout(tmp_path, monkeypatch) -> None:
    desk = Desk(tmp_path)
    desk.pair()
    seen: list[dict[str, Any]] = []

    def recorded(token: str, method: str, params: dict[str, Any], **more: Any) -> dict[str, Any]:
        seen.append({"method": method, **more})
        return {"ok": True, "result": {"message_id": 1}}

    monkeypatch.setattr(telegram_reach, "call_reach", recorded)
    production = TelegramReach(desk.rig.db)

    production._api("sendMessage", {"chat_id": "1", "text": "Hello"})

    assert "timeout" not in seen[0], seen  # the transport's default stays


def test_a_failed_poll_is_marked_so_the_loop_can_wait(tmp_path, monkeypatch) -> None:
    desk = Desk(tmp_path)
    desk.pair()
    monkeypatch.setattr(telegram_reach, "call_reach",
                        lambda *args, **more: {"ok": False, "description": "The read operation timed out"})
    production = TelegramReach(desk.rig.db)

    assert production.poll_once(7) == 7
    assert production.last_poll_ok is False


def test_the_wait_after_failed_polls_doubles_to_a_cap_and_a_good_poll_resets_it() -> None:
    backoff = PollBackoff()
    assert [backoff.failed() for _ in range(3)] == [5.0, 10.0, 20.0]
    for _ in range(20):
        last = backoff.failed()
    assert last == 300.0
    backoff.answered()
    assert backoff.failed() == 5.0


class _FailingTelegram:
    """Telegram that never answers: every poll comes back at once, failed."""

    def __init__(self) -> None:
        self.polls = 0
        self.last_poll_ok = True

    def should_poll(self) -> bool:
        return True

    def poll_once(self, offset: Any) -> Any:
        self.polls += 1
        self.last_poll_ok = False
        return offset


def test_the_reach_loop_does_not_poll_again_at_once_after_a_failed_poll(tmp_path) -> None:
    desk = Desk(tmp_path)
    failing = _FailingTelegram()
    desk.reach._telegram = lambda: failing
    desk.reach.tick = lambda: None  # the ladder's tick is not under test

    desk.reach.start()
    try:
        deadline = time.monotonic() + 5
        while failing.polls == 0 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert failing.polls == 1
        time.sleep(0.5)
        assert failing.polls == 1, "a failed poll waits its back-off; the loop polled again at once"
    finally:
        started = time.monotonic()
        desk.reach.stop()
        thread: threading.Thread = desk.reach._thread
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert time.monotonic() - started < 2, "stop() ends a back-off wait at once"
