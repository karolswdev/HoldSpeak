"""2026-11-07: a keystore read that never answers must not hang a status
read (the owner's hub stalled every /api/setup/status on a macOS Keychain
prompt no background process can answer)."""
from __future__ import annotations

import threading
import time

from holdspeak import trust_destinations
from holdspeak.services import telegram_reach


def test_a_blocking_keystore_read_counts_as_not_paired_within_the_deadline(monkeypatch) -> None:
    gate = threading.Event()

    def never(*_a, **_k):
        gate.wait(30)
        return ""

    monkeypatch.setattr(telegram_reach, "telegram_on", lambda: True)
    monkeypatch.setattr(telegram_reach, "bot_token", never)
    started = time.monotonic()
    assert trust_destinations._reach_telegram_paired(timeout=0.5) is False
    assert time.monotonic() - started < 3.0
    gate.set()


def test_a_paired_keystore_answers_true(monkeypatch) -> None:
    monkeypatch.setattr(telegram_reach, "telegram_on", lambda: True)
    monkeypatch.setattr(telegram_reach, "bot_token", lambda: "tok")
    monkeypatch.setattr(telegram_reach, "paired_chat", lambda: {"id": "1"})
    assert trust_destinations._reach_telegram_paired() is True
