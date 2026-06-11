"""HS-55-03 — the /history "Import a recording" affordance.

Page-content locks for the import panel (the affordance, the drop target,
the honest notes, the import lifecycle states, the failed-import remove
path) and the behavior markers in the Alpine factory.
"""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _page() -> str:
    return (_REPO / "web" / "src" / "pages" / "history.astro").read_text()


def _app_js() -> str:
    return (_REPO / "web" / "src" / "scripts" / "history-app.js").read_text()


def test_history_has_the_import_affordance_and_panel() -> None:
    page = _page()
    # The opener sits in the meetings toolbar.
    assert "import-open-btn" in page
    assert "Import a recording" in page
    # The panel: drop target + browse, metadata fields, actions.
    assert "import-panel" in page
    assert "import-drop" in page
    assert 'type="file"' in page
    assert "onImportDrop" in page
    assert 'x-model="importTitle"' in page
    assert 'x-model="importSpeaker"' in page
    assert 'x-model="importTags"' in page
    assert "submitImport" in page


def test_import_panel_states_the_honest_truths() -> None:
    page = _page()
    # ffmpeg for compressed formats; one speaker label; audio not retained;
    # local-only.
    assert "ffmpeg" in page
    assert "one speaker label" in page
    assert "audio file isn't kept" in page
    assert "stays on this machine" in page


def test_import_lifecycle_states_render_honestly() -> None:
    page = _page()
    js = _app_js()
    # The pill styles for both import states (reduced-motion-safe pulse).
    assert ".status-pill.importing" in page
    assert ".status-pill.import_failed" in page
    assert "prefers-reduced-motion" in page
    # The labels.
    assert '"Importing…"' in js
    assert '"Import failed"' in js
    # A failed import is removable (outside the card button — valid HTML).
    assert "card-remove" in page
    assert "removeMeeting" in js
    assert "/api/meetings/${meetingId}" in js


def test_history_has_the_facet_row() -> None:
    """HS-55-04: the server-side filter row composes with search."""
    page = _page()
    js = _app_js()
    assert "facet-row" in page
    assert 'x-model="facetDateFrom"' in page
    assert 'x-model="facetDateTo"' in page
    assert 'x-model="facetSpeaker"' in page
    assert 'x-model="facetTag"' in page
    assert 'x-model="facetOpenActions"' in page
    assert "clearFacets" in page
    # The query builder drives every meetings fetch (facets + search compose;
    # the quiet import poll keeps the active filters).
    assert "meetingsQuery" in js
    assert "has_open_actions" in js
    assert '"/api/meetings/facets"' in js


def test_import_behavior_markers() -> None:
    js = _app_js()
    # Multipart POST with the honest started_at_ms (File.lastModified).
    assert '"/api/meetings/import"' in js
    assert "started_at_ms" in js
    assert "lastModified" in js
    # Quiet polling only while an import is in flight.
    assert "watchImports" in js
    assert "refreshMeetingsQuiet" in js
    assert 'intel_status === "importing"' in js
