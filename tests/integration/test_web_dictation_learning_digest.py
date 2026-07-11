"""HS-48-01: integration tests for the learning-digest route + surface.

`GET /api/dictation/learning-digest?window=week|all` aggregates the durable
journal + correction stores into honest, windowed counts. A bare server (no
durable repos) returns an empty, zeroed digest rather than an error. Plus a
page-content check that the "What HoldSpeak learned" view ships in `/dictation`.
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
def bare_client() -> TestClient:
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
    database = Database(temp_dir / "learn.db")
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


# ── digest endpoint ───────────────────────────────────────────────────────

def test_bare_server_returns_empty_digest(bare_client: TestClient, settings_path: Path) -> None:
    body = bare_client.get("/api/dictation/learning-digest").json()
    assert body["window"] == "week"
    assert body["totals"]["corrections_made"] == 0
    assert body["totals"]["similar_nudged"] == 0
    assert body["corrections"] == []


def test_digest_counts_real_corrections_and_reach(persistent_db: Database, settings_path: Path) -> None:
    # A correction whose gist clearly overlaps two journal transcripts.
    persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="follow up with sam about the launch", value="action_item"
    )
    persistent_db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about the launch checklist",
        final_text="x",
    )
    persistent_db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about launch", final_text="y",
    )
    persistent_db.dictation_journal.record(
        source="dictation", transcript="remind me to water the plants", final_text="z",
    )
    client = _persistent_client(persistent_db)
    body = client.get("/api/dictation/learning-digest?window=all").json()
    assert body["totals"]["corrections_made"] == 1
    assert body["by_kind"]["intent"] == 1
    assert body["by_block"] == [{"block_id": "action_item", "count": 1}]
    # The two near-duplicate transcripts are within reach; the unrelated one is not.
    assert body["corrections"][0]["similar"] == 2
    assert body["totals"]["similar_nudged"] == 2


def test_digest_marks_corrected_dictations(persistent_db: Database, settings_path: Path) -> None:
    rec = persistent_db.dictation_journal.record(
        source="dictation", transcript="ship it", final_text="ship it",
    )
    persistent_db.dictation_journal.mark_corrected(rec.id)
    client = _persistent_client(persistent_db)
    body = client.get("/api/dictation/learning-digest?window=all").json()
    assert body["totals"]["dictations_corrected"] == 1


def test_digest_reports_corrections_enabled_posture(persistent_db: Database, settings_path: Path) -> None:
    body = _persistent_client(persistent_db).get("/api/dictation/learning-digest").json()
    # Off by default; the flag is honest about whether corrections actually route.
    assert body["enabled"] is False


# ── page content ──────────────────────────────────────────────────────────

def test_dictation_page_includes_learning_digest(bare_client: TestClient) -> None:
    assert '<div id="root"></div>' in bare_client.get("/dictation").text
    source = (Path(__file__).resolve().parents[2] / "web/src/pages/DictationPage.tsx").read_text()
    assert "Learning digest" in source
    assert "/api/dictation/learning-digest" in source


def test_learning_digest_styles_are_global(bare_client: TestClient) -> None:
    """The digest is React-owned and composes the shared status primitives."""
    source = (Path(__file__).resolve().parents[2] / "web/src/pages/DictationPage.tsx").read_text()
    assert "Learning digest" in source and "StatusPill" in source
    assert "dangerouslySetInnerHTML" not in source
