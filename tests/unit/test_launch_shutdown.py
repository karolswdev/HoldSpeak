"""Focused shutdown tests for launch delivery watchers."""

from __future__ import annotations

import threading
from types import SimpleNamespace
from unittest.mock import Mock

from holdspeak.delivery.first_message import FirstMessage


def _service(session_alive):
    ledger = SimpleNamespace(get=lambda _launch_id: {"session": "session-1"})
    return SimpleNamespace(_ledger=ledger, _session_alive=session_alive)


def _wait_for_watched_to_clear(delivery: FirstMessage) -> None:
    for _ in range(100):
        with delivery._lock:
            if not delivery._watched:
                return
        threading.Event().wait(0.01)
    raise AssertionError("launch watcher did not stop")


def test_preview_does_not_reconcile_an_existing_launch_after_shutdown():
    entered = threading.Event()
    release = threading.Event()

    def session_alive(_session: str) -> bool:
        entered.set()
        release.wait(2.0)
        return False

    delivery = FirstMessage(_service(session_alive))
    delivery.settle = Mock()  # type: ignore[method-assign]
    delivery.watch("launch-1")
    assert entered.wait(1.0)

    delivery.close()
    release.set()
    _wait_for_watched_to_clear(delivery)

    delivery.settle.assert_not_called()


def test_active_watcher_still_settles_when_session_ends():
    ended = threading.Event()

    def session_alive(_session: str) -> bool:
        return False

    delivery = FirstMessage(_service(session_alive))
    delivery.settle = Mock(side_effect=lambda _launch_id: ended.set())  # type: ignore[method-assign]
    delivery.watch("launch-1")

    assert ended.wait(1.0)
    _wait_for_watched_to_clear(delivery)
    delivery.settle.assert_called_once_with("launch-1")
