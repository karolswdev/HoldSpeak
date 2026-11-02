"""The control level for one agent launch (Programs PG13, design §6).

A launch that belongs to a Program's step follows the Program's own control
(``programs.control``: ``secure`` · ``normal`` · ``yolo``); every other
launch follows the desk's Control mode (``Config.control_mode``), as
before. The desk's answers (``AgentResponder``) and the tool gate
(``kernel/tool_call``) read the level here, never the desk's mode directly,
so a Program at YOLO on a Secure desk gets YOLO's answers for its own
agents, and a Program at Secure on a YOLO desk waits for him.

What the engine decided for him at that level (a routine answer typed, a
held call allowed) is recorded as a Decided-for-you line on the Program
(:func:`record_decision`: a ``program.checkpoint`` by the engine, with its
rule).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("services.control_level")

#: The ladder word -> the desk's Control mode word (``Config.control_mode``).
DESK_WORDS = {"secure": "safe", "normal": "neutral", "yolo": "yolo"}


def _desk_mode() -> str:
    from ..config import Config

    try:
        return str(Config.load().control_mode or "yolo")
    except Exception:
        return "yolo"


def _db_or_default(db: Any) -> Any:
    if db is not None:
        return db
    from ..db import get_database
    from ..runtime import composition

    return composition.db_or(get_database)


def step_of_launch(launch_id: Any, *, db: Any = None) -> Optional[tuple[dict[str, Any], dict[str, Any]]]:
    """``(program, step)`` when ``launch_id`` is a Program step's launch,
    else ``None`` (no id, no step, or no Programs store on this database)."""
    launch_id = str(launch_id or "").strip()
    if not launch_id:
        return None
    try:
        from ..db.programs import ProgramStore

        store = ProgramStore(_db_or_default(db))
        step = store.step_of_launch(launch_id)
        if not isinstance(step, dict) or not step.get("program_id"):
            return None
        program = store.get_program(str(step["program_id"]))
        if not isinstance(program, dict):
            return None
        return program, step
    except Exception:
        return None


#: The ladder, narrowest first.
_ORDER = {"secure": 0, "normal": 1, "yolo": 2}


def _narrower(one: str, other: str) -> str:
    return one if _ORDER.get(one, 0) <= _ORDER.get(other, 0) else other


def _helper_record(launch_id: str, ledger: Any = None) -> Optional[Mapping[str, Any]]:
    """The launch record of a helper (it names ``helper_of``), else None."""
    try:
        if ledger is None:
            from ..delivery.factory_launch import LaunchLedger

            ledger = LaunchLedger()
        record = ledger.get(launch_id) or {}
    except Exception:
        return None
    return record if isinstance(record, Mapping) and str(record.get("helper_of") or "").strip() else None


def _launch_level(launch_id: Any, *, db: Any, desk: Optional[Callable[[], Any]], ledger: Any,
                  depth: int = 0) -> Optional[str]:
    """The level of a step's launch (its Program's control) or of a helper
    (never wider than the launch that started it, nor than the level it was
    started at: IMP4 by precedent, Astra's post-merge check 2026-11-01);
    None for any other launch (the desk decides)."""
    from .program_rules import level_of

    found = step_of_launch(launch_id, db=db)
    if found is not None:
        return level_of(found[0].get("control"))
    record = _helper_record(str(launch_id or "").strip(), ledger) if launch_id and depth < 8 else None
    if record is None:
        return None
    parent = _launch_level(record.get("helper_of"), db=db, desk=desk, ledger=ledger, depth=depth + 1)
    if parent is None:
        parent = level_of((desk or _desk_mode)() or "yolo")
    started = str(record.get("control_mode") or "").strip()
    return _narrower(parent, level_of(started)) if started else parent


def level_for_launch(
    launch_id: Any, *, db: Any = None, desk: Optional[Callable[[], Any]] = None, ledger: Any = None,
) -> str:
    """``secure`` · ``normal`` · ``yolo``: the Program's control when the
    launch belongs to a step; a helper's starter's level (never wider);
    else the desk's Control mode on the ladder."""
    from .program_rules import level_of

    found = _launch_level(launch_id, db=db, desk=desk, ledger=ledger)
    if found is not None:
        return found
    return level_of((desk or _desk_mode)() or "yolo")


def mode_for_launch(
    launch_id: Any, *, db: Any = None, desk: Optional[Callable[[], Any]] = None, ledger: Any = None,
) -> str:
    """The same level as the desk's Control mode word (``safe`` ·
    ``neutral`` · ``yolo``), for the readers that speak it. A launch that is
    neither a step nor a helper gets the desk's own word back unchanged."""
    found = _launch_level(launch_id, db=db, desk=desk, ledger=ledger)
    if found is None:
        return str((desk or _desk_mode)() or "yolo").lower()
    return DESK_WORDS[found]


def program_of_step(step_id: Any, *, db: Any = None) -> Optional[dict[str, Any]]:
    """The Program of a step id, else ``None``."""
    step_id = str(step_id or "").strip()
    if not step_id:
        return None
    try:
        from ..db.programs import ProgramStore

        store = ProgramStore(_db_or_default(db))
        step = store.get_step(step_id)
        if not isinstance(step, dict) or not step.get("program_id"):
            return None
        program = store.get_program(str(step["program_id"]))
        return program if isinstance(program, dict) else None
    except Exception:
        return None


def mode_for_request(
    request: Any, *, db: Any = None, desk: Optional[Callable[[], Any]] = None,
) -> str:
    """The desk's Control mode word a NEW launch runs at (PG13b), read from
    the server-side request the hand builds, before the launch has an id on
    its step: a helper (``helper_of``) inherits its parent launch's level; a
    Program step's launch (``origin_ref`` ``program_step``) runs at its
    Program's control; every other launch at the desk's Control mode."""
    request = request if isinstance(request, Mapping) else {}
    helper_of = str(request.get("helper_of") or "").strip()
    if helper_of:
        return mode_for_launch(helper_of, db=db, desk=desk)
    origin = request.get("origin_ref") if isinstance(request.get("origin_ref"), Mapping) else {}
    if str(origin.get("kind") or "") == "program_step":
        program = program_of_step(origin.get("id"), db=db)
        if program is not None:
            from .program_rules import level_of

            return DESK_WORDS[level_of(program.get("control"))]
    return str((desk or _desk_mode)() or "yolo").lower()


def record_decision(
    launch_id: Any, kind: str, line: str, *, facts: Optional[Mapping[str, Any]] = None,
    db: Any = None, dedupe: bool = False, detail: str = "",
) -> Optional[dict[str, Any]]:
    """One Decided-for-you line on the step's Program (``kind``
    ``agent_question`` or ``gate_approval``), with the §6 rule of its level.
    ``dedupe``: the same line under the same rule on the same step is kept
    once (a YOLO agent runs many allowed calls of one tool). ``None`` for a
    launch that is not a step, or when the rule sends it to him."""
    found = step_of_launch(launch_id, db=db)
    if found is None:
        return None
    program, step = found
    from .program_rules import decide

    outcome = decide(program.get("control"), kind, dict(facts or {}))
    if outcome.to_owner:
        return None
    try:
        from .program_service import default_program_service

        service = default_program_service(_db_or_default(db))
        if dedupe and any(
            row.get("step_id") == step["id"] and row.get("line") == line and row.get("rule") == outcome.rule
            for row in service.decided_for_you(program["id"])
        ):
            return None
        row = service.engine_decision(program, step, kind, outcome, line, undo={"detail": detail} if detail else None)
        service.changed(program["id"], step["id"], verb="decided")
        return row
    except Exception as exc:
        log.warning(f"program decision not recorded for launch {launch_id}: {exc}")
        return None


__all__ = [
    "DESK_WORDS", "level_for_launch", "mode_for_launch", "mode_for_request", "program_of_step",
    "record_decision", "step_of_launch",
]
