"""HS-45-02: integration tests for the dictation journal routes + surface.

`GET /api/dictation/journal` lists rows newest-first (paged, source-filterable);
`DELETE …/{id}` and `DELETE …/journal` curate/wipe — all over the durable
`DictationJournalRepository` the server's recorder is backed by. Plus a
page-content check that the Journal tab + its surface (timeline host, search,
filters, latency strip, the local-only trust statement) ship in `/dictation`.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.db import Database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def test_client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        )
    )
    return TestClient(server.app)


@pytest.fixture
def persistent_db():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "journal.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _persistent_client(database: Database) -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    return TestClient(server.app)


def _seed(db: Database, **kw):
    base = dict(source="dictation", transcript="t", final_text="f")
    base.update(kw)
    return db.dictation_journal.record(**base)


# ── list ──────────────────────────────────────────────────────────────

def test_journal_empty_by_default(test_client: TestClient, settings_path: Path) -> None:
    body = test_client.get("/api/dictation/journal").json()
    assert body["enabled"] is True  # journal defaults ON
    assert body["count"] == 0
    assert body["items"] == []
    assert body["retention"] == 500


def test_journal_lists_rows_newest_first(persistent_db: Database, settings_path: Path) -> None:
    _seed(persistent_db, transcript="one", final_text="1", block_id="b1", confidence=0.7,
          stage_ms={"intent-router": 5.0, "project-rewriter": 50.0}, total_ms=55.0)
    _seed(persistent_db, source="dry_run", transcript="two", final_text="2")
    client = _persistent_client(persistent_db)
    body = client.get("/api/dictation/journal").json()
    assert body["count"] == 2
    assert [i["transcript"] for i in body["items"]] == ["two", "one"]
    first = body["items"][1]
    assert first["block_id"] == "b1"
    assert first["confidence"] == pytest.approx(0.7)
    assert first["stage_ms"] == {"intent-router": 5.0, "project-rewriter": 50.0}
    assert first["corrected"] is False


def test_journal_source_filter_and_limit(persistent_db: Database, settings_path: Path) -> None:
    _seed(persistent_db, source="dictation", transcript="spoken")
    _seed(persistent_db, source="dry_run", transcript="dry")
    client = _persistent_client(persistent_db)
    only_dry = client.get("/api/dictation/journal?source=dry_run").json()
    assert [i["transcript"] for i in only_dry["items"]] == ["dry"]
    limited = client.get("/api/dictation/journal?limit=1").json()
    assert len(limited["items"]) == 1


# ── curate ──────────────────────────────────────────────────────────────

def test_delete_one_entry(persistent_db: Database, settings_path: Path) -> None:
    rec = _seed(persistent_db, transcript="gone")
    _seed(persistent_db, transcript="kept")
    client = _persistent_client(persistent_db)
    resp = client.request("DELETE", f"/api/dictation/journal/{rec.id}")
    assert resp.status_code == 200
    assert resp.json()["removed"] is True
    assert persistent_db.dictation_journal.count() == 1
    again = client.request("DELETE", f"/api/dictation/journal/{rec.id}")
    assert again.status_code == 404


def test_clear_journal(persistent_db: Database, settings_path: Path) -> None:
    _seed(persistent_db, transcript="a")
    _seed(persistent_db, transcript="b")
    client = _persistent_client(persistent_db)
    resp = client.request("DELETE", "/api/dictation/journal")
    assert resp.status_code == 200
    assert resp.json()["removed"] == 2
    assert persistent_db.dictation_journal.count() == 0


def test_delete_without_repo_404s(test_client: TestClient, settings_path: Path) -> None:
    # A bare server has no durable journal — delete is a 404, never a 500.
    assert test_client.request("DELETE", "/api/dictation/journal/1").status_code == 404
    assert test_client.request("DELETE", "/api/dictation/journal").status_code == 404


# ── page content ─────────────────────────────────────────────────────────

def test_dictation_page_includes_journal_tab(test_client: TestClient) -> None:
    body = test_client.get("/dictation").text
    assert 'data-section="journal"' in body
    assert 'id="view-journal"' in body
    assert 'id="journal-list"' in body
    assert 'id="journal-search"' in body
    assert 'id="journal-filter-source"' in body
    assert 'id="journal-btn-clear"' in body
    # the local-only trust statement is first-class on the surface
    assert 'id="journal-trust"' in body
    assert "only on this machine" in body


def test_dictation_journal_premium_and_a11y_markers(test_client: TestClient) -> None:
    """The Journal carries the Phase-44 bar + a11y (markup present in the HTML;
    JS-rendered cards / linked-stylesheet classes are exercised live)."""
    body = test_client.get("/dictation").text
    # reduced-motion guard is in the inlined critical CSS
    assert "prefers-reduced-motion" in body
    # the trust note + its glyph + the search/filter controls are static markup
    assert 'class="journal-trust"' in body
    assert 'id="journal-filter-corrected"' in body
    assert "journal-trust-glyph" in body
    # warm empty-state copy + the said→typed framing live in the JS bundle
    built = (
        Path(__file__).resolve().parents[2]
        / "holdspeak" / "static" / "_built" / "dictation" / "index.html"
    )
    if built.exists():
        css = list(built.parent.parent.glob("_astro/dictation*.css"))
        joined = "\n".join(p.read_text() for p in css)
        assert "lat-strip" in joined  # the per-utterance latency strip
        assert "journal-card" in joined
        # REGRESSION GUARD: the journal/moment/replay DOM is injected by
        # dictation-app.js at runtime, so its CSS MUST be global. Astro scopes
        # `.journal-card { }` to `.journal-card[data-astro-cid-…]`, which never
        # matches runtime-injected elements — that left the whole surface
        # rendering naked. Keep these rules in a `<style is:global>` block.
        assert ".journal-card{" in joined.replace(" ", ""), (
            "journal styles must be global (is:global) — scoped CSS does not "
            "apply to the JS-injected journal cards"
        )
        assert "journal-card[data-astro-cid" not in joined, (
            "journal-card is scoped — it will NOT style the runtime-injected "
            "cards. Move these rules into <style is:global>."
        )
