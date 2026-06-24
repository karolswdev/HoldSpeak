"""HSM-13-04 — `_deliver_remote_dictation` delivers a companion answer into the
waiting coder the SAME way local dictation does (tmux reply → type fallback),
deliver-only (the route already ran the rich pipeline), and refuses to fake a
delivery it could not make.
"""

from __future__ import annotations

import threading

import pytest

from holdspeak.runtime.dictation_capture import DictationCaptureMixin


class _Session:
    def __init__(self, pane: str | None):
        self.tmux_pane = pane


class _Runtime(DictationCaptureMixin):
    """A minimal carrier of the mixin's delivery surface — no web server, no audio."""

    def __init__(self, typer=None):
        self.state_lock = threading.Lock()
        self.runtime_status: dict = {}
        self.typer = typer
        self.first_dictation_marks = 0

    def _mark_first_dictation(self) -> None:
        self.first_dictation_marks += 1


class _RecordingTyper:
    def __init__(self):
        self.calls: list[tuple] = []

    def type_text(self, text, *, target_profile=None, submit=False):
        self.calls.append((text, target_profile, submit))


@pytest.fixture
def _patch_session(monkeypatch):
    def _set(session):
        monkeypatch.setattr(
            "holdspeak.agent_context.get_recent_awaiting_agent_session",
            lambda *a, **k: session,
        )
    return _set


def test_delivers_to_the_waiting_agent_tmux_pane(monkeypatch, _patch_session):
    sent: list[dict] = []
    monkeypatch.setattr(
        "holdspeak.tmux_transport.send_text_to_pane",
        lambda *, pane, text, submit=True: sent.append({"pane": pane, "text": text, "submit": submit}),
    )
    _patch_session(_Session(pane="cli:0.1"))
    rt = _Runtime()

    result = rt._deliver_remote_dictation("[corrected] ship it friday")

    assert sent == [{"pane": "cli:0.1", "text": "[corrected] ship it friday", "submit": True}]
    assert result["delivered"] is True
    assert result["method"] == "tmux"
    assert result["target"] == "cli:0.1"
    assert rt.first_dictation_marks == 1


def test_falls_back_to_typing_when_no_tmux_pane(_patch_session):
    typer = _RecordingTyper()
    _patch_session(_Session(pane=None))     # waiting agent but no tmux pane → type it
    rt = _Runtime(typer=typer)

    result = rt._deliver_remote_dictation("the answer")

    assert result["delivered"] is True
    assert result["method"] == "type"
    assert typer.calls[0][0] == "the answer"
    assert typer.calls[0][2] is True        # submit, because there IS a target session


def test_types_into_focused_when_no_waiting_session(_patch_session):
    typer = _RecordingTyper()
    _patch_session(None)                     # nobody waiting → type into the focused target
    rt = _Runtime(typer=typer)

    result = rt._deliver_remote_dictation("freeform note")

    assert result["delivered"] is True
    assert typer.calls[0][2] is False        # no agent session → do not auto-submit


def test_raises_when_undeliverable(_patch_session):
    _patch_session(_Session(pane=None))      # no pane AND no typer → honest failure
    rt = _Runtime(typer=None)
    with pytest.raises(RuntimeError):
        rt._deliver_remote_dictation("nowhere to go")


def test_rejects_empty_text(_patch_session):
    _patch_session(_Session(pane="cli:0.1"))
    rt = _Runtime()
    with pytest.raises(ValueError):
        rt._deliver_remote_dictation("   ")


# ── HSM-15-01a: the explicit "focused" target mode ────────────────────────────


def test_focused_target_types_without_any_awaiting_session(monkeypatch):
    """target="focused" free-types via the typer with NO awaiting-agent lookup
    and NO auto-submit — and never raises on a missing agent session."""
    # If anything tried to consult an awaiting agent session, blow up loudly so
    # the test proves the focused path does not require one.
    monkeypatch.setattr(
        "holdspeak.agent_context.get_recent_awaiting_agent_session",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not be consulted")),
    )
    typer = _RecordingTyper()
    rt = _Runtime(typer=typer)

    result = rt._deliver_remote_dictation("freeform into the focused app", target="focused")

    assert result["delivered"] is True
    assert result["method"] == "type"
    assert typer.calls[0][0] == "freeform into the focused app"
    assert typer.calls[0][2] is False        # focused → never auto-submit
    assert rt.first_dictation_marks == 1


def test_focused_target_raises_when_typer_unavailable(monkeypatch):
    monkeypatch.setattr(
        "holdspeak.agent_context.get_recent_awaiting_agent_session",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not be consulted")),
    )
    rt = _Runtime(typer=None)
    with pytest.raises(RuntimeError):
        rt._deliver_remote_dictation("nowhere to type", target="focused")


def test_focused_target_honours_configured_profile_override():
    """The focused path types with the configured target_profile_override (a
    non-auto value becomes the typer's target_profile hint)."""
    import types

    typer = _RecordingTyper()
    rt = _Runtime(typer=typer)
    rt.config = types.SimpleNamespace(
        dictation=types.SimpleNamespace(
            pipeline=types.SimpleNamespace(target_profile_override="editor")
        )
    )

    rt._deliver_remote_dictation("typed into the editor", target="focused")

    assert typer.calls[0][1] == "editor"     # target_profile threaded through
    assert typer.calls[0][2] is False


def test_default_target_is_byte_identical_to_agent_path(monkeypatch, _patch_session):
    """An unset target == "agent": the existing tmux-then-typer behaviour, unchanged."""
    sent: list[dict] = []
    monkeypatch.setattr(
        "holdspeak.tmux_transport.send_text_to_pane",
        lambda *, pane, text, submit=True: sent.append({"pane": pane, "text": text}),
    )
    _patch_session(_Session(pane="cli:0.1"))
    rt = _Runtime()

    default_result = rt._deliver_remote_dictation("answer the coder")
    agent_result = rt._deliver_remote_dictation("answer the coder", target="agent")

    assert default_result == agent_result == {"delivered": True, "method": "tmux", "target": "cli:0.1"}
