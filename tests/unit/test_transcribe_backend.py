from __future__ import annotations

import pytest

from holdspeak.transcribe import TranscriberError, _resolve_backend


def test_resolve_backend_auto_prefers_mlx_on_darwin_arm64(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("holdspeak.transcribe._is_darwin_arm64", lambda: True)
    monkeypatch.setattr(
        "holdspeak.transcribe._module_available",
        lambda m: m in {"mlx", "mlx_whisper"},
    )
    assert _resolve_backend("auto") == "mlx"


def test_resolve_backend_auto_uses_faster_on_non_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("holdspeak.transcribe._is_darwin_arm64", lambda: False)
    monkeypatch.setattr(
        "holdspeak.transcribe._module_available",
        lambda m: m == "faster_whisper",
    )
    assert _resolve_backend("auto") == "faster-whisper"


def test_resolve_backend_faster_missing_has_linux_extra_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("holdspeak.transcribe._is_darwin_arm64", lambda: False)
    monkeypatch.setattr("holdspeak.transcribe._module_available", lambda _m: False)
    with pytest.raises(TranscriberError) as excinfo:
        _resolve_backend("faster-whisper")
    assert "'.[linux]'" in str(excinfo.value)


def test_resolve_backend_auto_missing_mentions_linux_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("holdspeak.transcribe._is_darwin_arm64", lambda: False)
    monkeypatch.setattr("holdspeak.transcribe._module_available", lambda _m: False)
    with pytest.raises(TranscriberError) as excinfo:
        _resolve_backend("auto")
    assert "'.[linux]'" in str(excinfo.value)

