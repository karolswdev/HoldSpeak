"""HS-200-05 — physical voice capture, correction and custody (real services).

The seam-level half lives in `tests/unit/test_phase200_voice_custody.py`; the
physical half (a real microphone, the macOS hotkey, a denied permission dialog,
a hub restart on the attested platform) is the owner's attended walk,
`tests/e2e/live200_voice_walk.py`. This module runs the REAL product between
those two ends: the real FastAPI application, the real database and reconciled
schema, the real dictation routes, the real journal recorder and correction
store, and the real streaming-mic socket.

Two adapters are substituted, because a runner has neither:

* the **speech engine** (`on_transcribe`) — no microphone, no model file;
* the **typing target** (`on_remote_dictation`) — a test never types into the
  machine's focused window.

Everything else is the shipped path, so the journal rows, the correction rows,
the `applied` counts and the delivery claims below are the product's own.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.voice_typing import VoiceTypingSession
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system import voice as voice_routes
from holdspeak.web.routes.system.voice import build_voice_router

HEARD = "the postgress migration lands on friday"
SAID = "the postgres migration lands on friday"
OWNER_TOKEN = "phase200-voice-custody-owner"


# ── the cold installation (isolated HOME, config and database) ───────────────


@pytest.fixture
def cold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A fresh data root and configuration; the owner's install is unreachable.

    `holdspeak.config.core.CONFIG_DIR` and `holdspeak.db.core.DEFAULT_DB_PATH`
    freeze at import time, so redirecting HOME alone is not enough.
    """
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database

    home = tmp_path / "home"
    (home / ".config" / "holdspeak").mkdir(parents=True, exist_ok=True)
    (home / ".local" / "share" / "holdspeak").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        config_module, "CONFIG_FILE", home / ".config" / "holdspeak" / "config.json"
    )
    db_path = home / ".local" / "share" / "holdspeak" / "holdspeak.db"
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", db_path)
    reset_database()
    yield SimpleNamespace(home=home, db_path=db_path)
    reset_database()


@pytest.fixture
def db(cold):
    from holdspeak.db import Database

    return Database(cold.db_path)


def _build_client(db: Any, monkeypatch: pytest.MonkeyPatch, **callback_kwargs: Any):
    """A server over the REAL application, durably wired to ``db``.

    The same wiring `holdspeak.web_runtime` performs at start-up: without the
    two repositories the journal and the correction store are no-ops, and a
    custody proof over no-ops proves nothing. ``callback_kwargs`` reach
    `WebRuntimeCallbacks` — `on_remote_dictation` is the substituted typing
    target.
    """
    import holdspeak.db as hsdb
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
            **callback_kwargs,
        ),
        dictation_corrections_repository=db.dictation_corrections,
        dictation_journal_repository=db.dictation_journal,
    )
    return server


@pytest.fixture
def client(db, monkeypatch):
    server = _build_client(db, monkeypatch)
    with TestClient(server.app) as test_client:
        yield test_client


# ── the streaming-mic harness (the browser leg) ──────────────────────────────


class _Socket:
    """The client half of ``/ws/dictation/stream``, scripted."""

    def __init__(
        self,
        *,
        start: dict | None = None,
        chunks: int = 1,
        end: bool = True,
        disconnect_after: int | None = None,
    ) -> None:
        self.headers = {
            "authorization": f"Bearer {OWNER_TOKEN}",
            "sec-websocket-protocol": "",
        }
        self.sent: list[dict[str, Any]] = []
        self.messages: list[dict[str, Any]] = []
        if start is not None:
            self.messages.append({"text": json.dumps(start)})
        for _ in range(chunks):
            self.messages.append(
                {"bytes": np.zeros(16000, dtype=np.int16).tobytes()}
            )
        if disconnect_after is not None:
            self.messages = self.messages[:disconnect_after]
            self.messages.append({"type": "websocket.disconnect"})
        elif end:
            self.messages.append({"text": json.dumps({"type": "end"})})
        self.closed = False

    async def accept(self, **_kw: Any) -> None:
        return None

    async def receive(self) -> dict[str, Any]:
        if not self.messages:
            return {"type": "websocket.disconnect"}
        return self.messages.pop(0)

    async def send_json(self, payload: dict[str, Any]) -> None:
        self.sent.append(dict(payload))

    async def close(self, **_kw: Any) -> None:
        self.closed = True

    def finals(self) -> list[dict[str, Any]]:
        return [e for e in self.sent if e.get("type") == "final"]

    def errors(self) -> list[dict[str, Any]]:
        return [e for e in self.sent if e.get("type") == "error"]


class _FakeInterval:
    """The socket's admitted open-mic interval.

    Admission itself is proven by `tests/unit/test_dictation_session_admission.py`
    and `tests/unit/test_speech_side_door_admission.py`; a cold runner has no
    speech assignment to admit against, so the interval is supplied here and
    everything downstream of it is the real route.
    """

    def __init__(self) -> None:
        self.handle = "mic_phase200"
        self.session = SimpleNamespace(
            fence=SimpleNamespace(
                publish=lambda _stage, work: (True, work()),
                reason=lambda: "",
            ),
            provider=lambda: None,
        )


class _FakeRegistry:
    def __init__(self) -> None:
        self.opened = 0
        self.closed: list[str] = []

    def open(self, _principal: Any, **_kw: Any) -> _FakeInterval:
        self.opened += 1
        return _FakeInterval()

    def close(self, _principal: Any, *, reason: str = "") -> str:
        self.closed.append(reason)
        return "mic_phase200"


def _endpoint_for(router: Any, path: str) -> Any:
    for route in router.routes:
        if getattr(route, "path", "") == path:
            return route.endpoint
    raise AssertionError(f"no route for {path}")


@pytest.fixture
def stream(db, monkeypatch):
    """Drive one scripted socket against the REAL websocket route."""
    from holdspeak.plugins.dictation.journal import DictationJournalRecorder

    registry = _FakeRegistry()
    monkeypatch.setattr(voice_routes, "browser_mic_sessions", lambda: registry)

    config = Config()
    # The passthrough lane: the real `dictation_runner` journals the utterance
    # and nothing reaches a model or a LAN endpoint.
    config.dictation.pipeline.enabled = False
    config.meeting.web_auth_token = OWNER_TOKEN
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))

    recorder = DictationJournalRecorder(db.dictation_journal)

    def run(
        *,
        start: dict | None = None,
        said: Any = HEARD,
        voice_session: Any = None,
        transcribe: Any = None,
        chunks: int = 1,
        disconnect_after: int | None = None,
    ) -> SimpleNamespace:
        typed: list[tuple[str, str]] = []

        def _transcribe(_audio: Any, **_kw: Any) -> str:
            if transcribe is not None:
                return transcribe()
            return said

        ctx = WebContext(
            get_state=lambda: {},
            on_transcribe=None if said is None else _transcribe,
            journal=recorder,
            voice_session=voice_session,
            on_remote_dictation=lambda text, *, target="agent": typed.append(
                (text, target)
            ),
            web_auth_token=OWNER_TOKEN,
        )
        endpoint = _endpoint_for(build_voice_router(ctx), "/ws/dictation/stream")
        socket = _Socket(
            start=start, chunks=chunks, disconnect_after=disconnect_after
        )
        asyncio.run(endpoint(socket))
        return SimpleNamespace(
            socket=socket, typed=typed, registry=registry, recorder=recorder
        )

    return run


# ── AC2: browser capture, its receipt, and visible microphone ownership ──────


def test_a_spoken_utterance_journals_one_row_and_its_final_frame_carries_the_facts(
    stream, db
) -> None:
    """The `final` frame is the run's own receipt (HS-176 C1).

    `raw_text`, `corrections_applied` and `journal_id` are carried out of the
    run that computed them — the deck never re-derives them from "the newest
    journal row" — and the row they name is the one the product wrote.
    """
    run = stream(start={"type": "start", "pipeline": True})

    finals = run.socket.finals()
    assert len(finals) == 1, run.socket.sent
    frame = finals[0]
    assert frame["text"] == HEARD
    assert frame["raw_text"] == HEARD
    assert frame["corrections_applied"] == []

    rows = db.dictation_journal.recent()
    assert len(rows) == 1, rows
    assert rows[0].source == "browser"
    assert rows[0].transcript == HEARD
    assert frame["journal_id"] == rows[0].id


def test_the_microphone_refuses_by_name_when_another_owner_holds_the_floor(
    stream, db
) -> None:
    """Visible ownership, server side: one audio floor with one named owner.

    A meeting holding the floor is not a silent failure — the socket says
    `audio_floor_held`, never opens a speech interval, and writes nothing.
    """
    session = VoiceTypingSession()
    assert session.acquire("meeting") is True

    run = stream(start={"type": "start", "pipeline": True}, voice_session=session)

    errors = run.socket.errors()
    assert [e["reason"] for e in errors] == ["audio_floor_held"]
    assert errors[0]["failure_category"] == "audio_floor_held"
    assert run.registry.opened == 0, "no interval opens over somebody else's mic"
    assert db.dictation_journal.recent() == []
    assert run.socket.finals() == []


def test_a_floor_taken_mid_utterance_closes_the_interval_and_writes_nothing(
    stream, db
) -> None:
    """The floor claim is a lease and every frame is its heartbeat.

    Losing it mid-utterance ends the capture BY NAME with the terminal
    `mic_interval: closed` the client honors, rather than recording into a
    microphone somebody else now owns.
    """
    session = VoiceTypingSession()

    class _Stolen:
        """Grants the claim, then reports the floor gone on the first frame."""

        def __init__(self) -> None:
            self.renewals = 0

        def acquire(self, *_a: Any, **_kw: Any) -> bool:
            return True

        def renew(self, *_a: Any, **_kw: Any) -> bool:
            self.renewals += 1
            return False

        def release(self, *_a: Any, **_kw: Any) -> None:
            return None

    del session
    run = stream(start={"type": "start", "pipeline": True}, voice_session=_Stolen())

    errors = run.socket.errors()
    assert [e["reason"] for e in errors] == ["audio_floor_lost"]
    assert errors[0]["mic_interval"] == "closed"
    assert run.socket.finals() == [], "no words from a session already told it was over"
    assert db.dictation_journal.recent() == []


def test_the_spoken_utterance_delivers_once_and_adds_no_second_journal_row(
    stream, db, monkeypatch
) -> None:
    """One utterance, one pipeline pass, one delivery, one row.

    The Speak room streams the final (which journals), then delivers it with
    `raw: true` so the words that were previewed are the words that land.
    """
    run = stream(start={"type": "start", "pipeline": True})
    landed = run.socket.finals()[0]["text"]
    assert db.dictation_journal.count() == 1

    typed: list[tuple[str, str]] = []
    server = _build_client(
        db,
        monkeypatch,
        on_remote_dictation=lambda text, *, target="agent": typed.append(
            (text, target)
        ),
    )
    with TestClient(server.app) as client:
        response = client.post(
            "/api/dictation/remote",
            json={
                "text": landed,
                "raw": True,
                "target_mode": "focused",
                "delivery_id": "speak:phase200-one",
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["delivered"] is True
    assert body["final_text"] == HEARD
    assert typed == [(HEARD, "focused")]
    assert db.dictation_journal.count() == 1, "a raw delivery re-journals nothing"


# ── AC3: denial, silence, interruption and a failed transcription ────────────


def test_an_unavailable_speech_engine_is_named_and_writes_nothing(
    stream, db
) -> None:
    """The browser's own permission dialog is his hand; this is the server's
    half of the same refusal — named, terminal, and it keeps no row."""
    run = stream(start={"type": "start", "pipeline": True}, said=None)

    errors = run.socket.errors()
    assert [e["reason"] for e in errors] == ["transcription_unavailable"]
    assert run.socket.closed is True
    assert db.dictation_journal.recent() == []


def test_silence_returns_an_empty_final_and_writes_no_row(stream, db) -> None:
    """No audio is not a failure: an empty final, and nothing kept."""
    run = stream(start={"type": "start", "pipeline": True}, chunks=0)

    assert [f["text"] for f in run.socket.finals()] == [""]
    assert run.socket.errors() == []
    assert db.dictation_journal.recent() == []


def test_a_failed_transcription_is_named_and_writes_no_row(stream, db) -> None:
    """The engine raised. The client is told which failure it was, so the face
    can offer Retry / Copy / Keep as note over the draft it still holds."""

    def _boom() -> str:
        raise RuntimeError("decode blew up")

    run = stream(start={"type": "start", "pipeline": True}, transcribe=_boom)

    errors = run.socket.errors()
    assert [e["reason"] for e in errors] == ["transcription_failed"]
    assert errors[0]["failure_category"] == "transcription_failed"
    assert run.socket.finals() == []
    assert db.dictation_journal.recent() == []


def test_a_disconnect_mid_utterance_keeps_the_words_and_ends_the_interval(
    stream, db
) -> None:
    """He walked away mid-sentence — and the words he already said are KEPT.

    This is the capture contract's loss rule, asserted rather than assumed: a
    client disconnect breaks the receive loop (`voice_stream.py:194`) and the
    audio already accumulated is still transcribed and journaled. The `final`
    frame has nowhere to go, so the journal row is the whole receipt: he finds
    the half-utterance on the Journal wing instead of losing it. The interval
    closes by name in the `finally`, and nothing is delivered — a disconnect is
    not a send.
    """
    run = stream(
        start={"type": "start", "pipeline": True}, chunks=2, disconnect_after=2
    )

    rows = db.dictation_journal.recent()
    assert [r.transcript for r in rows] == [HEARD], (
        "a disconnect must not throw away words that were already captured"
    )
    assert rows[0].source == "browser"
    assert run.typed == [], "a disconnect is not a delivery"
    assert run.registry.closed == ["browser_mic_stream_closed"]


def test_the_recovery_contract_keeps_the_draft_for_every_named_failure() -> None:
    """The capture contract, read off the shipped client vocabulary.

    Every failure a capture can end in offers Retry and, when words survive,
    Copy and Keep as note — the words are never dropped on the floor.
    """
    repo = Path(__file__).resolve().parents[2]
    source = (repo / "web/src/lib/dictationRecovery.ts").read_text(encoding="utf-8")
    for failure in (
        "permission_denied",
        "no_speech",
        "transcription_failed",
        "mic_interval_closed",
        "audio_floor_held",
    ):
        assert f"{failure}: {{" in source, failure
    # `applicableActions` adds Copy + Keep as note whenever a draft is present,
    # so the retained words always have a way out of the well.
    assert 'if (options.draftPresent) actions.push("copy", "keep_as_note");' in source


# ── AC4: one real correction, applied by the matcher, with honest counts ─────


def _teach_text_rule(client: TestClient) -> int:
    response = client.post(
        "/api/dictation/corrections",
        json={"kind": "text", "heard": "postgress", "said": "PostgreSQL"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["recorded"] is True, body
    return int(body["id"])


def _applied_for(client: TestClient, correction_id: int) -> int:
    listing = client.get("/api/dictation/corrections").json()
    for item in listing["items"]:
        if int(item["id"]) == correction_id:
            return int(item["applied"])
    raise AssertionError(f"correction {correction_id} not listed: {listing}")


def test_a_taught_rule_fires_on_a_later_utterance_and_the_count_moves_by_one(
    client,
) -> None:
    """`N APPLIED` counts real firings, not the teaching utterance.

    A brand-new rule reads 0. One utterance that it actually rewrites reads 1,
    and the journal row names the rule's durable id.
    """
    correction_id = _teach_text_rule(client)
    assert _applied_for(client, correction_id) == 0, "a teach is not an application"

    response = client.post("/api/dictation/dry-run", json={"utterance": HEARD})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["final_text"] == "the PostgreSQL migration lands on friday"
    assert body["raw_text"] == HEARD, "the heard text survives the rewrite"
    assert body["corrections_applied"] == [correction_id]

    assert _applied_for(client, correction_id) == 1


def test_a_replay_applies_the_rule_but_moves_no_count_because_it_journals_nothing(
    client,
) -> None:
    """A replay is a PREVIEW, and the count is honest about that.

    `/api/dictation/journal/{id}/replay` re-runs a stored transcript through
    the current pipeline with `journal=None` (routes/dictation/pipeline.py:1475)
    — no typing, no new row, the original row untouched. `applied` counts
    retained journal rows, so a replay must not move it: counting previews
    would make `N APPLIED` a count of times he pressed a button rather than
    times the rule changed a real dictation.
    """
    correction_id = _teach_text_rule(client)
    first = client.post("/api/dictation/dry-run", json={"utterance": HEARD})
    entry_id = int(first.json()["journal_id"])
    assert _applied_for(client, correction_id) == 1
    before = client.get("/api/dictation/journal").json()["count"]

    replay = client.post(f"/api/dictation/journal/{entry_id}/replay")
    assert replay.status_code == 200, replay.text
    body = replay.json()
    # The rule really did fire on the replay — that is what makes it visible.
    after_text = body.get("after", {}).get("final_text") or body.get("final_text")
    assert after_text == "the PostgreSQL migration lands on friday", body

    assert client.get("/api/dictation/journal").json()["count"] == before
    assert _applied_for(client, correction_id) == 1


# ── AC5: custody across a restart, and no duplicate typing ───────────────────


def test_kept_speech_and_correction_rows_survive_a_restart(
    cold, db, monkeypatch
) -> None:
    """Stop the hub, start it again on the same data root, read it all back.

    The correction ring is process memory; the rows are not. A second server
    over the same database file rehydrates the rule, keeps its durable id, and
    still reports the firing it recorded before the restart.
    """
    from holdspeak.db import Database, reset_database

    server = _build_client(db, monkeypatch)
    with TestClient(server.app) as first:
        correction_id = _teach_text_rule(first)
        first.post("/api/dictation/dry-run", json={"utterance": HEARD})
        journal_before = first.get("/api/dictation/journal").json()["count"]
        applied_before = _applied_for(first, correction_id)
    assert journal_before == 1
    assert applied_before == 1

    # The hub stops: every in-process store goes with it.
    reset_database()

    reopened = Database(cold.db_path)
    restarted = _build_client(reopened, monkeypatch)
    with TestClient(restarted.app) as second:
        listing = second.get("/api/dictation/corrections").json()
        assert listing["size"] == 1, listing
        assert [i["id"] for i in listing["items"]] == [correction_id]
        assert [i["key"] for i in listing["items"]] == ["postgress"]
        assert _applied_for(second, correction_id) == applied_before

        journal = second.get("/api/dictation/journal").json()
        assert journal["count"] == journal_before
        transcripts = [row["transcript"] for row in journal["items"]]
        assert HEARD in transcripts, journal

        # And the rehydrated rule still fires: custody is not just storage.
        again = second.post("/api/dictation/dry-run", json={"utterance": HEARD})
        assert again.json()["corrections_applied"] == [correction_id]


def test_an_uncertain_delivery_parks_pending_and_never_types_twice(
    db, monkeypatch
) -> None:
    """The typing hook raised after the text may already have landed.

    The claim stays `pending`, the response is 425 `delivery_pending`, and a
    retry of the SAME delivery id reads that state instead of replaying an
    effect nobody can prove did not happen. `tests/unit/test_speak_room_delivery.py:281`
    pins the named `DesktopTypeRefused` branch; this pins the unnamed one — an
    adapter that dies with an arbitrary exception must be exactly as safe.
    """
    calls = 0

    def _half_typed(_text: str, *, target: str = "agent") -> None:
        nonlocal calls
        calls += 1
        raise OSError("the accessibility bridge went away mid-keystroke")

    server = _build_client(db, monkeypatch, on_remote_dictation=_half_typed)
    payload = {
        "text": HEARD,
        "raw": True,
        "target_mode": "focused",
        "delivery_id": "speak:phase200-uncertain",
    }
    with TestClient(server.app) as client:
        first = client.post("/api/dictation/remote", json=payload)
        retry = client.post("/api/dictation/remote", json=payload)

    assert first.status_code == 425, first.text
    assert first.json()["error_code"] == "delivery_pending"
    assert retry.status_code == 425, retry.text
    assert calls == 1, "an uncertain effect is never replayed"
