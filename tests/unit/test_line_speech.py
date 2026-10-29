"""The Line (2026-10-29): the end-of-speech rule, barge-in, the lead trim, and
the licence rule (nothing GPL is imported by the Line)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import numpy as np

from holdspeak.line.audio import FRAME
from holdspeak.line.speech import BARGE_IN_MS, END_OF_SPEECH_MS, EndOfSpeech, trim_lead
from tests.fixtures.fake_baresip import tone

ROOT = Path(__file__).resolve().parents[2]


def _frames(pcm: np.ndarray) -> list[np.ndarray]:
    pcm = np.concatenate([pcm, np.zeros((-len(pcm)) % FRAME, dtype=np.int16)])
    return [pcm[i:i + FRAME] for i in range(0, len(pcm), FRAME)]


def test_an_utterance_ends_after_300_ms_of_quiet_and_not_before() -> None:
    eos = EndOfSpeech()
    speech = _frames(tone(500.0, 600))
    quiet = _frames(np.zeros(16000, dtype=np.int16))
    assert all(eos.feed(f) is None for f in speech)
    out = [eos.feed(f) for f in quiet[: END_OF_SPEECH_MS // 20]]
    assert all(o is None for o in out[:-1]) and out[-1] is not None  # the 15th quiet frame ends it
    assert len(out[-1]) == len(speech) * FRAME + END_OF_SPEECH_MS * 16
    # A short pause inside his words does not end them.
    eos = EndOfSpeech()
    pause = _frames(np.zeros(16 * 200, dtype=np.int16))
    assert all(eos.feed(f) is None for f in speech + pause + speech)
    # A click is not words.
    eos = EndOfSpeech()
    assert all(eos.feed(f) is None for f in _frames(tone(500.0, 40)) + quiet[:20])


def test_barge_in_needs_200_ms_of_his_speech() -> None:
    eos = EndOfSpeech()
    frames = _frames(tone(500.0, 400))
    barged = [eos.feed(f) is None and eos.barge_in() for f in frames]
    assert barged.index(True) == BARGE_IN_MS // 20 - 1


def test_the_lead_silence_of_the_first_chunk_is_trimmed() -> None:
    chunk = np.concatenate([np.zeros(3000, dtype=np.int16), tone(300.0, 100)])
    trimmed = trim_lead(chunk)
    # 10 ms are kept before his first loud sample (3000 quiet samples in).
    assert trimmed is not None and len(chunk) - 2850 <= len(trimmed) <= len(chunk) - 2830, len(trimmed)
    assert trim_lead(np.zeros(1000, dtype=np.int16)) is None


def test_the_line_imports_no_gpl_code() -> None:
    """Design §2: kokoro-onnx, phonemizer, espeak-ng and faster-whisper pull
    GPL code; the Line imports none of them, in its source or its process."""
    banned = re.compile(r"^\s*(import|from)\s+(kokoro_onnx|phonemizer|espeakng_loader|faster_whisper|piper|pjsua2?|av)\b", re.M)
    for path in (ROOT / "holdspeak" / "line").rglob("*.py"):
        assert not banned.search(path.read_text()), path
    probe = ("import sys, holdspeak.line.node, holdspeak.line.adapter, holdspeak.line.speech as s; "
             "print(','.join(s.gpl_loaded()))")
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "", out.stdout


def test_aupipe_carries_a_bsd_3_header_naming_holdspeak() -> None:
    source = (ROOT / "holdspeak" / "line" / "aupipe" / "aupipe.c").read_text()
    assert "Neither the name of HoldSpeak nor the names of its contributors" in source
    assert "GPL" not in source
