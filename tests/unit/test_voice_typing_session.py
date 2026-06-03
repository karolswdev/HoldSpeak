"""Unit tests for ``VoiceTypingSession`` (HS-14-05)."""

from __future__ import annotations

import threading

import numpy as np
import pytest

from holdspeak.voice_typing import VoiceTypingSession


class _FakeSource:
    """Minimal AudioSource double — enough to satisfy the Protocol."""

    def __init__(self) -> None:
        self.start_calls = 0
        self.stop_calls = 0
        self._recording = False
        self.audio = np.zeros(1600, dtype=np.float32)
        self.start_should_raise: Exception | None = None

    def start_recording(self) -> None:
        if self.start_should_raise is not None:
            raise self.start_should_raise
        self._recording = True
        self.start_calls += 1

    def stop_recording(self) -> np.ndarray:
        self._recording = False
        self.stop_calls += 1
        return self.audio


class TestVoiceTypingSession:
    def test_begin_starts_source_and_returns_true(self) -> None:
        session = VoiceTypingSession()
        source = _FakeSource()

        assert session.begin(source, owner="hotkey") is True
        assert source.start_calls == 1
        assert session.is_active is True
        assert session.active_owner == "hotkey"

    def test_second_begin_returns_false_and_leaves_first_alone(self) -> None:
        session = VoiceTypingSession()
        first = _FakeSource()
        second = _FakeSource()

        assert session.begin(first, owner="hotkey") is True
        assert session.begin(second, owner="device:aipi-1") is False

        # Second source must not have been started.
        assert second.start_calls == 0
        # The first session is still owned by "hotkey".
        assert session.active_owner == "hotkey"

    def test_end_returns_audio_for_matching_owner(self) -> None:
        session = VoiceTypingSession()
        source = _FakeSource()
        source.audio = np.full(800, 0.25, dtype=np.float32)

        session.begin(source, owner="hotkey")
        audio = session.end(owner="hotkey")

        assert audio is not None
        assert audio.shape == (800,)
        assert source.stop_calls == 1
        assert session.is_active is False

    def test_end_returns_none_for_mismatched_owner(self) -> None:
        session = VoiceTypingSession()
        source = _FakeSource()

        session.begin(source, owner="hotkey")
        audio = session.end(owner="device:aipi-1")

        assert audio is None
        assert source.stop_calls == 0
        # Active session is still held by hotkey.
        assert session.active_owner == "hotkey"

    def test_end_returns_none_when_no_session_active(self) -> None:
        session = VoiceTypingSession()
        assert session.end(owner="hotkey") is None

    def test_begin_failure_releases_session(self) -> None:
        session = VoiceTypingSession()
        source = _FakeSource()
        source.start_should_raise = RuntimeError("device went away")

        with pytest.raises(RuntimeError, match="went away"):
            session.begin(source, owner="device:aipi-1")

        # Session must not appear active after a failed begin —
        # otherwise a hotkey press would silently bounce.
        assert session.is_active is False
        # And a new begin should succeed.
        new_source = _FakeSource()
        assert session.begin(new_source, owner="hotkey") is True

    def test_cancel_drops_session_without_returning_audio(self) -> None:
        session = VoiceTypingSession()
        source = _FakeSource()

        session.begin(source, owner="device:aipi-1")
        session.cancel(owner="device:aipi-1")

        assert session.is_active is False
        # cancel should call stop_recording so the source flushes
        # any internal state, but the audio is discarded.
        assert source.stop_calls == 1

    def test_cancel_with_wrong_owner_is_noop(self) -> None:
        session = VoiceTypingSession()
        source = _FakeSource()

        session.begin(source, owner="hotkey")
        session.cancel(owner="device:aipi-1")

        assert session.is_active is True
        assert source.stop_calls == 0

    def test_begin_rejects_blank_owner(self) -> None:
        session = VoiceTypingSession()
        with pytest.raises(ValueError):
            session.begin(_FakeSource(), owner="")

    def test_concurrent_begins_serialize(self) -> None:
        """Hammer ``begin`` from multiple threads; only one wins."""
        session = VoiceTypingSession()
        sources = [_FakeSource() for _ in range(10)]
        accepts: list[bool] = []
        accepts_lock = threading.Lock()

        def _attempt(idx: int) -> None:
            ok = session.begin(sources[idx], owner=f"thread-{idx}")
            with accepts_lock:
                accepts.append(ok)

        threads = [threading.Thread(target=_attempt, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sum(1 for a in accepts if a) == 1
        # Exactly one source was started.
        assert sum(s.start_calls for s in sources) == 1


class TestAudioFloorArbitration:
    """HS-32-03: meeting (`acquire`/`release`) and voice typing (`begin`/`end`)
    share one floor — the single owner model for hotkey / device / meeting."""

    def test_acquire_claims_floor_and_blocks_begin(self) -> None:
        session = VoiceTypingSession()

        # A meeting claims the floor (no source — it drives its own recorder).
        assert session.acquire("meeting") is True
        assert session.active_owner == "meeting"

        # The hotkey can't grab the mic while the meeting holds the floor.
        source = _FakeSource()
        assert session.begin(source, owner="hotkey") is False
        assert source.start_calls == 0
        assert session.active_owner == "meeting"

    def test_begin_blocks_a_meeting_acquire(self) -> None:
        session = VoiceTypingSession()
        source = _FakeSource()

        # The hotkey is recording...
        assert session.begin(source, owner="hotkey") is True
        # ...so a meeting cannot acquire the floor (defined precedence:
        # first to hold it wins).
        assert session.acquire("meeting") is False
        assert session.active_owner == "hotkey"

    def test_release_frees_floor_for_begin(self) -> None:
        session = VoiceTypingSession()
        assert session.acquire("meeting") is True

        session.release("meeting")
        assert session.is_active is False

        source = _FakeSource()
        assert session.begin(source, owner="hotkey") is True
        assert source.start_calls == 1

    def test_release_is_noop_on_owner_mismatch(self) -> None:
        session = VoiceTypingSession()
        assert session.acquire("meeting") is True

        # A stray hotkey release must not free the meeting's floor.
        session.release("hotkey")
        assert session.active_owner == "meeting"
        assert session.begin(_FakeSource(), owner="hotkey") is False

    def test_acquire_does_not_start_or_stop_a_source(self) -> None:
        session = VoiceTypingSession()
        # acquire/release are source-less; end() on the floor returns None.
        assert session.acquire("meeting") is True
        assert session.end(owner="meeting") is None  # no source bound

    def test_acquire_rejects_blank_owner(self) -> None:
        session = VoiceTypingSession()
        with pytest.raises(ValueError):
            session.acquire("")

    def test_meeting_floor_excludes_all_concurrent_begins(self) -> None:
        """With a meeting holding the floor, no racing hotkey/device begin wins."""
        session = VoiceTypingSession()
        assert session.acquire("meeting") is True

        sources = [_FakeSource() for _ in range(10)]
        accepts: list[bool] = []
        accepts_lock = threading.Lock()

        def _attempt(idx: int) -> None:
            ok = session.begin(sources[idx], owner=f"device:{idx}")
            with accepts_lock:
                accepts.append(ok)

        threads = [threading.Thread(target=_attempt, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # The meeting keeps the floor; every begin is rejected, no source starts.
        assert not any(accepts)
        assert sum(s.start_calls for s in sources) == 0
        assert session.active_owner == "meeting"
