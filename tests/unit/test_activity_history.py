"""Unit tests for browser history activity readers."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from holdspeak.activity_history import (
    BrowserHistorySource,
    _copy_sqlite_snapshot,
    discover_browser_history_sources,
    import_browser_history,
    import_firefox_history,
    import_safari_history,
)
from holdspeak.db import MeetingDatabase


def _create_safari_history(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE history_items (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                visit_count INTEGER NOT NULL
            );
            CREATE TABLE history_visits (
                id INTEGER PRIMARY KEY,
                history_item INTEGER NOT NULL,
                visit_time REAL NOT NULL,
                title TEXT,
                load_successful BOOLEAN NOT NULL DEFAULT 1
            );
            """
        )
        conn.execute(
            "INSERT INTO history_items (id, url, visit_count) VALUES (?, ?, ?)",
            (1, "https://example.atlassian.net/browse/HS-803", 2),
        )
        conn.execute(
            "INSERT INTO history_visits (history_item, visit_time, title, load_successful) VALUES (?, ?, ?, ?)",
            (1, 799_200_000.0, "HS-803 activity reader", 1),
        )
        conn.execute(
            "INSERT INTO history_visits (history_item, visit_time, title, load_successful) VALUES (?, ?, ?, ?)",
            (1, 799_203_600.0, "HS-803 activity reader", 1),
        )
        conn.execute(
            "INSERT INTO history_items (id, url, visit_count) VALUES (?, ?, ?)",
            (2, "file:///Users/example/private.txt", 1),
        )
        conn.execute(
            "INSERT INTO history_visits (history_item, visit_time, title, load_successful) VALUES (?, ?, ?, ?)",
            (2, 799_203_700.0, "Local file", 1),
        )
        conn.commit()
    finally:
        conn.close()


def _create_firefox_history(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE moz_places (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT,
                visit_count INTEGER
            );
            CREATE TABLE moz_historyvisits (
                id INTEGER PRIMARY KEY,
                place_id INTEGER NOT NULL,
                visit_date INTEGER NOT NULL
            );
            """
        )
        conn.execute(
            "INSERT INTO moz_places (id, url, title, visit_count) VALUES (?, ?, ?, ?)",
            (1, "https://miro.com/app/board/uXjVTestBoard/", "Miro board", 4),
        )
        conn.execute(
            "INSERT INTO moz_historyvisits (place_id, visit_date) VALUES (?, ?)",
            (1, 1_745_665_200_000_000),
        )
        conn.execute(
            "INSERT INTO moz_historyvisits (place_id, visit_date) VALUES (?, ?)",
            (1, 1_745_668_800_000_000),
        )
        conn.commit()
    finally:
        conn.close()


def test_discover_browser_history_sources_defaults_readable_sources_enabled(tmp_path):
    safari_path = tmp_path / "Library" / "Safari" / "History.db"
    firefox_path = (
        tmp_path
        / "Library"
        / "Application Support"
        / "Firefox"
        / "Profiles"
        / "abcd.default-release"
        / "places.sqlite"
    )
    _create_safari_history(safari_path)
    _create_firefox_history(firefox_path)

    sources = discover_browser_history_sources(tmp_path)

    assert [(source.source_browser, source.source_profile, source.enabled) for source in sources] == [
        ("safari", "default", True),
        ("firefox", "abcd.default-release", True),
    ]


def test_copy_sqlite_snapshot_includes_wal_and_shm_companions(tmp_path):
    source = tmp_path / "History.db"
    source.write_text("main", encoding="utf-8")
    source.with_name("History.db-wal").write_text("wal", encoding="utf-8")
    source.with_name("History.db-shm").write_text("shm", encoding="utf-8")
    destination = tmp_path / "snapshot"

    copied = _copy_sqlite_snapshot(source, destination)

    assert copied.read_text(encoding="utf-8") == "main"
    assert copied.with_name("History.db-wal").read_text(encoding="utf-8") == "wal"
    assert copied.with_name("History.db-shm").read_text(encoding="utf-8") == "shm"


def test_import_safari_history_fixture_persists_activity_and_checkpoint(tmp_path):
    history_path = tmp_path / "History.db"
    _create_safari_history(history_path)
    db = MeetingDatabase(tmp_path / "holdspeak.db")

    result = import_safari_history(
        BrowserHistorySource("safari", "default", history_path),
        db=db,
    )

    assert result.error is None
    assert result.imported_count == 1
    assert result.checkpoint_raw == "799203600.0"
    records = db.list_activity_records(source_browser="safari")
    assert len(records) == 1
    assert records[0].url == "https://example.atlassian.net/browse/HS-803"
    assert records[0].title == "HS-803 activity reader"
    assert records[0].visit_count == 2
    assert records[0].entity_type == "jira_ticket"
    assert records[0].entity_id == "HS-803"
    assert records[0].first_seen_at == datetime(2026, 4, 30, 0, 0)
    assert records[0].last_visit_raw == "799203600.0"

    checkpoint = db.get_activity_import_checkpoint(
        source_browser="safari",
        source_profile="default",
        source_path_hash=result.source_path_hash,
    )
    assert checkpoint is not None
    assert checkpoint.last_visit_raw == "799203600.0"
    assert checkpoint.enabled is True


def test_import_firefox_history_fixture_persists_activity_and_checkpoint(tmp_path):
    places_path = tmp_path / "places.sqlite"
    _create_firefox_history(places_path)
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    db.update_activity_privacy_settings(retention_days=3650)

    result = import_firefox_history(
        BrowserHistorySource("firefox", "work", places_path),
        db=db,
    )

    assert result.error is None
    assert result.imported_count == 1
    assert result.checkpoint_raw == "1745668800000000"
    records = db.list_activity_records(source_browser="firefox")
    assert len(records) == 1
    assert records[0].url == "https://miro.com/app/board/uXjVTestBoard/"
    assert records[0].normalized_url == "https://miro.com/app/board/uXjVTestBoard"
    assert records[0].title == "Miro board"
    assert records[0].visit_count == 4
    assert records[0].entity_type == "miro_board"
    assert records[0].entity_id == "uXjVTestBoard"
    assert records[0].last_seen_at == datetime(2025, 4, 26, 12, 0)
    assert records[0].last_visit_raw == "1745668800000000"


def test_import_browser_history_uses_checkpoints_to_skip_reimport_churn(tmp_path):
    history_path = tmp_path / "History.db"
    _create_safari_history(history_path)
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    source = BrowserHistorySource("safari", "default", history_path)

    first_result = import_browser_history(db=db, sources=[source])[0]
    second_result = import_browser_history(db=db, sources=[source])[0]

    assert first_result.imported_count == 1
    assert second_result.imported_count == 0
    assert second_result.checkpoint_raw == "799203600.0"
    assert len(db.list_activity_records(source_browser="safari")) == 1


def test_import_browser_history_respects_global_pause(tmp_path):
    history_path = tmp_path / "History.db"
    _create_safari_history(history_path)
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    db.update_activity_privacy_settings(enabled=False)

    result = import_safari_history(
        BrowserHistorySource("safari", "default", history_path),
        db=db,
    )

    assert result.enabled is False
    assert result.imported_count == 0
    assert db.list_activity_records() == []


def test_import_browser_history_respects_excluded_domains(tmp_path):
    history_path = tmp_path / "History.db"
    _create_safari_history(history_path)
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    db.upsert_activity_domain_rule(domain="example.atlassian.net", action="exclude")

    result = import_safari_history(
        BrowserHistorySource("safari", "default", history_path),
        db=db,
    )

    assert result.enabled is True
    assert result.imported_count == 0
    assert result.checkpoint_raw == "799203600.0"
    assert db.list_activity_records() == []
