"""The Programs store (2026-10-28): three tables, static SQL only.

``programs``, ``program_steps`` and ``program_checkpoints``
(``holdspeak/db/schema.py``). Every write is a whole-row write of a known
column set, so each statement prepares against the schema
(``tests/unit/test_static_sql_matches_schema.py``). The rules of the states
live in ``services/program_service.py``; this module only reads and writes.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Optional

PROGRAM_COLUMNS = ('id', 'title', 'goal_markdown', 'project_id', 'repo_root', 'base_branch', 'control', 'spend_limit_usd', 'check_command', 'reviewer_profile', 'reviewer_engine', 'default_profile', 'default_engine', 'prefer_idle', 'template', 'origin_ref', 'for_person_id', 'created_by', 'state', 'note_id', 'closed_at', 'revision', 'created_at', 'updated_at', 'may_call')

STEP_COLUMNS = ('id', 'program_id', 'ordinal', 'title', 'brief_markdown', 'owns_json', 'after_json', 'profile', 'engine', 'prefer_idle', 'effort', 'race', 'race_of', 'gate_check', 'gate_review', 'review_depth', 'gate_merge', 'state', 'held_reason', 'launch_id', 'worktree', 'branch', 'head_commit', 'checked_commit', 'pr_url', 'pr_number', 'check_log', 'check_verdict', 'facts_json', 'review_verdict', 'findings_json', 'report', 'rounds', 'parked_reason', 'parked_by', 'origin_ref', 'for_person_id', 'started_at', 'ended_at', 'updated_at', 'may_call')

#: The JSON columns and their wire keys.
_JSON_FIELDS = {"owns_json": "owns", "after_json": "after", "findings_json": "findings", "facts_json": "facts"}
_DICT_FIELDS = frozenset({"facts_json"})
_FLAGS = ("prefer_idle", "gate_check", "may_call")

_PROGRAM_UPSERT = (
    "INSERT INTO programs (id, title, goal_markdown, project_id, repo_root, base_branch, "
    "control, spend_limit_usd, check_command, reviewer_profile, reviewer_engine, "
    "default_profile, default_engine, prefer_idle, template, origin_ref, for_person_id, "
    "created_by, state, note_id, closed_at, revision, created_at, updated_at, may_call) VALUES (?, ?, ?, "
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE "
    "SET title=excluded.title, goal_markdown=excluded.goal_markdown, "
    "project_id=excluded.project_id, repo_root=excluded.repo_root, "
    "base_branch=excluded.base_branch, control=excluded.control, "
    "spend_limit_usd=excluded.spend_limit_usd, check_command=excluded.check_command, "
    "reviewer_profile=excluded.reviewer_profile, reviewer_engine=excluded.reviewer_engine, "
    "default_profile=excluded.default_profile, default_engine=excluded.default_engine, "
    "prefer_idle=excluded.prefer_idle, template=excluded.template, "
    "origin_ref=excluded.origin_ref, for_person_id=excluded.for_person_id, "
    "created_by=excluded.created_by, state=excluded.state, note_id=excluded.note_id, "
    "closed_at=excluded.closed_at, revision=excluded.revision, updated_at=excluded.updated_at, "
    "may_call=excluded.may_call"
)

_STEP_UPSERT = (
    "INSERT INTO program_steps (id, program_id, ordinal, title, brief_markdown, owns_json, "
    "after_json, profile, engine, prefer_idle, effort, race, race_of, gate_check, gate_review, "
    "review_depth, gate_merge, state, held_reason, launch_id, worktree, branch, head_commit, "
    "checked_commit, pr_url, pr_number, check_log, check_verdict, facts_json, review_verdict, "
    "findings_json, report, rounds, parked_reason, parked_by, origin_ref, for_person_id, "
    "started_at, ended_at, updated_at, may_call) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO "
    "UPDATE SET ordinal=excluded.ordinal, title=excluded.title, "
    "brief_markdown=excluded.brief_markdown, owns_json=excluded.owns_json, "
    "after_json=excluded.after_json, profile=excluded.profile, engine=excluded.engine, "
    "prefer_idle=excluded.prefer_idle, effort=excluded.effort, race=excluded.race, "
    "race_of=excluded.race_of, gate_check=excluded.gate_check, "
    "gate_review=excluded.gate_review, review_depth=excluded.review_depth, "
    "gate_merge=excluded.gate_merge, state=excluded.state, held_reason=excluded.held_reason, "
    "launch_id=excluded.launch_id, worktree=excluded.worktree, branch=excluded.branch, "
    "head_commit=excluded.head_commit, checked_commit=excluded.checked_commit, "
    "pr_url=excluded.pr_url, pr_number=excluded.pr_number, check_log=excluded.check_log, "
    "check_verdict=excluded.check_verdict, facts_json=excluded.facts_json, "
    "review_verdict=excluded.review_verdict, findings_json=excluded.findings_json, "
    "report=excluded.report, rounds=excluded.rounds, parked_reason=excluded.parked_reason, "
    "parked_by=excluded.parked_by, origin_ref=excluded.origin_ref, "
    "for_person_id=excluded.for_person_id, started_at=excluded.started_at, "
    "ended_at=excluded.ended_at, updated_at=excluded.updated_at, may_call=excluded.may_call"
)


def _program(row: Any) -> dict[str, Any]:
    out = {key: row[key] for key in PROGRAM_COLUMNS}
    out["prefer_idle"] = bool(out["prefer_idle"])
    out["may_call"] = bool(out["may_call"])
    return out


def _step(row: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in STEP_COLUMNS:
        value = row[key]
        if key in _JSON_FIELDS:
            try:
                value = json.loads(value or ("{}" if key in _DICT_FIELDS else "[]"))
            except ValueError:
                value = {} if key in _DICT_FIELDS else []
            out[_JSON_FIELDS[key]] = value
            continue
        out[key] = value
    for flag in _FLAGS:
        out[flag] = bool(out[flag])
    return out


class ProgramStore:
    """Reads and whole-row writes of the three Program tables."""

    def __init__(self, db: Any) -> None:
        self._db = db

    # ── programs ─────────────────────────────────────────────────────

    def save_program(self, program: Mapping[str, Any]) -> None:
        values = [program.get(key) for key in PROGRAM_COLUMNS]
        values[PROGRAM_COLUMNS.index("prefer_idle")] = 1 if program.get("prefer_idle") else 0
        values[PROGRAM_COLUMNS.index("may_call")] = 1 if program.get("may_call") else 0
        with self._db._connection() as conn:
            conn.execute(_PROGRAM_UPSERT, values)

    def get_program(self, program_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM programs WHERE id=?", (program_id,)).fetchone()
        return _program(row) if row is not None else None

    def list_programs(self) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute("SELECT * FROM programs ORDER BY updated_at DESC, id").fetchall()
        return [_program(row) for row in rows]

    # ── steps ────────────────────────────────────────────────────────

    def save_step(self, step: Mapping[str, Any]) -> None:
        values: list[Any] = []
        for key in STEP_COLUMNS:
            if key in _JSON_FIELDS:
                values.append(json.dumps(step.get(_JSON_FIELDS[key]) or ({} if key in _DICT_FIELDS else [])))
            elif key in _FLAGS:
                values.append(1 if step.get(key) else 0)
            else:
                values.append(step.get(key))
        with self._db._connection() as conn:
            conn.execute(_STEP_UPSERT, values)

    def get_step(self, step_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM program_steps WHERE id=?", (step_id,)).fetchone()
        return _step(row) if row is not None else None

    def list_steps(self, program_id: str) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM program_steps WHERE program_id=? ORDER BY ordinal, race_of, id", (program_id,),
            ).fetchall()
        return [_step(row) for row in rows]

    def delete_step(self, step_id: str) -> None:
        with self._db._connection() as conn:
            conn.execute("DELETE FROM program_steps WHERE id=?", (step_id,))

    def step_of_launch(self, launch_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM program_steps WHERE launch_id=?", (launch_id,)).fetchone()
        return _step(row) if row is not None else None

    def file_to_project(self, project_id: str, resource_ref: str, now: str) -> None:
        """File a desk object (the handover note, a Later task) to a Project."""
        with self._db._connection() as conn:
            conn.execute(
                "INSERT INTO project_resources (project_id, resource_ref, relationship, source, confidence, "
                "created_at, last_modified, deleted) VALUES (?, ?, 'member', 'program', 1, ?, ?, 0) "
                "ON CONFLICT(project_id, resource_ref) DO UPDATE SET deleted=0, last_modified=excluded.last_modified",
                (project_id, resource_ref, now, now),
            )

    # ── checkpoints ──────────────────────────────────────────────────

    def add_checkpoint(
        self, *, step_id: str, program_id: str, at: str, by: str, line: str,
        operation_id: Optional[str] = None, kind: Optional[str] = None, choice: Optional[str] = None,
        rule: Optional[str] = None, overturnable: bool = False, undo: Optional[Mapping[str, Any]] = None,
    ) -> int:
        """One checkpoint line; with ``rule`` it is also an engine decision
        ("Decided for you")."""
        with self._db._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO program_checkpoints (step_id, program_id, at, by_kind, line, operation_id, kind, "
                "choice, rule, overturnable, undo_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (step_id, program_id, at, by, line, operation_id, kind, choice, rule, 1 if overturnable else 0,
                 json.dumps(dict(undo or {}))),
            )
            return int(cursor.lastrowid or 0)

    def mark_overturned(self, checkpoint_id: int, at: str) -> None:
        with self._db._connection() as conn:
            conn.execute("UPDATE program_checkpoints SET overturned_at=?, overturnable=0 WHERE id=?",
                         (at, int(checkpoint_id)))

    def list_checkpoints(self, program_id: str) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT id, step_id, at, by_kind, line, operation_id, kind, choice, rule, overturnable, "
                "overturned_at, undo_json FROM program_checkpoints WHERE program_id=? ORDER BY id DESC",
                (program_id,),
            ).fetchall()
        out = []
        for row in rows:
            try:
                undo = json.loads(row["undo_json"] or "{}")
            except ValueError:
                undo = {}
            out.append({
                "id": int(row["id"]), "step_id": row["step_id"], "at": row["at"], "by": row["by_kind"],
                "line": row["line"], "operation_id": row["operation_id"], "kind": row["kind"],
                "choice": row["choice"], "rule": row["rule"], "overturnable": bool(row["overturnable"]),
                "overturned_at": row["overturned_at"], "undo": undo,
            })
        return out


__all__ = ["PROGRAM_COLUMNS", "STEP_COLUMNS", "ProgramStore"]
