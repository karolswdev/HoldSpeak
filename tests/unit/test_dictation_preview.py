"""HS-75-01 — preview before it types (the P60 wake grammar on hold-key
dictation).

OFF (default) is byte-identical: the typer receives immediately and no
preview state exists — locked here, not claimed. ON: a finished dictation
journals its pipeline pass, arms ONE one-shot preview (token +
`dictation_preview` broadcast), and types NOTHING until the consume route
commits it; discard burns it; agent-reply sessions never preview.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Optional

import numpy as np
import pytest

from holdspeak.config import Config
from holdspeak.runtime.dictation_capture import DictationCaptureMixin


class _Rig:
    """A fake runtime `self` exercising the REAL mixin methods unbound."""

    def __init__(self, *, preview: bool) -> None:
        import threading

        self.config = Config()
        self.config.dictation.preview_before_type = preview
        self.transcription_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.runtime_status: dict[str, Any] = {}
        self.typed: list[str] = []
        self.typer = SimpleNamespace(
            type_text=lambda t, **k: self.typed.append(t)
        )
        self.frames: list[tuple[str, Any]] = []
        self.server = SimpleNamespace(
            broadcast=lambda t, d: self.frames.append((t, d))
        )
        self.dictation_previews: dict[str, dict[str, Any]] = {}
        self.activity: list[str] = []
        self.first_marked = 0
        self.text_processor = SimpleNamespace(process=lambda t: t)

    # ── the mixin's collaborators, stubbed honestly ──
    def _ensure_transcriber_loaded(self):
        return SimpleNamespace(transcribe=lambda audio: "hello world")

    def _set_runtime_activity(self, state: str, **kwargs) -> None:
        self.activity.append(kwargs.get("last_event", state))

    def _maybe_dispatch_voice_command(self, text: str, session) -> Optional[Any]:
        return None

    def _maybe_run_dictation_pipeline(self, text: str, **kwargs) -> str:
        return text

    def _try_tmux_agent_reply(self, text: str, session) -> bool:
        return False

    def _paste_target_profile(self, session):
        return None

    def _mark_first_dictation(self) -> None:
        self.first_marked += 1

    def _set_voice_state(self, state: str, **kwargs) -> None:
        pass

    # ── the real mixin methods under test ──
    _transcribe_and_type = DictationCaptureMixin._transcribe_and_type
    _arm_dictation_preview = DictationCaptureMixin._arm_dictation_preview
    consume_dictation_preview = DictationCaptureMixin.consume_dictation_preview
    type_dictation_preview = DictationCaptureMixin.type_dictation_preview
    discard_dictation_preview = DictationCaptureMixin.discard_dictation_preview


AUDIO = np.zeros(16000, dtype=np.float32)


def test_off_is_byte_identical() -> None:
    rig = _Rig(preview=False)
    rig._transcribe_and_type(AUDIO)
    assert rig.typed == ["hello world"], "the default path must type immediately"
    assert rig.dictation_previews == {}
    assert not [f for f in rig.frames if f[0] == "dictation_preview"]
    assert rig.first_marked == 1


def test_on_arms_one_preview_and_types_nothing() -> None:
    rig = _Rig(preview=True)
    rig._transcribe_and_type(AUDIO)
    assert rig.typed == [], "nothing may type while armed"
    assert len(rig.dictation_previews) == 1
    (token, entry), = rig.dictation_previews.items()
    assert entry["text"] == "hello world"
    previews = [d for (t, d) in rig.frames if t == "dictation_preview"]
    assert previews == [{"token": token, "text": "hello world"}]
    assert "dictation_preview" in rig.activity
    assert rig.first_marked == 0, "first-dictation marks on DELIVERY, not on arm"


def test_type_it_consumes_exactly_once() -> None:
    rig = _Rig(preview=True)
    rig._transcribe_and_type(AUDIO)
    (token,) = rig.dictation_previews.keys()
    assert rig.type_dictation_preview(token) == "hello world"
    assert rig.typed == ["hello world"]
    assert rig.first_marked == 1
    assert rig.type_dictation_preview(token) is None, "the token burns"
    assert rig.typed == ["hello world"], "a burned token types nothing"


def test_discard_burns_without_typing() -> None:
    rig = _Rig(preview=True)
    rig._transcribe_and_type(AUDIO)
    (token,) = rig.dictation_previews.keys()
    assert rig.discard_dictation_preview(token) is True
    assert rig.typed == []
    assert rig.first_marked == 0
    assert rig.discard_dictation_preview(token) is False


def test_one_active_preview_at_a_time() -> None:
    rig = _Rig(preview=True)
    rig._transcribe_and_type(AUDIO)
    (first,) = rig.dictation_previews.keys()
    rig._transcribe_and_type(AUDIO)
    (second,) = rig.dictation_previews.keys()
    assert first != second
    assert rig.type_dictation_preview(first) is None, "the old token died"
    assert rig.type_dictation_preview(second) == "hello world"


def test_agent_reply_sessions_never_preview() -> None:
    rig = _Rig(preview=True)
    rig._transcribe_and_type(AUDIO, agent_reply_session=SimpleNamespace(id="s1"))
    assert rig.dictation_previews == {}, "answering the coder stays immediate"
    assert rig.typed == ["hello world"]


def test_the_routes_enforce_the_one_shot_contract() -> None:
    from fastapi.testclient import TestClient

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    store = {"tok-1": "stored text"}
    server = MeetingWebServer(WebRuntimeCallbacks(
        on_bookmark=lambda *a, **k: None, on_stop=lambda *a, **k: None,
        get_state=lambda: {"activity": {"state": "idle"}},
        on_preview_type=lambda t: store.pop(t, None),
        on_preview_discard=lambda t: store.pop(t, None) is not None,
    ), host="127.0.0.1")
    client = TestClient(server.app)

    assert client.post("/api/dictation/preview/type", json={}).status_code == 400
    resp = client.post("/api/dictation/preview/type", json={"token": "tok-1"})
    assert resp.json() == {"success": True, "typed": "stored text"}
    assert client.post(
        "/api/dictation/preview/type", json={"token": "tok-1"}
    ).status_code == 404
    assert client.post(
        "/api/dictation/preview/discard", json={"token": "gone"}
    ).status_code == 404
