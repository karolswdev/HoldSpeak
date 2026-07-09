"""The run database — one sqlite file for every sitting the rig ever ran.

Schema lands here in HSU-1-01: **runs** (a booted, isolated HoldSpeak),
**scenario_executions** (a scenario walked inside a run), **step_verdicts**
(the per-(step, surface) human verdicts — the point of the whole rig), and
**findings** (a non-pass verdict promoted for triage). Verdict *writes*
land in HSU-1-04; the debrief reads ``findings`` in HSU-1-05. Defining the
whole shape now keeps later stories migration-free.

One connection per call (``check_same_thread`` is moot); WAL so the guided
site can read while a verdict writes.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from . import paths

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id            TEXT PRIMARY KEY,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    status        TEXT NOT NULL,          -- pending|booting|up|down|failed
    deck          TEXT,                   -- deck name, or NULL for an inline overlay
    config_json   TEXT,                   -- the raw overlay the run booted with
    product_host  TEXT,
    product_port  INTEGER,
    lan           INTEGER NOT NULL DEFAULT 0,
    pairing_url   TEXT,
    token         TEXT,                   -- the run's own per-HOME web auth token
    pid           INTEGER,
    error         TEXT                    -- failure summary + log tail when status=failed
);

CREATE TABLE IF NOT EXISTS sittings (
    id           TEXT PRIMARY KEY,
    run_id       TEXT REFERENCES runs(id) ON DELETE SET NULL,
    pack         TEXT NOT NULL,
    deck         TEXT,
    status       TEXT NOT NULL DEFAULT 'staging',   -- staging|walking|done|aborted
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    finished_at  TEXT
);

CREATE TABLE IF NOT EXISTS scenario_executions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    pack         TEXT NOT NULL,
    scenario_id  TEXT NOT NULL,
    title        TEXT,
    started_at   TEXT,
    ended_at     TEXT,
    status       TEXT NOT NULL DEFAULT 'pending',   -- pending|active|done|aborted
    UNIQUE(run_id, pack, scenario_id)
);

CREATE TABLE IF NOT EXISTS step_verdicts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    pack          TEXT NOT NULL,
    scenario_id   TEXT NOT NULL,
    step_index    INTEGER NOT NULL,
    surface       TEXT NOT NULL,          -- web|ipad|iphone
    verdict       TEXT NOT NULL,          -- pass|fail|partial|skip
    note          TEXT,
    shot_path     TEXT,
    started_at    TEXT,                   -- when the human landed on the step
    created_at    TEXT NOT NULL,          -- when the verdict was cast
    UNIQUE(run_id, pack, scenario_id, step_index, surface)
);

CREATE TABLE IF NOT EXISTS findings (
    id             TEXT PRIMARY KEY,      -- UAT-<run>-<n>
    run_id         TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    pack           TEXT,
    scenario_id    TEXT,
    step_index     INTEGER,
    surface        TEXT,
    verdict        TEXT,
    note           TEXT,
    title          TEXT,
    triage_state   TEXT NOT NULL DEFAULT 'untriaged',  -- untriaged|fix|wont-fix|by-design|duplicate
    disposition    TEXT,
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_verdicts_run ON step_verdicts(run_id);
CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(run_id);
"""


class Database:
    """Thin sqlite wrapper: connection-per-call, schema on init."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else paths.db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(_SCHEMA)

    # --- runs -------------------------------------------------------------

    def upsert_run(self, row: dict) -> None:
        cols = (
            "id", "created_at", "updated_at", "status", "deck", "config_json",
            "product_host", "product_port", "lan", "pairing_url", "token",
            "pid", "error",
        )
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "id")
        values = [row.get(c) for c in cols]
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO runs ({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {assignments}",
                values,
            )

    def get_run(self, run_id: str) -> dict | None:
        with self.connect() as conn:
            cur = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_runs(self) -> list[dict]:
        with self.connect() as conn:
            cur = conn.execute("SELECT * FROM runs ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

    def delete_run(self, run_id: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))

    # --- sittings ---------------------------------------------------------

    def upsert_sitting(self, row: dict) -> None:
        cols = ("id", "run_id", "pack", "deck", "status", "created_at", "updated_at", "finished_at")
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "id")
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO sittings ({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {assignments}",
                [row.get(c) for c in cols],
            )

    def get_sitting(self, sitting_id: str) -> dict | None:
        with self.connect() as conn:
            cur = conn.execute("SELECT * FROM sittings WHERE id = ?", (sitting_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_sittings(self) -> list[dict]:
        with self.connect() as conn:
            cur = conn.execute("SELECT * FROM sittings ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

    # --- verdicts ---------------------------------------------------------

    def cast_verdict(self, row: dict) -> None:
        """Upsert one (run, pack, scenario, step, surface) verdict — the moment cast."""
        cols = (
            "run_id", "pack", "scenario_id", "step_index", "surface",
            "verdict", "note", "shot_path", "started_at", "created_at",
        )
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(
            f"{c}=excluded.{c}" for c in ("verdict", "note", "shot_path", "created_at")
        )
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO step_verdicts ({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(run_id, pack, scenario_id, step_index, surface) "
                f"DO UPDATE SET {assignments}",
                [row.get(c) for c in cols],
            )

    def list_verdicts(self, run_id: str) -> list[dict]:
        with self.connect() as conn:
            cur = conn.execute(
                "SELECT * FROM step_verdicts WHERE run_id = ? "
                "ORDER BY scenario_id, step_index, surface",
                (run_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    # --- findings ---------------------------------------------------------

    def upsert_finding(self, row: dict) -> None:
        """Insert a finding, PRESERVING an existing triage_state/disposition.

        Regenerating a debrief re-derives findings; a triage the owner already
        set must survive (the disposition is the human's, not the generator's).
        """
        cols = (
            "id", "run_id", "pack", "scenario_id", "step_index", "surface",
            "verdict", "note", "title", "created_at",
        )
        placeholders = ", ".join("?" for _ in cols)
        # On conflict, refresh the derived fields but NOT triage_state/disposition.
        assignments = ", ".join(
            f"{c}=excluded.{c}" for c in ("pack", "scenario_id", "step_index",
                                          "surface", "verdict", "note", "title")
        )
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO findings ({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {assignments}",
                [row.get(c) for c in cols],
            )

    def get_finding(self, finding_id: str) -> dict | None:
        with self.connect() as conn:
            cur = conn.execute("SELECT * FROM findings WHERE id = ?", (finding_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def set_triage(self, finding_id: str, triage_state: str, disposition: str | None) -> bool:
        with self.connect() as conn:
            cur = conn.execute(
                "UPDATE findings SET triage_state = ?, disposition = ? WHERE id = ?",
                (triage_state, disposition, finding_id),
            )
            return cur.rowcount > 0

    def list_findings(self, run_id: str) -> list[dict]:
        with self.connect() as conn:
            cur = conn.execute(
                "SELECT * FROM findings WHERE run_id = ? ORDER BY id", (run_id,)
            )
            return [dict(r) for r in cur.fetchall()]
