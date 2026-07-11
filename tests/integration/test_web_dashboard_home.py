"""React live-room source locks."""
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def test_live_room_keeps_idle_and_active_primary_actions() -> None:
    page = (_REPO / "web/src/pages/LivePage.tsx").read_text()
    assert "Ready when you are" in page
    assert "Start meeting" in page
    assert "Stop meeting" in page
    assert '"/api/meeting/start"' in page
    assert '"/api/meeting/stop"' in page


def test_live_room_keeps_transcript_bookmarks_metadata_and_intel() -> None:
    page = (_REPO / "web/src/pages/LivePage.tsx").read_text()
    for marker in ("Transcript", "Bookmark", "Meeting details", "Intelligence"):
        assert marker in page
    assert "useRuntimeBus" in page
    assert "useRuntimeFrame" not in page  # one wildcard subscription owns room frames
