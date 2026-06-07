"""doctor + config honesty (HS-50-04).

doctor must report the database's real schema state (current / older / newer /
unreadable / absent) and flag a config written by a newer build. Config must
carry a `config_version` and coerce an older shape forward without dropping
fields, while flagging a newer one.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from holdspeak.commands import doctor
from holdspeak.config import CONFIG_VERSION, Config
from holdspeak.db import SCHEMA_VERSION, Database, reset_database


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Path:
    reset_database()
    path = tmp_path / "holdspeak.db"

    # Point the doctor database check at this throwaway DB.
    import holdspeak.db as db_pkg

    monkeypatch.setattr(db_pkg, "DEFAULT_DB_PATH", path)
    yield path
    reset_database()


def _stamp(path: Path, version: int) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()
    conn.close()


def test_database_check_absent_is_pass(db_path: Path) -> None:
    assert not db_path.exists()
    check = doctor._check_database()
    assert check.status == "PASS"
    assert "created on first use" in check.detail


def test_database_check_current_is_pass(db_path: Path) -> None:
    Database(db_path)
    check = doctor._check_database()
    assert check.status == "PASS"
    assert f"version {SCHEMA_VERSION}" in check.detail


def test_database_check_newer_is_fail(db_path: Path) -> None:
    Database(db_path)
    _stamp(db_path, SCHEMA_VERSION + 1)
    check = doctor._check_database()
    assert check.status == "FAIL"
    assert "newer than this build" in check.detail
    assert check.fix


def test_database_check_unreadable_is_warn(db_path: Path) -> None:
    db_path.write_text("not a sqlite database at all")
    check = doctor._check_database()
    assert check.status == "WARN"


# --- config_version ---


def test_config_default_carries_current_version() -> None:
    assert Config().config_version == CONFIG_VERSION


def test_config_roundtrips_version(tmp_path) -> None:
    path = tmp_path / "config.json"
    Config().save(path)
    on_disk = json.loads(path.read_text())
    assert on_disk["config_version"] == CONFIG_VERSION
    assert Config.load(path).config_version == CONFIG_VERSION


def test_config_without_version_is_coerced_forward(tmp_path) -> None:
    path = tmp_path / "config.json"
    # A pre-versioning config: real keys, no config_version, plus a retired key.
    path.write_text(json.dumps({"hotkey": {"key": "f13"}, "retired_key": 1}))
    config = Config.load(path)
    assert config.config_version == CONFIG_VERSION
    # The known field survived the coercion (no whole-config reset).
    assert config.hotkey.key == "f13"


def test_config_newer_version_is_kept_and_flagged(tmp_path, caplog) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"config_version": CONFIG_VERSION + 5, "hotkey": {"key": "f14"}}))
    with caplog.at_level("WARNING"):
        config = Config.load(path)
    # The newer value is preserved (honest), data is still loaded, and it warned.
    assert config.config_version == CONFIG_VERSION + 5
    assert config.hotkey.key == "f14"
    assert any("newer than this build" in r.message for r in caplog.records)


def test_doctor_config_check_flags_newer_config(tmp_path, monkeypatch) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"config_version": CONFIG_VERSION + 1}))
    monkeypatch.setattr(doctor, "CONFIG_FILE", path)
    # _check_config imports CONFIG_VERSION and loads CONFIG_FILE via Config.load();
    # point both at the temp file.
    monkeypatch.setattr("holdspeak.config.CONFIG_FILE", path)
    check, _ = doctor._check_config()
    assert check.status == "WARN"
    assert "newer than this build" in check.detail
