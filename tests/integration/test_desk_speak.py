"""Speak on the hub (betterment/capture C1): Talk never freezes the desk.

Speech-to-text and the dictation clean-up used to run ON the hub's event loop
(``voice_stream.py`` called ``transcribe(audio)`` directly, and
``process_transcript`` ran the pipeline inline). A browser that closed
mid-Talk froze every window of the desk for about 65 s (``RECON.md`` §5).

These tests run the real hub app with ONE event loop (the TestClient
lifespan), stream PCM over the real ``/ws/dictation/stream`` socket, and poll
``/health`` while a slow transcription and a slow clean-up run. Two adapters
are substituted, because a runner has neither: the speech engine
(``on_transcribe``, which sleeps) and the open-mic admission registry (a cold
runner has no speech assignment to admit against; admission is proven in
``tests/unit/test_dictation_session_admission.py``). The pipeline itself is
the real ``dictation_runner`` passthrough, which journals the utterance.
"""
from __future__ import annotations

import contextlib
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

import numpy as np
import pytest

pytestmark = [pytest.mark.timeout(120)]

TOKEN = "desk-speak"
HEARD = "the cut-over moves to thursday"
SLOW_S = 2.0
FAST_ENOUGH_S = 0.5


class _Interval:
    handle = "mic_desk_speak"

    def __init__(self) -> None:
        self.session = SimpleNamespace(
            fence=SimpleNamespace(publish=lambda _stage, work: (True, work()), reason=lambda: ""),
            provider=lambda: None,
        )


class _Registry:
    def __init__(self) -> None:
        self.closed: list[str] = []

    def open(self, _principal: Any, **_kw: Any) -> _Interval:
        return _Interval()

    def close(self, _principal: Any, *, reason: str = "") -> str:
        self.closed.append(reason)
        return _Interval.handle


@contextlib.contextmanager
def _hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[SimpleNamespace]:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    import holdspeak.dictation_runner as runner
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.runtime import composition
    from holdspeak.web.routes.system import voice as voice_routes
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    home = tmp_path / "home"
    (home / ".holdspeak").mkdir(parents=True, exist_ok=True)
    for name, value in {
        "HOME": str(home),
        "HOLDSPEAK_MACOS_CALENDAR": "0",
        "HOLDSPEAK_AGENT_STATE": "off",
        "HOLDSPEAK_ACTIVE_TARGET": "off",
        "HOLDSPEAK_DESKTOP_NOTIFY": "0",
        "HOLDSPEAK_TEST_NO_REAL_CLI": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "XDG_CONFIG_HOME": str(home / ".config"),
        "HOLDSPEAK_CHANNEL_KEYSTORE_FILE": str(home / "channel-keys.json"),
        "HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(home / "people.key"),
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    monkeypatch.setattr(db_core, "_db", None, raising=False)

    config = Config()
    config.dictation.pipeline.enabled = False  # the real passthrough journals the words
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))

    registry = _Registry()
    monkeypatch.setattr(voice_routes, "browser_mic_sessions", lambda: registry)

    phases: list[str] = []

    def slow_transcribe(_audio: Any, **_kw: Any) -> str:
        phases.append("transcribing")
        time.sleep(SLOW_S)
        return HEARD

    real_pipeline = runner.run_pipeline_corrections_only

    def slow_pipeline(*args: Any, **kwargs: Any) -> str:
        phases.append("cleaning")
        time.sleep(SLOW_S)
        return real_pipeline(*args, **kwargs)

    monkeypatch.setattr(runner, "run_pipeline_corrections_only", slow_pipeline)

    db = get_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            on_transcribe=slow_transcribe,
        ),
        auth_token=TOKEN,
        dictation_corrections_repository=db.dictation_corrections,
        dictation_journal_repository=db.dictation_journal,
    )
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    try:
        # lifespan: ONE event loop serves the socket and every request, as on the real hub.
        with client:
            yield SimpleNamespace(client=client, db=db, phases=phases, registry=registry)
    finally:
        client.close()
        reset_database()
        composition.install(composition.bare(label="pytest"))


@contextlib.contextmanager
def _real_capture_hub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[SimpleNamespace]:
    """A real WebRuntime capture controller behind the real MCP dispatcher.

    The native PortAudio start leaf is the only capture seam substituted: it
    waits and then leaves the recorder admitted without touching hardware.
    ``MeetingService``, the websocket, the authenticated principal and MCP
    composition root remain production paths.
    """
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    import holdspeak.meeting_recorder as recorder_module
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.runtime import composition
    from holdspeak.web.routes.system import voice as voice_routes
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from holdspeak.web_runtime import WebRuntime
    from starlette.testclient import TestClient

    home = tmp_path / "home"
    (home / ".holdspeak").mkdir(parents=True, exist_ok=True)
    for name, value in {
        "HOME": str(home),
        "HOLDSPEAK_MACOS_CALENDAR": "0",
        "HOLDSPEAK_AGENT_STATE": "off",
        "HOLDSPEAK_ACTIVE_TARGET": "off",
        "HOLDSPEAK_DESKTOP_NOTIFY": "0",
        "HOLDSPEAK_TEST_NO_REAL_CLI": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "XDG_CONFIG_HOME": str(home / ".config"),
        "HOLDSPEAK_CHANNEL_KEYSTORE_FILE": str(home / "channel-keys.json"),
        "HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(home / "people.key"),
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    monkeypatch.setattr(db_core, "_db", None, raising=False)

    config = Config()
    config.dictation.pipeline.enabled = False
    monkeypatch.setattr(Config, "load", classmethod(lambda _cls: config))

    registry = _Registry()
    monkeypatch.setattr(voice_routes, "browser_mic_sessions", lambda: registry)
    phases: list[str] = []

    def slow_transcribe(_audio: Any, **_kw: Any) -> str:
        phases.append("transcribing")
        time.sleep(SLOW_S)
        return "start recording"

    # Keep the controller and MCP operation real, but make the native audio
    # start deterministic for a machine without PortAudio devices.
    def delayed_native_start(self: Any) -> None:
        phases.append("capturing")
        time.sleep(SLOW_S)
        self._mic_stream = None
        self._mic_capture_rate = self.sample_rate

    monkeypatch.setattr(recorder_module.MeetingRecorder, "_resolve_mic_device", staticmethod(lambda _device: 0))
    monkeypatch.setattr(recorder_module.MeetingRecorder, "_resolve_system_device", staticmethod(lambda _device: None))
    # This native-adapter double runs in process. A fresh capture child cannot
    # inherit monkeypatches; C10 tests cover the actual child boundary.
    monkeypatch.setattr(recorder_module.MeetingRecorder, "capture_process_supported", False)
    monkeypatch.setattr(recorder_module.MeetingRecorder, "_start_mic_stream", delayed_native_start)

    runtime = WebRuntime(register_signal_handlers=False)
    db = get_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=runtime._on_bookmark,
            on_stop=runtime._on_stop,
            on_meeting_stop=runtime._on_meeting_stop,
            on_start=runtime._start_meeting,
            get_state=runtime._get_state,
            on_transcribe=slow_transcribe,
            voice_session=runtime.voice_session,
            device_registry=runtime.device_registry,
        ),
        auth_token=TOKEN,
        dictation_corrections_repository=db.dictation_corrections,
        dictation_journal_repository=db.dictation_journal,
    )
    runtime.server = server
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    try:
        with client:
            yield SimpleNamespace(
                client=client,
                db=db,
                phases=phases,
                registry=registry,
                runtime=runtime,
            )
    finally:
        client.close()
        reset_database()
        composition.install(composition.bare(label="pytest"))


def _pcm(seconds: float = 1.0) -> bytes:
    return np.zeros(int(16000 * seconds), dtype=np.int16).tobytes()


def _poll_health_while(hub: SimpleNamespace, worker: threading.Thread) -> list[tuple[str, float]]:
    """GET /health until ``worker`` ends; each answer with the phase it fell in."""
    answers: list[tuple[str, float]] = []
    while worker.is_alive():
        phase = hub.phases[-1] if hub.phases else "streaming"
        started = time.monotonic()
        resp = hub.client.get("/health")
        took = time.monotonic() - started
        assert resp.status_code == 200, resp.text
        answers.append((phase, took))
        time.sleep(0.05)
    return answers


def _assert_hub_answered(answers: list[tuple[str, float]], phases: tuple[str, ...]) -> None:
    slow = [(p, round(t, 2)) for p, t in answers if t >= FAST_ENOUGH_S]
    assert not slow, f"/health was slow while Talk ran: {slow}"
    for phase in phases:
        hits = [t for p, t in answers if p == phase]
        assert len(hits) >= 3, f"/health was polled {len(hits)} times while {phase}: {answers}"


def test_the_hub_answers_while_a_talk_transcribes_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with _hub(tmp_path, monkeypatch) as hub:
        frames: list[dict[str, Any]] = []

        def talk() -> None:
            with hub.client.websocket_connect(
                "/ws/dictation/stream", headers={"Authorization": f"Bearer {TOKEN}"}
            ) as ws:
                ws.send_text(json.dumps({"type": "start", "pipeline": True}))
                ws.send_bytes(_pcm())
                ws.send_text(json.dumps({"type": "end"}))
                frames.append(ws.receive_json())

        talking = threading.Thread(target=talk)
        talking.start()
        answers = _poll_health_while(hub, talking)
        talking.join(timeout=30)

        assert hub.phases == ["transcribing", "cleaning"], hub.phases
        _assert_hub_answered(answers, ("transcribing", "cleaning"))
        assert frames and frames[0]["type"] == "final", frames
        assert frames[0]["text"] == HEARD, frames
        rows = hub.db.dictation_journal.recent()
        assert [r.transcript for r in rows] == [HEARD]


def test_the_hub_answers_while_a_real_record_macro_starts_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real MCP + MeetingService stay responsive during native start."""
    with _real_capture_hub(tmp_path, monkeypatch) as hub:
        frames: list[dict[str, Any]] = []

        def talk() -> None:
            with hub.client.websocket_connect(
                "/ws/dictation/stream", headers={"Authorization": f"Bearer {TOKEN}"}
            ) as ws:
                ws.send_text(json.dumps({"type": "start", "pipeline": True}))
                ws.send_bytes(_pcm())
                ws.send_text(json.dumps({"type": "end"}))
                frames.append(ws.receive_json())

        talking = threading.Thread(target=talk)
        talking.start()
        answers = _poll_health_while(hub, talking)
        talking.join(timeout=30)

        assert hub.phases == ["transcribing", "capturing"], hub.phases
        _assert_hub_answered(answers, ("transcribing", "capturing"))
        assert frames and frames[0]["type"] == "final", frames
        assert frames[0]["fired"]["kind"] == "desk_verb", frames
        assert frames[0]["fired"]["result"]["desk_verb"] == "record", frames
        started = frames[0]["fired"]["result"]["result"]
        assert started["id"] and started["ended_at"] is None, started
        assert started["capture_status"] == "recording", started

        # The next authenticated Stop reaches the same real MCP composition
        # root and releases the meeting floor after native teardown.
        response = hub.client.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "stop-after-record",
                "method": "tools/call",
                "params": {"name": "meeting.stop_capture", "arguments": {}},
            },
        )
        assert response.status_code == 200, response.text
        stop_body = response.json()
        assert stop_body.get("result", {}).get("isError") is False, stop_body
        assert hub.runtime.voice_session.active_owner is None


def test_a_browser_gone_mid_talk_keeps_the_words_and_never_stalls_the_hub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RECON.md §5: the browser closed while TALK was held. The words already
    streamed are still transcribed and journaled, nothing is sent, and the
    hub answers the whole time."""
    with _hub(tmp_path, monkeypatch) as hub:
        def kept() -> None:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if hub.registry.closed:
                    return
                time.sleep(0.05)

        with hub.client.websocket_connect(
            "/ws/dictation/stream", headers={"Authorization": f"Bearer {TOKEN}"}
        ) as ws:
            ws.send_text(json.dumps({"type": "start", "pipeline": True}))
            ws.send_bytes(_pcm())
            # The browser goes away: a disconnect, no `end` frame. The session
            # stays open until the work ends, because the TestClient cancels
            # the handler when the block exits and a real server does not.
            ws.close()
            waiting = threading.Thread(target=kept)
            waiting.start()
            answers = _poll_health_while(hub, waiting)
            waiting.join(timeout=30)

        assert hub.phases == ["transcribing", "cleaning"], hub.phases
        _assert_hub_answered(answers, ("transcribing", "cleaning"))
        assert hub.registry.closed == ["browser_mic_stream_closed"]
        rows = hub.db.dictation_journal.recent()
        assert [r.transcript for r in rows] == [HEARD], "the words he said are kept"
