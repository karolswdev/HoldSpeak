"""Phase-91 React import and facet locks.

HS-132-12: HS-117-09 decomposed ``HistoryCore.tsx`` into ``cores/history/*``
— the shell keeps the facet params and the footer, the import well and the
queue roster moved into their own modules. Each lock is re-pointed at the
module that actually holds it.
"""
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_HISTORY = _REPO / "web/src/pages/cores/history"


def _page() -> str:
    """The History shell (facet params, wings, footer verbs)."""
    return (_REPO / "web/src/pages/cores/HistoryCore.tsx").read_text()


def _import_section() -> str:
    return (_HISTORY / "ImportSection.tsx").read_text()


def test_history_has_audio_and_transcript_import() -> None:
    page = _page()
    section = _import_section()
    # HS-102-04: Record leads; import is the in-surface ImportSection
    # with the drop well ("or drop a recording below").
    assert "Record meeting" in page and "ImportSection" in page
    for suffix in (".wav", ".mp3", ".m4a", ".flac", ".vtt", ".srt", ".txt"):
        assert suffix in section, suffix
    assert "ffmpeg" in section
    assert '"/api/meetings/import"' in section
    # HS-201-10 (rehearsal defect 10): the import door used to send the
    # FILE's `lastModified` as `started_at_ms`, so a WAV copied onto the
    # disk in June landed the meeting under JUN 03. The import moment is
    # the one fact this gesture knows, and the hub stamps it. The fields
    # the door DOES send stay pinned here, and the two it must never send
    # again are pinned as absent.
    for field in ('"file"', '"title"', '"speaker"', '"tags"'):
        assert f"body.append({field}" in section, field
    appended = [line for line in section.splitlines() if "body.append(" in line]
    assert appended
    assert not [line for line in appended if "lastModified" in line], (
        f"the import door sent the file's mtime again: {appended}"
    )
    assert not [line for line in appended if "started_at_ms" in line], (
        f"the import door sent a client-chosen start again: {appended}"
    )


def test_history_has_composable_server_facets() -> None:
    page = _page()
    for marker in ("date_from", "date_to", "speaker", "tag", "has_open_actions"):
        assert marker in page
    assert '"/api/meetings/facets"' in page


def test_history_search_uses_backend_search_contract() -> None:
    page = _page()
    assert 'meetingParams.set("search", query)' in page


def test_history_never_sends_the_retired_search_param() -> None:
    # The half of the search contract that still holds: `q` was retired and
    # the API 422s it by name — the client must never send it.
    page = _page()
    assert 'meetingParams.set("q", query)' not in page
    assert '"q"' not in page
    crud = (_REPO / "holdspeak/web/routes/meetings/crud.py").read_text()
    assert "unsupported query parameter 'q'; use 'search'" in crud


def test_failed_import_and_queue_states_stay_visible() -> None:
    helpers = (_HISTORY / "helpers.ts").read_text()
    assert "import_failed" in helpers
    # HS-111-03: the queue-status Select became the CycleGadget; the
    # wire states now ride its options roster (in the door section).
    door = (_HISTORY / "DoorSection.tsx").read_text()
    for state in ("pending", "running", "failed", "complete"):
        assert f'value: "{state}"' in door, state
