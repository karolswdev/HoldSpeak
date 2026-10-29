"""The Line's speech (LINE design §7): Parakeet in, Pocket out, an energy VAD.

- **In**: Parakeet TDT 0.6B v2 int8 through ``onnx-asr`` (MIT) on
  ``onnxruntime`` (MIT); weights CC-BY-4.0 (``istupakov/parakeet-tdt-0.6b-v2-onnx``
  from NVIDIA's model). CPU, 4 threads, no thread spinning (the design's
  measured setting; default threads spin 24 cores on the home box).
- **Out**: Kyutai Pocket TTS (``pocket-tts``, MIT), the ungated weights
  ``kyutai/pocket-tts-without-voice-cloning`` (CC-BY-4.0), streamed; the
  lead silence of the first chunk is trimmed (it cost 150–200 ms).
- **End of speech**: the energy rule the spike measured (start above 600
  RMS, end after 300 ms below 250 RMS).

Licence rule: nothing here imports ``kokoro_onnx``, ``phonemizer``,
``espeakng_loader`` or ``faster_whisper`` (each pulls GPL code; design §2).
The engines load only when the Line starts; the tests use their own.
"""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Iterator, Optional, Protocol

import numpy as np

from ..logging_config import get_logger
from .audio import FRAME_MS, RATE, resample, rms, to_pcm16

log = get_logger("line.speech")

#: The energy rule (RMS of one 20 ms frame of s16 PCM).
START_RMS = 600.0
QUIET_RMS = 250.0
#: 300 ms of quiet ends an utterance.
END_OF_SPEECH_MS = 300
#: 200 ms of his speech while we speak stops our voice.
BARGE_IN_MS = 200
#: An utterance shorter than this is a click, not words.
MIN_UTTERANCE_MS = 120
#: The most of one utterance kept (a longer one is cut and heard as is).
MAX_UTTERANCE_S = 30.0

STT_REPO = "istupakov/parakeet-tdt-0.6b-v2-onnx"
STT_MODEL = "nemo-parakeet-tdt-0.6b-v2"
TTS_REPO = "kyutai/pocket-tts-without-voice-cloning"
TTS_VOICE = "alba"
#: The models, with their licences (the Line names them where it fetches them).
MODELS = (
    {"id": "line-stt", "name": "Phone speech in (Parakeet)", "repo": STT_REPO, "size_mb": 631,
     "code": "onnx-asr (MIT), onnxruntime (MIT)", "weights": "CC-BY-4.0 (NVIDIA Parakeet TDT 0.6B v2)"},
    {"id": "line-tts", "name": "Phone voice (Pocket)", "repo": TTS_REPO, "size_mb": 215,
     "code": "pocket-tts (MIT)", "weights": "CC-BY-4.0 (Kyutai Pocket TTS)"},
)
#: Modules the Line's process must never load (design §2).
GPL_MODULES = ("kokoro_onnx", "phonemizer", "espeakng_loader", "faster_whisper", "piper")


class STT(Protocol):
    def transcribe(self, pcm: np.ndarray) -> str:
        """16 kHz int16 PCM → the words."""
        ...


class TTS(Protocol):
    def stream(self, text: str, stop: Optional[threading.Event] = None) -> Iterator[np.ndarray]:
        """The words → 16 kHz int16 chunks as they are made."""
        ...


# ── end of speech ─────────────────────────────────────────────────────


@dataclass
class EndOfSpeech:
    """Frames in; a whole utterance out after 300 ms of quiet.

    ``talking`` counts his loud frames in a row (the barge-in rule reads it)."""

    start_rms: float = START_RMS
    quiet_rms: float = QUIET_RMS
    end_ms: int = END_OF_SPEECH_MS
    in_speech: bool = False
    quiet: int = 0
    talking: int = 0
    frames: list[np.ndarray] = field(default_factory=list)

    def feed(self, frame: np.ndarray) -> Optional[np.ndarray]:
        energy = rms(frame)
        self.talking = self.talking + 1 if energy >= self.start_rms else 0
        if not self.in_speech:
            if energy >= self.start_rms:
                self.in_speech = True
                self.quiet = 0
                self.frames = [frame]
            return None
        self.frames.append(frame)
        self.quiet = self.quiet + 1 if energy < self.quiet_rms else 0
        too_long = len(self.frames) * FRAME_MS >= MAX_UTTERANCE_S * 1000
        if self.quiet * FRAME_MS >= self.end_ms or too_long:
            utterance = np.concatenate(self.frames)
            self.reset()
            if len(utterance) * 1000 // RATE < MIN_UTTERANCE_MS + self.end_ms:
                return None
            return utterance
        return None

    def barge_in(self, ms: int = BARGE_IN_MS) -> bool:
        return self.talking * FRAME_MS >= ms

    def reset(self) -> None:
        self.in_speech = False
        self.quiet = 0
        self.frames = []


# ── the engines ───────────────────────────────────────────────────────


def _threads() -> int:
    return max(1, int(os.environ.get("HOLDSPEAK_LINE_THREADS", "4") or 4))


class Parakeet:
    """Parakeet TDT 0.6B v2, int8, on the CPU."""

    def __init__(self, *, threads: Optional[int] = None) -> None:
        import onnx_asr  # MIT
        import onnxruntime as rt  # MIT

        options = rt.SessionOptions()
        options.intra_op_num_threads = threads or _threads()
        options.add_session_config_entry("session.intra_op.allow_spinning", "0")
        self._model = onnx_asr.load_model(STT_MODEL, quantization="int8", providers=["CPUExecutionProvider"],
                                          sess_options=options)
        self._lock = threading.Lock()
        # Warm on an utterance-sized input, twice: the first real-sized pass
        # after a short warm-up cost about 200 ms more (measured on this Mac).
        noise = (np.random.default_rng(0).standard_normal(RATE * 4) * 800).astype(np.int16)
        for _ in range(2):
            self.transcribe(noise)

    def transcribe(self, pcm: np.ndarray) -> str:
        audio = np.asarray(pcm, dtype=np.float32) / 32768.0
        with self._lock:
            return str(self._model.recognize(audio, sample_rate=RATE)).strip()


def trim_lead(pcm: np.ndarray, *, threshold: int = 600, keep_ms: int = 10) -> Optional[np.ndarray]:
    """The chunk from just before its first loud sample; None when all quiet."""
    loud = np.nonzero(np.abs(pcm.astype(np.int32)) > threshold)[0]
    if not len(loud):
        return None
    return pcm[max(0, int(loud[0]) - RATE * keep_ms // 1000):]


class Pocket:
    """Kyutai Pocket TTS, streamed, at 16 kHz."""

    def __init__(self, *, voice: str = TTS_VOICE, threads: Optional[int] = None) -> None:
        import torch
        from pocket_tts import TTSModel  # MIT

        torch.set_num_threads(threads or _threads())
        self._model = TTSModel.load_model()
        self._state = self._model.get_state_for_audio_prompt(voice)
        self._rate = int(getattr(self._model, "sample_rate", 24000))
        self._lock = threading.Lock()
        for _ in self.stream("Warm up."):
            pass

    def stream(self, text: str, stop: Optional[threading.Event] = None) -> Iterator[np.ndarray]:
        lead = True
        with self._lock:
            for chunk in self._model.generate_audio_stream(self._state, text, stop=stop):
                pcm = to_pcm16(resample(chunk.numpy().astype(np.float32), self._rate, RATE))
                if lead:
                    trimmed = trim_lead(pcm)
                    if trimmed is None:
                        continue
                    pcm, lead = trimmed, False
                yield pcm
                if stop is not None and stop.is_set():
                    return


def say_once(tts: TTS, text: str) -> np.ndarray:
    """The whole PCM of a short line (the fills are made once at start)."""
    parts = list(tts.stream(text))
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.int16)


def gpl_loaded() -> list[str]:
    """GPL code mapped into this process: the Python modules by name, and on
    Linux the shared libraries (espeak, x264, x265) from ``/proc/self/maps``."""
    import sys

    found = [name for name in GPL_MODULES if name in sys.modules]
    try:
        with open("/proc/self/maps", encoding="utf-8") as maps:
            libs = {line.rsplit("/", 1)[-1].strip() for line in maps if any(k in line for k in ("espeak", "x264", "x265"))}
        found += sorted(libs)
    except OSError:
        pass
    return found


__all__ = [
    "BARGE_IN_MS", "END_OF_SPEECH_MS", "EndOfSpeech", "GPL_MODULES", "MODELS", "Parakeet", "Pocket", "STT", "TTS",
    "gpl_loaded", "say_once", "trim_lead",
]
