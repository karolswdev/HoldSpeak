"""Isolated-HOME assembly, deck overlay writing, and the run DB schema."""

from __future__ import annotations

import json

from uat.conductor import home as home_mod
from uat.conductor.db import Database


def test_assemble_home_creates_skeleton(tmp_path):
    home = tmp_path / "home"
    home_mod.assemble_home(home, link_caches=False)
    assert (home / ".config" / "holdspeak").is_dir()
    assert (home / ".local" / "share" / "holdspeak").is_dir()
    assert (home / ".cache").is_dir()
    # Idempotent: a second call does not raise.
    home_mod.assemble_home(home, link_caches=False)


def test_assemble_home_links_caches(tmp_path, monkeypatch):
    real_home = tmp_path / "real"
    (real_home / ".cache" / "huggingface").mkdir(parents=True)
    (real_home / "Models").mkdir(parents=True)
    monkeypatch.setenv("UAT_REAL_HOME", str(real_home))
    home = tmp_path / "home"
    home_mod.assemble_home(home, link_caches=True)
    assert (home / ".cache" / "huggingface").is_symlink()
    assert (home / "Models").is_symlink()


def test_write_config_defaults_version_and_roundtrips(tmp_path):
    home = tmp_path / "home"
    home_mod.assemble_home(home, link_caches=False)
    path = home_mod.write_config(home, {"model": {"warm_on_start": False}})
    data = json.loads(path.read_text())
    assert data["config_version"] == 1
    assert data["model"]["warm_on_start"] is False
    assert home_mod.read_config(home) == data


def test_db_schema_tables_exist(tmp_path):
    db = Database(tmp_path / "uat.db")
    with db.connect() as conn:
        names = {
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert {"runs", "scenario_executions", "step_verdicts", "findings"} <= names


def test_db_run_upsert_roundtrip(tmp_path):
    db = Database(tmp_path / "uat.db")
    row = {
        "id": "run-x",
        "created_at": "t0",
        "updated_at": "t0",
        "status": "up",
        "deck": "golden-local",
        "config_json": "{}",
        "product_host": "127.0.0.1",
        "product_port": 8788,
        "lan": 0,
        "pairing_url": "http://127.0.0.1:8788",
        "token": None,
        "pid": 123,
        "error": None,
    }
    db.upsert_run(row)
    got = db.get_run("run-x")
    assert got["status"] == "up"
    assert got["deck"] == "golden-local"
    # Upsert updates in place, no duplicate row.
    row["status"] = "down"
    db.upsert_run(row)
    assert db.get_run("run-x")["status"] == "down"
    assert len(db.list_runs()) == 1
