"""Focused shutdown tests for launch delivery watchers."""

from __future__ import annotations

import threading
from types import SimpleNamespace
from unittest.mock import Mock

from holdspeak.delivery import first_message
from holdspeak.delivery.factory_launch import LaunchLedger
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

    def session_alive(_session: str) -> bool:
        entered.set()
        delivery._stop.wait(2.0)
        return False

    delivery = FirstMessage(_service(session_alive))
    delivery.settle = Mock()  # type: ignore[method-assign]
    delivery.watch("launch-1")
    assert entered.wait(1.0)

    delivery.close()
    assert delivery._stop.is_set()
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


def test_close_joins_the_launch_watcher(tmp_path, monkeypatch):
    ledger = LaunchLedger(tmp_path / "launches.json")
    ledger.record({"launch_id": "watcher", "session": "isolated-tmux-session"})
    service = SimpleNamespace(_ledger=ledger, _session_alive=lambda _session: True)
    worker = first_message.FirstMessage(service)
    sleeping = threading.Event()
    joined = []
    threads = []

    def poll(_seconds):
        thread = threading.current_thread()
        threads.append(thread)
        original = thread.join

        def join(timeout=None):
            joined.append(thread)
            return original(timeout)

        monkeypatch.setattr(thread, "join", join)
        sleeping.set()
        worker._stop.wait()

    monkeypatch.setattr(first_message, "time", SimpleNamespace(sleep=poll))
    try:
        worker.watch("watcher")
        assert sleeping.wait(5), "the session watcher did not reach its poll"
        worker.close()
        assert joined == threads
        assert not threads[0].is_alive()
    finally:
        worker._stop.set()
        for thread in threads:
            thread.join(5)
