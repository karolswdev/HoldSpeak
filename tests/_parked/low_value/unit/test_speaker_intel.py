# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_speaker_intel.py to restore.

# ruff: noqa


# --- TestSpeakerEmbedding::test_init: P1: reads back constructor arguments and defaults it just set
# (was a method of class TestSpeakerEmbedding)
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


# --- TestSpeakerDiarizer::test_init: P1: reads back constructor arguments and defaults it just set
# (was a method of class TestSpeakerDiarizer)
def test_init(self, mock_encoder):
    """Test initializing diarizer."""
    diarizer = SpeakerDiarizer(db=None, enable_cross_meeting=False)
    assert diarizer.db is None
    assert diarizer.enable_cross_meeting is False
    assert len(diarizer._session_speakers) == 0


# --- TestSpeakerDiarizer::test_init_with_custom_threshold: P1: reads back constructor arguments and defaults it just set
# (was a method of class TestSpeakerDiarizer)
def test_init_with_custom_threshold(self, mock_encoder):
    """Test initializing with custom similarity threshold."""
    diarizer = SpeakerDiarizer(
        db=None,
        similarity_threshold=0.85,
    )
    assert diarizer.SIMILARITY_THRESHOLD == 0.85
