"""Phone (2026-10-28): the call state machine and its ring timer."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.phone import devices as devs
from holdspeak.phone.calls import TRANSITIONS, RingTimers, can_move, missed_words
from holdspeak.phone.push import NullPush
from holdspeak.phone.service import OWNER, PhoneRefused, PhoneService


class _NoNumber:
    def number(self) -> str:
        return ""

    def available(self) -> tuple[bool, str]:
        return False, "no number"


def _wait(predicate, seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("timed out")


@pytest.fixture
def phone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PhoneService:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "keys.json"))
    devs.forget_cached_secret()
    service = PhoneService(Database(tmp_path / "phone.db"), push=NullPush(), number=_NoNumber(),
                           kernel=lambda data: None, ring_seconds=0.2, rering_seconds=0.2)
    token = service.pair_token(OWNER, hub_urls=[])["token"]
    service.redeem({"pair_token": token, "name": "Phone", "platform": "test", "push_token": "t"})
    yield service
    service.stop()
    devs.forget_cached_secret()


def test_the_transitions() -> None:
    assert can_move("ringing", "answered") and can_move("answered", "ended") and can_move("held", "ringing")
    assert can_move("missed", "ringing")  # the urgent re-ring
    assert not can_move("ended", "ringing") and not can_move("declined", "answered")
    assert TRANSITIONS["declined"] == frozenset() == TRANSITIONS["ended"]
    assert missed_words({"reason": "The deploy waits."}) == "Missed call: The deploy waits. Reply here, or call the desk."


def test_the_ring_timer_fires_once_and_stop_cancels_it() -> None:
    fired: list[str] = []
    timers = RingTimers(on_timeout=fired.append, on_rering=fired.append, ring_seconds=0.05, rering_seconds=0.05)
    assert timers.ringing("a") == 1
    timers.ringing("b")
    timers.stop("b")
    _wait(lambda: fired == ["a"])
    time.sleep(0.15)
    assert fired == ["a"] and timers.rings("a") == 1


def test_ringing_then_missed_after_the_timeout_then_a_message(phone: PhoneService) -> None:
    made = phone.call(OWNER, reason="A question")
    assert phone.store.get_call(made["call_id"])["state"] == "ringing"
    _wait(lambda: phone.store.get_call(made["call_id"])["state"] == "missed" and phone.store.recent_messages())
    assert phone.store.recent_messages()[0]["origin_ref"] == f"phone_call:{made['call_id']}"
    assert phone.wait_answer(made["call_id"], 1)["state"] == "missed"


def test_accept_then_end_and_the_wrong_moves_are_refused(phone: PhoneService) -> None:
    made = phone.call(OWNER, reason="A question")
    with pytest.raises(PhoneRefused, match="call is on"):
        phone.call(OWNER, reason="Another")  # never a second call while one rings
    phone.accept(made["call_id"])
    with pytest.raises(PhoneRefused):
        phone.accept(made["call_id"])
    ended = phone.end(made["call_id"])
    assert ended["state"] == "ended" and ended["end_reason"] == "hung_up" and ended["duration_s"] is not None
    with pytest.raises(PhoneRefused):
        phone.decline(made["call_id"])
    time.sleep(0.3)  # the stopped timer does not make it missed
    assert phone.store.get_call(made["call_id"])["state"] == "ended"


def test_decline_and_a_held_call_let_wait(phone: PhoneService) -> None:
    made = phone.call(OWNER, reason="A question")
    assert phone.decline(made["call_id"])["state"] == "declined"
    from holdspeak.principals import Principal, PrincipalKind

    held = phone.call(Principal(PrincipalKind.AGENT, "a"), reason="Drop the column?")
    assert held["state"] == "held"
    assert phone.decline(held["call_id"])["end_reason"] == "let_wait"


def test_an_urgent_missed_call_rings_again_once(phone: PhoneService) -> None:
    made = phone.call(OWNER, reason="Production lost data", urgent=True)
    _wait(lambda: phone.timers.rings(made["call_id"]) == 2 and phone.store.get_call(made["call_id"])["state"] == "missed"
          and phone.store.recent_messages())
    invites = [e for e in phone.events.replay(0) if e["type"] == "call.invite"]
    assert len(invites) == 2


def test_an_agent_may_not_make_a_call_urgent_without_security_or_data_loss(phone: PhoneService, monkeypatch) -> None:
    from holdspeak.principals import Principal, PrincipalKind

    agent = Principal(PrincipalKind.AGENT, "a")
    held = phone.call(agent, reason="Lunch is ready", urgent=True)
    assert phone.store.get_call(held["call_id"])["urgent"] is False
    phone.decline(held["call_id"])
    leak = phone.call(agent, reason="A secret leaked in a log", urgent=True)
    assert phone.store.get_call(leak["call_id"])["urgent"] is True


def test_the_frame_names_the_kind_id_and_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "keys.json"))
    frames: list = []
    service = PhoneService(Database(tmp_path / "f.db"), push=NullPush(), number=_NoNumber(),
                           kernel=lambda data: None, broadcast=lambda kind, data: frames.append((kind, data)))
    message = service.send_from_desk("Hello.")
    assert ("phone_changed", {"kind": "message", "id": message["id"], "state": "sent"}) in frames
    lock = threading.Lock()
    with lock:
        pass
    service.stop()
