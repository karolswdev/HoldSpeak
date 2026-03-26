"""Speaker diarization and identification for HoldSpeak meetings.

Uses resemblyzer for speaker embeddings to identify distinct speakers
within the system audio stream.
"""

from __future__ import annotations

import random
import threading
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

import numpy as np

from .logging_config import get_logger

if TYPE_CHECKING:
    from .db import MeetingDatabase

log = get_logger("speaker_intel")

# Fun avatar pool for speaker icons
SPEAKER_AVATARS = [
    # Animals
    "🐶", "🐱", "🐼", "🦊", "🐻", "🐨", "🦁", "🐸", "🐵", "🐷",
    "🐰", "🐯", "🦄", "🐲", "🦉", "🐙", "🦋", "🐢", "🐳", "🦩",
    "🐧", "🦈", "🐺", "🦖", "🦚", "🐞", "🦜", "🐝", "🦔", "🦥",
    # Expressive
    "😎", "🤓", "🧐", "🤠", "👻", "🤖", "👽", "🎃", "🥷", "🧙",
    "🧛", "🧜", "🧝", "🦸", "🦹", "🥸", "🤡", "💂", "👨‍🚀", "🧑‍🎤",
    # Nature/Objects
    "🌵", "🍄", "⭐", "🔮", "🎱", "🎭", "🌈", "❄️", "🔥", "💎",
    "🌻", "🍀", "🌙", "☀️", "🌊", "⚡", "🎸", "🎯", "🎪", "🎨",
]


def get_random_avatar(exclude: Optional[set[str]] = None) -> str:
    """Get a random avatar emoji, optionally excluding some."""
    available = SPEAKER_AVATARS
    if exclude:
        available = [a for a in SPEAKER_AVATARS if a not in exclude]
        if not available:
            available = SPEAKER_AVATARS  # Fallback if all excluded
    return random.choice(available)

# Lazy-loaded encoder to avoid loading model at startup
_encoder = None
_encoder_lock = threading.Lock()


def _get_encoder():
    """Lazy-load the speaker encoder.

    The resemblyzer VoiceEncoder is ~100MB and takes a moment to load,
    so we only load it when first needed.
    """
    global _encoder
    if _encoder is None:
        with _encoder_lock:
            if _encoder is None:
                try:
                    from resemblyzer import VoiceEncoder
                    _encoder = VoiceEncoder()
                    log.info("Speaker encoder loaded")
                except ImportError:
                    log.warning("resemblyzer not installed - speaker diarization unavailable")
                    raise
    return _encoder


@dataclass
class SpeakerEmbedding:
    """A speaker's voice embedding with metadata."""

    id: str
    name: str
    embedding: np.ndarray  # 256-dim float32 vector
    sample_count: int = 1
    avatar: Optional[str] = None  # Emoji avatar for visual identity
    created_at: str = field(default_factory=lambda: "")
    updated_at: str = field(default_factory=lambda: "")

    def similarity(self, other: np.ndarray) -> float:
        """Calculate cosine similarity to another embedding.

        Args:
            other: Another 256-dim embedding vector.

        Returns:
            Cosine similarity score between 0 and 1.
        """
        norm_self = np.linalg.norm(self.embedding)
        norm_other = np.linalg.norm(other)
        if norm_self == 0 or norm_other == 0:
            return 0.0
        return float(np.dot(self.embedding, other) / (norm_self * norm_other))

    def update(self, new_embedding: np.ndarray, alpha: float = 0.3) -> None:
        """Update embedding with exponential moving average.

        This refines the speaker's voice profile as more samples are heard.

        Args:
            new_embedding: New embedding to incorporate.
            alpha: Weight of new embedding (0-1). Higher = more influence.
        """
        self.embedding = (1 - alpha) * self.embedding + alpha * new_embedding
        # Re-normalize to unit length for consistent similarity calculations
        norm = np.linalg.norm(self.embedding)
        if norm > 0:
            self.embedding = self.embedding / norm
        self.sample_count += 1

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "avatar": self.avatar,
            "sample_count": self.sample_count,
        }


class SpeakerDiarizer:
    """Real-time speaker diarization for system audio stream.

    Identifies distinct speakers within audio chunks and assigns them
    labels like "Speaker 1", "Speaker 2", etc. Supports cross-meeting
    speaker recognition through stored voice embeddings.

    Example:
        diarizer = SpeakerDiarizer(db=get_database())

        # During transcription:
        speaker_id, speaker_name = diarizer.identify_speaker(audio_chunk)

        # After meeting:
        diarizer.save_speakers()
    """

    # Cosine similarity threshold for matching speakers
    # Higher = stricter matching (fewer false positives, more fragmentation)
    # Lower = looser matching (more false positives, less fragmentation)
    SIMILARITY_THRESHOLD = 0.75

    # Minimum audio duration for reliable embedding extraction
    MIN_AUDIO_DURATION = 1.0  # seconds

    def __init__(
        self,
        db: Optional["MeetingDatabase"] = None,
        enable_cross_meeting: bool = True,
        similarity_threshold: Optional[float] = None,
    ):
        """Initialize speaker diarizer.

        Args:
            db: Database for cross-meeting speaker persistence.
            enable_cross_meeting: Load/save speakers for recognition across meetings.
            similarity_threshold: Override default similarity threshold.
        """
        self.db = db
        self.enable_cross_meeting = enable_cross_meeting
        if similarity_threshold is not None:
            self.SIMILARITY_THRESHOLD = similarity_threshold

        # Session speakers (current meeting)
        self._session_speakers: dict[str, SpeakerEmbedding] = {}
        self._lock = threading.Lock()
        self._speaker_counter = 0

        # Cache of known speakers from database
        self._known_speakers_loaded = False
        self._known_speakers: dict[str, SpeakerEmbedding] = {}

        log.info(f"SpeakerDiarizer initialized (cross_meeting={enable_cross_meeting})")

    def extract_embedding(
        self, audio: np.ndarray, sample_rate: int = 16000
    ) -> Optional[np.ndarray]:
        """Extract speaker embedding from audio chunk.

        Args:
            audio: Audio samples as float32 array.
            sample_rate: Sample rate (must be 16000 for resemblyzer).

        Returns:
            256-dim embedding vector, or None if audio too short.
        """
        duration = len(audio) / sample_rate
        if duration < self.MIN_AUDIO_DURATION:
            log.debug(f"Audio too short for embedding: {duration:.2f}s < {self.MIN_AUDIO_DURATION}s")
            return None

        try:
            encoder = _get_encoder()
            # resemblyzer expects float32 at 16kHz
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            embedding = encoder.embed_utterance(audio)
            return embedding.astype(np.float32)
        except Exception as e:
            log.error(f"Embedding extraction failed: {e}")
            return None

    def identify_speaker(
        self, audio: np.ndarray, sample_rate: int = 16000
    ) -> tuple[Optional[str], str]:
        """Identify speaker from audio chunk.

        The algorithm:
        1. Extract embedding from audio
        2. Compare to session speakers (current meeting)
        3. Compare to known speakers (database, if cross-meeting enabled)
        4. Create new speaker if no match

        Args:
            audio: Audio samples as float32 array.
            sample_rate: Sample rate (default 16000).

        Returns:
            Tuple of (speaker_id, speaker_name).
            speaker_id may be None for very short audio.
        """
        embedding = self.extract_embedding(audio, sample_rate)
        if embedding is None:
            return self._get_fallback_speaker()

        with self._lock:
            # First check session speakers (current meeting)
            best_match = self._find_best_match(embedding, self._session_speakers)

            # Then check database speakers if cross-meeting enabled
            if best_match is None and self.enable_cross_meeting:
                self._load_known_speakers_if_needed()
                best_match = self._find_best_match(embedding, self._known_speakers)
                if best_match:
                    # Copy to session speakers
                    self._session_speakers[best_match.id] = SpeakerEmbedding(
                        id=best_match.id,
                        name=best_match.name,
                        embedding=best_match.embedding.copy(),
                        sample_count=best_match.sample_count,
                    )
                    best_match = self._session_speakers[best_match.id]

            if best_match:
                # Update embedding with new sample (refines voice profile)
                best_match.update(embedding)
                log.debug(f"Matched speaker: {best_match.name} (samples={best_match.sample_count})")
                return best_match.id, best_match.name

            # No match - create new speaker
            new_speaker = self._create_new_speaker(embedding)
            log.info(f"New speaker created: {new_speaker.name} (id={new_speaker.id})")
            return new_speaker.id, new_speaker.name

    def _find_best_match(
        self,
        embedding: np.ndarray,
        speakers: dict[str, SpeakerEmbedding],
    ) -> Optional[SpeakerEmbedding]:
        """Find the best matching speaker above similarity threshold.

        Args:
            embedding: Query embedding vector.
            speakers: Dictionary of speaker_id -> SpeakerEmbedding.

        Returns:
            Best matching speaker, or None if no match above threshold.
        """
        best_speaker = None
        best_similarity = self.SIMILARITY_THRESHOLD

        for speaker in speakers.values():
            similarity = speaker.similarity(embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_speaker = speaker

        if best_speaker:
            log.debug(f"Best match: {best_speaker.name} (similarity={best_similarity:.3f})")

        return best_speaker

    def _create_new_speaker(self, embedding: np.ndarray) -> SpeakerEmbedding:
        """Create a new speaker identity.

        Args:
            embedding: The speaker's voice embedding.

        Returns:
            Newly created SpeakerEmbedding.
        """
        self._speaker_counter += 1

        # Pick a unique avatar (avoid duplicates in current session)
        used_avatars = {s.avatar for s in self._session_speakers.values() if s.avatar}
        avatar = get_random_avatar(exclude=used_avatars)

        speaker = SpeakerEmbedding(
            id=str(uuid.uuid4())[:12],
            name=f"Speaker {self._speaker_counter}",
            embedding=embedding,
            sample_count=1,
            avatar=avatar,
        )
        self._session_speakers[speaker.id] = speaker
        return speaker

    def _get_fallback_speaker(self) -> tuple[Optional[str], str]:
        """Return fallback speaker for short/invalid audio.

        Returns the most recently active speaker, or a default.
        """
        with self._lock:
            if self._session_speakers:
                # Return most recent speaker
                last_speaker = list(self._session_speakers.values())[-1]
                return last_speaker.id, last_speaker.name
        return None, "Remote"

    def _load_known_speakers_if_needed(self) -> None:
        """Load known speakers from database (once per session)."""
        if self._known_speakers_loaded or self.db is None:
            return

        try:
            speakers = self.db.get_all_speakers()
            self._known_speakers = {s.id: s for s in speakers}
            self._known_speakers_loaded = True
            log.info(f"Loaded {len(self._known_speakers)} known speakers from database")
        except Exception as e:
            log.error(f"Failed to load known speakers: {e}")
            self._known_speakers_loaded = True  # Don't retry

    def save_speakers(self) -> None:
        """Persist session speakers to database for cross-meeting recognition.

        Should be called when meeting ends.
        """
        if self.db is None:
            log.debug("No database - skipping speaker save")
            return

        with self._lock:
            saved_count = 0
            for speaker in self._session_speakers.values():
                try:
                    self.db.save_speaker(speaker)
                    saved_count += 1
                except Exception as e:
                    log.error(f"Failed to save speaker {speaker.id}: {e}")

            log.info(f"Saved {saved_count} speakers to database")

    def rename_speaker(self, speaker_id: str, new_name: str) -> bool:
        """Rename a speaker identity.

        Updates both session and database.

        Args:
            speaker_id: ID of speaker to rename.
            new_name: New display name.

        Returns:
            True if speaker found and renamed.
        """
        with self._lock:
            if speaker_id in self._session_speakers:
                self._session_speakers[speaker_id].name = new_name
                log.info(f"Renamed speaker {speaker_id} to '{new_name}'")

                if self.db is not None:
                    try:
                        self.db.update_speaker_name(speaker_id, new_name)
                    except Exception as e:
                        log.error(f"Failed to persist speaker rename: {e}")

                return True

        return False

    def get_session_speakers(self) -> list[SpeakerEmbedding]:
        """Get all speakers detected in current session.

        Returns:
            List of speaker embeddings.
        """
        with self._lock:
            return list(self._session_speakers.values())

    def reset(self) -> None:
        """Reset session state for a new meeting.

        Clears session speakers and counter, but preserves known speakers.
        """
        with self._lock:
            self._session_speakers.clear()
            self._speaker_counter = 0
            log.debug("Speaker diarizer reset")
