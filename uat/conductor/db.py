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

import json
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
    surface       TEXT NOT NULL,          -- legacy compatibility column
    execution_target TEXT,                -- protocol-v2 implementation identity
    form_factor   TEXT,                   -- protocol-v2 environment/device shape
    slot_id       TEXT,                   -- <target>:<form_factor>, server-derived
    device_session_id TEXT,               -- required for native Swift verdicts
    verdict       TEXT NOT NULL,          -- pass|fail|partial|observe|skip
    note          TEXT,
    shot_path     TEXT,
    started_at    TEXT,                   -- when the human landed on the step
    measurements_json TEXT NOT NULL DEFAULT '{}', -- typed raw exit measurements
    created_at    TEXT NOT NULL,          -- when the verdict was cast
    UNIQUE(run_id, pack, scenario_id, step_index, surface)
);

CREATE TABLE IF NOT EXISTS step_transitions (
    run_id        TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    pack          TEXT NOT NULL,
    scenario_id   TEXT NOT NULL,
    step_index    INTEGER NOT NULL,
    status        TEXT NOT NULL,          -- running|done|failed
    result_json   TEXT,
    error         TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    PRIMARY KEY(run_id, pack, scenario_id, step_index)
);

CREATE TABLE IF NOT EXISTS scenario_stages (
    run_id             TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    pack               TEXT NOT NULL,
    scenario_id        TEXT NOT NULL,
    status             TEXT NOT NULL,      -- running|done|failed
    result_json        TEXT,
    error              TEXT,
    manual_confirmed   INTEGER NOT NULL DEFAULT 0,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    PRIMARY KEY(run_id, pack, scenario_id)
);

CREATE TABLE IF NOT EXISTS findings (
    id             TEXT PRIMARY KEY,      -- UAT-<run>-<n>
    run_id         TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    pack           TEXT,
    scenario_id    TEXT,
    step_index     INTEGER,
    surface        TEXT,
    execution_target TEXT,
    form_factor    TEXT,
    slot_id        TEXT,
    verdict        TEXT,
    note           TEXT,
    title          TEXT,
    triage_state   TEXT NOT NULL DEFAULT 'untriaged',  -- untriaged|fix|wont-fix|by-design|duplicate
    disposition    TEXT,
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_verdicts_run ON step_verdicts(run_id);
CREATE INDEX IF NOT EXISTS idx_transitions_run ON step_transitions(run_id);
CREATE INDEX IF NOT EXISTS idx_stages_run ON scenario_stages(run_id);
CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(run_id);

CREATE TABLE IF NOT EXISTS device_sessions (
    id               TEXT PRIMARY KEY,
    sitting_id       TEXT NOT NULL REFERENCES sittings(id) ON DELETE CASCADE,
    run_id           TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    execution_target TEXT NOT NULL,
    form_factor      TEXT NOT NULL,
    device_name      TEXT NOT NULL,
    os_version       TEXT NOT NULL,
    bundle_id        TEXT NOT NULL,
    build_number     TEXT NOT NULL,
    install_source   TEXT,
    pairing_verified INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_device_sessions_sitting ON device_sessions(sitting_id);
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
            # Preserve old sittings, but mark every old verdict as explicitly
            # unqualified evidence. CREATE TABLE IF NOT EXISTS cannot add the
            # protocol-v2 columns to an existing database.
            self._ensure_column(conn, "step_verdicts", "execution_target", "TEXT")
            self._ensure_column(conn, "step_verdicts", "form_factor", "TEXT")
            self._ensure_column(conn, "step_verdicts", "slot_id", "TEXT")
            self._ensure_column(conn, "step_verdicts", "device_session_id", "TEXT")
            self._ensure_column(
                conn, "step_verdicts", "measurements_json", "TEXT NOT NULL DEFAULT '{}'"
            )
            self._ensure_column(conn, "findings", "execution_target", "TEXT")
            self._ensure_column(conn, "findings", "form_factor", "TEXT")
            self._ensure_column(conn, "findings", "slot_id", "TEXT")
            conn.execute(
                "UPDATE step_verdicts SET execution_target = 'legacy_unqualified' "
                "WHERE execution_target IS NULL"
            )
            conn.execute(
                "UPDATE step_verdicts SET form_factor = surface WHERE form_factor IS NULL"
            )
            conn.execute(
                "UPDATE step_verdicts SET slot_id = 'legacy_unqualified:' || surface "
                "WHERE slot_id IS NULL"
            )

    @staticmethod
    def _ensure_column(
        conn: sqlite3.Connection, table: str, column: str, declaration: str
    ) -> None:
        existing = {
            row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")

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
        """Upsert one exact protocol-v2 execution-slot verdict."""
        cols = (
            "run_id", "pack", "scenario_id", "step_index", "surface",
            "execution_target", "form_factor", "slot_id", "device_session_id",
            "verdict", "note", "shot_path", "started_at", "created_at",
            "measurements_json",
        )
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(
            f"{c}=excluded.{c}" for c in (
                "execution_target", "form_factor", "slot_id", "device_session_id",
                "verdict", "note", "shot_path", "created_at", "measurements_json"
            )
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
                "ORDER BY scenario_id, step_index, slot_id",
                (run_id,),
            )
            rows = []
            for raw in cur.fetchall():
                row = dict(raw)
                try:
                    row["measurements"] = json.loads(row.get("measurements_json") or "{}")
                except (TypeError, ValueError):
                    row["measurements"] = {}
                rows.append(row)
            return rows

    # --- native device attestations --------------------------------------

    def upsert_device_session(self, row: dict) -> None:
        cols = (
            "id", "sitting_id", "run_id", "execution_target", "form_factor",
            "device_name", "os_version", "bundle_id", "build_number",
            "install_source", "pairing_verified", "created_at",
        )
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(
            f"{column}=excluded.{column}"
            for column in cols
            if column not in {"id", "created_at"}
        )
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO device_sessions ({', '.join(cols)}) "
                f"VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {assignments}",
                [row.get(column) for column in cols],
            )

    def get_device_session(self, session_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM device_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_device_sessions(self, sitting_id: str) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM device_sessions WHERE sitting_id = ? "
                "ORDER BY created_at, execution_target, form_factor",
                (sitting_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    # --- step transitions -------------------------------------------------

    def upsert_step_transition(self, row: dict) -> None:
        cols = (
            "run_id", "pack", "scenario_id", "step_index", "status",
            "result_json", "error", "created_at", "updated_at",
        )
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(
            f"{column}=excluded.{column}"
            for column in ("status", "result_json", "error", "updated_at")
        )
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO step_transitions ({', '.join(cols)}) "
                f"VALUES ({placeholders}) ON CONFLICT(run_id, pack, scenario_id, step_index) "
                f"DO UPDATE SET {assignments}",
                [row.get(column) for column in cols],
            )

    def get_step_transition(
        self, run_id: str, pack: str, scenario_id: str, step_index: int
    ) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM step_transitions WHERE run_id = ? AND pack = ? "
                "AND scenario_id = ? AND step_index = ?",
                (run_id, pack, scenario_id, step_index),
            ).fetchone()
            return dict(row) if row else None

    def list_step_transitions(self, run_id: str) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM step_transitions WHERE run_id = ? "
                "ORDER BY scenario_id, step_index",
                (run_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    # --- scenario staging -------------------------------------------------

    def upsert_scenario_stage(self, row: dict) -> None:
        cols = (
            "run_id", "pack", "scenario_id", "status", "result_json",
            "error", "manual_confirmed", "created_at", "updated_at",
        )
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(
            f"{column}=excluded.{column}"
            for column in (
                "status", "result_json", "error", "manual_confirmed", "updated_at"
            )
        )
        with self.connect() as conn:
            conn.execute(
                f"INSERT INTO scenario_stages ({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(run_id, pack, scenario_id) DO UPDATE SET {assignments}",
                [row.get(column) for column in cols],
            )

    def get_scenario_stage(self, run_id: str, pack: str, scenario_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM scenario_stages WHERE run_id = ? AND pack = ? "
                "AND scenario_id = ?",
                (run_id, pack, scenario_id),
            ).fetchone()
            return dict(row) if row else None

    def list_scenario_stages(self, run_id: str) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM scenario_stages WHERE run_id = ? ORDER BY scenario_id",
                (run_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    # --- findings ---------------------------------------------------------

    def upsert_finding(self, row: dict) -> None:
        """Insert a finding, PRESERVING an existing triage_state/disposition.

        Regenerating a debrief re-derives findings; a triage the owner already
        set must survive (the disposition is the human's, not the generator's).
        """
        cols = (
            "id", "run_id", "pack", "scenario_id", "step_index", "surface",
            "execution_target", "form_factor", "slot_id",
            "verdict", "note", "title", "created_at",
        )
        placeholders = ", ".join("?" for _ in cols)
        # On conflict, refresh the derived fields but NOT triage_state/disposition.
        assignments = ", ".join(
            f"{c}=excluded.{c}" for c in ("pack", "scenario_id", "step_index",
                                          "surface", "execution_target", "form_factor",
                                          "slot_id", "verdict", "note", "title")
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

    def delete_findings_except(self, run_id: str, finding_ids: set[str]) -> None:
        """Remove findings that are no longer derived from the current verdicts.

        Verdicts are editable until a sitting is finished. If a fail is corrected
        to pass, its old triage row must not leak into a later BACKLOG block.
        """
        with self.connect() as conn:
            if not finding_ids:
                conn.execute("DELETE FROM findings WHERE run_id = ?", (run_id,))
                return
            marks = ", ".join("?" for _ in finding_ids)
            conn.execute(
                f"DELETE FROM findings WHERE run_id = ? AND id NOT IN ({marks})",
                (run_id, *sorted(finding_ids)),
            )
