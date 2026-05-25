"""AIPI-4-15 — overlap-window tests for MeetingSession transcription.

Sentences that span 10 s transcription boundaries used to get cut by
Whisper because each pass saw a fresh chunk with no prior context.
``MeetingSession._apply_overlap`` keeps the last ~1.5 s of each
stream's audio between passes and prepends it to the next pass's
chunk, so Whisper has continuity at the boundary.
"""

from __future__ import annotations

import numpy as np

from holdspeak.meeting_session import MeetingSession


class _NoopTranscriber:
    """Stub transcriber to satisfy the MeetingSession constructor.
    Not actually called by these tests — we exercise ``_apply_overlap``
    directly."""

    model_name = "stub"

    def transcribe(self, audio: np.ndarray) -> str:
        return ""


def _make_session() -> MeetingSession:
    return MeetingSession(
        transcriber=_NoopTranscriber(),
        intel_enabled=False,
    )


def test_overlap_seconds_default() -> None:
    session = _make_session()
    # 1.5 s default — matches the comment in __init__.
    assert session._overlap_tail_seconds == 1.5


def test_first_pass_no_prior_tail() -> None:
    """A fresh stream returns the audio unchanged on the first pass."""
    session = _make_session()
    audio = np.ones(16000 * 5, dtype=np.float32)  # 5 s

    out = session._apply_overlap("mic", audio, final=False)

    assert np.array_equal(out, audio)
    # Tail saved for next pass = last 1.5 s.
    assert "mic" in session._stream_tails
    assert session._stream_tails["mic"].size == int(1.5 * 16000)


def test_second_pass_prepends_previous_tail() -> None:
    """Second pass gets last-1.5 s of previous audio prepended."""
    session = _make_session()
    first = np.full(16000 * 5, 1.0, dtype=np.float32)
    second = np.full(16000 * 5, 2.0, dtype=np.float32)

    session._apply_overlap("mic", first, final=False)
    combined = session._apply_overlap("mic", second, final=False)

    # Combined length = 1.5 s tail + 5 s new = 6.5 s.
    assert combined.size == int(1.5 * 16000) + int(5 * 16000)
    # Leading 1.5 s comes from previous audio (value 1.0).
    tail_samples = int(1.5 * 16000)
    assert np.all(combined[:tail_samples] == 1.0)
    # Remaining 5 s comes from current audio (value 2.0).
    assert np.all(combined[tail_samples:] == 2.0)


def test_third_pass_carries_overlap_forward() -> None:
    """Tail keeps rolling: each pass saves *its* last 1.5 s."""
    session = _make_session()
    p1 = np.full(16000 * 3, 1.0, dtype=np.float32)
    p2 = np.full(16000 * 3, 2.0, dtype=np.float32)
    p3 = np.full(16000 * 3, 3.0, dtype=np.float32)

    session._apply_overlap("mic", p1, final=False)
    session._apply_overlap("mic", p2, final=False)
    combined = session._apply_overlap("mic", p3, final=False)

    # Leading samples come from p2's tail (value 2.0), not p1.
    tail_samples = int(1.5 * 16000)
    assert np.all(combined[:tail_samples] == 2.0)
    assert np.all(combined[tail_samples:] == 3.0)


def test_final_pass_clears_tail() -> None:
    """On the final pass the tail is discarded — there's no next pass
    to feed."""
    session = _make_session()
    first = np.full(16000 * 5, 1.0, dtype=np.float32)
    session._apply_overlap("mic", first, final=False)
    assert "mic" in session._stream_tails

    final = np.full(16000 * 2, 2.0, dtype=np.float32)
    out = session._apply_overlap("mic", final, final=True)

    # Final pass still gets the prepended tail (so the LAST sentence
    # isn't cut), but no new tail is saved.
    assert out.size == int(1.5 * 16000) + int(2 * 16000)
    assert "mic" not in session._stream_tails


def test_streams_are_independent() -> None:
    """mic / system / device:<id> streams keep their own tails."""
    session = _make_session()
    mic_audio = np.full(16000 * 3, 1.0, dtype=np.float32)
    sys_audio = np.full(16000 * 3, 2.0, dtype=np.float32)
    dev_audio = np.full(16000 * 3, 3.0, dtype=np.float32)

    session._apply_overlap("mic", mic_audio, final=False)
    session._apply_overlap("system", sys_audio, final=False)
    session._apply_overlap("device:aipi-1", dev_audio, final=False)

    mic_combined = session._apply_overlap("mic", mic_audio, final=False)
    sys_combined = session._apply_overlap("system", sys_audio, final=False)
    dev_combined = session._apply_overlap("device:aipi-1", dev_audio, final=False)

    tail_samples = int(1.5 * 16000)
    assert np.all(mic_combined[:tail_samples] == 1.0)
    assert np.all(sys_combined[:tail_samples] == 2.0)
    assert np.all(dev_combined[:tail_samples] == 3.0)


def test_small_first_chunk_saves_whole_chunk_as_tail() -> None:
    """If the first pass's audio is shorter than the overlap window,
    save the whole thing as tail."""
    session = _make_session()
    tiny = np.full(16000, 1.0, dtype=np.float32)  # 1 s — shorter than 1.5 s

    session._apply_overlap("mic", tiny, final=False)

    assert session._stream_tails["mic"].size == 16000
    assert np.all(session._stream_tails["mic"] == 1.0)
