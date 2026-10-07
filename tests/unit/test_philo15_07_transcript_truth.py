"""PHILO-15-07 (B01, B30): the transcript must not lie.

Rehearsal 1 part A: the import cut the fixture at a hard 30 s window; Whisper
`base` looped "finally" about 250 times at the end of window 1, Priya Shah's
action item was lost, and the face said "299 WORDS" with no warning.

These fences run the real import engine and the real SQLite layer with a
transcriber double that reads the audio it is handed the way Whisper does:
each sample carries its own time, so the double knows which stretch of the
meeting a window covers and returns segments with window-relative timestamps,
cutting a sentence when the window ends inside it.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pytest

from holdspeak import meeting_import
from holdspeak.db import get_database, reset_database
from holdspeak.meeting_import import (
    TARGET_SAMPLE_RATE,
    _boundary_split,
    humanize_title,
    import_meeting,
)
from holdspeak.transcript_guard import (
    count_unclear,
    is_degenerate,
    loop_start,
    mark_degenerate,
    unclear_mark,
)

PRIYA = "Priya Shah will add the named failure fence before ship."

# The rehearsal fixture's shape: the third action item runs across 30 s.
TIMELINE = [
    (0.0, 9.5, "Decision one: use SQLite for the local meeting ledger."),
    (9.5, 19.0, "Decision two: keep summary retrieval on the local desk."),
    (19.0, 28.2, "Decision three: use a recorded provider reply. Owner: Priya Shah."),
    (28.2, 33.0, PRIYA),
    (33.0, 34.6, "Marker: HoldSpeak synthetic architect three."),
]
DURATION = 34.7


class TimelineWhisper:
    """A Whisper double: decodes whatever stretch of the timeline it is handed.

    A sentence that runs past the end of the window comes back cut: its first
    half, ending at the window's end (what Whisper does at a hard cut).
    ``loop`` makes the cut segment a "finally" loop instead (the rehearsal).
    """

    supports_segments = True

    def __init__(self, *, loop_cut: bool = False, loop_always: bool = False):
        self.loop_cut = loop_cut
        self.loop_always = loop_always
        self.calls: list[dict] = []

    def transcribe(self, audio, *, admission=None, segments=False, temperature=None):
        assert segments is True, "the real Transcriber path asks for segments"
        audio = np.asarray(audio)
        offset = float(audio[0])
        length = len(audio) / TARGET_SAMPLE_RATE
        self.calls.append({"offset": round(offset, 2), "temperature": temperature})
        out = []
        for start, end, text in TIMELINE:
            if start < offset - 0.01 or start >= offset + length:
                continue
            rel_start, rel_end = start - offset, end - offset
            if rel_end > length:
                words = text.split()
                cut = " ".join(words[: max(1, len(words) // 2)])
                if self.loop_cut or self.loop_always:
                    cut = cut + " " + " ".join(["finally"] * 250)
                out.append({"start": rel_start, "end": length, "text": cut})
            else:
                if self.loop_always and text == PRIYA:
                    text = "Priya Shah will " + " ".join(["finally"] * 250)
                out.append({"start": rel_start, "end": rel_end, "text": text})
        return out


def _config():
    return SimpleNamespace(meeting=SimpleNamespace(intel_enabled=True, intel_deferred_enabled=True))


@pytest.fixture()
def db(tmp_path):
    reset_database()
    database = get_database(tmp_path / "truth.db")
    yield database
    reset_database()


@pytest.fixture()
def timed_audio(tmp_path, monkeypatch):
    """A file whose decoded samples are their own timestamps (seconds)."""
    path = tmp_path / "philo3_architect_meeting.wav"
    path.write_bytes(b"RIFF")
    samples = (np.arange(int(DURATION * TARGET_SAMPLE_RATE)) / TARGET_SAMPLE_RATE).astype(np.float32)
    monkeypatch.setattr(meeting_import, "load_audio", lambda _p: (samples, TARGET_SAMPLE_RATE))
    return path


def _text(state) -> str:
    return " ".join(segment.text for segment in state.segments)


# --------------------------------------------------------------- the guard


def test_a_finally_loop_is_degenerate_and_ordinary_speech_is_not():
    loop = "Owner, Priya Shah. Action. " + " ".join(["finally"] * 250)
    assert is_degenerate(loop)
    assert is_degenerate("Sukekekekeke" + "ke" * 200)  # a loop inside one token
    assert is_degenerate("and multiply " * 12)  # a two-word group
    assert not is_degenerate(PRIYA)
    assert not is_degenerate(" ".join(text for _s, _e, text in TIMELINE))
    assert not is_degenerate("No, no, no. We ship on Friday.")


def test_a_looping_span_keeps_every_word_and_gets_an_honest_mark():
    """Ruling on Astra's iteration 2: a mark NEVER deletes recognised words."""
    loop = "Owner, Priya Shah. Action. " + " ".join(["finally"] * 250)
    assert loop_start(loop) == 4
    marked = mark_degenerate(loop, 28.24, 30.0)
    assert marked == loop + " [unclear 0:28–0:30]"
    assert marked.split()[:-2] == loop.split()
    assert count_unclear([marked, "clean text"]) == 1
    assert unclear_mark(61.0, 65.4) == "[unclear 1:01–1:05]"


# ---------------------------------------------------------- the window merge


def test_boundary_split_drops_the_cut_segment_and_names_the_resume_point():
    decoded = [
        {"start": 0.0, "end": 26.8, "text": "whole"},
        {"start": 28.2, "end": 30.0, "text": "Priya Shah will"},
    ]
    kept, resume = _boundary_split(decoded, window_len=30.0, final=False, min_advance=15.0)
    assert [seg["text"] for seg in kept] == ["whole"]
    assert resume == 28.2
    # The last window keeps everything; a drop that would not move forward keeps all.
    assert _boundary_split(decoded, window_len=30.0, final=True, min_advance=15.0)[1] is None
    one = [{"start": 0.0, "end": 30.0, "text": "a run-on"}]
    assert _boundary_split(one, window_len=30.0, final=False, min_advance=15.0) == (one, None)


def test_a_sentence_across_the_window_boundary_is_whole(db, timed_audio):
    whisper = TimelineWhisper()
    result = import_meeting(timed_audio, db=db, transcriber=whisper, config=_config())

    text = _text(result.state)
    assert text.count(PRIYA) == 1, text
    assert "Priya Shah will add the" not in text.replace(PRIYA, "")  # no cut half
    # The second window starts where the cut sentence starts.
    assert [call["offset"] for call in whisper.calls] == [0.0, 28.2]
    stored = db.meetings.get_meeting(result.state.id)
    assert PRIYA in " ".join(s.text for s in stored.segments)
    assert stored.to_dict()["unclearSpans"] == 0


def test_the_rehearsal_loop_at_the_cut_never_reaches_the_transcript(db, timed_audio):
    result = import_meeting(
        timed_audio, db=db, transcriber=TimelineWhisper(loop_cut=True), config=_config()
    )
    text = _text(result.state)
    assert "finally" not in text
    assert text.count(PRIYA) == 1


def test_a_window_still_degenerate_after_the_retry_carries_a_mark_and_a_count(db, timed_audio):
    whisper = TimelineWhisper(loop_always=True)
    result = import_meeting(timed_audio, db=db, transcriber=whisper, config=_config())

    text = _text(result.state)
    # The loop keeps its words and carries the mark; nothing is deleted.
    assert text.count("finally") == 250, text
    assert "finally [unclear 0:28–0:33]" in text, text
    # The degenerate window was decoded once more, warm, before the mark.
    assert any(call["temperature"] for call in whisper.calls)
    stored = db.meetings.get_meeting(result.state.id)
    assert stored.to_dict()["unclearSpans"] == 1
    row = next(m for m in db.meetings.list_meetings() if m.id == result.state.id)
    assert row.unclear_spans == 1


def test_a_text_only_transcriber_still_gets_the_honest_mark(db, timed_audio):
    class TextOnly:
        def transcribe(self, audio, **_kwargs):
            return "Owner, Priya Shah. Action. " + " ".join(["finally"] * 250)

    result = import_meeting(timed_audio, db=db, transcriber=TextOnly(), config=_config())
    text = result.state.segments[0].text
    assert text.startswith("Owner, Priya Shah. Action. finally")
    assert text.endswith("finally [unclear 0:00–0:30]")


# --------------------------------------------------------------- the title


@pytest.mark.parametrize(
    "filename, title",
    [
        ("philo3_architect_meeting.wav", "Philo3 architect meeting"),
        ("standup recording.wav", "Standup recording"),
        ("zoom_0d3f9a7c2b_weekly-sync.m4a", "Zoom weekly sync"),
        ("2026-10-07 design review.mp3", "2026-10-07 design review"),
        ("3f2a9c1e-77b0-4c1d-9e2f-0a1b2c3d4e5f.wav", "Imported recording"),
    ],
)
def test_an_imported_title_is_the_file_name_humanised(filename, title):
    assert humanize_title(filename) == title


def test_the_import_titles_the_meeting_without_the_file_name(db, timed_audio):
    result = import_meeting(timed_audio, db=db, transcriber=TimelineWhisper(), config=_config())
    assert result.state.title == "Philo3 architect meeting"
    stated = import_meeting(
        timed_audio, db=db, transcriber=TimelineWhisper(), config=_config(), title="Arch sync"
    )
    assert stated.state.title == "Arch sync"


# ------------------------------------------- Astra r1 on #982: her probes


@pytest.mark.parametrize(
    "speech",
    [
        "yes yes yes",
        "yes yes yes yes yes yes",
        "Go team! " * 6,
        " ".join(f"number {n}" for n in range(1, 51)),  # ratio 4.08, no repeat group
    ],
)
def test_legitimate_repetition_is_speech_never_unclear(speech):
    assert not is_degenerate(speech)


def test_an_empty_retry_never_discards_good_words(db, tmp_path):
    """Her probe: the first decode holds a good line and a loop; the retry is
    empty. The good line stays and the loop is an honest, counted mark."""
    path = tmp_path / "meeting.wav"
    import wave

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(np.zeros(65 * 16000, dtype=np.int16).tobytes())

    class Backend:
        supports_segments = True

        def __init__(self):
            self.calls = 0

        def transcribe(self, audio, *, admission=None, segments=False, temperature=None):
            self.calls += 1
            if temperature is not None:
                return []
            if self.calls == 1:
                return [
                    {"start": 0, "end": 8, "text": "Priya owns the migration."},
                    {"start": 8, "end": 18, "text": "finally " * 250},
                ]
            return [{"start": 0, "end": min(10, len(audio) / 16000), "text": "Leo tests restart."}]

    result = import_meeting(path, db=db, transcriber=Backend(), config=_config())
    stored = db.meetings.get_meeting(result.state.id)
    text = " ".join(s.text for s in stored.segments)
    assert "Priya owns the migration." in text
    # The first decode's words stay (all of them) and the mark is added.
    assert text.count("finally") == 250
    assert "finally [unclear 0:08–0:18]" in text
    assert stored.to_dict()["unclearSpans"] == 1


def test_a_window_that_is_all_loop_and_an_empty_retry_is_an_unclear_span(db, timed_audio):
    class AllLoop:
        supports_segments = True

        def transcribe(self, audio, *, admission=None, segments=False, temperature=None):
            if temperature is not None:
                return []
            length = len(audio) / TARGET_SAMPLE_RATE
            return [{"start": 0.0, "end": length, "text": "finally " * 250}]

    result = import_meeting(timed_audio, db=db, transcriber=AllLoop(), config=_config())
    stored = db.meetings.get_meeting(result.state.id)
    assert stored.to_dict()["unclearSpans"] >= 1
    assert "[unclear " in " ".join(s.text for s in stored.segments)


@pytest.mark.parametrize(
    "text, marks",
    [
        ("A " + unclear_mark(1, 2) + " B " + unclear_mark(3, 4), 2),
        ("The notation [unclear explanation] is discussed.", 0),
    ],
)
def test_list_and_detail_count_marks_by_one_definition(db, tmp_path, text, marks):
    from holdspeak.meeting_import import import_transcript

    path = tmp_path / "notes.srt"
    path.write_text("1\n00:00:00,000 --> 00:00:05,000\n" + text + "\n")
    result = import_transcript(path, db=db, config=_config())
    stored = db.meetings.get_meeting(result.state.id)
    row = next(r for r in db.meetings.list_meetings() if r.id == stored.id)
    assert stored.to_dict()["unclearSpans"] == marks
    assert row.unclear_spans == marks


def test_the_sent_summary_says_how_many_spans_are_unclear(db):
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.services.document_sources import render_document

    def save(meeting_id, texts):
        db.meetings.save_meeting(
            MeetingState(
                id=meeting_id,
                started_at=datetime(2026, 10, 7, 10, 0, 0),
                title="Arch sync",
                segments=[
                    TranscriptSegment(text=t, speaker="Recording", start_time=i, end_time=i + 1)
                    for i, t in enumerate(texts)
                ],
                intel=IntelSnapshot(timestamp=1.0, topics=[], summary="Three decisions.", action_items=[]),
            )
        )

    save("gappy", ["Owner, Priya Shah. " + unclear_mark(28, 30), "Then " + unclear_mark(40, 41)])
    save("clean", ["Owner, Priya Shah."])
    body = render_document(db, "meeting_summary:gappy").body_md
    assert "Transcript: 2 unclear spans" in body
    # The line comes from the marks, never the model, and never a zero.
    assert "unclear" not in render_document(db, "meeting_summary:clean").body_md


def test_twelve_spoken_nexts_keep_all_twelve_words_and_carry_the_mark(db, timed_audio):
    """Astra's iteration-2 probe: "next." twelve times in one decoded segment.
    The guard may not tell it from a loop; it keeps every word and adds the mark."""

    class Nexts:
        supports_segments = True

        def transcribe(self, audio, *, admission=None, segments=False, temperature=None):
            length = len(audio) / TARGET_SAMPLE_RATE
            if length < 20:
                return []
            return [{"start": 0.0, "end": 22.0, "text": " ".join(["next."] * 12)}]

    result = import_meeting(timed_audio, db=db, transcriber=Nexts(), config=_config())
    stored = db.meetings.get_meeting(result.state.id)
    text = " ".join(s.text for s in stored.segments)
    assert text == " ".join(["next."] * 12) + " [unclear 0:00–0:22]", text
    assert stored.to_dict()["unclearSpans"] == 1

