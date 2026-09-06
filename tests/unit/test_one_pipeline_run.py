"""HS-132-04 — one utterance, one pipeline.

Two seams are pinned here.

**The Speak room** runs the DIR pipeline exactly ONCE per utterance: the
streaming final pass processes it (`/ws/dictation/stream`), and the delivery
that follows sends ``raw: true`` so `/api/dictation/remote` types those exact
words instead of rewriting a rewrite (the route's own comment: re-running the
pipeline makes the receipt a lie). One journal row per utterance, not two.

**A field mic** (speak-to-fill: every desk text input) is the user typing with
their voice. Its socket declares ``{"type": "start", "pipeline": false}`` and
the final pass is verbatim — no intent routing, no enrichment, no rewriting,
and NO journal row. The documented seam in ``dictation_capture`` ("a
speak-to-fill is the user typing with their voice... No journaling") is
reachable at last.

The transcriber is a stub and the pipeline runs with
``dictation.pipeline.enabled = False`` so the journal passthrough (the real
``dictation_runner`` code path, not a simulation of it) is what records the
row — these tests reach no model and no LAN endpoint.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.config import Config
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.web.context import WebContext
from holdspeak.web.routes.dictation.pipeline import build_pipeline_router
from holdspeak.web.routes.system import voice as voice_routes
from holdspeak.web.routes.system.voice import build_voice_router

TRANSCRIPT = "ship it friday"
OWNER_TOKEN = "one-pipeline-owner-token"


# ── the recorders ────────────────────────────────────────────────────────────


class _Journal:
    """Stands in for the dictation journal recorder; counts rows, nothing else.

    It returns the row it wrote (as the real recorder does), so HS-176 C1's
    `journal_id` has a real value to carry.
    """

    repository = None

    def __init__(self) -> None:
        self.rows: list[str] = []

    def record(self, run: Any, *, source: str, **_kw: Any) -> Any:
        self.rows.append(source)
        return SimpleNamespace(id=100 + len(self.rows))


class _FakeFence:
    """The interval's cancellation election, as the route sees it."""

    def __init__(self, *, elected: bool = True) -> None:
        self.elected = elected
        self.stages: list[str] = []

    def publish(self, stage: str, publication: Any) -> tuple[bool, Any]:
        self.stages.append(stage)
        if not self.elected:
            # cancelled / expired / revoked: NOTHING runs, no effect fires.
            return False, None
        return True, publication()

    def reason(self) -> str:
        return "" if self.elected else "speech_session_not_live"


class _FakeSession:
    def __init__(self, *, elected: bool = True) -> None:
        self.fence = _FakeFence(elected=elected)

    def provider(self) -> Any:
        # A provider with no fence publishes directly — the pipeline election is
        # HS-131-09's ground, not this story's.
        return object()


class _FakeInterval:
    """The socket's admitted open-mic interval (admission itself is HS-131-09's)."""

    def __init__(self, *, elected: bool = True) -> None:
        self.handle = "mic_one_pipeline"
        self.session = _FakeSession(elected=elected)


class _FakeRegistry:
    def __init__(self, *, elected: bool = True) -> None:
        self.opened = 0
        self.closed: list[str] = []
        self.elected = elected
        self.interval: _FakeInterval | None = None

    def open(self, _principal: Any, **_kw: Any) -> _FakeInterval:
        self.opened += 1
        self.interval = _FakeInterval(elected=self.elected)
        return self.interval

    def close(self, _principal: Any, *, reason: str = "") -> str:
        self.closed.append(reason)
        return "mic_one_pipeline"


class _Socket:
    """The client half of ``/ws/dictation/stream``, scripted."""

    def __init__(self, *, start: dict | None = None, late: dict | None = None) -> None:
        self.headers = {
            "authorization": f"Bearer {OWNER_TOKEN}",
            "sec-websocket-protocol": "",
        }
        self.sent: list[dict[str, Any]] = []
        self.messages: list[dict[str, Any]] = []
        if start is not None:
            self.messages.append({"text": json.dumps(start)})
        self.messages.append({"bytes": np.zeros(16000, dtype=np.int16).tobytes()})
        if late is not None:
            self.messages.append({"text": json.dumps(late)})
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

    def finals(self) -> list[str]:
        return [event["text"] for event in self.sent if event.get("type") == "final"]

    def final_frames(self) -> list[dict[str, Any]]:
        """The `final` frames as sent — the whole shape, not just the text."""
        return [event for event in self.sent if event.get("type") == "final"]

    def fired(self) -> list[dict[str, Any]]:
        return [
            event["fired"]
            for event in self.sent
            if event.get("type") == "final" and event.get("fired")
        ]

    def errors(self) -> list[dict[str, Any]]:
        return [event for event in self.sent if event.get("type") == "error"]


@dataclass
class _Run:
    """Everything one socket's lifetime produced."""

    socket: _Socket
    passes: list[str]
    journal: _Journal
    typed: list[tuple[str, str]]
    registry: _FakeRegistry


@pytest.fixture
def stream(monkeypatch):
    """Run one scripted socket against the real WS route; report what happened."""
    registry = _FakeRegistry()
    monkeypatch.setattr(voice_routes, "browser_mic_sessions", lambda: registry)

    config = Config()
    # The passthrough lane: the real pipeline function runs and journals, with
    # no model call anywhere near it.
    config.dictation.pipeline.enabled = False
    config.meeting.web_auth_token = OWNER_TOKEN
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))

    passes: list[str] = []

    import holdspeak.dictation_runner as dictation_runner

    original = dictation_runner.process_transcript

    async def counted(*args: Any, **kwargs: Any) -> str:
        passes.append(str(kwargs.get("raw_text", args[0] if args else "")))
        return await original(*args, **kwargs)

    monkeypatch.setattr(dictation_runner, "process_transcript", counted)

    def run(
        start: dict | None = None,
        late: dict | None = None,
        *,
        macro: tuple[str, str, str] | None = None,
        said: str = TRANSCRIPT,
        elected: bool = True,
    ) -> _Run:
        from holdspeak.config import MacrosConfig, VoiceMacro, VoiceMacroAction

        registry.elected = elected
        if macro is not None:
            keyword, kind, payload = macro
            config.dictation.macros = MacrosConfig(
                enabled=True,
                items=[VoiceMacro(keyword, VoiceMacroAction(kind, payload))],
            )
        else:
            config.dictation.macros = MacrosConfig(enabled=False, items=[])

        journal = _Journal()
        typed: list[tuple[str, str]] = []
        ctx = WebContext(
            get_state=lambda: {},
            on_transcribe=lambda _audio, **_kw: said,
            journal=journal,
            on_remote_dictation=lambda text, *, target="agent": typed.append(
                (text, target)
            ),
            web_auth_token=OWNER_TOKEN,
        )
        endpoint = _endpoint_for(build_voice_router(ctx), "/ws/dictation/stream")
        socket = _Socket(start=start, late=late)
        asyncio.run(endpoint(socket))
        return _Run(socket, passes, journal, typed, registry)

    return run


def _endpoint_for(router: Any, path: str) -> Any:
    for route in router.routes:
        if getattr(route, "path", "") == path:
            return route.endpoint
    raise AssertionError(f"no route for {path}")


# ── the field mic: verbatim, unjournaled ─────────────────────────────────────


def test_a_field_fill_runs_zero_pipeline_stages_and_writes_no_journal_row(stream):
    """`pipeline: false` -> the words the user said, and nothing else happened."""
    run = stream({"type": "start", "pipeline": False})

    assert run.socket.finals() == [TRANSCRIPT]  # verbatim to the field
    assert run.passes == [], "a speak-to-fill must not reach the DIR pipeline"
    assert run.journal.rows == [], "the user typing with their voice is not journaled"


def test_a_field_fills_declaration_cannot_be_flipped_back_mid_stream(stream):
    """The kind of utterance is declared ONCE, before the audio. A later frame
    asking for the pipeline does not turn a field fill into a journaled,
    rewritten utterance after the fact."""
    run = stream(
        {"type": "start", "pipeline": False},
        late={"type": "start", "pipeline": True},
    )

    assert run.socket.finals() == [TRANSCRIPT]
    assert run.passes == []
    assert run.journal.rows == []


# ── the Speak room: piped exactly once ───────────────────────────────────────


def test_the_speak_rooms_talk_key_pipes_the_final_exactly_once(stream):
    """`pipeline: true` (the transport key) -> one pass, one journal row."""
    run = stream({"type": "start", "pipeline": True})

    assert run.socket.finals() == [TRANSCRIPT]
    assert run.passes == [TRANSCRIPT], "exactly one pipeline execution"
    assert run.journal.rows == ["browser"], "exactly one journal row"


def test_a_socket_that_declares_nothing_keeps_the_pipelined_final(stream):
    """No start frame -> the pre-132-04 behavior, unchanged."""
    run = stream(None)

    assert run.socket.finals() == [TRANSCRIPT]
    assert run.passes == [TRANSCRIPT]
    assert run.journal.rows == ["browser"]


# ── voice macros: fired ONCE, on the delivery leg only ───────────────────────

MACRO = ("standup", "type_text", "## Standup")


def test_a_spoken_keyword_fires_its_macro_once_on_the_delivery_leg(stream):
    """Parity with the hotkey path (runtime/dictation_capture.py:117-173) and the
    remote relay (routes/dictation/pipeline.py:724-764): a configured keyword
    FIRES and is not dictated as prose. It fires here, on the leg that already
    runs the pipeline — the `raw: true` delivery that follows never dispatches,
    so one utterance fires one macro."""
    run = stream({"type": "start", "pipeline": True}, macro=MACRO, said="standup")

    assert run.typed == [("## Standup", "focused")], "fired exactly once"
    assert run.socket.finals() == [""], "the command consumed the utterance"
    assert run.socket.fired() == [
        {
            "keyword": "standup",
            "kind": "type_text",
            "preview": "types: ## Standup",
            "ok": True,
            "error": "",
        }
    ]
    assert run.passes == [], "a fired command is not also a dictation"
    assert run.journal.rows == []


def test_a_field_fill_never_fires_a_macro(stream):
    """Typing with your voice is not commanding: the same keyword, in a field,
    is the word the user said."""
    run = stream({"type": "start", "pipeline": False}, macro=MACRO, said="standup")

    assert run.typed == [], "a speak-to-fill dispatches nothing"
    assert run.socket.finals() == ["standup"], "verbatim into the field"
    assert run.socket.fired() == []
    assert run.passes == [] and run.journal.rows == []


def test_a_non_keyword_utterance_is_unchanged_by_the_macro_seam(stream):
    """Macros configured, nothing matched -> the single pass and its one row."""
    run = stream({"type": "start", "pipeline": True}, macro=MACRO)

    assert run.typed == []
    assert run.socket.finals() == [TRANSCRIPT]
    assert run.passes == [TRANSCRIPT]
    assert run.journal.rows == ["browser"]


def test_macros_off_never_reaches_the_election(stream):
    """The default desk: no macro configured -> no election, no dispatch."""
    run = stream({"type": "start", "pipeline": True})

    assert run.registry.interval is not None
    assert run.registry.interval.session.fence.stages == []
    assert run.passes == [TRANSCRIPT]


def test_a_cancelled_session_fires_no_macro_and_says_so(stream):
    """The effect runs inside the cancellation election the hotkey path uses: a
    session cancelled while Whisper worked fires nothing and publishes nothing."""
    run = stream(
        {"type": "start", "pipeline": True}, macro=MACRO, said="standup", elected=False
    )

    assert run.typed == [], "no connector effect under a dead session"
    assert run.socket.finals() == []
    assert run.passes == [] and run.journal.rows == []
    assert run.socket.errors()[0]["reason"] == "speech_session_not_live"


# ── the delivery half: raw, so the one pass is the only pass ─────────────────

PIPELINE = "holdspeak.web.routes.dictation.pipeline._run_dictation_dry_run_text"


def _delivery_client(ctx: WebContext) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def authenticated(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "one-pipeline-test")
        return await call_next(request)

    app.include_router(build_pipeline_router(ctx, project_doc_suggestions={}))
    return TestClient(app)


def test_the_room_delivers_the_single_passes_output_verbatim(monkeypatch):
    """What the deck posts after the WS final: `raw: true`, so the pipeline does
    not run a second time and the delivered words ARE the receipt's words."""
    passes: list[str] = []

    def counting_pipeline(text, *_a, **_kw):
        passes.append(text)
        return {"final_text": f"[corrected] {text}"}

    monkeypatch.setattr(PIPELINE, counting_pipeline)
    # hermetic: macros off, no read of the owner's real config
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: Config()))
    journal = _Journal()
    typed: list = []
    ctx = WebContext(
        get_state=lambda: {},
        journal=journal,
        on_remote_dictation=lambda t, *, target="agent": typed.append((t, target)),
    )

    response = _delivery_client(ctx).post(
        "/api/dictation/remote",
        json={
            # the text the WS final already produced
            "text": "[corrected] ship it friday",
            "target_mode": "focused",
            "raw": True,
            "delivery_id": f"speak:{uuid.uuid4()}",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["final_text"] == "[corrected] ship it friday"  # not re-corrected
    assert typed == [("[corrected] ship it friday", "focused")]
    assert passes == [], "the delivery half runs zero pipeline passes"
    assert journal.rows == [], "the second journal row is gone"


def test_a_typed_utterance_still_takes_its_one_pipeline_pass(monkeypatch):
    """Text the user TYPED into the well carries no receipt: it is piped here,
    exactly once — the raw flag is the deck's honest claim, not a blanket."""
    passes: list[str] = []

    def counting_pipeline(text, *_a, **_kw):
        passes.append(text)
        return {"final_text": f"[corrected] {text}"}

    monkeypatch.setattr(PIPELINE, counting_pipeline)
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: Config()))
    typed: list = []
    ctx = WebContext(
        get_state=lambda: {},
        on_remote_dictation=lambda t, *, target="agent": typed.append((t, target)),
    )

    response = _delivery_client(ctx).post(
        "/api/dictation/remote",
        json={
            "text": "ship it friday",
            "target_mode": "focused",
            "delivery_id": f"speak:{uuid.uuid4()}",
        },
    )

    assert response.status_code == 200
    assert passes == ["ship it friday"]
    assert typed == [("[corrected] ship it friday", "focused")]


# ── HS-176 C1 — the SPOKEN leg's `final` frame carries the run's facts ───────
#
# The Speak face's TALK key delivers `raw: true`, so the delivery reply runs no
# pipeline and rightly reports no run facts. The leg that DID run the pipeline
# is this socket, and it wrote the journal row. Counsel's re-read: unless this
# frame carries `raw_text`, `corrections_applied` and `journal_id`, the spoken
# Tuesday has no APPLIED chip, pre-fills the TEXT teach from the LANDED text,
# and teaches on the corrections fallback instead of the journal route.
#
# R2: the facts are CARRIED out of the run that computed them. Nothing here
# looks up "the newest journal row".


def test_the_spoken_final_frame_carries_the_runs_three_facts(stream):
    """`pipeline: true` -> the frame the browser reads has all three keys."""
    run = stream({"type": "start", "pipeline": True})

    frames = run.socket.final_frames()
    assert len(frames) == 1
    frame = frames[0]
    assert frame["text"] == TRANSCRIPT
    # the transcript AS HEARD (the string the `text` rules were applied to)
    assert frame["raw_text"] == TRANSCRIPT
    # the ids that fired: none, on the passthrough lane — but the key is there
    assert frame["corrections_applied"] == []
    # the row THIS run wrote, so `teach()` takes the journal correct route
    assert frame["journal_id"] == 101
    assert run.journal.rows == ["browser"]


def test_the_spoken_facts_name_the_row_this_run_wrote(stream):
    """Two utterances, two rows: each frame names its OWN row, never the newest."""
    first = stream({"type": "start", "pipeline": True}, said="ship it friday")
    second = stream({"type": "start", "pipeline": True}, said="ship it monday")

    assert first.socket.final_frames()[0]["journal_id"] == 101
    assert first.socket.final_frames()[0]["raw_text"] == "ship it friday"
    # a fresh journal per socket in this rig; what is pinned is that each frame
    # carries the id from its own publication rather than a read-time lookup.
    assert second.socket.final_frames()[0]["journal_id"] == 101
    assert second.socket.final_frames()[0]["raw_text"] == "ship it monday"


def test_a_field_fills_final_frame_carries_no_run_facts(stream):
    """A speak-to-fill runs no pipeline and writes no row: it invents nothing."""
    run = stream({"type": "start", "pipeline": False})

    frame = run.socket.final_frames()[0]
    assert frame["text"] == TRANSCRIPT
    assert "raw_text" not in frame
    assert "corrections_applied" not in frame
    assert "journal_id" not in frame
    assert run.journal.rows == []


def test_a_fired_macros_final_frame_carries_no_run_facts(stream):
    """A command consumed the utterance: no pipeline, no row, no facts."""
    run = stream({"type": "start", "pipeline": True}, macro=MACRO, said="standup")

    frame = run.socket.final_frames()[0]
    assert frame["text"] == ""
    assert frame["fired"]["keyword"] == "standup"
    assert "raw_text" not in frame
    assert "journal_id" not in frame
