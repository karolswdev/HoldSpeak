"""HS-32-04: ungated end-to-end smoke test of the core path.

audio (a fixed, checked-in WAV of a known phrase) -> the REAL transcription
backend (smallest Whisper, "tiny") -> text processing -> the injection seam
(captured, not sent to a real keyboard) -> assert the produced text contains the
spoken phrase.

This is the only CI test that runs *real* transcription on *real* audio. The
hotkey->text **wiring** (``VoiceTypingSession`` + ``WebRuntime._transcribe_and_type``
dispatching to the typer) is covered by ``test_web_runtime`` /
``test_voice_typing_session`` with a *fake* transcriber. Together they close the
"core promise" gap that was previously validated only behind the never-in-CI
``metal`` / ``spoken_e2e`` markers: a real transcription regression is caught
here; an injection-seam wiring regression is caught there. Both run on every push.

The fixture ``tests/fixtures/core_path_smoke_16k.wav`` was generated once on
macOS with::

    say -o tests/fixtures/core_path_smoke_16k.wav \
        --data-format=LEI16@16000 --file-format=WAVE \
        "the quick brown fox jumps over the lazy dog"

and is committed so both CI environments (and local runs) read the same bytes —
no ``say``/TTS or microphone is needed at test time.

It exercises the exact transformation ``_transcribe_and_type`` performs to obtain
the text it hands the typer (transcribe -> ``TextProcessor.process`` ->
``type_text``); the optional DIR-01 dictation pipeline is intentionally *not*
driven (it is off by default and is a separate, network-dependent concern with
its own tests). Skips only where no Whisper backend is installed (e.g. the Linux
unit job); runs for real on the macOS integration job (``mlx-whisper`` is a core
dep there), which executes on every push -> ungated.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from holdspeak.text_processor import TextProcessor
from holdspeak.transcribe import Transcriber, TranscriberError, _resolve_backend

_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "core_path_smoke_16k.wav"
_SMOKE_MODEL = "tiny"  # smallest viable model; deterministic greedy decode


def _require_backend() -> None:
    try:
        _resolve_backend("auto")
    except TranscriberError as exc:
        pytest.skip(f"no Whisper backend installed: {exc}")


def _load_wav_16k_mono(path: Path) -> np.ndarray:
    """Read a 16 kHz mono 16-bit PCM WAV into float32 [-1, 1] (stdlib only)."""
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == 16000, "fixture must be 16 kHz"
        assert w.getnchannels() == 1, "fixture must be mono"
        assert w.getsampwidth() == 2, "fixture must be 16-bit PCM"
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def _normalize(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace — tolerant matching."""
    return " ".join("".join(c if c.isalnum() else " " for c in text.lower()).split())


class _CapturingTyper:
    """Stands in for ``TextTyper`` at the injection seam — records, never types."""

    def __init__(self) -> None:
        self.typed: list[str] = []

    def type_text(self, text: str, **_kwargs) -> None:
        self.typed.append(text)


def test_core_path_audio_to_injected_text() -> None:
    """Real audio -> real transcript -> injection seam, asserting on the text."""
    _require_backend()
    assert _FIXTURE.exists(), f"missing fixture: {_FIXTURE}"

    audio = _load_wav_16k_mono(_FIXTURE)

    # The transformation `WebRuntime._transcribe_and_type` runs to get the text
    # it hands the typer: transcribe -> process -> type_text(seam).
    transcript = Transcriber(model_name=_SMOKE_MODEL).transcribe(audio)
    processed = TextProcessor().process(transcript)

    typer = _CapturingTyper()
    typer.type_text(processed)

    assert typer.typed, "nothing reached the injection seam"
    injected = _normalize(typer.typed[0])
    # Substring with tolerance: assert the salient tokens, not exact equality,
    # to stay robust to model quirks while still catching real breakage.
    assert "quick brown fox" in injected, f"got: {injected!r}"
    assert "lazy dog" in injected, f"got: {injected!r}"


def test_core_path_smoke_assertion_is_not_vacuous() -> None:
    """Mutation guard: the substring assertion *rejects* a wrong transcript, so a
    broken transcription path would turn the smoke test red (no backend needed)."""
    wrong = _normalize("Goodbye everyone, see you later.")
    assert "quick brown fox" not in wrong
    assert "lazy dog" not in wrong
