"""Unit tests for the speaker intelligence module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from pathlib import Path

from holdspeak.speaker_intel import SpeakerEmbedding, SpeakerDiarizer


class TestSpeakerEmbedding:
    """Tests for SpeakerEmbedding dataclass."""

    def test_init(self):
        """Test creating a speaker embedding."""
        embedding = np.random.randn(256).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)  # Normalize

        speaker = SpeakerEmbedding(
            id="test123",
            name="John Doe",
            embedding=embedding,
            sample_count=1,
        )

        assert speaker.id == "test123"
        assert speaker.name == "John Doe"
        assert speaker.embedding.shape == (256,)
        assert speaker.sample_count == 1

    def test_similarity_same_embedding(self):
        """Test similarity of identical embeddings."""
        embedding = np.random.randn(256).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)

        speaker = SpeakerEmbedding(
            id="test1",
            name="Speaker",
            embedding=embedding,
        )

        similarity = speaker.similarity(embedding)
        assert similarity == pytest.approx(1.0, abs=1e-5)

    def test_similarity_orthogonal_embeddings(self):
        """Test similarity of orthogonal embeddings."""
        # Create two orthogonal vectors
        e1 = np.zeros(256, dtype=np.float32)
        e1[0] = 1.0
        e2 = np.zeros(256, dtype=np.float32)
        e2[1] = 1.0

        speaker = SpeakerEmbedding(
            id="test1",
            name="Speaker",
            embedding=e1,
        )

        similarity = speaker.similarity(e2)
        assert similarity == pytest.approx(0.0, abs=1e-5)

    def test_similarity_similar_embeddings(self):
        """Test similarity of similar (but not identical) embeddings."""
        # Use deterministic vectors to avoid flaky tests
        e1 = np.ones(256, dtype=np.float32)
        e1 = e1 / np.linalg.norm(e1)

        # Create a similar vector by slightly modifying just one component
        e2 = e1.copy()
        e2[0] = e1[0] * 1.01  # 1% change to one component
        e2 = e2 / np.linalg.norm(e2)

        speaker = SpeakerEmbedding(
            id="test1",
            name="Speaker",
            embedding=e1,
        )

        similarity = speaker.similarity(e2)
        # Should be extremely high (essentially the same) but not exactly 1.0
        # due to the tiny perturbation
        assert 0.9999 < similarity < 1.0

    def test_update_embedding(self):
        """Test updating embedding with EMA."""
        e1 = np.ones(256, dtype=np.float32)
        e1 = e1 / np.linalg.norm(e1)

        speaker = SpeakerEmbedding(
            id="test1",
            name="Speaker",
            embedding=e1.copy(),
            sample_count=1,
        )

        # New embedding (different direction)
        e2 = np.zeros(256, dtype=np.float32)
        e2[0] = 1.0

        speaker.update(e2, alpha=0.5)

        # Sample count should increase
        assert speaker.sample_count == 2

        # Embedding should be updated (mix of e1 and e2)
        # After normalization, should be unit vector
        assert np.linalg.norm(speaker.embedding) == pytest.approx(1.0, abs=1e-5)

    def test_to_dict(self):
        """Test converting to dictionary."""
        embedding = np.random.randn(256).astype(np.float32)

        speaker = SpeakerEmbedding(
            id="test123",
            name="John Doe",
            embedding=embedding,
            sample_count=5,
        )

        d = speaker.to_dict()
        assert d["id"] == "test123"
        assert d["name"] == "John Doe"
        assert d["sample_count"] == 5
        # Embedding should not be in dict (too large for JSON)
        assert "embedding" not in d


class TestSpeakerDiarizer:
    """Tests for SpeakerDiarizer class."""

    @pytest.fixture
    def mock_encoder(self):
        """Mock the voice encoder to avoid loading the model."""
        with patch("holdspeak.speaker_intel._get_encoder") as mock:
            encoder = MagicMock()
            # Return a random embedding when called
            encoder.embed_utterance.side_effect = lambda audio: np.random.randn(256).astype(np.float32)
            mock.return_value = encoder
            yield encoder

    @pytest.fixture
    def diarizer(self, mock_encoder):
        """Create a diarizer instance with mocked encoder."""
        return SpeakerDiarizer(db=None, enable_cross_meeting=False)

    def test_init(self, mock_encoder):
        """Test initializing diarizer."""
        diarizer = SpeakerDiarizer(db=None, enable_cross_meeting=False)
        assert diarizer.db is None
        assert diarizer.enable_cross_meeting is False
        assert len(diarizer._session_speakers) == 0

    def test_init_with_custom_threshold(self, mock_encoder):
        """Test initializing with custom similarity threshold."""
        diarizer = SpeakerDiarizer(
            db=None,
            similarity_threshold=0.85,
        )
        assert diarizer.SIMILARITY_THRESHOLD == 0.85

    def test_extract_embedding_too_short(self, diarizer):
        """Test that short audio returns None."""
        # Audio shorter than MIN_AUDIO_DURATION (1.0 second)
        short_audio = np.random.randn(8000).astype(np.float32)  # 0.5 seconds

        result = diarizer.extract_embedding(short_audio, sample_rate=16000)
        assert result is None

    def test_extract_embedding_valid(self, diarizer, mock_encoder):
        """Test extracting embedding from valid audio."""
        # Audio longer than MIN_AUDIO_DURATION
        audio = np.random.randn(32000).astype(np.float32)  # 2 seconds

        result = diarizer.extract_embedding(audio, sample_rate=16000)
        assert result is not None
        assert result.shape == (256,)
        mock_encoder.embed_utterance.assert_called_once()

    def test_identify_speaker_creates_new(self, diarizer, mock_encoder):
        """Test that identifying unknown speaker creates a new one."""
        audio = np.random.randn(32000).astype(np.float32)

        speaker_id, speaker_name = diarizer.identify_speaker(audio)

        assert speaker_id is not None
        assert speaker_name == "Speaker 1"
        assert len(diarizer._session_speakers) == 1

    def test_identify_speaker_matches_existing(self, diarizer, mock_encoder):
        """Test that similar audio matches existing speaker."""
        # Create a fixed embedding
        fixed_embedding = np.random.randn(256).astype(np.float32)
        fixed_embedding = fixed_embedding / np.linalg.norm(fixed_embedding)

        # Clear side_effect and set return_value (side_effect takes precedence)
        mock_encoder.embed_utterance.side_effect = None
        mock_encoder.embed_utterance.return_value = fixed_embedding

        audio = np.random.randn(32000).astype(np.float32)

        # First call creates speaker
        id1, name1 = diarizer.identify_speaker(audio)
        assert name1 == "Speaker 1"

        # Second call should match the same speaker
        id2, name2 = diarizer.identify_speaker(audio)
        assert id1 == id2
        assert name1 == name2

        # Still only one speaker
        assert len(diarizer._session_speakers) == 1

    def test_identify_speaker_creates_multiple(self, diarizer, mock_encoder):
        """Test that different speakers get different IDs."""
        audio = np.random.randn(32000).astype(np.float32)

        # Each call returns a different random embedding (default behavior)
        # Since they're random, cosine similarity will be low

        # Create first speaker
        diarizer._speaker_counter = 0
        id1, name1 = diarizer.identify_speaker(audio)

        # Force a new embedding that's very different
        # by resetting mock to return orthogonal vector
        e2 = np.zeros(256, dtype=np.float32)
        e2[0] = 1.0  # Completely different direction
        mock_encoder.embed_utterance.return_value = e2

        id2, name2 = diarizer.identify_speaker(audio)

        # Should be different speakers
        assert id1 != id2
        assert name1 == "Speaker 1"
        assert name2 == "Speaker 2"
        assert len(diarizer._session_speakers) == 2

    def test_identify_speaker_short_audio_returns_fallback(self, diarizer):
        """Test that short audio returns fallback speaker."""
        short_audio = np.random.randn(8000).astype(np.float32)  # 0.5 seconds

        # With no session speakers, should return default
        speaker_id, speaker_name = diarizer.identify_speaker(short_audio)
        assert speaker_id is None
        assert speaker_name == "Remote"

    def test_identify_speaker_short_audio_returns_last_speaker(self, diarizer, mock_encoder):
        """Test that short audio returns last known speaker."""
        # First, create a speaker with valid audio
        audio = np.random.randn(32000).astype(np.float32)
        id1, name1 = diarizer.identify_speaker(audio)

        # Now short audio should return that speaker
        short_audio = np.random.randn(8000).astype(np.float32)
        id2, name2 = diarizer.identify_speaker(short_audio)

        assert id2 == id1
        assert name2 == name1

    def test_rename_speaker(self, diarizer, mock_encoder):
        """Test renaming a speaker."""
        audio = np.random.randn(32000).astype(np.float32)
        speaker_id, _ = diarizer.identify_speaker(audio)

        result = diarizer.rename_speaker(speaker_id, "John Smith")
        assert result is True

        # Verify the name changed
        speaker = diarizer._session_speakers[speaker_id]
        assert speaker.name == "John Smith"

    def test_rename_nonexistent_speaker(self, diarizer):
        """Test renaming a speaker that doesn't exist."""
        result = diarizer.rename_speaker("nonexistent", "New Name")
        assert result is False

    def test_get_session_speakers(self, diarizer, mock_encoder):
        """Test getting list of session speakers."""
        audio = np.random.randn(32000).astype(np.float32)

        # Create two different speakers
        diarizer.identify_speaker(audio)

        e2 = np.zeros(256, dtype=np.float32)
        e2[0] = 1.0
        mock_encoder.embed_utterance.return_value = e2
        diarizer.identify_speaker(audio)

        speakers = diarizer.get_session_speakers()
        assert len(speakers) == 2

    def test_reset(self, diarizer, mock_encoder):
        """Test resetting diarizer state."""
        audio = np.random.randn(32000).astype(np.float32)
        diarizer.identify_speaker(audio)
        assert len(diarizer._session_speakers) == 1

        diarizer.reset()

        assert len(diarizer._session_speakers) == 0
        assert diarizer._speaker_counter == 0


class TestSpeakerDiarizerWithDatabase:
    """Tests for SpeakerDiarizer with database integration."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test.db"
        yield db_path
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_encoder(self):
        """Mock the voice encoder."""
        with patch("holdspeak.speaker_intel._get_encoder") as mock:
            encoder = MagicMock()
            mock.return_value = encoder
            yield encoder

    def test_save_speakers(self, temp_db_path, mock_encoder):
        """Test saving speakers to database."""
        from holdspeak.db import MeetingDatabase, reset_database

        try:
            db = MeetingDatabase(temp_db_path)

            # Create diarizer with database
            diarizer = SpeakerDiarizer(db=db, enable_cross_meeting=True)

            # Create a speaker
            fixed_embedding = np.random.randn(256).astype(np.float32)
            fixed_embedding = fixed_embedding / np.linalg.norm(fixed_embedding)
            mock_encoder.embed_utterance.return_value = fixed_embedding

            audio = np.random.randn(32000).astype(np.float32)
            speaker_id, _ = diarizer.identify_speaker(audio)

            # Save speakers
            diarizer.save_speakers()

            # Verify speaker was saved to database
            saved_speakers = db.get_all_speakers()
            assert len(saved_speakers) == 1
            assert saved_speakers[0].id == speaker_id
            assert saved_speakers[0].name == "Speaker 1"
        finally:
            reset_database()

    def test_cross_meeting_recognition(self, temp_db_path, mock_encoder):
        """Test recognizing speakers across meetings."""
        from holdspeak.db import MeetingDatabase, reset_database

        try:
            db = MeetingDatabase(temp_db_path)

            # Fixed embedding for this "person"
            fixed_embedding = np.random.randn(256).astype(np.float32)
            fixed_embedding = fixed_embedding / np.linalg.norm(fixed_embedding)
            mock_encoder.embed_utterance.return_value = fixed_embedding

            audio = np.random.randn(32000).astype(np.float32)

            # Meeting 1: Create and name speaker
            diarizer1 = SpeakerDiarizer(db=db, enable_cross_meeting=True)
            speaker_id_1, _ = diarizer1.identify_speaker(audio)
            diarizer1.rename_speaker(speaker_id_1, "Sarah Chen")
            diarizer1.save_speakers()

            # Meeting 2: Should recognize Sarah
            diarizer2 = SpeakerDiarizer(db=db, enable_cross_meeting=True)
            speaker_id_2, speaker_name_2 = diarizer2.identify_speaker(audio)

            # Should be the same speaker with the name we set
            assert speaker_id_2 == speaker_id_1
            assert speaker_name_2 == "Sarah Chen"
        finally:
            reset_database()
