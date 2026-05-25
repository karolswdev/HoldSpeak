from __future__ import annotations

import threading
from types import SimpleNamespace

import numpy as np
import pytest

from holdspeak.agent_context import AgentSession
import holdspeak.web_runtime as web_runtime


def _config(
    *,
    auto_open: bool = True,
    warm_on_start: bool = False,
    dictation_enabled: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        model=SimpleNamespace(name="base", warm_on_start=warm_on_start),
        hotkey=SimpleNamespace(key="alt_r", display="Right Option"),
        meeting=SimpleNamespace(
            mic_device=None,
            system_audio_device=None,
            mic_label="Me",
            remote_label="Remote",
            intel_enabled=False,
            intel_realtime_model="model.gguf",
            intel_provider="local",
            intel_cloud_model="gpt-5-mini",
            intel_cloud_api_key_env="OPENAI_API_KEY",
            intel_cloud_base_url=None,
            intel_cloud_reasoning_effort=None,
            intel_cloud_store=False,
            intel_deferred_enabled=True,
            diarization_enabled=False,
            diarize_mic=False,
            cross_meeting_recognition=True,
            web_auto_open=auto_open,
            mir_enabled=True,
            mir_profile="balanced",
        ),
        dictation=SimpleNamespace(
            pipeline=SimpleNamespace(
                enabled=dictation_enabled,
                stages=["project-rewriter"],
                max_total_latency_ms=600,
                target_profile_override="auto",
            ),
            runtime=SimpleNamespace(),
        ),
    )


def test_run_web_runtime_starts_and_stops_services(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(web_runtime.Config, "load", lambda: _config(auto_open=True))

    server_instances: list[object] = []
    browser_urls: list[str] = []
    listener_events: list[str] = []

    class FakeServer:
        def __init__(self, **kwargs):
            _ = kwargs
            self.started = False
            self.stopped = False
            server_instances.append(self)

        def start(self) -> str:
            self.started = True
            return "http://127.0.0.1:9999"

        def stop(self) -> None:
            self.stopped = True

    class FakeAudioRecorder:
        def __init__(self, **kwargs):
            _ = kwargs

    class FakeHotkeyListener:
        def __init__(self, **kwargs):
            _ = kwargs

        def start(self) -> None:
            listener_events.append("start")

        def stop(self) -> None:
            listener_events.append("stop")

    class FakeTextTyper:
        def type_text(self, _text: str) -> None:
            return None

    monkeypatch.setattr(web_runtime, "MeetingWebServer", FakeServer)
    monkeypatch.setattr(web_runtime, "AudioRecorder", FakeAudioRecorder)
    monkeypatch.setattr(web_runtime, "HotkeyListener", FakeHotkeyListener)
    monkeypatch.setattr(web_runtime, "TextTyper", FakeTextTyper)
    monkeypatch.setattr(web_runtime.webbrowser, "open", lambda url: browser_urls.append(url))

    stop_event = threading.Event()
    stop_event.set()

    web_runtime.run_web_runtime(
        no_open=False,
        stop_event=stop_event,
        register_signal_handlers=False,
    )

    assert len(server_instances) == 1
    assert server_instances[0].started is True
    assert server_instances[0].stopped is True
    assert listener_events == ["start", "stop"]
    assert browser_urls == ["http://127.0.0.1:9999"]


def test_run_web_runtime_no_open_skips_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(web_runtime.Config, "load", lambda: _config(auto_open=True))

    browser_urls: list[str] = []

    class FakeServer:
        def __init__(self, **kwargs):
            _ = kwargs

        def start(self) -> str:
            return "http://127.0.0.1:9998"

        def stop(self) -> None:
            return None

    class FakeAudioRecorder:
        def __init__(self, **kwargs):
            _ = kwargs

    class FakeHotkeyListener:
        def __init__(self, **kwargs):
            _ = kwargs

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    monkeypatch.setattr(web_runtime, "MeetingWebServer", FakeServer)
    monkeypatch.setattr(web_runtime, "AudioRecorder", FakeAudioRecorder)
    monkeypatch.setattr(web_runtime, "HotkeyListener", FakeHotkeyListener)
    monkeypatch.setattr(web_runtime.webbrowser, "open", lambda url: browser_urls.append(url))

    stop_event = threading.Event()
    stop_event.set()

    web_runtime.run_web_runtime(
        no_open=True,
        stop_event=stop_event,
        register_signal_handlers=False,
    )

    assert browser_urls == []


def test_run_web_runtime_warms_transcriber_on_start(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(web_runtime.Config, "load", lambda: _config(auto_open=False, warm_on_start=True))

    loaded = threading.Event()
    server_instances: list[object] = []

    class FakeServer:
        def __init__(self, **kwargs):
            self.on_get_status = kwargs["on_get_status"]
            server_instances.append(self)

        def start(self) -> str:
            return "http://127.0.0.1:9996"

        def stop(self) -> None:
            return None

    class FakeAudioRecorder:
        def __init__(self, **kwargs):
            _ = kwargs

    class FakeHotkeyListener:
        def __init__(self, **kwargs):
            _ = kwargs

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    class FakeTranscriber:
        def __init__(self, model_name: str):
            self.model_name = model_name
            loaded.set()

        def transcribe(self, _audio):
            return "hello world"

    monkeypatch.setattr(web_runtime, "MeetingWebServer", FakeServer)
    monkeypatch.setattr(web_runtime, "AudioRecorder", FakeAudioRecorder)
    monkeypatch.setattr(web_runtime, "HotkeyListener", FakeHotkeyListener)
    monkeypatch.setattr(web_runtime, "Transcriber", FakeTranscriber)

    stop_event = threading.Event()
    stop_event.set()

    web_runtime.run_web_runtime(
        no_open=True,
        stop_event=stop_event,
        register_signal_handlers=False,
    )

    assert loaded.wait(1.0)
    status = server_instances[0].on_get_status()
    assert status["transcription"] == {
        "model": "base",
        "warm_on_start": True,
        "status": "loaded",
        "error": "",
    }


def test_run_web_runtime_fails_with_actionable_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(web_runtime.Config, "load", lambda: _config(auto_open=False))

    class FailingServer:
        def __init__(self, **kwargs):
            _ = kwargs

        def start(self) -> str:
            raise RuntimeError("fastapi missing")

    monkeypatch.setattr(web_runtime, "MeetingWebServer", FailingServer)

    with pytest.raises(SystemExit) as exc:
        web_runtime.run_web_runtime(register_signal_handlers=False)

    assert exc.value.code == 1


def test_runtime_meeting_control_callbacks_are_wired(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(web_runtime.Config, "load", lambda: _config(auto_open=False))
    saved_windows: list[dict[str, object]] = []
    saved_runs: list[dict[str, object]] = []
    saved_artifacts: list[dict[str, object]] = []
    drain_calls: list[dict[str, object]] = []

    def _fake_drain_plugin_run_queue(*, host, db, max_jobs=None, include_scheduled=False, **kwargs):
        _ = host, db, kwargs
        drain_calls.append(
            {
                "max_jobs": max_jobs,
                "include_scheduled": include_scheduled,
            }
        )
        return 3 if include_scheduled else 1

    monkeypatch.setattr(web_runtime, "drain_plugin_run_queue", _fake_drain_plugin_run_queue)

    class FakeDb:
        def record_intent_window(self, **kwargs):
            saved_windows.append(dict(kwargs))

        def record_plugin_run(self, **kwargs):
            saved_runs.append(dict(kwargs))

        def list_plugin_runs(self, meeting_id: str, *, limit: int = 5000):
            _ = limit
            return [
                SimpleNamespace(
                    id=index + 1,
                    meeting_id=meeting_id,
                    window_id=run["window_id"],
                    plugin_id=run["plugin_id"],
                    plugin_version=run["plugin_version"],
                    status=run["status"],
                    output=run.get("output"),
                    created_at=f"2026-03-29T00:00:{index:02d}",
                )
                for index, run in enumerate(saved_runs)
                if run.get("meeting_id") == meeting_id
            ]

        def record_artifact(self, **kwargs):
            saved_artifacts.append(dict(kwargs))

    import holdspeak.db as db_module

    monkeypatch.setattr(db_module, "get_database", lambda: FakeDb())

    captured_callbacks: dict[str, object] = {}

    class FakeState:
        def __init__(self) -> None:
            self.id = "meeting-1"
            self.web_url = None
            self._active = True
            self.title = None
            self.tags: list[str] = []
            self.devices: list[object] = []

        def to_dict(self) -> dict[str, object]:
            return {
                "id": self.id,
                "started_at": "2026-03-29T00:00:00",
                "ended_at": None if self._active else "2026-03-29T00:10:00",
                "duration": 12.0,
                "formatted_duration": "00:12",
                "title": self.title,
                "tags": list(self.tags),
                "segments": [],
                "bookmarks": [],
                "intel": None,
                "intel_status": {"state": "disabled", "detail": None, "requested_at": None, "completed_at": None},
                "mic_label": "Me",
                "remote_label": "Remote",
                "web_url": self.web_url,
            }

    class FakeMeetingSession:
        def __init__(self, **kwargs):
            _ = kwargs
            self._state = FakeState()
            self._active = False

        @property
        def is_active(self) -> bool:
            return self._active

        @property
        def state(self):
            return self._state if self._active else None

        def start(self):
            self._active = True
            self._state._active = True
            self._state.web_url = "http://127.0.0.1:9997"
            return self._state

        def stop(self):
            self._active = False
            self._state._active = False
            return self._state

        def save(self):
            return SimpleNamespace(
                database_saved=True,
                json_saved=False,
                json_path=None,
                intel_job_enqueued=False,
            )

        def set_title(self, title: str):
            self._state.title = str(title).strip() or None

        def set_tags(self, tags: list[str]):
            self._state.tags = [str(tag).strip().lower() for tag in tags if str(tag).strip()]

    class FakeServer:
        def __init__(self, **kwargs):
            captured_callbacks.update(kwargs)
            self.events: list[tuple[str, object]] = []

        def start(self) -> str:
            status_cb = captured_callbacks["on_get_status"]
            start_cb = captured_callbacks["on_start"]
            stop_meeting_cb = captured_callbacks["on_meeting_stop"]
            stop_cb = captured_callbacks["on_stop"]
            update_meeting_cb = captured_callbacks["on_update_meeting"]
            get_intent_controls_cb = captured_callbacks["on_get_intent_controls"]
            set_intent_profile_cb = captured_callbacks["on_set_intent_profile"]
            set_intent_override_cb = captured_callbacks["on_set_intent_override"]
            route_preview_cb = captured_callbacks["on_route_preview"]
            process_plugin_jobs_cb = captured_callbacks["on_process_plugin_jobs"]

            status_before = status_cb()
            assert status_before["meeting_active"] is False
            assert status_before["state"]["title"] == ""

            # Runtime control plane can stage meeting metadata before a meeting is active.
            idle_updated = update_meeting_cb(title="  Planning Sync  ", tags=["Ops", " qA "])
            assert idle_updated["meeting_active"] is False
            assert idle_updated["title"] == "Planning Sync"
            assert idle_updated["tags"] == ["ops", "qa"]

            started = start_cb()
            assert started["id"] == "meeting-1"
            assert started["title"] == "Planning Sync"
            assert started["tags"] == ["ops", "qa"]

            active_updated = update_meeting_cb(title="Live Update", tags=["Delivery"])
            assert active_updated["title"] == "Live Update"
            assert active_updated["tags"] == ["delivery"]

            status_after = status_cb()
            assert status_after["meeting_active"] is True
            assert status_after["meeting"]["title"] == "Live Update"
            assert status_after["state"]["title"] == "Live Update"

            active_process = process_plugin_jobs_cb(max_jobs=2, include_scheduled=False)
            assert active_process["processed"] == 0
            assert active_process["skipped_active_meeting"] is True
            assert drain_calls == []

            controls = get_intent_controls_cb()
            assert controls["enabled"] is True
            assert controls["profile"] == "balanced"

            updated_controls = set_intent_profile_cb("architect")
            assert updated_controls["profile"] == "architect"
            updated_controls = set_intent_override_cb(["incident", "comms"])
            assert updated_controls["override_intents"] == ["incident", "comms"]

            route = route_preview_cb(
                profile=None,
                threshold=0.6,
                intent_scores={"architecture": 0.9},
                override_intents=None,
                previous_intents=None,
                tags=["design"],
                transcript="Discuss architecture and API evolution",
            )
            assert route["profile"] == "architect"
            assert route["override_intents"] == ["incident", "comms"]
            assert "plugin_chain" in route
            assert isinstance(route["plugin_runs"], list)
            assert route["plugin_runs"]
            # `blocked` is a legitimate outcome for plugins whose
            # required capabilities (e.g. `llm` on `mermaid_architecture`
            # since HS-16-01) are not enabled in this test host.
            assert all(
                run["status"] in {"success", "deduped", "blocked"}
                for run in route["plugin_runs"]
            )

            cleared_controls = set_intent_override_cb([])
            assert cleared_controls["override_intents"] == []
            lexical_route = route_preview_cb(
                profile=None,
                threshold=0.2,
                intent_scores=None,
                override_intents=None,
                previous_intents=None,
                tags=["incident"],
                transcript="Incident mitigation update for stakeholders",
            )
            assert "incident" in lexical_route["active_intents"]
            assert isinstance(lexical_route["plugin_runs"], list)
            assert lexical_route["plugin_runs"]

            stopped = stop_meeting_cb()
            assert stopped["status"] == "stopped"
            assert stopped["save"]["intent_windows_saved"] == 2
            assert stopped["save"]["plugin_runs_saved"] >= 2
            assert stopped["save"]["artifacts_saved"] >= 1
            assert stopped["save"]["artifact_synthesis_error"] is None

            retry_now_process = process_plugin_jobs_cb(max_jobs=5, include_scheduled=True)
            assert retry_now_process["processed"] == 3
            assert retry_now_process["skipped_active_meeting"] is False

            due_only_process = process_plugin_jobs_cb(max_jobs=4, include_scheduled=False)
            assert due_only_process["processed"] == 1
            assert due_only_process["skipped_active_meeting"] is False
            assert drain_calls == [
                {"max_jobs": 5, "include_scheduled": True},
                {"max_jobs": 4, "include_scheduled": False},
            ]

            stopped_runtime = stop_cb()
            assert stopped_runtime["status"] == "stopping_runtime"

            return "http://127.0.0.1:9997"

        def broadcast(self, message_type: str, data) -> None:
            self.events.append((message_type, data))

        def stop(self) -> None:
            return None

    class FakeAudioRecorder:
        def __init__(self, **kwargs):
            _ = kwargs

    class FakeHotkeyListener:
        def __init__(self, **kwargs):
            _ = kwargs

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    class FakeTranscriber:
        def __init__(self, model_name: str):
            self.model_name = model_name

        def transcribe(self, _audio):
            return "hello world"

    class FakeTextTyper:
        def type_text(self, _text: str) -> None:
            return None

    monkeypatch.setattr(web_runtime, "MeetingSession", FakeMeetingSession)
    monkeypatch.setattr(web_runtime, "MeetingWebServer", FakeServer)
    monkeypatch.setattr(web_runtime, "AudioRecorder", FakeAudioRecorder)
    monkeypatch.setattr(web_runtime, "HotkeyListener", FakeHotkeyListener)
    monkeypatch.setattr(web_runtime, "Transcriber", FakeTranscriber)
    monkeypatch.setattr(web_runtime, "TextTyper", FakeTextTyper)

    stop_event = threading.Event()
    stop_event.set()

    web_runtime.run_web_runtime(
        no_open=True,
        stop_event=stop_event,
        register_signal_handlers=False,
    )
    assert len(saved_windows) == 2
    assert len(saved_runs) >= 2
    assert len(saved_artifacts) >= 1


def test_device_voice_reply_uses_waiting_agent_target_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    monkeypatch.setattr(
        web_runtime.Config,
        "load",
        lambda: _config(auto_open=False, dictation_enabled=True),
    )

    typed: list[str] = []
    pipeline_calls: list[object] = []
    completed = threading.Event()
    agent_session = AgentSession(
        agent="codex",
        session_id="abc",
        cwd=str(repo),
        updated_at="2026-05-24T00:00:00Z",
        hook_event_name="Stop",
        repo_root=str(repo),
        repo_anchor="git",
        project_name="repo",
        last_assistant_text="Should I run the focused tests?",
        awaiting_response=True,
    )

    class FakeServer:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def start(self) -> str:
            source = FakeSource()
            assert self.kwargs["on_device_voice_start"]("aipi-1", source) is True
            self.kwargs["on_device_voice_stop"]("aipi-1", source)
            assert completed.wait(timeout=2.0)
            return "http://127.0.0.1:9995"

        def stop(self) -> None:
            return None

    class FakeSource:
        def start_recording(self) -> None:
            return None

        def stop_recording(self):
            return np.ones(2000, dtype=np.float32)

    class FakeAudioRecorder:
        def __init__(self, **kwargs):
            _ = kwargs

    class FakeHotkeyListener:
        def __init__(self, **kwargs):
            _ = kwargs

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    class FakeTranscriber:
        def __init__(self, model_name: str):
            self.model_name = model_name

        def transcribe(self, _audio):
            return "yes run focused tests first"

    class FakeTextTyper:
        def type_text(self, text: str) -> None:
            typed.append(text)
            completed.set()

    class FakePipeline:
        def run(self, utt):
            pipeline_calls.append(utt)
            return SimpleNamespace(final_text="Run the focused tests first.")

    class FakeBuildResult:
        runtime_status = "loaded"
        pipeline = FakePipeline()

    monkeypatch.setattr(web_runtime, "MeetingWebServer", FakeServer)
    monkeypatch.setattr(web_runtime, "AudioRecorder", FakeAudioRecorder)
    monkeypatch.setattr(web_runtime, "HotkeyListener", FakeHotkeyListener)
    monkeypatch.setattr(web_runtime, "Transcriber", FakeTranscriber)
    monkeypatch.setattr(web_runtime, "TextTyper", FakeTextTyper)

    import holdspeak.agent_context as agent_context
    import holdspeak.plugins.dictation.assembly as assembly

    monkeypatch.setattr(
        agent_context,
        "get_recent_awaiting_agent_session",
        lambda **_kwargs: agent_session,
    )
    monkeypatch.setattr(assembly, "build_pipeline", lambda *_args, **_kwargs: FakeBuildResult())

    stop_event = threading.Event()
    stop_event.set()

    web_runtime.run_web_runtime(
        no_open=True,
        stop_event=stop_event,
        register_signal_handlers=False,
    )

    assert typed == ["Run the focused tests first."]
    assert len(pipeline_calls) == 1
    utt = pipeline_calls[0]
    assert utt.raw_text == "yes run focused tests first"
    assert utt.project["root"] == str(repo)
    assert utt.activity["target"]["id"] == "codex_cli"
    assert utt.activity["target"]["source"] == "override"
    assert utt.activity["agent"]["session_id"] == "abc"
