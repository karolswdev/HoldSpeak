"""HS-59-01 — the language knob: registry, backends, facade, sites.

The invariant under test: "auto" is byte-identical to the pre-knob world —
no `language` kwarg ever reaches a backend call — while a pinned code
reaches BOTH backends. The registry validates at the boundary without
importing any whisper library.
"""
from __future__ import annotations

import numpy as np
import pytest

import holdspeak.transcribe as transcribe_mod
from holdspeak.languages import (
    WHISPER_LANGUAGES,
    language_choices,
    normalize_language,
)
from holdspeak.transcribe import (
    Transcriber,
    _FasterWhisperTranscriber,
    _MlxTranscriber,
)

# ── the registry ─────────────────────────────────────────────────────────────


def test_normalize_auto_forms_mean_detection() -> None:
    for value in (None, "", "auto", "AUTO", "  auto  "):
        assert normalize_language(value) is None


def test_normalize_codes_and_names() -> None:
    assert normalize_language("pl") == "pl"
    assert normalize_language("PL") == "pl"
    assert normalize_language("Polish") == "pl"
    assert normalize_language("cantonese") == "yue"


def test_normalize_rejects_unknown_actionably() -> None:
    with pytest.raises(ValueError, match="Unknown language.*'auto'"):
        normalize_language("klingon")


def test_registry_is_whisper_sized() -> None:
    assert len(WHISPER_LANGUAGES) >= 99
    assert all(code == code.lower() for code in WHISPER_LANGUAGES)


def test_choices_lead_with_auto() -> None:
    choices = language_choices()
    assert choices[0] == {"code": "auto", "name": "Auto-detect"}
    names = [c["name"] for c in choices[1:]]
    assert names == sorted(names)


def test_registry_module_is_light() -> None:
    # The registry must be importable at config time: no transcription
    # backend, no numpy. Check real import statements, not docstring words.
    import holdspeak.languages as mod

    lines = [l.strip() for l in open(mod.__file__) if l.strip().startswith(("import ", "from "))]
    for line in lines:
        for heavy in ("mlx", "faster_whisper", "numpy", "torch"):
            assert heavy not in line, f"heavy import in languages.py: {line}"


# ── the mlx backend call shape ───────────────────────────────────────────────


class _FakeMlxModule:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def transcribe(self, audio, **kwargs):
        self.calls.append(kwargs)
        return {"text": "ok"}


def _mlx(language):
    import concurrent.futures

    impl = _MlxTranscriber.__new__(_MlxTranscriber)
    impl._mlx_whisper = _FakeMlxModule()
    impl._path_or_hf_repo = "repo"
    impl.language = language
    impl.device = "mlx"
    impl.compute_type = "default"
    # HS-60: real instances pin all MLX work to one thread.
    impl._mlx_thread = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    return impl


def test_mlx_auto_passes_no_language() -> None:
    impl = _mlx(None)
    impl.transcribe(np.zeros(160, dtype=np.float32))
    (call,) = impl._mlx_whisper.calls
    assert "language" not in call  # byte-identical to the pre-knob call


def test_mlx_pinned_passes_the_code() -> None:
    impl = _mlx("pl")
    impl.transcribe(np.zeros(160, dtype=np.float32))
    (call,) = impl._mlx_whisper.calls
    assert call["language"] == "pl"


# ── the faster-whisper backend call shape ────────────────────────────────────


class _FakeFwModel:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def transcribe(self, audio, **kwargs):
        self.calls.append(kwargs)
        return iter(()), None


def _fw(language):
    impl = _FasterWhisperTranscriber.__new__(_FasterWhisperTranscriber)
    impl._model = _FakeFwModel()
    impl.language = language
    impl.device = "cpu"
    impl.compute_type = "int8"
    return impl


def test_faster_whisper_auto_passes_no_language() -> None:
    impl = _fw(None)
    impl.transcribe(np.zeros(160, dtype=np.float32))
    (call,) = impl._model.calls
    assert "language" not in call


def test_faster_whisper_pinned_passes_the_code() -> None:
    impl = _fw("de")
    impl.transcribe(np.zeros(160, dtype=np.float32))
    (call,) = impl._model.calls
    assert call["language"] == "de"


# ── the facade normalizes once, for both backends ────────────────────────────


def test_facade_normalizes_and_threads(monkeypatch) -> None:
    seen: dict[str, object] = {}

    class _Recorder:
        def __init__(self, **kwargs):
            seen.update(kwargs)
            self.device = "x"
            self.compute_type = "y"

    monkeypatch.setattr(transcribe_mod, "_resolve_backend", lambda _b: "mlx")
    monkeypatch.setattr(transcribe_mod, "_MlxTranscriber", _Recorder)

    t = Transcriber(model_name="base", language="Polish")
    assert t.language == "pl"
    assert seen["language"] == "pl"

    seen.clear()
    t = Transcriber(model_name="base", language="auto")
    assert t.language is None
    assert seen["language"] is None


def test_facade_rejects_unknown_language(monkeypatch) -> None:
    monkeypatch.setattr(transcribe_mod, "_resolve_backend", lambda _b: "mlx")
    with pytest.raises(ValueError, match="Unknown language"):
        Transcriber(model_name="base", language="klingon")


# ── every construction site threads the knob ────────────────────────────────


def test_all_construction_sites_thread_the_language() -> None:
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    sites = {
        # HS-63-04: the runtime's Transcriber construction moved with its
        # method (_ensure_transcriber_loaded) into the transcriber_state mixin.
        "holdspeak/runtime/transcriber_state.py": 'language=getattr(self.config.model, "language", "auto")',
        "holdspeak/main.py": 'language=getattr(config.model, "language", "auto")',
        "holdspeak/web/routes/meeting_import.py": 'language=getattr(config.model, "language", "auto")',
        "holdspeak/commands/import_recording.py": 'language=getattr(config.model, "language", "auto")',
    }
    for path, marker in sites.items():
        assert marker in (repo / path).read_text(), f"{path} does not thread the language knob"


# ── config carries it ────────────────────────────────────────────────────────


def test_model_config_default_and_coercion() -> None:
    from holdspeak.config import ModelConfig

    assert ModelConfig().language == "auto"
    # An older config shape without the field coerces forward to the default.
    old_shape = {"name": "small", "warm_on_start": False, "backend": "auto"}
    assert ModelConfig(**old_shape).language == "auto"
