# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_intel_streaming.py to restore.

# ruff: noqa


# --- TestStreamingIntelAnalysis: P2: five tests call the mock_streaming_intel fake and assert what the fake returns; no product code runs
@pytest.mark.integration
class TestStreamingIntelAnalysis:
    """Tests for MeetingIntel streaming analysis."""

    def test_analyze_stream_true_returns_iterator(self, mock_streaming_intel):
        """analyze(stream=True) should return an iterator."""
        result = mock_streaming_intel.analyze("Test transcript", stream=True)
        assert hasattr(result, "__iter__")

    def test_analyze_stream_false_returns_result(self, mock_streaming_intel, mock_intel_result):
        """analyze(stream=False) should return IntelResult directly."""
        result = mock_streaming_intel.analyze("Test transcript", stream=False)
        assert isinstance(result, IntelResult)

    def test_streaming_yields_tokens_then_result(self, mock_streaming_intel):
        """Streaming should yield string tokens followed by IntelResult."""
        stream = mock_streaming_intel.analyze("Test transcript", stream=True)

        items = list(stream)
        # All but last should be strings
        tokens = items[:-1]
        final = items[-1]

        assert all(isinstance(t, str) for t in tokens)
        assert isinstance(final, IntelResult)

    def test_streaming_tokens_not_empty(self, mock_streaming_intel):
        """Should yield at least one token before final result."""
        stream = mock_streaming_intel.analyze("Test transcript", stream=True)
        items = list(stream)

        tokens = [i for i in items if isinstance(i, str)]
        assert len(tokens) > 0

    def test_streaming_preserves_transcript(self, mock_streaming_intel):
        """Streaming should receive the full transcript."""
        transcript = "Full meeting transcript with multiple speakers."
        _ = list(mock_streaming_intel.analyze(transcript, stream=True))

        assert mock_streaming_intel.analyze_called
        assert mock_streaming_intel.transcript_received == transcript


# --- TestStreamingInterruption: P1: sets session._current_analysis_id by hand and asserts it reads back; no product code runs
@pytest.mark.integration
class TestStreamingInterruption:
    """Tests for intel streaming interruption handling."""

    def test_analysis_id_changes_on_new_analysis(self, mock_transcriber):
        """New analysis should get a new analysis ID."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
        )

        # Simulate starting analysis
        session._current_analysis_id = "first-id"

        # New analysis would set new ID
        new_id = "second-id"
        session._current_analysis_id = new_id

        # Old analysis should detect interruption
        assert session._current_analysis_id != "first-id"
        assert session._current_analysis_id == "second-id"

    def test_concurrent_analysis_detection(self, mock_transcriber):
        """Concurrent analysis should be detected via analysis_id."""
        session = MeetingSession(
            transcriber=mock_transcriber,
            intel_enabled=False,
        )

        # First analysis starts
        analysis_1_id = "analysis-001"
        session._current_analysis_id = analysis_1_id

        # Simulate check in first analysis
        assert session._current_analysis_id == analysis_1_id

        # Second analysis starts, interrupting first
        analysis_2_id = "analysis-002"
        session._current_analysis_id = analysis_2_id

        # First analysis detects interruption
        assert session._current_analysis_id != analysis_1_id
