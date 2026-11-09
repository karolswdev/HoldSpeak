# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_voice_command_dispatch.py to restore.

# ruff: noqa


# --- test_web_runtime_delegate_injects_typer_and_activity: P7: a spy checks the delegate passes its arguments through ('captured["config"] == "CFG"')
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
