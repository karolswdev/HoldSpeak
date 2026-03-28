"""Integration test for quitting while a meeting is active."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.controller as controller_module
from holdspeak.config import Config
from holdspeak.controller import HoldSpeakAppWithController


class _FakeTranscriber:
    model_name = "base"


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

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


class _FakeTextTyper:
    def type_text(self, _text: str) -> None:
        pass


class _FakeMeetingSession:
    def __init__(self) -> None:
        self.is_active = True
        self.stop_calls = 0
        self.save_calls = 0

    def stop(self):
        self.stop_calls += 1
        return SimpleNamespace(id="meeting-quit", segments=["s1"])

    def save(self):
        self.save_calls += 1
        return SimpleNamespace(database_saved=True, intel_job_enqueued=False, json_saved=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quit_finalizes_active_meeting(monkeypatch) -> None:
    monkeypatch.setattr(controller_module, "AudioRecorder", _FakeAudioRecorder)
    monkeypatch.setattr(controller_module, "HotkeyListener", _FakeHotkeyListener)
    monkeypatch.setattr(controller_module, "TextTyper", _FakeTextTyper)
    monkeypatch.setattr(controller_module, "start_intel_queue_worker", lambda *args, **kwargs: None)

    app = HoldSpeakAppWithController(config=Config(), preloaded_transcriber=_FakeTranscriber())

    async with app.run_test(size=(100, 30)) as pilot:
        assert app._controller is not None
        fake_meeting = _FakeMeetingSession()
        app._controller._meeting_session = fake_meeting

        await pilot.press("q")
        await pilot.pause()

        assert app.is_running is False
        assert fake_meeting.stop_calls == 1
        assert fake_meeting.save_calls == 1
