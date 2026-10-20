"""HS-52-04: the voice command dispatch at the top of the dictation seam.

Pins the decision: off by default and on no match returns None (the caller dictates
normally, byte-identical); on a configured keyword it fires the bounded connector,
types nothing, surfaces a runtime activity, and reports the outcome. The `WebRuntime`
method is a thin delegate that injects the runtime typer.
"""
from __future__ import annotations

from types import SimpleNamespace

import holdspeak.runtime.dictation_processing as dictation_processing
import holdspeak.web_runtime as web_runtime
from holdspeak.config import Config, MacrosConfig, VoiceMacro, VoiceMacroAction
from holdspeak.dictation_runner import dispatch_voice_command


def _config_with(*macros: VoiceMacro, enabled: bool = True) -> Config:
    cfg = Config()
    cfg.dictation.macros = MacrosConfig(enabled=enabled, items=list(macros))
    return cfg


def _ok_runner(captured: dict):
    def _run(argv, **kwargs):
        captured["argv"] = list(argv)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return _run


def test_macros_off_returns_none() -> None:
    cfg = _config_with(
        VoiceMacro("ship it", VoiceMacroAction("shell", "echo hi")), enabled=False
    )
    assert dispatch_voice_command("ship it", config=cfg) is None


def test_no_match_returns_none() -> None:
    cfg = _config_with(VoiceMacro("ship it", VoiceMacroAction("shell", "echo hi")))
    assert dispatch_voice_command("write the docs", config=cfg) is None


def test_shell_command_fires_bounded_argv() -> None:
    captured: dict = {}
    cfg = _config_with(VoiceMacro("ship it", VoiceMacroAction("shell", "echo hi")))
    result = dispatch_voice_command(
        "Ship it.", config=cfg, runner=_ok_runner(captured), platform="darwin"
    )
    assert result is not None and result.handled and result.ok
    assert result.kind == "shell"
    assert captured["argv"] == ["sh", "-c", "echo hi"]


def test_type_text_command_types_via_injected_writer() -> None:
    typed: list[str] = []
    cfg = _config_with(VoiceMacro("standup", VoiceMacroAction("type_text", "## Standup")))
    result = dispatch_voice_command("standup", config=cfg, type_writer=typed.append)
    assert result is not None and result.handled and result.ok
    assert typed == ["## Standup"]


def test_desk_verb_requires_the_trusted_dispatcher() -> None:
    cfg = _config_with(VoiceMacro("new note", VoiceMacroAction("desk_verb", "new_note")))
    result = dispatch_voice_command("new note", config=cfg)
    assert result is not None and result.handled and not result.ok
    assert "desk_dispatch_required" in result.error


def test_desk_verbs_use_only_the_closed_mcp_operation_path() -> None:
    calls: list[tuple[str, dict]] = []

    def dispatch(name: str, arguments: dict) -> dict:
        calls.append((name, arguments))
        return {"id": "note-1", "title": "New note"} if name == "desk.create" else {"id": "meeting-1"}

    for keyword, verb, expected in [
        ("start recording", "record", "meeting.start_capture"),
        ("stop recording", "stop", "meeting.stop_capture"),
        ("new note", "new_note", "desk.create"),
    ]:
        calls.clear()
        cfg = _config_with(VoiceMacro(keyword, VoiceMacroAction("desk_verb", verb)))
        result = dispatch_voice_command(keyword, config=cfg, desk_dispatch=dispatch)
        assert result is not None and result.ok
        assert calls == [(expected, {"kind": "notes", "data": {}} if verb == "new_note" else {})]
        assert result.result is not None


def test_ui_desk_verbs_return_closed_intents_without_engine_call() -> None:
    calls: list[tuple[str, dict]] = []
    cfg = _config_with(VoiceMacro("ask HoldSpeak", VoiceMacroAction("desk_verb", "ask")))
    result = dispatch_voice_command(
        "ask HoldSpeak", config=cfg, desk_dispatch=lambda name, args: calls.append((name, args))
    )
    assert result is not None and result.ok
    assert result.result == {"desk_verb": "ask", "ui_intent": "ask"}
    assert calls == []


def test_activity_is_emitted_on_match() -> None:
    seen: list[str] = []
    cfg = _config_with(VoiceMacro("terminal", VoiceMacroAction("launch_app", "Terminal")))
    dispatch_voice_command(
        "terminal",
        config=cfg,
        runner=_ok_runner({}),
        platform="darwin",
        on_activity=seen.append,
    )
    assert seen == ["command: terminal"]


def test_command_failure_is_handled_not_typed() -> None:
    def _bad_runner(argv, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    cfg = _config_with(VoiceMacro("ship it", VoiceMacroAction("shell", "false")))
    result = dispatch_voice_command(
        "ship it", config=cfg, runner=_bad_runner, platform="darwin"
    )
    assert result is not None and result.handled is True
    assert result.ok is False
    assert "boom" in result.error or "exited 1" in result.error


def test_web_runtime_delegate_injects_typer_and_activity(monkeypatch) -> None:
    captured: dict = {}

    def _spy(text, *, config, type_writer, on_activity):
        captured.update(text=text, config=config, type_writer=type_writer, on_activity=on_activity)
        return "SENTINEL"

    monkeypatch.setattr(dictation_processing, "dispatch_voice_command", _spy)
    typed: list[str] = []
    fake_self = SimpleNamespace(
        config="CFG",
        typer=SimpleNamespace(type_text=lambda t, **k: typed.append(t)),
        _paste_target_profile=lambda _s: None,
        _set_runtime_activity=lambda *a, **k: None,
    )
    out = web_runtime.WebRuntime._maybe_dispatch_voice_command(fake_self, "ship it", None)
    assert out == "SENTINEL"
    assert captured["text"] == "ship it"
    assert captured["config"] == "CFG"
    # The injected type_writer routes to the runtime typer.
    captured["type_writer"]("hello")
    assert typed == ["hello"]
