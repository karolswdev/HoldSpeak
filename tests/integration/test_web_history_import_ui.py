"""Phase-91 React import and facet locks."""
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web/src/pages/cores/HistoryCore.tsx").read_text()


def test_history_has_audio_and_transcript_import() -> None:
    page = _page()
    assert "Import a recording or transcript" in page
    for suffix in (".wav", ".mp3", ".m4a", ".flac", ".vtt", ".srt", ".txt"):
        assert suffix in page
    assert "ffmpeg" in page
    assert '"/api/meetings/import"' in page
    assert "started_at_ms" in page and "lastModified" in page


def test_history_has_composable_server_facets() -> None:
    page = _page()
    for marker in ("date_from", "date_to", "speaker", "tag", "has_open_actions"):
        assert marker in page
    assert '"/api/meetings/facets"' in page


def test_failed_import_and_queue_states_stay_visible() -> None:
    page = _page()
    assert "import_failed" in page
    for state in ("pending", "running", "failed", "complete"):
        assert f'value="{state}"' in page
