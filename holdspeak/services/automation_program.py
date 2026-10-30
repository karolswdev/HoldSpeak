"""Programs PG14: an automation runs a Program (RECIPE PG14, design §9b).

The Do kind ``run_program``: each run (Run now, a schedule, a Watch event)
makes one Program from the automation's template and Project, sets its
control level and Runs on, starts it, and leaves one result that links the
Program. While the last Program it made still runs, a run starts nothing and
says so.

- **From the desk** takes the automation's Project and one step per open
  action (``ProgramService.plan_from_project``).
- Every other template takes the automation's instruction as the goal and
  one step per source item (the source is the step's origin), or one step
  from the instruction when there are no sources.

The Program's ``origin_ref`` is ``automation:<workbench id>``; its place line
reads "From the automation <name>".
"""
from __future__ import annotations

from holdspeak.db.models import _json_list

from datetime import datetime
from typing import Any, Mapping, Optional

from .errors import ValidationError

#: The Program states in which a run starts nothing.
STILL_RUNNING = frozenset({"running", "waiting"})
ORIGIN_KIND = "automation"
_PROFILE_ALIASES = {"claude": "claude-default", "claude-code": "claude-default", "codex": "codex-default",
                    "pi": "pi-default"}


def origin_of(workbench_id: str) -> str:
    return f"{ORIGIN_KIND}:{workbench_id}"


def _programs(db: Any) -> Any:
    # Looked up at call time: tests hand the runner their own service.
    from . import program_service

    return program_service.default_program_service(db)


# ── configuration ─────────────────────────────────────────────────────


def clean_program_fields(fields: dict[str, Any]) -> None:
    """Validate the PG14 fields in place (template, control, Runs on, flags)."""
    from ..program_templates import TEMPLATE_IDS
    from .program_rules import DESK_MODES
    from .program_service import AGENT_LABELS, MAX_RUNS_ON

    if "program_template" in fields:
        template = str(fields["program_template"] or "").strip().lower()
        if template and template not in TEMPLATE_IDS:
            raise ValidationError(f"program_template is one of: {', '.join(TEMPLATE_IDS)}")
        fields["program_template"] = template
    if "program_control" in fields:
        raw = str(fields["program_control"] or "").strip().lower()
        control = DESK_MODES.get(raw, "") if raw else ""
        if raw and control not in ("secure", "normal", "yolo"):
            raise ValidationError("program_control is secure, normal or yolo")
        fields["program_control"] = control
    if "program_runs_on" in fields:
        raw_list = fields["program_runs_on"]
        if raw_list in (None, ""):
            raw_list = []
        if isinstance(raw_list, (str, Mapping)):
            raw_list = [raw_list]
        if not isinstance(raw_list, (list, tuple)):
            raise ValidationError("program_runs_on is a list of agents")
        out: list[dict[str, Any]] = []
        for index, entry in enumerate(raw_list, start=1):
            if isinstance(entry, str):
                profile, engine = entry, None
            elif isinstance(entry, Mapping):
                profile, engine = entry.get("profile"), entry.get("engine")
            else:
                raise ValidationError(f"program_runs_on {index}: an agent is a name or {{profile, engine}}")
            profile = str(profile or "").strip()
            profile = _PROFILE_ALIASES.get(profile.lower(), profile)
            if profile not in AGENT_LABELS:
                raise ValidationError(f"program_runs_on {index}: there is no agent {profile!r}")
            engine = str(engine or "").strip() or None
            if engine and profile != "pi-default":
                raise ValidationError(f"program_runs_on {index}: an engine is for pi only")
            row = {"profile": profile, "engine": engine}
            if row not in out:
                out.append(row)
        if len(out) > MAX_RUNS_ON:
            raise ValidationError(f"program_runs_on: at most {MAX_RUNS_ON} agents")
        fields["program_runs_on"] = out
    for flag in ("program_may_call", "program_may_handoff"):
        if flag in fields:
            if fields[flag] is not None and not isinstance(fields[flag], bool):
                raise ValidationError(f"{flag} is true or false")
            fields[flag] = bool(fields[flag])


def automation_project(db: Any, wb: Any) -> Optional[str]:
    """The automation's Project: its first ``project:<id>`` source, else the
    Project its results go to (``project_updates:<id>``)."""
    from .automation_runs import PROJECT_UPDATES_PREFIX, sources_of

    for ref in sources_of(wb):
        kind, _, ident = str(ref).partition(":")
        if kind == "project" and ident.strip():
            return ident.strip()
    target = str(getattr(wb, "output_target", "") or "")
    if target.startswith(PROJECT_UPDATES_PREFIX):
        return target[len(PROJECT_UPDATES_PREFIX):].strip() or None
    return None


def runs_on_of(wb: Any) -> list[dict[str, Any]]:
    rows = _json_list(wb.program_runs_on_json)
    return [dict(row) for row in rows if isinstance(row, Mapping) and row.get("profile")]


def latest_program(db: Any, workbench_id: str) -> Optional[dict[str, Any]]:
    """The newest Program this automation made, as the Programs list reads it."""
    with db._connection() as conn:
        row = conn.execute(
            "SELECT id FROM programs WHERE origin_ref=? ORDER BY created_at DESC, id DESC LIMIT 1",
            (origin_of(workbench_id),),
        ).fetchone()
    if row is None:
        return None
    service = _programs(db)
    program = service.store.get_program(str(row["id"]))
    if program is None:
        return None
    return service._summary(program, service.store.list_steps(program["id"]))


def program_payload(db: Any, wb: Any) -> dict[str, Any]:
    """What the automation window shows of a run_program automation."""
    from ..program_templates import get_template
    from .program_rules import level_word

    template = str(getattr(wb, "program_template", "") or "")
    shape = get_template(template) or {}
    defaults = dict(shape.get("program") or {})
    control = str(getattr(wb, "program_control", "") or "") or str(defaults.get("control") or "")
    rows = runs_on_of(wb) or ([{"profile": defaults["default_profile"], "engine": defaults.get("default_engine")}]
                              if defaults.get("default_profile") else [])
    labels: list[dict[str, Any]] = []
    try:
        service = _programs(db)
        labels = [service.entry_wire(row) for row in rows]
    except Exception:
        labels = [{"profile": row["profile"], "engine": row.get("engine"), "label": row["profile"]} for row in rows]
    latest = None
    try:
        latest = latest_program(db, wb.id)
    except Exception:
        latest = None
    return {
        "template": template or None,
        "template_name": str(shape.get("name") or "") or None,
        "control": control or None,
        "control_word": level_word(control) if control else None,
        "runs_on": labels,
        "runs_on_words": " · then ".join(str(row.get("label") or "") for row in labels),
        "own_runs_on": bool(runs_on_of(wb)),
        "may_call": bool(getattr(wb, "program_may_call", False)),
        "may_handoff": bool(getattr(wb, "program_may_handoff", False)),
        "project_id": automation_project(db, wb),
        "latest": {
            "id": latest["id"], "title": latest["title"], "state": latest["state"],
            "state_word": latest["state_word"], "window": f"pullout:program:{latest['id']}",
        } if latest else None,
    }


# ── a run ─────────────────────────────────────────────────────────────


def _day_words(now: Optional[datetime] = None) -> str:
    moment = now or datetime.now().astimezone()
    return f"{moment.strftime('%a')} {moment.day} {moment.strftime('%b')}"


def _first_line(text: str) -> str:
    line = next((row.strip() for row in str(text or "").splitlines() if row.strip()), "")
    return line.lstrip("#-* ").strip()[:120]


def goal_steps(db: Any, wb: Any) -> list[dict[str, Any]]:
    """The steps of a goal template: one per source item, else one from the
    instruction. Each source step names its source as its origin."""
    from .automation_runs import hand_sources

    instruction = str(getattr(wb, "instruction", "") or "").strip()
    steps = []
    for source in hand_sources(db, wb):
        title = str(source.get("title") or source["id"])[:120]
        brief = f"{instruction}\n\nThe item: {title}" if instruction else title
        steps.append({"title": title, "brief": brief, "origin_ref": source["ref"]})
    if steps:
        return steps
    if instruction:
        return [{"title": _first_line(instruction) or str(getattr(wb, "name", "") or "Step"), "brief": instruction}]
    return []


def run_program(db: Any, principal: Any, wb: Any, *, now: Optional[datetime] = None) -> dict[str, Any]:
    """Make, plan and start one Program for this run.

    The answer: ``started`` (bool), ``program_id``, ``title``, ``steps``,
    ``window``; a run that starts nothing has ``reason`` in words. A refusal
    (no template, no repository, no open action) raises ``ServiceError``."""
    from ..program_templates import FROM_THE_DESK
    from .program_service import ProgramRefused

    latest = latest_program(db, wb.id)
    if latest is not None and latest["state"] in STILL_RUNNING:
        return {
            "started": False, "program_id": latest["id"], "title": latest["title"],
            "window": f"pullout:program:{latest['id']}",
            "reason": f"The program {latest['title']} is still running. Nothing started.",
        }
    template = str(getattr(wb, "program_template", "") or "")
    if not template:
        raise ProgramRefused("program_template_required", "Choose a template under Do.", status=400)
    project_id = automation_project(db, wb)
    service = _programs(db)
    if template == FROM_THE_DESK:
        if not project_id:
            raise ProgramRefused("project_required", "From the desk needs a project: add one under About.")
        actions = [item for item in db.projects.get_project_action_items(project_id)
                   if str(getattr(item, "status", "open") or "open") in ("open", "pending", "")]
        if not actions:
            raise ProgramRefused("no_open_actions", "The project has no open action. Nothing started.")
        steps: list[dict[str, Any]] = []
    else:
        steps = goal_steps(db, wb)
        if not steps:
            raise ProgramRefused("steps_required", "Say what the program should do under Do.", status=400)
    from .automation_runs import work_folder_of

    runs_on = runs_on_of(wb)
    title = f"{str(getattr(wb, 'name', '') or 'Automation').strip()} · {_day_words(now)}"
    made = service.create(
        principal, title=title, goal=str(getattr(wb, "instruction", "") or ""),
        repository=work_folder_of(wb), project_id=project_id, template=template,
        control=str(getattr(wb, "program_control", "") or "") or None,
        runs_on=runs_on or None,
        may_call=bool(getattr(wb, "program_may_call", False)),
        may_handoff=bool(getattr(wb, "program_may_handoff", False)),
        origin_ref=origin_of(wb.id),
    )
    program_id = made["id"]
    if template == FROM_THE_DESK:
        planned = service.plan_from_project(principal, program_id)
    else:
        planned = service.plan(principal, program_id, steps=steps)
    service.start(principal, program_id)
    return {
        "started": True, "program_id": program_id, "title": title,
        "steps": len(planned.get("steps") or []), "window": f"pullout:program:{program_id}",
    }


def result_words(answer: Mapping[str, Any]) -> str:
    """The result's one line: what the run started."""
    count = int(answer.get("steps") or 0)
    return f"Started the program {answer['title']} · {count} step{'s' if count != 1 else ''}"


__all__ = [
    "ORIGIN_KIND", "STILL_RUNNING", "automation_project", "clean_program_fields", "goal_steps",
    "latest_program", "origin_of", "program_payload", "result_words", "run_program", "runs_on_of",
]
