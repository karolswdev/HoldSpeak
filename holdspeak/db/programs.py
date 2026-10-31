"""The Programs store (2026-10-28): five tables, static SQL only.

``programs``, ``program_steps``, ``program_checkpoints``, (PG-REQ,
2026-10-31) ``program_requirements`` and (PG-LANG, 2026-10-31) ``program_rounds``
(``holdspeak/db/schema.py``). Every write is a whole-row write of a known
column set, so each statement prepares against the schema
(``tests/unit/test_static_sql_matches_schema.py``). The rules of the states
live in ``services/program_service.py``; this module only reads and writes.
"""
from __future__ import annotations

import json
from typing import Any, Mapping, Optional

PROGRAM_COLUMNS = ('id', 'title', 'goal_markdown', 'project_id', 'repo_root', 'base_branch', 'control', 'spend_limit_usd', 'check_command', 'reviewer_profile', 'reviewer_engine', 'default_profile', 'default_engine', 'prefer_idle', 'template', 'origin_ref', 'for_person_id', 'created_by', 'state', 'note_id', 'closed_at', 'revision', 'created_at', 'updated_at', 'default_runs_on_json', 'allowed_profiles_json', 'may_handoff', 'usage_warning_share', 'may_call', 'review_depth', 'planner_engine', 'budget_tokens', 'night_json', 'within_json', 'delivery_ref', 'rounds_before_start')

STEP_COLUMNS = ('id', 'program_id', 'ordinal', 'title', 'brief_markdown', 'owns_json', 'after_json', 'profile', 'engine', 'prefer_idle', 'effort', 'race', 'race_of', 'gate_check', 'gate_review', 'review_depth', 'gate_merge', 'state', 'held_reason', 'launch_id', 'worktree', 'branch', 'head_commit', 'checked_commit', 'pr_url', 'pr_number', 'check_log', 'check_verdict', 'facts_json', 'review_verdict', 'findings_json', 'report', 'rounds', 'parked_reason', 'parked_by', 'origin_ref', 'for_person_id', 'started_at', 'ended_at', 'updated_at', 'runs_on_json', 'handoffs_json', 'may_call', 'budget_tokens')

REQUIREMENT_COLUMNS = ('id', 'program_id', 'step_id', 'ordinal', 'text', 'kind', 'required', 'spec_json', 'each_step', 'parent_id', 'state', 'judged_commit', 'evidence_json', 'waived_reason', 'rounds', 'by_kind', 'created_at', 'updated_at', 'judged_at')

#: The JSON columns and their wire keys.
_JSON_FIELDS = {"owns_json": "owns", "after_json": "after", "findings_json": "findings", "facts_json": "facts",
                "runs_on_json": "runs_on", "handoffs_json": "handoffs"}
#: The Program's JSON columns (PG19) and their wire keys.
_PROGRAM_JSON = {"default_runs_on_json": "default_runs_on", "allowed_profiles_json": "allowed_profiles",
                 "within_json": "within"}
#: PG-LANG: the Program's JSON objects (NULL: not set).
_PROGRAM_OBJECTS = {"night_json": "night"}
_DICT_FIELDS = frozenset({"facts_json"})
_FLAGS = ("prefer_idle", "gate_check", "may_call")

_PROGRAM_UPSERT = (
    "INSERT INTO programs (id, title, goal_markdown, project_id, repo_root, base_branch, "
    "control, spend_limit_usd, check_command, reviewer_profile, reviewer_engine, "
    "default_profile, default_engine, prefer_idle, template, origin_ref, for_person_id, "
    "created_by, state, note_id, closed_at, revision, created_at, updated_at, default_runs_on_json, "
    "allowed_profiles_json, may_handoff, usage_warning_share, may_call, review_depth, planner_engine, "
    "budget_tokens, night_json, within_json, delivery_ref, rounds_before_start) VALUES (?, ?, ?, "
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
    "ON CONFLICT(id) DO UPDATE "
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
    "default_runs_on_json=excluded.default_runs_on_json, allowed_profiles_json=excluded.allowed_profiles_json, "
    "may_handoff=excluded.may_handoff, usage_warning_share=excluded.usage_warning_share, may_call=excluded.may_call, "
    "review_depth=excluded.review_depth, planner_engine=excluded.planner_engine, "
    "budget_tokens=excluded.budget_tokens, night_json=excluded.night_json, within_json=excluded.within_json, "
    "delivery_ref=excluded.delivery_ref, rounds_before_start=excluded.rounds_before_start"
)

_STEP_UPSERT = (
    "INSERT INTO program_steps (id, program_id, ordinal, title, brief_markdown, owns_json, "
    "after_json, profile, engine, prefer_idle, effort, race, race_of, gate_check, gate_review, "
    "review_depth, gate_merge, state, held_reason, launch_id, worktree, branch, head_commit, "
    "checked_commit, pr_url, pr_number, check_log, check_verdict, facts_json, review_verdict, "
    "findings_json, report, rounds, parked_reason, parked_by, origin_ref, for_person_id, "
    "started_at, ended_at, updated_at, runs_on_json, handoffs_json, may_call, budget_tokens) VALUES (?, ?, ?, ?, ?, "
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
    "?, ?, ?) ON CONFLICT(id) DO "
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
    "ended_at=excluded.ended_at, updated_at=excluded.updated_at, runs_on_json=excluded.runs_on_json, "
    "handoffs_json=excluded.handoffs_json, may_call=excluded.may_call, budget_tokens=excluded.budget_tokens"
)


_REQUIREMENT_UPSERT = (
    "INSERT INTO program_requirements (id, program_id, step_id, ordinal, text, kind, required, spec_json, "
    "each_step, parent_id, state, judged_commit, evidence_json, waived_reason, rounds, by_kind, created_at, "
    "updated_at, judged_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE "
    "SET step_id=excluded.step_id, ordinal=excluded.ordinal, text=excluded.text, kind=excluded.kind, "
    "required=excluded.required, spec_json=excluded.spec_json, each_step=excluded.each_step, "
    "parent_id=excluded.parent_id, state=excluded.state, judged_commit=excluded.judged_commit, "
    "evidence_json=excluded.evidence_json, waived_reason=excluded.waived_reason, rounds=excluded.rounds, "
    "by_kind=excluded.by_kind, updated_at=excluded.updated_at, judged_at=excluded.judged_at"
)


def _requirement(row: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in REQUIREMENT_COLUMNS:
        value = row[key]
        if key in ("spec_json", "evidence_json"):
            try:
                value = json.loads(value or "{}")
            except ValueError:
                value = {}
            out[key[:-5]] = value if isinstance(value, dict) else {}
            continue
        out[key] = value
    out["required"] = bool(out["required"])
    out["each_step"] = bool(out["each_step"])
    out["by"] = out.pop("by_kind")
    return out


def _program(row: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in PROGRAM_COLUMNS:
        if key in _PROGRAM_JSON:
            try:
                value = json.loads(row[key] or "[]")
            except ValueError:
                value = []
            out[_PROGRAM_JSON[key]] = value if isinstance(value, list) else []
            continue
        if key in _PROGRAM_OBJECTS:
            try:
                value = json.loads(row[key]) if row[key] else None
            except ValueError:
                value = None
            out[_PROGRAM_OBJECTS[key]] = value if isinstance(value, dict) else None
            continue
        out[key] = row[key]
    out["prefer_idle"] = bool(out["prefer_idle"])
    out["may_handoff"] = bool(out["may_handoff"])
    out["may_call"] = bool(out["may_call"])
    out["rounds_before_start"] = bool(out["rounds_before_start"])
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
        values = [json.dumps(list(program.get(_PROGRAM_JSON[key]) or [])) if key in _PROGRAM_JSON else
                  (json.dumps(dict(program[_PROGRAM_OBJECTS[key]])) if program.get(_PROGRAM_OBJECTS[key]) else None)
                  if key in _PROGRAM_OBJECTS else program.get(key) for key in PROGRAM_COLUMNS]
        values[PROGRAM_COLUMNS.index("prefer_idle")] = 1 if program.get("prefer_idle") else 0
        values[PROGRAM_COLUMNS.index("may_handoff")] = 1 if program.get("may_handoff") else 0
        values[PROGRAM_COLUMNS.index("may_call")] = 1 if program.get("may_call") else 0
        values[PROGRAM_COLUMNS.index("rounds_before_start")] = 1 if program.get("rounds_before_start") else 0
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

    def decide_checkpoint(self, checkpoint_id: int, choice: str, undo: Mapping[str, Any]) -> None:
        """PG-REQ: his answer on a proposal row (a requirement, a step change,
        an amendment an agent proposed): its choice and its payload."""
        with self._db._connection() as conn:
            conn.execute("UPDATE program_checkpoints SET choice=?, undo_json=? WHERE id=?",
                         (choice, json.dumps(dict(undo or {})), int(checkpoint_id)))

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
                # PG16: the proposed decision record this checkpoint made.
                "decision_record_id": (undo.get("decision_record_id") or None) if isinstance(undo, dict) else None,
                # PG20: the hidden ref this checkpoint pinned the step's worktree to.
                "ref": _pin_of(undo).get("ref") or None,
                "ref_commit": _pin_of(undo).get("commit") or None,
                "pin_note": _pin_of(undo).get("note") or None,
            })
        return out


    # ── requirements (PG-REQ) ────────────────────────────────────────

    def save_requirement(self, requirement: Mapping[str, Any]) -> None:
        values: list[Any] = []
        for key in REQUIREMENT_COLUMNS:
            if key in ("spec_json", "evidence_json"):
                values.append(json.dumps(dict(requirement.get(key[:-5]) or {})))
            elif key in ("required", "each_step"):
                values.append(1 if requirement.get(key) else 0)
            elif key == "by_kind":
                values.append(requirement.get("by") or "owner")
            else:
                values.append(requirement.get(key))
        with self._db._connection() as conn:
            conn.execute(_REQUIREMENT_UPSERT, values)

    def get_requirement(self, requirement_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM program_requirements WHERE id=?", (requirement_id,)).fetchone()
        return _requirement(row) if row is not None else None

    def list_requirements(self, program_id: str) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM program_requirements WHERE program_id=? ORDER BY ordinal, step_id, id", (program_id,),
            ).fetchall()
        return [_requirement(row) for row in rows]

    def delete_requirement(self, requirement_id: str) -> None:
        """An every-step copy on a removed step (its parent stays)."""
        with self._db._connection() as conn:
            conn.execute("DELETE FROM program_requirements WHERE id=?", (requirement_id,))

    def next_requirement_ordinal(self, program_id: str) -> int:
        """R n: unique in the Program, never reused (an every-step copy
        carries its parent's number)."""
        with self._db._connection() as conn:
            row = conn.execute("SELECT MAX(ordinal) FROM program_requirements WHERE program_id=?",
                               (program_id,)).fetchone()
        return int((row[0] if row else 0) or 0) + 1


    # ── rounds (PG-LANG §6.2) ────────────────────────────────────────

    def list_rounds(self, program_id: str) -> list[dict[str, Any]]:
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT program_id, name, state, ordinal, questions_json, updated_at FROM program_rounds "
                "WHERE program_id=? ORDER BY ordinal, name", (program_id,),
            ).fetchall()
        out = []
        for row in rows:
            try:
                questions = json.loads(row["questions_json"] or "[]")
            except ValueError:
                questions = []
            out.append({"program_id": row["program_id"], "name": row["name"], "state": row["state"],
                        "ordinal": int(row["ordinal"] or 0),
                        "questions": [item for item in questions if isinstance(item, dict)] if isinstance(questions, list) else [],
                        "updated_at": row["updated_at"]})
        return out

    def save_round(self, round_: Mapping[str, Any]) -> None:
        with self._db._connection() as conn:
            conn.execute(
                "INSERT INTO program_rounds (program_id, name, state, ordinal, questions_json, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(program_id, name) DO UPDATE SET state=excluded.state, "
                "ordinal=excluded.ordinal, questions_json=excluded.questions_json, updated_at=excluded.updated_at",
                (round_["program_id"], round_["name"], round_.get("state") or "open", int(round_.get("ordinal") or 0),
                 json.dumps(list(round_.get("questions") or [])), round_["updated_at"]),
            )

    def delete_round(self, program_id: str, name: str) -> None:
        with self._db._connection() as conn:
            conn.execute("DELETE FROM program_rounds WHERE program_id=? AND name=?", (program_id, name))


def _pin_of(undo: Any) -> dict[str, Any]:
    pin = undo.get("pin") if isinstance(undo, dict) else None
    return pin if isinstance(pin, dict) else {}


__all__ = ["PROGRAM_COLUMNS", "REQUIREMENT_COLUMNS", "STEP_COLUMNS", "ProgramStore"]
