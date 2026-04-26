"""Unit tests for controller runtime config + shutdown behavior."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from holdspeak.config import Config
import holdspeak.controller as controller_module
from holdspeak.controller import HoldSpeakAppWithController, HoldSpeakController


class _FakeTranscriber:
    model_name = "base"

    def transcribe(self, _audio):
        return "ok"


class _FakeAudioRecorder:
    def __init__(self, *, device=None, on_level=None):
        self.device = device
        self.on_level = on_level

    def start_recording(self) -> None:
        pass

    def stop_recording(self):
        return [0.0] * 2000


class _FakeHotkeyListener:
    def __init__(self, on_press=None, on_release=None, hotkey="alt_r"):
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.hotkey = hotkey
        self.started = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.started = False


class _FakeTextTyper:
    def type_text(self, _text: str) -> None:
        pass


class _FakeApp:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.ui_state = SimpleNamespace(
            focused_hold_to_talk_key="v",
            is_idle=True,
            is_recording=False,
            meeting=SimpleNamespace(active=False),
        )
        self.notifications = []
        self.meeting_active = None
        self.cockpit_hidden = False
        self.hotkey_display = None

    def set_focused_hold_to_talk_key(self, key: str) -> None:
        self.ui_state.focused_hold_to_talk_key = key

    def set_text_injection_status(self, _enabled: bool, _reason: str = "") -> None:
        pass

    def set_global_hotkey_status(self, _enabled: bool, _reason: str = "") -> None:
        pass

    def set_state(self, _state: str) -> None:
        pass

    def set_audio_level(self, _level: float) -> None:
        pass

    def add_transcription(self, _text: str) -> None:
        pass

    def copy_to_clipboard(self, _text: str) -> bool:
        return True

    def notify(self, message: str, **kwargs) -> None:
        self.notifications.append((message, kwargs))

    def set_meeting_active(self, active: bool) -> None:
        self.meeting_active = active

    def set_meeting_has_system_audio(self, _has: bool) -> None:
        pass

    def show_meeting_cockpit(self, title: str = "", has_system_audio: bool = False) -> None:
        self.cockpit = (title, has_system_audio)

    def set_meeting_web_url(self, _url: str) -> None:
        pass

    def set_meeting_mic_level(self, _level: float) -> None:
        pass

    def set_meeting_system_level(self, _level: float) -> None:
        pass

    def hide_meeting_cockpit(self) -> None:
        self.cockpit_hidden = True

    def set_meeting_duration(self, _duration: str) -> None:
        pass

    def update_meeting_cockpit_segment(self, _segment) -> None:
        pass

    def update_meeting_cockpit_intel(self, _topics, _action_items, _summary) -> None:
        pass

    def update_meeting_cockpit_bookmark(self, _bookmark) -> None:
        pass

    def show_meeting_transcript(self, _segments, _bookmarks=None) -> None:
        pass

    def show_meeting_metadata(self, _title: str = "", _tags=None) -> None:
        pass

    def set_meeting_title(self, _title: str) -> None:
        pass

    def update_hotkey_display(self, display: str) -> None:
        self.hotkey_display = display


def _patch_runtime_deps(monkeypatch) -> None:
    monkeypatch.setattr(controller_module, "AudioRecorder", _FakeAudioRecorder)
    monkeypatch.setattr(controller_module, "HotkeyListener", _FakeHotkeyListener)
    monkeypatch.setattr(controller_module, "TextTyper", _FakeTextTyper)
    monkeypatch.setattr(controller_module, "start_intel_queue_worker", lambda *args, **kwargs: None)


def test_settings_apply_updates_runtime_and_new_meeting_uses_latest_devices(monkeypatch) -> None:
    _patch_runtime_deps(monkeypatch)

    captured_kwargs = {}

    class _FakeMeetingSession:
        def __init__(self, transcriber, **kwargs):
            _ = transcriber
            captured_kwargs.update(kwargs)
            self.has_system_audio = bool(kwargs.get("system_device"))
            self._state = SimpleNamespace(
                id="meeting-1",
                title="",
                web_url=None,
                segments=[],
                format_duration=lambda: "00:00",
            )

        @property
        def is_active(self) -> bool:
            return True

        @property
        def state(self):
            return self._state

        def start(self):
            return self._state

    monkeypatch.setattr(controller_module, "MeetingSession", _FakeMeetingSession)

    config = Config()
    app = _FakeApp(config)
    controller = HoldSpeakController(app, preloaded_transcriber=_FakeTranscriber())
    controller._meeting_timer_loop = lambda: None  # Avoid background timer work in this unit test.

    app.config.hotkey.key = "f2"
    app.config.meeting.mic_device = "USB Mic"
    app.config.meeting.system_audio_device = "Monitor of Built-in Audio"
    app.config.meeting.diarization_enabled = True
    app.config.meeting.diarize_mic = True

    controller.apply_runtime_config()
    controller._start_meeting()

    assert controller.recorder.device == "USB Mic"
    assert controller.hotkey_listener is not None
    assert controller.hotkey_listener.hotkey == "f2"
    assert captured_kwargs["mic_device"] == "USB Mic"
    assert captured_kwargs["system_device"] == "Monitor of Built-in Audio"
    assert captured_kwargs["diarization_enabled"] is True
    assert captured_kwargs["diarize_mic"] is True


def test_stop_with_finalize_persists_active_meeting_before_shutdown(monkeypatch) -> None:
    _patch_runtime_deps(monkeypatch)

    config = Config()
    app = _FakeApp(config)
    controller = HoldSpeakController(app, preloaded_transcriber=_FakeTranscriber())

    class _FakeSession:
        def __init__(self):
            self.stop_calls = 0
            self.save_calls = 0
            self.is_active = True

        def stop(self):
            self.stop_calls += 1
            return SimpleNamespace(id="meeting-2", segments=["seg"])

        def save(self):
            self.save_calls += 1
            return SimpleNamespace(database_saved=True, intel_job_enqueued=False, json_saved=True)

    session = _FakeSession()
    controller._meeting_session = session  # type: ignore[assignment]

    controller.stop(finalize_active_meeting=True, notify=False)

    assert session.stop_calls == 1
    assert session.save_calls == 1
    assert app.meeting_active is False
    assert app.cockpit_hidden is True


def test_intel_queue_worker_restarts_on_runtime_config_changes(monkeypatch) -> None:
    monkeypatch.setattr(controller_module, "AudioRecorder", _FakeAudioRecorder)
    monkeypatch.setattr(controller_module, "HotkeyListener", _FakeHotkeyListener)
    monkeypatch.setattr(controller_module, "TextTyper", _FakeTextTyper)

    started_workers = []

    class _FakeWorker:
        def __init__(
            self,
            model_path,
            poll_seconds,
            *,
            provider="local",
            cloud_model="gpt-5-mini",
            cloud_api_key_env="OPENAI_API_KEY",
            cloud_base_url=None,
            cloud_reasoning_effort=None,
            cloud_store=False,
            retry_base_seconds=30,
            retry_max_seconds=900,
            retry_max_attempts=6,
            failure_alert_percent=50.0,
            failure_alert_hysteresis_minutes=5.0,
            failure_alert_webhook_url=None,
            failure_alert_webhook_header_name=None,
            failure_alert_webhook_header_value=None,
        ):
            self.model_path = model_path
            self.provider = provider
            self.cloud_model = cloud_model
            self.cloud_api_key_env = cloud_api_key_env
            self.cloud_base_url = cloud_base_url
            self.cloud_reasoning_effort = cloud_reasoning_effort
            self.cloud_store = cloud_store
            self.retry_base_seconds = retry_base_seconds
            self.retry_max_seconds = retry_max_seconds
            self.retry_max_attempts = retry_max_attempts
            self.failure_alert_percent = failure_alert_percent
            self.failure_alert_hysteresis_seconds = max(0.0, float(failure_alert_hysteresis_minutes) * 60.0)
            self.failure_alert_webhook_url = (failure_alert_webhook_url or "").strip() or None
            self.failure_alert_webhook_header_name = (failure_alert_webhook_header_name or "").strip() or None
            self.failure_alert_webhook_header_value = (failure_alert_webhook_header_value or "").strip() or None
            self.poll_seconds = poll_seconds
            self._alive = True
            self.stop_calls = 0

        def stop(self, timeout: float = 5.0) -> None:
            _ = timeout
            self.stop_calls += 1
            self._alive = False

        def is_alive(self) -> bool:
            return self._alive

    def _start_worker(
        model_path=None,
        *,
        provider="local",
        cloud_model="gpt-5-mini",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url=None,
        cloud_reasoning_effort=None,
        cloud_store=False,
        retry_base_seconds=30,
        retry_max_seconds=900,
        retry_max_attempts=6,
        failure_alert_percent=50.0,
        failure_alert_hysteresis_minutes=5.0,
        failure_alert_webhook_url=None,
        failure_alert_webhook_header_name=None,
        failure_alert_webhook_header_value=None,
        poll_seconds=120.0,
    ):
        worker = _FakeWorker(
            model_path,
            poll_seconds,
            provider=provider,
            cloud_model=cloud_model,
            cloud_api_key_env=cloud_api_key_env,
            cloud_base_url=cloud_base_url,
            cloud_reasoning_effort=cloud_reasoning_effort,
            cloud_store=cloud_store,
            retry_base_seconds=retry_base_seconds,
            retry_max_seconds=retry_max_seconds,
            retry_max_attempts=retry_max_attempts,
            failure_alert_percent=failure_alert_percent,
            failure_alert_hysteresis_minutes=failure_alert_hysteresis_minutes,
            failure_alert_webhook_url=failure_alert_webhook_url,
            failure_alert_webhook_header_name=failure_alert_webhook_header_name,
            failure_alert_webhook_header_value=failure_alert_webhook_header_value,
        )
        started_workers.append(worker)
        return worker

    monkeypatch.setattr(controller_module, "start_intel_queue_worker", _start_worker)

    config = Config()
    app = _FakeApp(config)
    controller = HoldSpeakController(app, preloaded_transcriber=_FakeTranscriber())

    assert len(started_workers) == 1
    first_worker = started_workers[0]

    app.config.meeting.intel_queue_poll_seconds = 30
    controller.apply_runtime_config()

    assert len(started_workers) == 2
    assert first_worker.stop_calls == 1
    second_worker = started_workers[1]
    assert second_worker.poll_seconds == 30.0

    app.config.meeting.intel_deferred_enabled = False
    controller.apply_runtime_config()

    assert second_worker.stop_calls == 1
    assert controller._intel_queue_worker is None


def test_request_quit_finalizes_controller_before_exit() -> None:
    app = HoldSpeakAppWithController(config=Config())
    app._controller = MagicMock()

    with patch.object(app, "exit") as exit_mock:
        app.request_quit()

    app._controller.stop.assert_called_once_with(finalize_active_meeting=True, notify=False)
    exit_mock.assert_called_once()


def test_on_web_settings_applied_updates_runtime(monkeypatch) -> None:
    _patch_runtime_deps(monkeypatch)

    config = Config()
    app = _FakeApp(config)
    controller = HoldSpeakController(app, preloaded_transcriber=_FakeTranscriber())

    updated = Config()
    updated.hotkey.key = "f9"
    updated.hotkey.display = "F9"

    with patch.object(controller, "apply_runtime_config") as apply_runtime_config:
        controller._on_web_settings_applied(updated)

    assert app.config is updated
    assert app.hotkey_display == "F9"
    apply_runtime_config.assert_called_once()
    assert any(message == "Settings saved from web UI" for message, _kwargs in app.notifications)


# ---------------------------------------------------------------------------
# DIR-01 (HS-1-07) — controller wiring of the dictation pipeline.
# ---------------------------------------------------------------------------


class _FakeStageResult:
    def __init__(self, stage_id: str, elapsed_ms: float) -> None:
        self.stage_id = stage_id
        self.elapsed_ms = elapsed_ms


class _FakeIntent:
    def __init__(self, matched: bool, block_id: str | None) -> None:
        self.matched = matched
        self.block_id = block_id


class _FakePipelineRun:
    def __init__(
        self,
        final_text: str,
        *,
        stage_results=None,
        intent=None,
        warnings=None,
        total_elapsed_ms: float = 0.0,
        short_circuited: bool = False,
    ) -> None:
        self.final_text = final_text
        self.stage_results = stage_results or []
        self.intent = intent
        self.warnings = warnings or []
        self.total_elapsed_ms = total_elapsed_ms
        self.short_circuited = short_circuited


class _FakeDictationPipeline:
    def __init__(self, run_result: _FakePipelineRun, on_run=None) -> None:
        self._run_result = run_result
        self._on_run = on_run
        self.calls: list[object] = []

    def run(self, utt):
        self.calls.append(utt)
        if self._on_run is not None:
            self._on_run(self._run_result)
        return self._run_result


def _make_controller(monkeypatch, *, pipeline_enabled: bool = False) -> HoldSpeakController:
    _patch_runtime_deps(monkeypatch)
    config = Config()
    config.dictation.pipeline.enabled = pipeline_enabled
    app = _FakeApp(config)
    return HoldSpeakController(app, preloaded_transcriber=_FakeTranscriber())


def test_dictation_disabled_path_is_byte_identical_and_does_not_build_pipeline(monkeypatch) -> None:
    controller = _make_controller(monkeypatch, pipeline_enabled=False)

    builder_called = []

    def _refuse_to_build() -> object:
        builder_called.append(True)
        raise AssertionError("builder must not be called when pipeline disabled")

    monkeypatch.setattr(controller, "_build_dictation_pipeline", _refuse_to_build)

    out = controller._maybe_run_dictation_pipeline(
        "hello world",
        audio_duration_s=1.0,
        transcribed_at=datetime.now(),
    )

    assert out == "hello world"
    assert builder_called == []
    assert controller._dictation_pipeline is None
    assert controller._dictation_pipeline_failed is False


def test_dictation_enabled_runs_pipeline_and_types_final_text(monkeypatch) -> None:
    controller = _make_controller(monkeypatch, pipeline_enabled=True)

    intent = _FakeIntent(matched=True, block_id="ai_prompt_buildout")
    run_result = _FakePipelineRun(
        final_text="ENRICHED",
        stage_results=[_FakeStageResult("intent-router", 12.5), _FakeStageResult("kb-enricher", 0.4)],
        intent=intent,
        warnings=[],
        total_elapsed_ms=13.0,
    )
    fake_pipeline = _FakeDictationPipeline(run_result, on_run=controller._emit_pipeline_run)

    monkeypatch.setattr(controller, "_build_dictation_pipeline", lambda: fake_pipeline)

    log_records: list[tuple[str, dict]] = []

    def _capture(msg, *args, **kwargs):
        log_records.append((msg, kwargs.get("extra", {})))

    monkeypatch.setattr(controller_module.dictation_log, "info", _capture)

    out = controller._maybe_run_dictation_pipeline(
        "raw text",
        audio_duration_s=2.5,
        transcribed_at=datetime.now(),
    )

    assert out == "ENRICHED"
    assert len(fake_pipeline.calls) == 1
    utt = fake_pipeline.calls[0]
    assert utt.raw_text == "raw text"
    assert utt.audio_duration_s == 2.5
    assert utt.project is None

    # DIR-O-001 — one structured log line per run with the expected keys.
    assert len(log_records) == 1
    msg, extra = log_records[0]
    assert msg == "dictation_pipeline_run"
    assert extra["stage_ids"] == ["intent-router", "kb-enricher"]
    assert extra["elapsed_ms"] == {"intent-router": 12.5, "kb-enricher": 0.4}
    assert extra["intent_matched"] is True
    assert extra["intent_block_id"] == "ai_prompt_buildout"
    assert extra["total_elapsed_ms"] == 13.0


def test_dictation_pipeline_build_failure_falls_back_to_processed_text(monkeypatch) -> None:
    controller = _make_controller(monkeypatch, pipeline_enabled=True)

    build_calls = []

    def _broken_build() -> object:
        build_calls.append(True)
        raise RuntimeError("model file not found")

    monkeypatch.setattr(controller, "_build_dictation_pipeline", _broken_build)

    out = controller._maybe_run_dictation_pipeline(
        "fallback text",
        audio_duration_s=0.5,
        transcribed_at=datetime.now(),
    )
    assert out == "fallback text"
    assert controller._dictation_pipeline_failed is True

    # Sticky for the controller lifetime: subsequent utterance does not rebuild.
    out2 = controller._maybe_run_dictation_pipeline(
        "another",
        audio_duration_s=0.5,
        transcribed_at=datetime.now(),
    )
    assert out2 == "another"
    assert len(build_calls) == 1


def test_dictation_pipeline_run_exception_falls_back_to_processed_text(monkeypatch) -> None:
    controller = _make_controller(monkeypatch, pipeline_enabled=True)

    class _Exploding:
        def run(self, _utt):
            raise RuntimeError("backend exploded")

    monkeypatch.setattr(controller, "_build_dictation_pipeline", lambda: _Exploding())

    out = controller._maybe_run_dictation_pipeline(
        "stays the same",
        audio_duration_s=1.0,
        transcribed_at=datetime.now(),
    )
    assert out == "stays the same"


def test_apply_runtime_config_invalidates_dictation_pipeline(monkeypatch) -> None:
    controller = _make_controller(monkeypatch, pipeline_enabled=True)

    builds = []

    def _build():
        builds.append(True)
        return _FakeDictationPipeline(_FakePipelineRun(final_text="X"))

    monkeypatch.setattr(controller, "_build_dictation_pipeline", _build)

    controller._maybe_run_dictation_pipeline(
        "first",
        audio_duration_s=1.0,
        transcribed_at=datetime.now(),
    )
    assert len(builds) == 1
    assert controller._dictation_pipeline is not None

    controller.apply_runtime_config()
    assert controller._dictation_pipeline is None
    assert controller._dictation_pipeline_failed is False

    controller._maybe_run_dictation_pipeline(
        "second",
        audio_duration_s=1.0,
        transcribed_at=datetime.now(),
    )
    assert len(builds) == 2
