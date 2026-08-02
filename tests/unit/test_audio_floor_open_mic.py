"""HS-112-06 — the browser's open mic is an owner on the ONE audio floor.

The Desk's ambient mic captures in a browser, on the same machine as the
hotkey, the meeting recorder and the wake listener. These tests pin that it
claims the *same* arbiter rather than a second, invisible one:

* a meeting cannot start under a live open mic, and an open mic cannot open
  under a live meeting — each refused BY NAME;
* the browser's claim is leased, so a closed tab frees the floor instead of
  wedging the owner's hotkey forever;
* a heartbeat renews it, and re-claiming is a renewal, not a refusal.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.voice_typing import VoiceTypingSession
from holdspeak.web.context import WebContext
from holdspeak.web.routes.dictation import build_dictation_router


class FakeClock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _client(session: Any) -> TestClient:
    app = FastAPI()
    app.include_router(
        build_dictation_router(WebContext(get_state=dict, voice_session=session))
    )
    return TestClient(app)


# ── the arbiter's lease ──────────────────────────────────────────────


def test_leased_claim_frees_itself_when_the_tab_stops_renewing() -> None:
    clock = FakeClock()
    session = VoiceTypingSession(clock=clock)

    assert session.acquire("open_mic", lease_seconds=20) is True
    assert session.active_owner == "open_mic"

    clock.advance(19)
    assert session.active_owner == "open_mic"

    # the tab died: nobody renewed, and the floor is nobody's again.
    clock.advance(2)
    assert session.active_owner is None
    assert session.acquire("meeting") is True


def test_renew_extends_the_lease_and_answers_false_once_it_is_gone() -> None:
    clock = FakeClock()
    session = VoiceTypingSession(clock=clock)
    session.acquire("open_mic", lease_seconds=20)

    clock.advance(10)
    assert session.renew("open_mic", 20) is True
    clock.advance(15)  # would have expired without the renewal
    assert session.active_owner == "open_mic"

    clock.advance(30)
    assert session.renew("open_mic", 20) is False


def test_a_reclaim_by_the_same_leased_owner_renews_instead_of_refusing() -> None:
    clock = FakeClock()
    session = VoiceTypingSession(clock=clock)
    session.acquire("open_mic", lease_seconds=20)

    clock.advance(10)
    assert session.acquire("open_mic", lease_seconds=20) is True
    clock.advance(15)
    assert session.active_owner == "open_mic"


def test_in_process_owners_never_expire() -> None:
    clock = FakeClock()
    session = VoiceTypingSession(clock=clock)
    session.acquire("meeting")

    clock.advance(86_400)
    # a meeting holds the floor until it releases — no lease, no expiry.
    assert session.active_owner == "meeting"
    assert session.acquire("open_mic", lease_seconds=20) is False


def test_a_leased_claim_blocks_the_hotkey_exactly_like_any_owner() -> None:
    session = VoiceTypingSession()
    session.acquire("open_mic", lease_seconds=20)

    class Source:
        def start_recording(self) -> None:  # pragma: no cover - never reached
            raise AssertionError("the hotkey must not start under a held floor")

    assert session.begin(Source(), owner="hotkey") is False
    session.release("open_mic")
    assert session.active_owner is None


def test_lease_seconds_must_be_positive() -> None:
    session = VoiceTypingSession()
    with pytest.raises(ValueError):
        session.acquire("open_mic", lease_seconds=0)
    with pytest.raises(ValueError):
        session.renew("open_mic", -1)


# ── the routes ───────────────────────────────────────────────────────


def test_floor_route_reports_the_active_owner_by_name() -> None:
    session = VoiceTypingSession()
    client = _client(session)

    assert client.get("/api/dictation/floor").json() == {
        "arbitrated": True,
        "held": False,
        "owner": None,
    }

    session.acquire("meeting")
    assert client.get("/api/dictation/floor").json() == {
        "arbitrated": True,
        "held": True,
        "owner": "meeting",
    }


def test_claim_takes_the_floor_and_a_meeting_is_then_refused() -> None:
    session = VoiceTypingSession()
    client = _client(session)

    claimed = client.post("/api/dictation/floor/claim", json={"lease_seconds": 20})
    assert claimed.status_code == 200
    assert claimed.json()["owner"] == "open_mic"
    assert claimed.json()["lease_seconds"] == 20

    # the meeting recorder is now refused by the SAME arbiter — one floor.
    assert session.acquire("meeting") is False


def test_a_claim_under_a_meeting_is_refused_by_name() -> None:
    session = VoiceTypingSession()
    session.acquire("meeting")
    client = _client(session)

    refused = client.post("/api/dictation/floor/claim", json={})
    assert refused.status_code == 409
    body = refused.json()
    assert body["refusal"] == "floor_held_meeting"
    assert body["owner"] == "meeting"
    # …and the refusal did not quietly steal the floor.
    assert session.active_owner == "meeting"


def test_release_frees_the_floor_and_is_safe_when_it_holds_nothing() -> None:
    session = VoiceTypingSession()
    client = _client(session)
    client.post("/api/dictation/floor/claim", json={})

    assert client.post("/api/dictation/floor/release").json() == {
        "held": False,
        "owner": None,
    }
    assert session.active_owner is None
    # a second release is a no-op, not an error.
    assert client.post("/api/dictation/floor/release").status_code == 200


def test_a_lease_is_capped_so_a_client_cannot_hold_the_floor_forever() -> None:
    session = VoiceTypingSession()
    client = _client(session)

    claimed = client.post(
        "/api/dictation/floor/claim", json={"lease_seconds": 100_000}
    )
    assert claimed.json()["lease_seconds"] == 120.0


def test_without_an_arbiter_the_routes_say_so_instead_of_inventing_a_floor() -> None:
    client = _client(None)

    assert client.get("/api/dictation/floor").json()["arbitrated"] is False
    claimed = client.post("/api/dictation/floor/claim", json={})
    assert claimed.status_code == 200
    assert claimed.json()["arbitrated"] is False
