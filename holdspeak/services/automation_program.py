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


def _hand_control(wb: Any) -> str:
    """A hand keeps the desk's authority; its own setting may narrow it."""
    from ..config import Config
    from .program_rules import DESK_MODES, LEVELS

    try:
        desk = DESK_MODES.get(str(Config.load().control_mode or "").strip().lower(), "secure")
    except Exception:
        desk = "secure"
    requested = DESK_MODES.get(str(wb.program_control or "").strip().lower(), desk)
    return min((desk, requested), key=LEVELS.index)


def _programs(db: Any) -> Any:
    # Looked up at call time: tests hand the runner their own service.
    from . import program_service

    return program_service.default_program_service(db)


# ── configuration ─────────────────────────────────────────────────────


def clean_program_fields(fields: dict[str, Any]) -> None:
    """Validate the PG14 fields in place (template, control, Runs on, flags)."""
    from ..program_templates import TEMPLATE_IDS
    from .program_rules import DESK_MODES
    from .program_definitions import AGENT_LABELS, MAX_RUNS_ON

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
    return _programs(db).summary_record(str(row["id"]))


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


def run_program(
    db: Any, principal: Any, wb: Any, *, now: Optional[datetime] = None,
    item_ids: list[str] | None = None, key: str | None = None,
) -> dict[str, Any]:
    """Make, plan and start one Program for this run.

    The answer: ``started`` (bool), ``program_id``, ``title``, ``steps``,
    ``window``; a run that starts nothing has ``reason`` in words. A refusal
    (no template, no repository, no open action) raises ``ServiceError``."""
    from ..program_templates import FROM_THE_DESK
    from .program_definitions import ProgramRefused

    from ..db.programs import ProgramStore
    from .automation_runs import program_runs

    store = ProgramStore(db)
    if key:
        for program in program_runs(db, wb.id):
            steps = store.list_steps(program["id"])
            if any((step.get("facts") or {}).get("run_key") == key for step in steps):
                return {"started": False, "program_id": program["id"], "title": program["title"],
                        "window": f"pullout:program:{program['id']}", "reason": "This start was already recorded."}
    latest = latest_program(db, wb.id)
    if latest is not None and latest["state"] in STILL_RUNNING:
        return {
            "started": False, "program_id": latest["id"], "title": latest["title"],
            "window": f"pullout:program:{latest['id']}",
            "reason": f"The program {latest['title']} is still running. Nothing started.",
        }
    hand = str(getattr(wb, "do_kind", "")) == "hand_to_agent"
    template = "" if hand else str(getattr(wb, "program_template", "") or "")
    control = effective_authority(db, principal, wb)["material"]["control"]
    if not template and not hand:
        raise ProgramRefused("program_template_required", "Choose a template under Do.", status=400)
    project_id = automation_project(db, wb)
    service = _programs(db)
    if hand:
        from .agent_hand_service import project_for_item
        from .automation_runs import _hand_context, hand_item_id, hand_sources

        sources = hand_sources(db, wb)
        if item_ids is not None:
            sources = [source for source in sources if hand_item_id(wb.id, source["ref"]) in item_ids]
        prior = {step.get("origin_ref") for program in program_runs(db, wb.id)
                 if program["state"] != "drafting" for step in store.list_steps(program["id"])}
        # Pre-fold hands may still be queued or running. Never hand one again.
        for source in sources:
            item = db.workbench_items.get(hand_item_id(wb.id, source["ref"]), include_parked=True)
            claim = _hand_context(item).get("agent_hand") or {}
            if item and (item.status in {"claimed", "done", "failed"}
                         or claim.get("status") in {"starting", "queued", "launched", "done", "failed"}
                         or claim.get("launch_id") or claim.get("queue_id")):
                prior.add(source["ref"])
        sources = [source for source in sources if source["ref"] not in prior]
        if not sources and latest is not None:
            return {"started": False, "program_id": latest["id"], "title": latest["title"],
                    "reason": "No new source items. Nothing started."}
        projects = {project_for_item(db, source["kind"], source["id"]) for source in sources}
        projects.discard(None)
        projects.discard("")
        if len(projects) > 1 or (project_id and projects and projects != {project_id}):
            raise ProgramRefused("different_projects", "Use one automation for each project's agent work.")
        project_id = project_id or next(iter(projects), None)
        from .agent_brief import compose_agent_brief

        steps = [{"title": source["title"], "origin_ref": source["ref"],
                  "brief": compose_agent_brief(
                      db, source["ref"], project_id=project_id, instruction=wb.instruction,
                      control_mode=control, principal=principal)["text"],
                  "gate_review": "agent" if wb.review_by not in ("", "none") else "none"}
                 for source in sources]
        if not steps:
            raise ProgramRefused("steps_required", "Add an item under About first.", status=400)
    elif template == FROM_THE_DESK:
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
    from .automation_runs import checked_work_folder

    repository = checked_work_folder(service, wb, project_id=project_id)

    runs_on = runs_on_of(wb)
    title = f"{str(getattr(wb, 'name', '') or 'Automation').strip()} · {_day_words(now)}"
    made = service.create(
        principal, title=title, goal=str(getattr(wb, "instruction", "") or ""),
        repository=repository, project_id=project_id, template=template or None,
        default_profile=(str(wb.agent_profile or "") or None) if hand else None,
        reviewer_profile=_PROFILE_ALIASES.get(str(wb.review_by), str(wb.review_by)) if hand and wb.review_by not in ("", "none") else None,
        control=control,
        runs_on=runs_on or None,
        may_call=bool(getattr(wb, "program_may_call", False)),
        may_handoff=bool(getattr(wb, "program_may_handoff", False)),
        origin_ref=origin_of(wb.id),
        plan_goal=False,  # the run writes its own steps and starts at once
    )
    program_id = made["id"]
    if template == FROM_THE_DESK:
        planned = service.plan_from_project(principal, program_id)
    else:
        planned = service.plan(principal, program_id, steps=steps)
    if key or hand:
        for step in store.list_steps(program_id):
            step["facts"] = {**(step.get("facts") or {}), **({"run_key": key} if key else {}),
                             **({"automation_target": str(wb.output_target or "inbox")} if hand else {})}
            store.save_step(step)
    from .held_authority import program_authority
    service.start(principal, program_id, expected_authority=program_authority(service.store.get_program(program_id)))
    return {
        "started": True, "program_id": program_id, "title": title,
        "steps": len(planned.get("steps") or []), "window": f"pullout:program:{program_id}",
    }


def deliver_finished_hands(service: Any, program: Mapping[str, Any], steps: list[dict[str, Any]]) -> None:
    """A finished agent step uses the prompt step's result delivery, once."""
    from .program_prompt import _deliver, _finished_notice
    from .program_service import _LOCK

    candidates = [step for step in steps if (step.get("facts") or {}).get("automation_target")
                  and step["state"] in {"merged", "done"} and not (step.get("facts") or {}).get("delivered")]
    if not candidates:
        return
    with _LOCK:
        for candidate in candidates:
            step = service.store.get_step(candidate["id"]) or candidate
            facts = dict(step.get("facts") or {})
            target = facts.get("automation_target")
            if (not target or step["state"] not in {"merged", "done"}
                    or facts.get("delivered")):
                continue
            result = _deliver(service, program, step, str(target), str(step.get("report") or ""),
                              [str(step["origin_ref"])] if step.get("origin_ref") else [])
            step["facts"] = {**facts, "delivered": result}
            service.store.save_step(step)
            candidate.update(step)
            _finished_notice(service.db, program)



def result_words(answer: Mapping[str, Any]) -> str:
    """The result's one line: what the run started."""
    count = int(answer.get("steps") or 0)
    return f"Started the program {answer['title']} · {count} step{'s' if count != 1 else ''}"


def start_automation(
    db: Any, principal: Any, wb: Any, *, request_id: str | None = None,
    source_event: dict[str, Any] | None = None, item_ids: list[str] | None = None,
    expected_authority: Any = None,
) -> dict[str, Any]:
    """Translate an Automation definition to Programs; never execute its items here."""
    from ..principals import PrincipalKind
    from .errors import ServiceError
    from . import automation_runs, engine_door
    from .program_prompt import JOB

    from .held_authority import check_authority
    if principal is None or principal.kind is PrincipalKind.NONE:
        raise ServiceError("principal_authentication_required", "Sign in first.", context={"status": 401})
    if principal.kind is PrincipalKind.SCHEDULER:
        raise ServiceError("schedule_delegation_required", "A scheduled start needs its live owner delegation.",
                           context={"status": 409})
    if expected_authority is not None:
        check_authority(expected_authority, effective_authority(db, principal, wb))
    kind = str(wb.do_kind or "run")
    if kind in {"hand_to_agent", "run_program"}:
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can start this agent program.",
                               context={"status": 403})
        # The Program service's existing lock serializes definition-to-Program
        # creation with its state writes. A double press adopts the active run.
        from .program_service import _LOCK

        with _LOCK:
            ran = run_program(db, principal, wb, item_ids=item_ids, key=f"request:{request_id}" if request_id else None)
        return {**ran, "run_id": ran["program_id"], "program_started": ran["started"],
                "skipped": not ran["started"], "status": "running"}
    if item_ids:
        raise ServiceError("set_up_as_program", "Programs run this queue now: set it up as a program.",
                           context={"status": 409})
    if not automation_runs.runs_as_program(wb) and not source_event:
        if automation_runs.effective_instruction(db, wb)[1] == "agent":
            raise ServiceError("set_up_as_program", "Programs run this queue now: set it up as a program.",
                               context={"status": 409})
        return {"error": f"The automation {wb.name} has nothing to do yet: write what it should do."}
    from ..kernel.runtime import _service

    try:
        engine_door.engine_for(_service(), JOB, subject=("workbench", str(wb.id)))
    except engine_door.EngineDoorError as exc:
        raise ServiceError("no_assignment", exc.detail, context={"status": 409}) from None
    ran = automation_runs.run_as_program(
        db, principal, wb, wait=True, event=source_event,
        key=f"request:{request_id}" if request_id else None,
    )
    delivered = automation_runs.program_delivery(db, ran["program_id"])
    return {**ran, **({"deliveries": [delivered]} if delivered else {})}


def start_scheduled(db: Any, principal: Any, wb: Any, *, due_minute: int | None = None) -> dict[str, Any]:
    """Keep the local schedule's admission and deduplication, then start a Program.

    The parent records authority for this start only. The Program owns all
    running work and its history; no workbench_runs row is made.
    """
    import time
    from ..principals import Principal, PrincipalKind
    from ..kernel.runtime import _configure
    from .errors import ServiceError
    from .schedule_delegation import ScheduleDelegationService

    if principal.kind is not PrincipalKind.SCHEDULER:
        raise ServiceError("scheduler_principal_required", "Scheduler principal required", context={"status": 403})
    minute = int(time.time() // 60 if due_minute is None else due_minute)
    controller = _configure(db).parent_run_controller
    snapshot = {"workbench_id": wb.id, "due_minute": minute}
    terms = dict(definition_ref=f"workbench:{wb.id}", definition_revision=str(wb.last_modified),
                 deadline_at=time.time() + 600, idempotency_key=f"schedule:{wb.id}:{minute}")
    try:
        delegation = ScheduleDelegationService(db).validate(wb.id)
    except ServiceError as exc:
        controller.record_delegated_refusal(principal, input_snapshot=snapshot, child_budget=0,
                                           reason=exc.code, **terms)
        raise
    # Prompt schedules already have a durable Program run key. Preserve
    # their replay (including the frozen delivery) without a second parent.
    from . import automation_runs

    if automation_runs.runs_as_program(wb):
        return automation_runs.run_as_program(db, principal, wb, wait=True, key=f"schedule:{minute}")
    snapshot.update({"delegation_id": delegation["id"], "terms_sha256": delegation["terms_sha256"],
                     "delegator_kind": delegation["delegator_kind"],
                     "delegator_identity": delegation["delegator_identity"],
                     "deployment_revision_id": delegation["deployment_revision_id"],
                     **({"do_kind": wb.do_kind, "agent_profile": wb.agent_profile, "review_by": wb.review_by}
                        if wb.do_kind == "hand_to_agent" else {"do_kind": wb.do_kind,
                        "program_template": wb.program_template, "program_control": wb.program_control,
                        "program_runs_on": _json_list(wb.program_runs_on_json)})})
    parent = controller.start_delegated_schedule(principal, input_snapshot=snapshot, child_budget=1, **terms)
    try:
        answer = start_automation(db, Principal(PrincipalKind.OWNER, "local-automation-conductor"), wb,
                                  request_id=f"schedule:{minute}")
    except Exception:
        controller.close(parent.context, "failed", principal=principal)
        raise
    receipt = controller.close(parent.context, "succeeded", f"program:{answer.get('program_id', '')}", principal=principal)
    return {**answer, "parent_operation_id": parent.operation_id,
            "receipt_id": receipt["receipt_id"], "terminal_disposition": receipt["outcome"]}


__all__ = [
    "ORIGIN_KIND", "STILL_RUNNING", "automation_project", "clean_program_fields", "goal_steps",
    "latest_program", "origin_of", "program_payload", "result_words", "run_program", "runs_on_of",
    "start_automation", "start_scheduled",
]


def effective_authority(db: Any, principal: Any, wb: Any) -> dict[str, Any]:
    """The exact definition-to-Program Control fallback used by Run now."""
    from ..program_templates import get_template
    from .held_authority import program_authority
    from .automation_runs import checked_work_folder
    service = _programs(db)
    kind = str(wb.do_kind or 'run')
    hand = kind == 'hand_to_agent'
    template = '' if hand else str(getattr(wb, 'program_template', '') or '')
    defaults = dict((get_template(template) or {}).get('program') or {}) if template else {}
    raw = _hand_control(wb) if hand else (str(wb.program_control or '') or None)
    control, _ = service.effective_control(principal, raw if kind != 'run' else 'yolo', defaults)
    project_id = automation_project(db, wb)
    root = checked_work_folder(service, wb, project_id=project_id)
    program = {'control': control, 'repo_root': root, 'default_profile': str(wb.agent_profile or defaults.get('default_profile') or 'claude-default'),
        'allowed_profiles': [], 'may_call': bool(wb.program_may_call), 'may_handoff': bool(wb.program_may_handoff),
        'spend_limit_usd': wb.spend_limit_usd}
    authority = program_authority(program)
    authority['material'].update(workbench_id=wb.id, definition={key: getattr(wb, key, None) for key in
        ('do_kind', 'instruction', 'source_refs_json', 'output_target', 'agent_profile', 'review_by', 'program_template',
         'program_control', 'program_runs_on_json', 'program_may_call', 'program_may_handoff', 'work_folder')}, template=defaults)
    if kind == 'run':
        authority.update(agent='One prompt run', files='No agent worktree', commands='No coding agent commands',
                         network='Yes, to the assigned engine and allowed tools', until='Until this prompt run ends')
    return authority
