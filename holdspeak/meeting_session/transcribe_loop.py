"""The background transcription loop (HS-63-02).

The loop, the overlap window, and chunk transcription — verbatim moves
out of MeetingSession; `self` is the session.
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, TYPE_CHECKING
import json

import numpy as np

from ..meeting_recorder import MeetingRecorder, concatenate_chunks, AudioChunk
from ..transcribe import Transcriber
from ..logging_config import get_logger

if TYPE_CHECKING:
    from ..audio import AudioSource
    from ..device_audio import DeviceDescriptor

# Optional imports for intel (the same guarded pattern as session.py).
try:
    from ..intel import (
        MeetingIntel,
        IntelResult,
        ActionItem,
        get_intel_runtime_status,
        resolve_intel_provider,
    )
except ImportError:
    MeetingIntel = None  # type: ignore
    IntelResult = None  # type: ignore
    ActionItem = None  # type: ignore
    get_intel_runtime_status = None  # type: ignore
    resolve_intel_provider = None  # type: ignore

try:
    from ..speaker_intel import SpeakerDiarizer
except ImportError:
    SpeakerDiarizer = None  # type: ignore

from .models import (
    Bookmark,
    IntelSnapshot,
    MeetingSaveResult,
    MeetingState,
    TranscriptSegment,
)

log = get_logger("meeting_session")


class TranscribeLoopMixin:
    def _transcribe_loop(self) -> None:
        """Background thread that transcribes audio periodically."""
        log.debug("Transcription loop started")

        while not self._stop_event.is_set():
            # Wait for interval or stop
            self._stop_event.wait(self.TRANSCRIBE_INTERVAL)

            if self._stop_event.is_set():
                break

            with self._lock:
                if self._recorder is None:
                    continue

                # Get chunks since last transcription
                mic_chunks, system_chunks = self._recorder.get_pending_chunks(
                    since=self._last_transcribe_time
                )
                device_chunks = self._recorder.get_pending_device_chunks()

            if mic_chunks or system_chunks or device_chunks:
                self._transcribe_chunks(
                    mic_chunks, system_chunks, device_chunks=device_chunks
                )

        log.debug("Transcription loop ended")

    def _apply_overlap(self, stream_id: str, audio: "np.ndarray", final: bool) -> "np.ndarray":
        """Prepend the previous pass's tail and stash a fresh tail for next.

        AIPI-4-15 / HS-17 overlap windows. Returns the audio to feed
        to Whisper (previous tail + current chunk). Updates the tail
        store with the last ``self._overlap_tail_seconds`` of the
        combined audio so next pass can re-prepend. On the final pass
        the tail is cleared — no next pass to feed.
        """
        import numpy as _np

        tail = self._stream_tails.get(stream_id)
        if tail is not None and tail.size > 0:
            audio = _np.concatenate([tail, audio])
        if final:
            self._stream_tails.pop(stream_id, None)
        else:
            tail_samples = int(self._overlap_tail_seconds * 16000)
            self._stream_tails[stream_id] = (
                audio[-tail_samples:].copy() if audio.size > tail_samples else audio.copy()
            )
        return audio

    def _transcribe_chunks(
        self,
        mic_chunks: list[AudioChunk],
        system_chunks: list[AudioChunk],
        final: bool = False,
        *,
        device_chunks: Optional[dict[str, list[AudioChunk]]] = None,
    ) -> None:
        """Transcribe audio chunks and add to segments."""
        new_segments: list[TranscriptSegment] = []
        device_chunks = device_chunks or {}

        # Process mic chunks
        if mic_chunks:
            mic_audio = concatenate_chunks(mic_chunks)
            mic_audio = self._apply_overlap("mic", mic_audio, final)
            duration = len(mic_audio) / 16000

            if duration >= self.MIN_CHUNK_DURATION:
                start_time = mic_chunks[0].timestamp
                end_time = mic_chunks[-1].end_time

                try:
                    text = self.transcriber.transcribe(mic_audio)
                    if text and text.strip():
                        # Optionally diarize mic audio (for on-site meetings)
                        speaker_id: Optional[str] = None
                        speaker_name = self.mic_label
                        if self.diarize_mic and self._diarizer is not None:
                            try:
                                speaker_id, speaker_name = self._diarizer.identify_speaker(mic_audio)
                            except Exception as e:
                                log.error(f"Mic speaker diarization error: {e}")

                        segment = TranscriptSegment(
                            text=text.strip(),
                            speaker=speaker_name,
                            speaker_id=speaker_id,
                            start_time=start_time,
                            end_time=end_time,
                        )
                        with self._lock:
                            if self._state:
                                self._state.segments.append(segment)
                        new_segments.append(segment)
                        if self.on_segment:
                            try:
                                self.on_segment(segment)
                            except Exception as e:
                                log.error(f"on_segment callback error: {e}")
                        log.debug(f"Mic segment: {segment}")
                except Exception as e:
                    log.error(f"Mic transcription error: {e}")

        # Process system chunks
        if system_chunks:
            system_audio = concatenate_chunks(system_chunks)
            system_audio = self._apply_overlap("system", system_audio, final)
            duration = len(system_audio) / 16000

            if duration >= self.MIN_CHUNK_DURATION:
                start_time = system_chunks[0].timestamp
                end_time = system_chunks[-1].end_time

                try:
                    text = self.transcriber.transcribe(system_audio)
                    if text and text.strip():
                        # Identify speaker via diarization
                        speaker_id: Optional[str] = None
                        speaker_name = self.remote_label
                        if self._diarizer is not None:
                            try:
                                speaker_id, speaker_name = self._diarizer.identify_speaker(system_audio)
                            except Exception as e:
                                log.error(f"Speaker diarization error: {e}")

                        segment = TranscriptSegment(
                            text=text.strip(),
                            speaker=speaker_name,
                            speaker_id=speaker_id,
                            start_time=start_time,
                            end_time=end_time,
                        )
                        with self._lock:
                            if self._state:
                                self._state.segments.append(segment)
                        new_segments.append(segment)
                        if self.on_segment:
                            try:
                                self.on_segment(segment)
                            except Exception as e:
                                log.error(f"on_segment callback error: {e}")
                        log.debug(f"System segment: {segment}")
                except Exception as e:
                    log.error(f"System transcription error: {e}")

        # Process device chunks (HS-14-06): each registered device's
        # audio is transcribed independently, with the device's
        # registered label as the speaker and its id stamped onto
        # every produced segment.
        for device_id, chunks in device_chunks.items():
            if not chunks:
                continue
            audio = concatenate_chunks(chunks)
            audio = self._apply_overlap(f"device:{device_id}", audio, final)
            duration = len(audio) / 16000
            if duration < self.MIN_CHUNK_DURATION:
                continue

            label = self.mic_label
            if self._recorder is not None:
                resolved_label = self._recorder.device_label(device_id)
                if resolved_label:
                    label = resolved_label

            start_time = chunks[0].timestamp
            end_time = chunks[-1].end_time
            try:
                text = self.transcriber.transcribe(audio)
            except Exception as e:
                log.error(f"Device {device_id!r} transcription error: {e}")
                continue

            if text and text.strip():
                segment = TranscriptSegment(
                    text=text.strip(),
                    speaker=label,
                    start_time=start_time,
                    end_time=end_time,
                    device_id=device_id,
                )
                with self._lock:
                    if self._state:
                        self._state.segments.append(segment)
                new_segments.append(segment)
                if self.on_segment:
                    try:
                        self.on_segment(segment)
                    except Exception as e:
                        log.error(f"on_segment callback error: {e}")
                log.debug(f"Device segment ({device_id}): {segment}")

        # Emit new segments to the observer's broadcast channel
        for segment in new_segments:
            self._emit_broadcast("segment", segment.to_dict())

        # Update last transcribe time
        if mic_chunks or system_chunks:
            max_end = 0.0
            if mic_chunks:
                max_end = max(max_end, mic_chunks[-1].end_time)
            if system_chunks:
                max_end = max(max_end, system_chunks[-1].end_time)
            self._last_transcribe_time = max_end

        # HS-92-04: transcript checkpoints are atomic SQLite transactions. Only
        # after one lands do we release old audio, retaining the overlap guard.
        if new_segments or mic_chunks or system_chunks or device_chunks:
            try:
                from ..db import get_database

                if self._capture_journal is not None:
                    self._capture_journal.checkpoint()
                with self._lock:
                    state = self._state
                    if state is not None:
                        state.capture_status = "recording"
                        state.capture_failure = None
                        state.capture_checkpoint_at = datetime.now()
                        state.capture_checkpoint_seconds = max(
                            state.capture_checkpoint_seconds,
                            self._last_transcribe_time,
                        )
                        get_database().meetings.save_meeting(state)
                recorder = self._recorder
                if recorder is not None and self._last_transcribe_time > 0:
                    recorder.trim_before(
                        max(0.0, self._last_transcribe_time - self._overlap_tail_seconds)
                    )
            except Exception as exc:
                with self._lock:
                    if self._state is not None:
                        self._state.capture_status = "recoverable"
                        self._state.capture_failure = f"Checkpoint failed: {exc}"
                self._emit_broadcast(
                    "capture_recovery",
                    {"status": "recoverable", "error": str(exc),
                     "actions": ["retry", "discard"]},
                )
                log.error("Meeting checkpoint failed: %s", exc)

        # Trigger intel analysis periodically
        if new_segments:
            self._segments_since_intel += len(new_segments)
            if self._intel is not None and self._segments_since_intel >= self.INTEL_SEGMENT_INTERVAL:
                self._maybe_run_intel()
