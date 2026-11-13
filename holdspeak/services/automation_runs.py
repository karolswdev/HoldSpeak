"""Automation definitions, Program results, and retained occurrence results.

Every new run is a Program: one prompt step, agent steps, or a template.
Its report and step facts supply the Automation face's result and history.
Pre-fold items and artifacts remain readable; no new workbench_runs row is
written. A prompt result goes to Inbox, Needs you, Today, project updates,
or a prepared send (the owner presses Send).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Mapping, Optional

from ..logging_config import get_logger
from ..timestamps import local_now, utc_now_iso
from .errors import ValidationError

log = get_logger("services.automation_runs")

#: The context marker of an occurrence item (``workbench_items.context_json``).
OCCURRENCE = "occurrence"
#: The Inbox zone (``holdspeak/seeds/fresh-desk.yaml``).
INBOX_DIRECTORY_ID = "hs-seed-inbox"
OUTPUT_TARGETS = ("inbox", "needs_you", "today")
DESTINATION_PREFIX = "destination:"
# A project update is a first-class automation result.  It stays in the
# project_updates ledger; it is not copied to an Inbox note.
PROJECT_UPDATES_PREFIX = "project_updates:"
#: A plain prompt for an automation that has an instruction and no agent.
PLAIN_SYSTEM_PROMPT = (
    "You do one job for the owner. Use only the sources you are given. "
    "Answer in Markdown."
)

#: Betterment A5: the relative sets About offers. Each one is a set of
#: sources that a run reads at the time it starts.
SET_SOURCES: dict[str, str] = {
    "meetings:this_week": "This week's meetings",
    "notes:this_week": "This week's notes",
    "decisions:this_week": "This week's decisions",
    "jira:bugs:agent-ok": "Jira bugs labelled agent-ok",
    "github:review_requests": "GitHub review requests",
}
#: A person (a People relationship). A run reads the name only: the People
#: record stays on this device (an engine with the desk's tools may read it).
PERSON_PREFIX = "person:"
#: Betterment A10: a folder (a repository on the desk) an agent engine works
#: in, read only. Its path stays on the hub; the source names its id.
FOLDER_PREFIX = "repository:"


# ── configuration ──────────────────────────────────────────────────────


def clean_sources(value: Any) -> list[str]:
    """Validate a sources list: unique qualified refs (``note:<id>``, ...)."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError("sources must be a list of refs, for example note:<id>")
    from ..grounding import GROUNDING_MAX_REFS, qualified_ref

    refs: list[str] = []
    for raw in value:
        if not isinstance(raw, str) or not raw.strip():
            raise ValidationError("Each source must be a ref, for example note:<id>")
        text = raw.strip()
        # Betterment A5: a relative set and a person are About sources too.
        # They are expanded when a run starts (``expand_sources``).
        if text in SET_SOURCES or any(
                text.startswith(prefix) and text[len(prefix):].strip() for prefix in (PERSON_PREFIX, FOLDER_PREFIX)):
            ref = text
        else:
            try:
                ref = qualified_ref(text)
            except ValueError as exc:
                raise ValidationError(f"Unknown source: {text} ({exc})") from None
        if ref not in refs:
            refs.append(ref)
    if len(refs) > GROUNDING_MAX_REFS:
        raise ValidationError(f"Too many sources: {len(refs)} of {GROUNDING_MAX_REFS}")
    return refs


def clean_output_target(db: Any, value: Any) -> str:
    """``inbox`` | ``needs_you`` | ``today`` | ``destination:<saved destination id>``."""
    target = str(value or "inbox").strip()
    if target in OUTPUT_TARGETS:
        return target
    if target.startswith(DESTINATION_PREFIX):
        destination_id = target[len(DESTINATION_PREFIX):].strip()
        if destination_id and db.channel_destinations.get(destination_id) is not None:
            return DESTINATION_PREFIX + destination_id
        raise ValidationError(f"Unknown destination: {destination_id or '(none)'}")
    if target.startswith(PROJECT_UPDATES_PREFIX):
        project_id = target[len(PROJECT_UPDATES_PREFIX):].strip()
        if project_id and db.projects.get_project(project_id) is not None:
            return PROJECT_UPDATES_PREFIX + project_id
        raise ValidationError(f"Unknown project: {project_id or '(none)'}")
    raise ValidationError("output_target must be inbox, needs_you, today or destination:<id>")


def effective_instruction(db: Any, wb: Any) -> tuple[str, str]:
    """The Do text and where it comes from: ``automation`` | ``agent`` | ``""``.

    Migration on read: an old automation with an agent (recipe) shows the
    recipe's ``user_template``, else its ``system_prompt``. Nothing is
    written: the queue run stays until he edits the instruction.
    """
    own = str(getattr(wb, "instruction", "") or "").strip()
    if own:
        return own, "automation"
    recipe = db.recipes.get(wb.recipe_id) if getattr(wb, "recipe_id", None) else None
    if recipe is not None:
        for text in (getattr(recipe, "user_template", ""), getattr(recipe, "system_prompt", "")):
            if str(text or "").strip():
                return str(text).strip(), "agent"
    return "", ""


def sources_of(wb: Any) -> list[str]:
    try:
        value = json.loads(getattr(wb, "sources_json", "") or "[]")
    except (TypeError, ValueError):
        return []
    return [str(ref) for ref in value if isinstance(ref, str) and ref.strip()] if isinstance(value, list) else []


# ── the occurrence item ────────────────────────────────────────────────


def occurrence_title(wb: Any, now: Optional[datetime] = None) -> str:
    when = (now or local_now()).astimezone()
    return f"{wb.name or 'Automation'}, {when:%a} {when.day} {when:%b %Y}"


def _event_block(event: dict[str, Any]) -> str:
    """The event's subject, as the run's evidence (its refs are not desk sources)."""
    facts = dict(event.get("facts") or {})
    subject = {
        "event_type": event.get("event_type", ""),
        "subject": event.get("subject_ref", ""),
        "title": facts.get("entity_title", ""),
        "url": facts.get("url", ""),
        "changed": facts.get("changed"),
        "current": facts.get("current"),
    }
    return "[EVENT]\n" + json.dumps(subject, sort_keys=True, indent=2, default=str)


# ── a run is a Program of one prompt step (2026-11-08) ─────────────────

#: A Program an automation started names it as its origin.
PROGRAM_ORIGIN_PREFIX = "workbench:"


def runs_as_program(wb: Any) -> bool:
    """An automation with its own instruction (no agent hand, no Program
    template) runs each time as a Program of one prompt step."""
    return bool(str(getattr(wb, "instruction", "") or "").strip()) and str(
        getattr(wb, "do_kind", "run") or "run") not in ("hand_to_agent", "run_program")


def program_runs(db: Any, workbench_id: str) -> list[dict[str, Any]]:
    """The Programs an automation started, newest first (store rows)."""
    from ..db.programs import ProgramStore

    with db._connection() as conn:
        ids = [str(row["id"]) for row in conn.execute(
            "SELECT id FROM programs WHERE origin_ref IN (?, ?) ORDER BY created_at DESC, id DESC",
            (PROGRAM_ORIGIN_PREFIX + workbench_id, "automation:" + workbench_id))]
    store = ProgramStore(db)
    return [row for row in (store.get_program(pid) for pid in ids) if row is not None]


def run_as_program(
    db: Any, principal: Any, wb: Any, *, now: Optional[datetime] = None,
    event: Optional[dict[str, Any]] = None, title: Optional[str] = None,
    start: bool = True, wait: bool = False, key: Optional[str] = None,
    context: Optional[dict[str, Any]] = None, brief: Optional[str] = None,
    sources: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Start one run of an automation: a Program titled "<name>, <date>"
    (or the event's title) with one prompt step that does the instruction
    about the automation's sources and delivers where Put it in says. An
    event start adds the event to the brief; an automation with no
    instruction gets the event's words as its brief. ``key`` names the run
    (a scheduled minute, one event): a second start with the same key
    returns the first Program and starts nothing. ``context`` is kept on
    the step (``facts.run_context``: the watch and event a start came
    from). ``wait``: the step's call runs in this thread before the return.
    ``{"program_id", "run_id", "started"}``."""
    from ..db.programs import ProgramStore
    from .program_service import default_program_service

    if key:
        store = ProgramStore(db)
        for row in program_runs(db, str(wb.id)):
            if any((step.get("facts") or {}).get("run_key") == key for step in store.list_steps(row["id"])):
                return {"program_id": row["id"], "run_id": row["id"], "started": False}
    # ``brief``/``sources``: the run's own words and sources (an idle routine's
    # item), in place of the automation's instruction and About.
    explicit = brief is not None
    brief = str(brief if explicit else (wb.instruction or "")).strip()
    if event is not None:
        # With no instruction, the event's own words are the brief.
        words = brief or f"Something happened: {title or event.get('event_type') or 'an event'}. Say what it means for me."
        brief = f"{words}\n\n{_event_block(event)}"
    target = str(wb.output_target or "inbox")
    project_id = target[len(PROJECT_UPDATES_PREFIX):] if target.startswith(PROJECT_UPDATES_PREFIX) else None
    service = default_program_service(db)
    checked_work_folder(service, wb, project_id=project_id, sources=sources)
    owner = _delivery_principal(principal)
    made = service.create(
        owner, title=str(title or occurrence_title(wb, now)), project_id=project_id,
        # His schedule (or his press) is the go-ahead: a prompt step merges
        # nothing, so the run asks him nothing on the way.
        control="yolo", origin_ref=PROGRAM_ORIGIN_PREFIX + str(wb.id),
        spend_limit_usd=getattr(wb, "spend_limit_usd", None),
        steps=[{"title": str(wb.name or "Automation"), "brief": brief, "kind": "prompt",
                "deliver": target, "sources": list(sources) if sources is not None else sources_of(wb)}],
    )
    if key or context:
        store = ProgramStore(db)
        for step in store.list_steps(made["id"]):
            step["facts"] = {**(step.get("facts") or {}), **({"run_key": key} if key else {}),
                             **({"run_context": dict(context)} if context else {})}
            store.save_step(step)
    if wait:
        # A caller waits on the answer (the Room's Draft update): the step's
        # call runs here, in this thread, through the same hand the tick uses.
        from . import program_prompt

        steps = made["steps"]
        claimed = [step["id"] for step in steps if program_prompt.claim(step["id"])]
        try:
            service.start(owner, made["id"], by="engine")
            runner = service.runner()
            for step_id in claimed:
                program = service.store.get_program(made["id"])
                step = service.store.get_step(step_id)
                if program is not None and step is not None:
                    program_prompt.run_claimed(runner, program, step, broker=getattr(runner, "_broker", None))
        finally:
            # run_claimed gives its hand back; a step it never reached is released here.
            for step_id in claimed:
                program_prompt.release(step_id)
        service.changed(made["id"], verb="step")
    elif start:
        service.start(owner, made["id"], by="engine")
    return {"program_id": made["id"], "run_id": made["id"], "started": start or wait}


def project_update_material(
    db: Any, principal: Any, project_id: str,
) -> tuple[list[str], str, list[str]]:
    """What a project update run reads: ``(refs, material, excluded_refs)``.

    ``refs`` are the P2-eligible leaf refs a ``project:`` source becomes;
    ``material`` is the records draft and the three standing project pages
    (P8's no-tool contract), read sentence by sentence with the same P2
    exclusions, so a stale private source cannot come back at this seam;
    ``excluded_refs`` are the refs a tool-capable engine must not read.
    When the source list cannot be established the run reads nothing broad:
    ``([], "", [])``."""
    try:
        from .memory_grounding import MemoryContext, page_excerpts, project_pages
        from .project_service import ProjectService
        from .project_update_service import ProjectUpdateService

        update_service = ProjectUpdateService(db, project_service=ProjectService(db))
        refs = update_service.project_update_grounding_refs(principal, project_id)
        records = update_service.draft_update(principal, project_id, generator="deterministic", persist=False)
        excluded = update_service.project_update_excluded_refs(principal, project_id)
        excluded_folded = {str(ref).casefold() for ref in excluded}

        def page_sentence_is_safe(sentence: Any) -> bool:
            found = sentence.get("refs") if isinstance(sentence, dict) else []
            return not any(str(ref.get("ref") or "").split("#", 1)[0].casefold() in excluded_folded
                           for ref in found or [] if isinstance(ref, dict))

        pages = page_excerpts(
            db, project_pages(project_id, "what-we-decided", "what-is-open", "what-changed-this-week"),
            exclude_refs=excluded, sentence_filter=page_sentence_is_safe,
        )
        records_body = str(records.get("body_md") or "").strip()
        page_body = MemoryContext(tuple(pages)).prompt_block("PROJECT PAGES")
        material = "\n\n".join(part for part in (
            f"[RECORDS DRAFT]\n{records_body}\n[END RECORDS DRAFT]" if records_body else "", page_body) if part)
        return list(refs), material, sorted(excluded)
    except Exception:
        return [], "", []


def program_delivery(db: Any, program_id: str) -> dict[str, Any]:
    """Where the run's prompt step put its answer (``facts.delivered``), or ``{}``."""
    from ..db.programs import ProgramStore

    step = next((row for row in ProgramStore(db).list_steps(program_id) if row.get("kind") == "prompt"), None)
    return dict(((step or {}).get("facts") or {}).get("delivered") or {})


def _program_results(db: Any, workbench_id: str, limit: int) -> list[dict[str, Any]]:
    """The automation's Program runs as result rows (the shape of
    ``results_of``): the prompt step's report is the text."""
    from ..db.programs import ProgramStore
    from ..intel.cli_engine_runs import cost_by_item
    from .run_trace import use_by_item

    store = ProgramStore(db)
    rows: list[dict[str, Any]] = []
    for program in program_runs(db, workbench_id)[:limit]:
        result_steps = [row for row in store.list_steps(program["id"])
                        if row.get("kind") == "prompt" or (row.get("facts") or {}).get("automation_target")]
        if not result_steps:
            steps = store.list_steps(program["id"])
            summary = _program_links(db, [program["id"]])[program["id"]]
            first = steps[0] if steps else {}
            failed = program["state"] == "failed"
            rows.append({
                "item_id": str(first.get("id") or program["id"]), "title": program["title"],
                "status": "failed" if failed else "done", "artifact_id": None,
                "new": False, "error": _failure_line(store, first) if failed else None,
                "text": "\n\n".join(str(s.get("report") or "") for s in steps if s.get("report"))
                        or f"Started the program {program['title']} · {len(steps)} steps",
                "completed_at": program.get("closed_at") or program.get("created_at"),
                "seconds": _seconds_between(program.get("created_at"), program.get("closed_at")),
                "model": "", "boundary": "", "note_id": program.get("note_id"), "cost_usd": None,
                "used": None, "program": summary, "_at": program.get("created_at") or "",
            })
            continue
        for step in result_steps:
            facts = step.get("facts") or {}
            prompt = facts.get("prompt") or {}
            state = str(step.get("state") or "")
            status = "done" if state in {"done", "merged"} else ("failed" if state == "failed" else "running")
            rows.append({
                # The result's own id is the step's: Open marks it read (``open_result``).
                "item_id": str(step["id"]),
                "title": str(step.get("title") if facts.get("automation_target") else program.get("title") or ""),
                "status": status,
                "artifact_id": str(step["id"]), "new": status == "done" and not facts.get("opened_at"),
                "update_id": (facts.get("delivered") or {}).get("update_id"),
                "error": (str(prompt.get("error") or "") or _failure_line(store, step)) if status == "failed" else None,
                "text": str(step.get("report") or "") if status == "done" else None,
                "completed_at": step.get("ended_at"),
                "seconds": _seconds_between(step.get("started_at"), step.get("ended_at")) if step.get("ended_at") else None,
                "model": str(prompt.get("model") or ""), "boundary": str(prompt.get("egress") or ""),
                "note_id": (facts.get("delivered") or {}).get("note_id"),
                # An agent CLI engine's reported cost, keyed by the step (run_trace).
                "cost_usd": cost_by_item(db, [str(step["id"])]).get(str(step["id"])),
                "used": use_by_item(db, [str(step["id"])]).get(str(step["id"])),
                "program": (_program_links(db, [program["id"]])[program["id"]] if facts.get("automation_target")
                            else {"id": program["id"], "title": program["title"], "state": program["state"]}),
                # The run itself is this Program (no artifact: its answer's note is what is sent).
                "program_run": True,
                "_at": str(step.get("ended_at") or program.get("created_at") or ""),
            })
    return rows


def program_run_rows(db: Any, workbench_id: str) -> list[dict[str, Any]]:
    """The automation's Program runs in the Runs wing's shape (one step each)."""
    from ..db.programs import ProgramStore

    store = ProgramStore(db)
    rows = []
    for program in program_runs(db, workbench_id):
        steps = store.list_steps(program["id"])
        prompts = [(step.get("facts") or {}).get("prompt") or {} for step in steps]
        state = str(program.get("state") or "")
        rows.append({
            "id": program["id"], "workbench_id": workbench_id,
            "started_at": next((s["started_at"] for s in steps if s.get("started_at")), program.get("created_at")),
            "completed_at": program.get("closed_at"),
            "items_attempted": sum(bool(s.get("started_at")) for s in steps),
            "items_completed": sum(s["state"] in {"done", "merged"} for s in steps),
            "items_failed": sum(s["state"] in {"failed", "check_failed"} for s in steps),
            "mint_failures": 0, "total_tokens": sum(int(p.get("tokens") or 0) for p in prompts),
            "egress_boundary": next((p["egress"] for p in prompts if p.get("egress")), ""),
            "model": next((p["model"] for p in prompts if p.get("model")), ""),
            "constitutional_context_revision": 0, "constitutional_context_hash": "", "skills_injected": [],
            "status": "completed" if state == "done" else state,
            "program_id": program["id"],
        })
    return rows


def _open_program_result(db: Any, workbench_id: str, step_id: str) -> Optional[dict[str, Any]]:
    """Open a Program run's result: it is read from now on. None when the id
    is not a run of this automation."""
    from ..db.programs import ProgramStore

    store = ProgramStore(db)
    step = store.get_step(step_id)
    if step is None:
        return None
    program = store.get_program(str(step["program_id"])) or {}
    if str(program.get("origin_ref") or "") not in {PROGRAM_ORIGIN_PREFIX + workbench_id, "automation:" + workbench_id}:
        return None
    facts = dict(step.get("facts") or {})
    if not facts.get("opened_at"):
        facts["opened_at"] = utc_now_iso()
        step["facts"] = facts
        store.save_step(step)
    return {"artifact_id": step_id, "status": "read"}


def _failure_line(store: Any, step: Mapping[str, Any]) -> str:
    rows = [row for row in store.list_checkpoints(str(step["program_id"])) if row.get("step_id") == step["id"]]
    return str((rows[0] if rows else {}).get("line") or "The engine gave no answer")


def _week_start(now: Optional[datetime] = None) -> datetime:
    """Monday 00:00 of this week, on the hub's own clock."""
    from datetime import timedelta

    today = (now or local_now()).astimezone()
    return (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _set_members(db: Any, ref: str, now: Optional[datetime] = None) -> list[str]:
    """The sources a relative set holds now, newest first."""
    from ..timestamps import parse_stamp

    since = _week_start(now)
    if ref == "meetings:this_week":
        query = "SELECT id, started_at AS at FROM meetings WHERE parked = 0"
        kind = "meeting"
    elif ref == "notes:this_week":
        # An automation's own results (Inbox notes) are not its sources.
        query = ("SELECT id, COALESCE(NULLIF(updated_at, ''), created_at) AS at FROM notes "
                 "WHERE deleted = 0 AND id NOT LIKE 'note\\_result\\_%' ESCAPE '\\'")
        kind = "note"
    elif ref == "decisions:this_week":
        query = "SELECT id, COALESCE(NULLIF(updated_at, ''), created_at) AS at FROM decision_records WHERE deleted = 0"
        kind = "decision_record"
    elif ref in {"jira:bugs:agent-ok", "github:review_requests"}:
        return _watch_set_members(db, ref)
    else:
        return []
    with db._connection() as conn:
        rows = conn.execute(query).fetchall()
    dated = []
    for row in rows:
        at = parse_stamp(row["at"])
        if at is not None and at >= since:
            dated.append((at, f"{kind}:{row['id']}"))
    return [ref for _at, ref in sorted(dated, reverse=True)]


def _watch_set_members(db: Any, ref: str) -> list[str]:
    """Read actual issue snapshots for the AG14 source starters."""
    connector = "jira" if ref.startswith("jira:") else "gh"
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT id, query_kind, snapshot_json, last_success_at, last_error
               FROM connector_watches
               WHERE connector_id IN (?, ?)
                 AND query_kind IN ('issues','pull_requests')
                 AND enabled=1""",
            (connector, "github" if connector == "gh" else connector),
        ).fetchall()
    found: list[str] = []
    for row in rows:
        # A starter is an action on the producer's current, healthy
        # observation.  A cached snapshot with no successful refresh (or an
        # outstanding provider error) is stale and must stay out of New
        # automation.
        if not str(row["last_success_at"] or "").strip() or str(row["last_error"] or "").strip():
            continue
        try:
            snapshot = json.loads(row["snapshot_json"] or "{}")
        except (TypeError, ValueError):
            continue
        entities = snapshot.get("entities") if isinstance(snapshot, dict) else snapshot
        if isinstance(entities, dict):
            entities = list(entities.values())
        if not isinstance(entities, list):
            continue
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            labels = entity.get("labels") if isinstance(entity.get("labels"), list) else []
            labels = {str(label.get("name") if isinstance(label, dict) else label).strip().lower() for label in labels}
            reviews = entity.get("review_requests") or entity.get("reviewRequests") or []
            if ref == "jira:bugs:agent-ok" and ("agent-ok" not in labels or str(entity.get("issue_type") or "").strip().lower() != "bug"):
                continue
            if ref == "github:review_requests" and not reviews:
                continue
            entity_id = str(entity.get("id") or entity.get("key") or entity.get("number") or "").strip()
            if entity_id:
                found.append(f"issue:{row['id']}.{entity_id}")
    return list(dict.fromkeys(found))


def _people_names() -> dict[str, str]:
    """Each person's name (the owner's People list); empty when People is not
    set up on this device."""
    try:
        from ..mcp.families.people import build_people_service
        from ..principals import Principal, PrincipalKind

        rows = build_people_service().list_relationships(
            Principal(PrincipalKind.OWNER, "local-automation-conductor"))
    except Exception as exc:  # People not set up: a person is named missing
        log.debug("automation people names: %s", exc)
        return {}
    return {str(row.get("id") or ""): str(row.get("display_name") or "") for row in rows}


def expand_sources(
    db: Any, refs: list[str], now: Optional[datetime] = None,
) -> tuple[list[str], list[str]]:
    """The run's grounding refs, and the lines it adds to the instruction.

    A relative set becomes the sources it holds now (Friday's run reads the
    meetings since Monday). A person adds a line with the name. A set that
    holds nothing says so, so the engine does not guess.
    """
    from ..grounding import GROUNDING_MAX_REFS

    grounding: list[str] = []
    about: list[str] = []
    people: Optional[dict[str, str]] = None
    for ref in refs:
        if ref in SET_SOURCES:
            members = _set_members(db, ref, now)
            if not members:
                about.append(f"{SET_SOURCES[ref]}: none yet.")
            grounding.extend(m for m in members if m not in grounding)
        elif ref.startswith(PERSON_PREFIX):
            people = _people_names() if people is None else people
            name = people.get(ref[len(PERSON_PREFIX):], "")
            if name:
                about.append(f"Person: {name}")
        elif ref.startswith(FOLDER_PREFIX):
            continue  # A10: the agent reads the folder itself (work_folder_of)
        elif ref not in grounding:
            grounding.append(ref)
    return grounding[:GROUNDING_MAX_REFS], about


def _folder_source(source_id: str) -> Any:
    """The desk repository a folder source names; None when it is gone."""
    from ..delivery import DeliveryRegistry

    try:
        return DeliveryRegistry().get(source_id)
    except Exception as exc:  # an unreadable registry names the folder missing
        log.debug("automation folder %s: %s", source_id, exc)
        return None


def work_folder_of(wb: Any) -> Optional[str]:
    """Betterment A10: the folder an agent engine works in for this
    automation (its first Folder source that is still a folder), or None."""
    from pathlib import Path

    for ref in sources_of(wb):
        if not ref.startswith(FOLDER_PREFIX):
            continue
        source = _folder_source(ref[len(FOLDER_PREFIX):])
        path = str(getattr(source, "primary_path", "") or "")
        if path and Path(path).is_dir():
            return str(Path(path).resolve())
    return None


def checked_work_folder(
    service: Any, wb: Any, *, project_id: Optional[str] = None, sources: Optional[list[str]] = None,
) -> Optional[str]:
    """A Folder carrying project material must be that project's repository."""
    from pathlib import Path
    from .agent_hand_service import project_for_item
    from .automation_program import automation_project
    from .program_definitions import ProgramRefused

    folder = work_folder_of(wb)
    if not folder:
        return None
    refs, _ = expand_sources(service.db, sources if sources is not None else sources_of(wb))
    projects = {ident if kind == "project" else project_for_item(service.db, kind, ident)
                for kind, _, ident in (str(ref).partition(":") for ref in refs)}
    projects.discard(None)
    projects.discard("")
    declared = project_id or automation_project(service.db, wb)
    if declared:
        projects.add(declared)
    if len(projects) == 1:
        source = service._project_source(next(iter(projects)))
        expected = str(getattr(source, "primary_path", "") or "")
        if expected and Path(expected).expanduser().resolve() == Path(folder).resolve():
            return folder
    elif not projects:
        return folder
    raise ProgramRefused("different_projects", "Use one automation for each project's agent work.")


# ── AG14: one durable hand per source item ─────────────────────────────

HAND_ITEM_PREFIX = "wbhand_"
HAND_SOURCE_KINDS = frozenset({
    "action", "artifact", "decision", "decision_record", "issue", "meeting",
    "note", "project_item", "thread",
})


def hand_item_id(workbench_id: str, source_ref: str) -> str:
    """Stable Workbench item identity for one source item.

    The Workbench item is the existing durable item ledger.  Its context holds
    the launch and queue receipt; no second automation run ledger is needed.
    """
    digest = hashlib.sha256(f"{workbench_id}:{source_ref}".encode()).hexdigest()[:20]
    return HAND_ITEM_PREFIX + digest


def hand_sources(db: Any, wb: Any) -> list[dict[str, str]]:
    """Resolve the current About refs to handable desk items.

    Relative sets are expanded at run time.  A source that is not an actual
    desk item is omitted, so a hand automation never launches one generic
    occurrence for an unreadable source.
    """
    from .agent_hand_service import item_exists, item_title

    refs, _about = expand_sources(db, sources_of(wb))
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for ref in refs:
        kind, sep, item_id = str(ref).partition(":")
        kind, item_id = kind.strip(), item_id.strip()
        if not sep or kind not in HAND_SOURCE_KINDS or not item_id:
            continue
        canonical = f"{kind}:{item_id}"
        if canonical in seen:
            continue
        try:
            exists = item_exists(db, kind, item_id)
        except Exception:
            exists = False
        if not exists:
            continue
        seen.add(canonical)
        try:
            title = item_title(db, kind, item_id)
        except Exception:
            title = ""
        found.append({"ref": canonical, "kind": kind, "id": item_id, "title": title or item_id})
    return found


def _hand_context(item: Any) -> dict[str, Any]:
    try:
        value = json.loads(getattr(item, "context_json", "") or "{}")
    except (TypeError, ValueError):
        value = {}
    return value if isinstance(value, dict) else {}


def _persist_agent_result(
    db: Any, *, item: Any, context: dict[str, Any], words: str,
    flight: dict[str, Any],
) -> Optional[tuple[dict[str, Any], dict[str, Any]]]:
    """Link an agent Done turn to the existing result/artifact models."""
    from ..timestamps import utc_now_iso

    now = utc_now_iso()
    launch_id = str((context.get("agent_hand") or {}).get("launch_id") or flight.get("launch_id") or "")
    artifact_id = "artifact_" + hashlib.sha256(f"agent-hand:{item.id}:{launch_id}".encode()).hexdigest()[:16]
    body = str(words or "").strip() or "Agent completed this item."
    hand = dict(context.get("agent_hand") or {})
    hand.update({"status": "done", "done_turn_id": str(flight.get("turn_id") or "")})
    context["agent_hand"] = hand
    egress = {"boundary": "local", "model": str(hand.get("profile") or flight.get("agent") or "")}
    run_id = str(hand.get("run_id") or "")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO artifacts (
                id, meeting_id, origin, artifact_type, title, body_markdown,
                structured_json, confidence, status, plugin_id, plugin_version,
                source_run_id, source_item_id, created_at, updated_at
            ) VALUES (?, NULL, 'run', 'agent_result', ?, ?, ?, 0.0, 'new',
                      'automation_agent_hand', '1', ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET title=excluded.title,
                body_markdown=excluded.body_markdown,
                structured_json=excluded.structured_json,
                status='new', updated_at=excluded.updated_at""",
            (
                artifact_id,
                str(item.title or "Agent result"),
                body,
                json.dumps({"launch_id": launch_id, "source_ref": hand.get("source_ref") or ""}, sort_keys=True),
                run_id or None,
                item.id,
                now,
                now,
            ),
        )
        conn.execute(
            "INSERT OR IGNORE INTO artifact_sources (artifact_id, source_type, source_ref, created_at) VALUES (?, 'workbench_item', ?, ?)",
            (artifact_id, item.id, now),
        )
        advanced = conn.execute(
            """UPDATE workbench_items
               SET status='done', result=?, result_egress_json=?, result_artifact_id=?,
                   context_json=?, completed_at=?, last_modified=?
               WHERE id=? AND status != 'done'""",
            (body, json.dumps(egress, sort_keys=True), artifact_id, json.dumps(context, sort_keys=True), now, now, item.id),
        ).rowcount
        if advanced != 1:
            return None
    row = {
        "artifact_id": artifact_id, "item_id": item.id, "workbench_id": item.workbench_id,
        "title": item.title, "result": body,
    }
    return row, context


def sync_agent_results(db: Any, workbench_id: Optional[str] = None) -> int:
    """Turn each newly observed agent Done into one automation result."""
    from ..timestamps import utc_now_iso
    from ..agent_context import event_log
    from .agent_flights import agent_flights
    from .agent_helpers import last_words

    # Native hooks spool their Stop event before updating the session. Drain
    # the existing event log here so a result read observes the same words as
    # the agent flight, including a hand that came from the shared queue.
    try:
        event_log.drain_spool(db._connection)
    except Exception as exc:
        log.debug("agent hand event spool not drained: %s", exc)
    # HS-S31: a Waiting occurrence first reads its queue id's terminal outcome.
    try:
        sync_queue_outcomes(db, workbench_id=workbench_id)
    except Exception as exc:
        log.debug("queue outcomes not read: %s", exc)

    query = "SELECT * FROM workbench_items WHERE json_extract(context_json, '$.agent_hand.launch_id') IS NOT NULL AND parked=0"
    params: list[Any] = []
    if workbench_id:
        query += " AND workbench_id=?"
        params.append(workbench_id)
    with db._connection() as conn:
        rows = conn.execute(query, params).fetchall()
    flights = {str(f.get("launch_id") or ""): f for f in agent_flights(db) if f.get("launch_id")}
    changed = 0
    delivered: list[dict[str, Any]] = []
    for raw in rows:
        item = db.workbench_items.get(str(raw["id"]), include_parked=True)
        if item is None or item.status == "done":
            continue
        context = _hand_context(item)
        hand = context.get("agent_hand") if isinstance(context.get("agent_hand"), dict) else {}
        launch_id = str(hand.get("launch_id") or "")
        flight = flights.get(launch_id)
        if not flight or str(flight.get("state") or "") != "done":
            continue
        try:
            words = last_words(db, launch_id)
        except Exception:
            words = None
        words = str(words or flight.get("last_words") or flight.get("result") or "")
        persisted = _persist_agent_result(db, item=item, context=context, words=words, flight=flight)
        if persisted is None:
            continue
        row, context = persisted
        delivered.append(row)
        changed += 1
    if delivered:
        # Reuse the established automation egress and finished notice path.
        from ..principals import Principal, PrincipalKind
        owner = Principal(PrincipalKind.OWNER, "local-automation-conductor")
        for row in delivered:
            wb = db.workbenches.get(str(row["workbench_id"]), include_deleted=True)
            if wb is None:
                continue
            try:
                outcome = _deliver_one(db, owner, wb, row)
                _finished_notices(db, [row])
            except Exception as exc:
                log.warning("agent result delivery failed for %s: %s", row["item_id"], exc)
                outcome = {"outcome": "failed", "error": str(exc)}
            with db._connection() as conn:
                current = conn.execute("SELECT context_json FROM workbench_items WHERE id=?", (row["item_id"],)).fetchone()
                try:
                    updated = json.loads(current["context_json"] or "{}") if current else {}
                except (TypeError, ValueError):
                    updated = {}
                if isinstance(updated, dict):
                    updated.setdefault("agent_hand", {})["delivered"] = outcome.get("outcome")
                    conn.execute("UPDATE workbench_items SET context_json=?, last_modified=? WHERE id=?", (json.dumps(updated, sort_keys=True), utc_now_iso(), row["item_id"]))
    return changed


def sync_agent_hand_launches(db: Any, answers: list[dict[str, Any]]) -> int:
    """Attach queue starts to their existing Workbench hand occurrence.

    ``HandQueue`` is shared by direct agent hands and Workbench runs, so its
    durable entry carries the source ref and queue id.  When the existing hub
    heartbeat starts one, connect that answer to the matching occurrence so
    the normal Done/result projector can follow the launch id.
    """
    from ..timestamps import utc_now_iso

    changed = 0
    for answer in answers:
        if str(answer.get("status") or "") != "launched" or not answer.get("launch_id"):
            continue
        queue_id = str(answer.get("queue_id") or "")
        origin = answer.get("origin_ref") if isinstance(answer.get("origin_ref"), dict) else {}
        kind = str(origin.get("kind") or "")
        source_id = str(origin.get("id") or "")
        if not queue_id or not kind or not source_id:
            continue
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT id, context_json FROM workbench_items WHERE parked=0 AND json_extract(context_json, '$.agent_hand.queue_id')=?",
                (queue_id,),
            ).fetchall()
            for row in rows:
                try:
                    context = json.loads(row["context_json"] or "{}")
                except (TypeError, ValueError):
                    context = {}
                hand = context.get("agent_hand") if isinstance(context, dict) else None
                if not isinstance(hand, dict) or str(hand.get("source_ref") or "") != f"{kind}:{source_id}":
                    continue
                if hand.get("launch_id"):
                    continue
                hand.update({
                    "status": "launched",
                    "launch_id": str(answer["launch_id"]),
                    "attempt_id": str(answer.get("attempt_id") or ""),
                    "profile": str(answer.get("profile") or hand.get("profile") or ""),
                })
                context["agent_hand"] = hand
                conn.execute(
                    "UPDATE workbench_items SET context_json=?, last_modified=? WHERE id=?",
                    (json.dumps(context, sort_keys=True), utc_now_iso(), row["id"]),
                )
                changed += 1
    return changed


def sync_queue_outcomes(db: Any, queue: Any = None, workbench_id: Optional[str] = None) -> int:
    """HS-S31: each Waiting occurrence (its hand ``queued``, a queue id, no
    launch) reads its queue id's outcome (``agent_hand_queue.queue_outcome``)
    and shows a terminal one. Every matching nonparked occurrence reads the
    same answer (zero to many consumers; never the first match only).

    - ``waiting`` and ``unknown``: nothing is written (an unknown is never
      read as failed and never handed again);
    - ``launched``: the launch id is attached the way the heartbeat does
      (``sync_agent_hand_launches``: the source must match; a linked launch
      is never replaced), so the Done projector can follow it;
    - ``cancelled`` / ``failed``: the occurrence ends with the reason; its
      queue id stays, so a later Run skips it (a cancelled entry is never
      revived).

    A read never starts, re-queues or repeats a hand. Returns the rows changed."""
    from .agent_hand_queue import CANCELLED, FAILED, LAUNCHED, HandQueue

    queue = queue or HandQueue()
    sql = ("SELECT id, context_json FROM workbench_items WHERE parked=0 AND status='pending' "
           "AND json_extract(context_json, '$.agent_hand.status')='queued' "
           "AND json_extract(context_json, '$.agent_hand.queue_id') IS NOT NULL")
    args: tuple[Any, ...] = ()
    if workbench_id:
        sql, args = sql + " AND workbench_id=?", (workbench_id,)
    with db._connection() as conn:
        rows = conn.execute(sql, args).fetchall()
    answers: dict[str, dict[str, Any]] = {}
    changed = 0
    for row in rows:
        try:
            context = json.loads(row["context_json"] or "{}")
        except (TypeError, ValueError):
            continue
        hand = context.get("agent_hand") if isinstance(context, dict) else None
        if not isinstance(hand, dict) or hand.get("launch_id"):
            continue
        queue_id = str(hand.get("queue_id") or "")
        if queue_id not in answers:
            answers[queue_id] = queue.outcome(queue_id)
        answer = answers[queue_id]
        source_ref = str(hand.get("source_ref") or "")
        if answer["outcome"] == LAUNCHED:
            kind, _, source_id = str(answer.get("source_ref") or "").partition(":")
            if answer.get("launch_id") and kind and source_id:
                changed += sync_agent_hand_launches(db, [{
                    "status": "launched", "launch_id": answer["launch_id"], "queue_id": queue_id,
                    "origin_ref": {"kind": kind, "id": source_id},
                }])
            continue
        if answer["outcome"] not in (CANCELLED, FAILED) or answer.get("source_ref") != source_ref:
            continue
        cancelled = answer["outcome"] == CANCELLED
        words = "Cancelled before it started" if cancelled else f"Not started · {answer.get('code') or 'refused'}"
        hand.update({"status": "cancelled" if cancelled else "refused",
                     "queue_outcome": {key: answer.get(key) for key in ("outcome", "code", "at")}})
        context["agent_hand"] = hand
        now = utc_now_iso()
        with db._connection() as conn:
            changed += conn.execute(
                "UPDATE workbench_items SET status='failed', result=?, context_json=?, completed_at=?, last_modified=? "
                "WHERE id=? AND status='pending'",
                (f"Error: {words}", json.dumps(context, sort_keys=True), now, now, row["id"]),
            ).rowcount
    return changed


# ── the per-engine time limit ──────────────────────────────────────────


def cli_endpoint_of(conn: Any, profile_id: str) -> str:
    """The ``cli:`` endpoint of an engine profile; '' when it is not an agent CLI."""
    if profile_id.startswith("legacy-"):
        row = conn.execute(
            "SELECT kind, base_url FROM profiles WHERE id=?", (profile_id.removeprefix("legacy-"),),
        ).fetchone()
        return str(row["base_url"] or "") if row is not None and str(row["kind"]) == "cliCommand" else ""
    row = conn.execute(
        """SELECT d.kind, d.endpoint FROM model_profile_binding_heads h
           JOIN model_profile_binding_revisions b
             ON b.binding_id = h.binding_id AND b.revision = h.revision
           JOIN deployment_revisions d ON d.id = b.deployment_revision_id
           WHERE h.profile_id = ?""",
        (profile_id,),
    ).fetchone()
    return str(row["endpoint"] or "") if row is not None and str(row["kind"]) == "cli_engine" else ""


# ── results ────────────────────────────────────────────────────────────


def open_result(db: Any, workbench_id: str, artifact_id: str) -> dict[str, Any]:
    """Opening a result reads it: ``new`` becomes ``read`` (once)."""
    from holdspeak.timestamps import utc_now_iso

    from .errors import NotFound

    with db._connection() as conn:
        row = conn.execute(
            """SELECT a.id, a.status FROM artifacts a
               JOIN workbench_items i ON i.id = a.source_item_id
               WHERE a.id = ? AND i.workbench_id = ?""",
            (artifact_id, workbench_id),
        ).fetchone()
        if row is None:
            opened = _open_program_result(db, workbench_id, artifact_id)
            if opened is not None:
                return opened
            raise NotFound("result", artifact_id)
        if str(row["status"]) == "new":
            conn.execute(
                "UPDATE artifacts SET status='read', updated_at=? WHERE id=? AND status='new'",
                (utc_now_iso(), artifact_id),
            )
    return {"artifact_id": artifact_id, "status": "read" if str(row["status"]) in {"new", "read"} else str(row["status"])}


def new_results(db: Any) -> list[dict[str, Any]]:
    """The automations that hold a NEW result, newest first (Betterment A6).

    One row per automation: its name, how many results are NEW, and the
    newest one's title and time. Today shows "<name> has a new result" from
    it, and the Automations dock tile counts it. A result stops being NEW
    when it is opened (``open_result``), so the row goes everywhere at once.
    These rows are not Needs-you rows: an automation whose Put it in is
    Needs you adds its own Door item (``_to_needs_you``)."""
    sync_agent_results(db)
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT w.id AS workbench_id, w.name, COUNT(*) AS new_count,
                      MAX(COALESCE(i.completed_at, i.created_at)) AS newest_at
               FROM artifacts a
               JOIN workbench_items i ON i.id = a.source_item_id
               JOIN workbenches w ON w.id = i.workbench_id
               WHERE a.status = 'new' AND i.status = 'done' AND i.parked = 0 AND w.deleted = 0
                 AND json_extract(i.context_json, '$.occurrence') = 1
               GROUP BY w.id ORDER BY newest_at DESC, w.id""",
        ).fetchall()
    found = {str(row["workbench_id"]): {
        "workbench_id": str(row["workbench_id"]),
        "name": str(row["name"] or "Automation"),
        "new_count": int(row["new_count"]),
        "newest_at": row["newest_at"],
    } for row in rows}
    # A run that is a Program: its result is NEW until it is opened.
    with db._connection() as conn:
        origins = [str(r["origin_ref"]) for r in conn.execute(
            "SELECT DISTINCT origin_ref FROM programs WHERE origin_ref LIKE ? OR origin_ref LIKE ?",
            (PROGRAM_ORIGIN_PREFIX + "%", "automation:%"))]
    for workbench_id in {origin.split(":", 1)[1] for origin in origins}:
        wb = db.workbenches.get(workbench_id)
        if wb is None or getattr(wb, "deleted", False):
            continue
        fresh = [row for row in _program_results(db, str(wb.id), 50) if row["new"]]
        if not fresh:
            continue
        row = found.setdefault(str(wb.id), {"workbench_id": str(wb.id), "name": str(wb.name or "Automation"),
                                            "new_count": 0, "newest_at": None})
        row["new_count"] += len(fresh)
        newest = max(str(r["completed_at"] or "") for r in fresh)
        row["newest_at"] = max(str(row["newest_at"] or ""), newest)
    return sorted(found.values(), key=lambda r: (str(r["newest_at"] or ""), r["workbench_id"]), reverse=True)


def prepared_for_today(db: Any, principal: Any) -> Optional[dict[str, Any]]:
    """Betterment daily D9: Today's Prepared block, or None.

    The newest done result of a live automation whose Put it in is Today
    (Morning prep), with its automation's name, the engine it runs on (the
    With line's name) and what its agent looked at. None when no such
    automation has a done result: Today then draws no block at all."""
    sync_agent_results(db)
    newest: Optional[tuple[str, Any, dict[str, Any]]] = None
    for wb in db.workbenches.list():
        if getattr(wb, "deleted", False) or str(wb.output_target or "") != "today":
            continue
        # A run is a Program of one prompt step (its report is the text); the
        # runs before it are occurrence items. ``results_of`` reads both.
        result = next((r for r in results_of(db, str(wb.id), limit=5) if r["status"] == "done"), None)
        at = str((result or {}).get("completed_at") or "")
        if result is not None and (newest is None or at > newest[0]):
            newest = (at, wb, result)
    if newest is None:
        return None
    _at, wb, result = newest
    workbench_id = str(wb.id)
    return {
        "workbench_id": workbench_id,
        "name": str(wb.name or "Morning prep"),
        "engine": engine_name(db, principal, workbench_id) or result.get("model") or "",
        "result": result,
    }


def engine_name(db: Any, principal: Any, workbench_id: str) -> str:
    """The name of the engine an automation runs on ('' when none resolves)."""
    from ..principals import Principal, PrincipalKind
    from .inference_assignment_service import InferenceAssignmentService

    owner = principal if getattr(principal, "kind", None) is PrincipalKind.OWNER else Principal(
        PrincipalKind.OWNER, "local-automation-conductor")
    try:
        effective = InferenceAssignmentService(db).resolve_effective(
            owner, capability_id="workbench.item", subject_kind="workbench", subject_id=workbench_id)
    except Exception:
        return ""
    entries = (effective.get("assignment") or {}).get("entries") or []
    return str(entries[0].get("label") or "") if entries else ""


def tool_engine_profile(db: Any) -> str:
    """The profile id of the automations' engine when it is an agent CLI (it
    gets the desk's tools, MCP M1), else ''. An HTTP engine's tool support is
    a network check (``ask_desk.server_takes_tools``); it is not asked here."""
    from ..principals import Principal, PrincipalKind
    from .inference_assignment_service import InferenceAssignmentService

    try:
        effective = InferenceAssignmentService(db).resolve_effective(
            Principal(PrincipalKind.OWNER, "local-automation-conductor"), capability_id="workbench.item")
    except Exception:
        return ""
    entries = (effective.get("assignment") or {}).get("entries") or []
    profile_id = str(entries[0].get("profile_id") or "") if entries else ""
    if not profile_id:
        return ""
    with db._connection() as conn:
        return profile_id if cli_endpoint_of(conn, profile_id) else ""


def ensure_morning_prep(db: Any) -> Optional[str]:
    """Betterment daily D9, owner decision 3: once an engine with the desk's
    tools exists, the Morning prep automation is made, On, weekdays 07:30.

    Once only: it has a stable id, and a row with that id (live, turned off,
    or deleted) means it was made, so it is never made again. Returns the id
    when it was made now, else None. Called by the workbench conductor's tick."""
    from holdspeak.workbench_templates import MORNING_PREP_ID, MORNING_PREP_STARTER, get_starter

    if db.workbenches.get(MORNING_PREP_ID, include_deleted=True) is not None:
        return None
    if not tool_engine_profile(db):
        return None
    from ..principals import Principal, PrincipalKind
    from .workbench_service import WorkbenchService

    owner = Principal(PrincipalKind.OWNER, "local-automation-conductor")
    service = WorkbenchService(db)
    starter = get_starter(MORNING_PREP_STARTER)
    assert starter is not None
    service.make_from_starter(owner, starter, workbench_id=MORNING_PREP_ID)
    try:
        service.set_when(owner, MORNING_PREP_ID, dict(starter["when"]))
    except Exception as exc:  # the automation stays, its schedule off
        log.warning("Morning prep: the schedule stays off: %s", exc)
    _changed("workbench", MORNING_PREP_ID)
    log.info("Morning prep made, weekdays 07:30")
    return MORNING_PREP_ID


def result_note_id(artifact_id: str) -> str:
    """The Inbox note one result makes (``_to_inbox``): stable per result."""
    return "note_result_" + hashlib.sha256(str(artifact_id).encode()).hexdigest()[:16]


def _seconds_between(start: Any, end: Any) -> Optional[int]:
    try:
        began = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        ended = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if (began.tzinfo is None) != (ended.tzinfo is None):
        return None
    seconds = int(round((ended - began).total_seconds()))
    return seconds if seconds >= 0 else None


def results_of(db: Any, workbench_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """The occurrence results, newest first: one per run.

    Betterment A3: each result also carries what the automation window shows,
    so the face reads no second record: ``text`` (the engine's answer, for a
    done result), ``seconds`` (claimed to completed), ``model`` (the run's
    record) and ``boundary`` (where the prompt went), and ``note_id`` when the Inbox note
    for it exists.

    Betterment M2: ``cost_usd``, the cost an agent CLI engine reported for the
    item's runs (``cli_engine_runs``; None when none was reported), and
    ``used``, what its agent looked at, wrote and prepared
    (``services/run_trace.py``; None when it touched nothing)."""
    sync_agent_results(db, workbench_id)
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT i.id, i.title, i.status, i.result, i.result_artifact_id, i.completed_at,
                      i.created_at, i.claimed_at, i.result_egress_json, a.status AS artifact_status,
                      r.model AS run_model,
                      json_extract(i.context_json, '$.program.program_id') AS program_id
               FROM workbench_items i LEFT JOIN artifacts a ON a.id = i.result_artifact_id
               LEFT JOIN workbench_runs r ON r.id = a.source_run_id
               WHERE i.workbench_id = ? AND i.parked = 0
                 AND json_extract(i.context_json, '$.occurrence') = 1
               ORDER BY COALESCE(i.completed_at, i.created_at) DESC, i.id DESC LIMIT ?""",
            (workbench_id, max(1, int(limit))),
        ).fetchall()
    from ..intel.cli_engine_runs import cost_by_item
    from .run_trace import use_by_item

    item_ids = [str(row["id"]) for row in rows]
    costs = cost_by_item(db, item_ids)
    uses = use_by_item(db, item_ids)
    programs = _program_links(db, [str(row["program_id"]) for row in rows if row["program_id"]])
    results = []
    for row in rows:
        # A pre-fold occurrence that points to a retained Program is only a
        # link to that run. Read the Program once, rather than show two runs.
        if row["program_id"] in programs:
            continue
        status = str(row["status"])
        failed = status == "failed"
        try:
            egress = json.loads(row["result_egress_json"] or "{}") or {}
        except (TypeError, ValueError):
            egress = {}
        artifact_id = row["result_artifact_id"]
        note_id = result_note_id(artifact_id) if artifact_id else None
        if note_id and db.notes.get(note_id) is None:
            note_id = None
        results.append({
            "item_id": str(row["id"]),
            "title": str(row["title"] or ""),
            "status": status,
            "artifact_id": artifact_id,
            "new": str(row["artifact_status"] or "") == "new",
            "error": str(row["result"] or "").removeprefix("Error: ") if failed else None,
            "text": str(row["result"] or "") if status == "done" else None,
            "completed_at": row["completed_at"],
            "seconds": _seconds_between(row["claimed_at"], row["completed_at"]) if row["completed_at"] else None,
            # The run's record names the model that answered (A0); the
            # egress row names the route's target, which can be a profile id.
            "model": str(row["run_model"] or ""),
            "boundary": str(egress.get("boundary") or "") if isinstance(egress, dict) else "",
            "note_id": note_id,
            "cost_usd": costs.get(str(row["id"])),
            "used": uses.get(str(row["id"])),
            # PG14: a run_program run's result links the Program it started.
            **({"program": programs[str(row["program_id"])]} if row["program_id"] in programs else {}),
            "_at": str(row["completed_at"] or row["created_at"] or ""),
        })
    # 2026-11-08: a run is a Program of one prompt step; its rows join the
    # occurrence rows of the runs before it, newest first.
    results.extend(_program_results(db, workbench_id, max(1, int(limit))))
    results.sort(key=lambda row: row["_at"], reverse=True)
    for row in results:
        row.pop("_at", None)
    return results[:max(1, int(limit))]


def _program_links(db: Any, program_ids: list[str]) -> dict[str, dict[str, Any]]:
    """PG14: each Program a result names, with its state now and its window."""
    if not program_ids:
        return {}
    from .program_service import default_program_service

    service = default_program_service(db)
    links: dict[str, dict[str, Any]] = {}
    for program_id in dict.fromkeys(program_ids):
        try:
            summary = service.summary_record(program_id)
            if summary is None:
                continue
        except Exception as exc:  # a Program read never fails the results
            log.debug("program link %s: %s", program_id, exc)
            continue
        links[program_id] = {
            "id": program_id, "title": summary["title"], "state": summary["state"],
            "state_word": summary["state_word"], "done": summary["done"], "total": summary["total"],
            "window": f"pullout:program:{program_id}",
        }
    return links


def source_names(db: Any, refs: list[str]) -> list[dict[str, Any]]:
    """Each source by name, for the About line (Betterment A3). A source that
    no longer exists stays listed as ``missing``; its ref is never shown."""
    from ..grounding import _hydrate_qualified

    named: list[dict[str, Any]] = []
    people: Optional[dict[str, str]] = None
    for ref in refs:
        title = ""
        # Betterment A5: a relative set, a person and a drawer read as words.
        if ref in SET_SOURCES:
            named.append({"ref": ref, "kind": "set", "label": SET_SOURCES[ref], "missing": False})
            continue
        if ref.startswith(PERSON_PREFIX):
            people = _people_names() if people is None else people
            title = people.get(ref[len(PERSON_PREFIX):], "")
            named.append({"ref": ref, "kind": "person", "label": title, "missing": not title})
            continue
        if ref.startswith(FOLDER_PREFIX):
            source = _folder_source(ref[len(FOLDER_PREFIX):])
            title = str(getattr(source, "label", "") or "") if source is not None else ""
            named.append({"ref": ref, "kind": "folder", "label": title, "missing": not title})
            continue
        if ref.startswith("zone:"):
            zone = db.directories.get(ref.split(":", 1)[1])
            title = f"Notes in {zone.name}" if zone is not None and zone.name else ""
            named.append({"ref": ref, "kind": "zone", "label": title, "missing": not title})
            continue
        try:
            blocks, unknown = _hydrate_qualified(db, ref, "summary", set())
            if blocks and not unknown:
                title = " ".join(str(blocks[0].title or "").split())
                if title == ref.split(":", 1)[-1]:  # an untitled thing is named by its id: hide it
                    title = "Untitled"
        except Exception as exc:  # a source that cannot be read is named missing
            log.debug("automation source %s: %s", ref, exc)
        kind = ref.split(":", 1)[0]
        named.append({"ref": ref, "kind": kind, "label": title, "missing": not title})
    return named


def _delivery_principal(principal: Any) -> Any:
    """Who prepares or files a result: the caller, or for a scheduled run the
    owner who enabled the schedule (the conductor's own owner identity)."""
    from ..principals import Principal, PrincipalKind

    if principal is None or principal.kind in {PrincipalKind.SCHEDULER, PrincipalKind.NONE}:
        return Principal(PrincipalKind.OWNER, "local-automation-conductor")
    return principal


def _finished_notices(db: Any, rows: list[Any]) -> None:
    """Betterment daily D8 (decision 2): a run that made a new result raises
    one quiet notice per automation (``HeartbeatService.finished_notice``).
    Once per run: a replayed run delivers nothing and comes not here. A
    failed notice is logged; it never fails the run."""
    named: dict[str, int] = {}
    for row in rows:
        named[str(row["workbench_id"])] = named.get(str(row["workbench_id"]), 0) + 1
    if not named:
        return
    try:
        from .heartbeat_service import HeartbeatService

        heartbeat = HeartbeatService(db)
        for workbench_id, count in named.items():
            wb = db.workbenches.get(workbench_id, include_deleted=True)
            if wb is None or getattr(wb, "deleted", False):
                continue
            heartbeat.finished_notice(workbench_id, str(wb.name or "Automation"), count)
    except Exception as exc:
        log.warning("automation finished notice failed: %s", exc)


def _deliver_one(db: Any, principal: Any, wb: Any, row: dict[str, Any]) -> dict[str, Any]:
    target = str(wb.output_target or "inbox")
    artifact_id = str(row["artifact_id"])
    if target.startswith(PROJECT_UPDATES_PREFIX):
        return _to_project_updates(db, _delivery_principal(principal), wb, row,
                                   target[len(PROJECT_UPDATES_PREFIX):])
    if target == "needs_you":
        return _to_needs_you(db, principal, wb, row)
    if target == "today":
        # Betterment daily D9: Today reads the newest result itself.
        return {"artifact_id": artifact_id, "target": "today", "outcome": "shown"}
    if target.startswith(DESTINATION_PREFIX):
        return _to_destination(
            db, principal, target[len(DESTINATION_PREFIX):], artifact_id,
            automation_origin={
                "kind": "automation",
                "workbench_id": str(wb.id),
                "workbench_name": str(wb.name or ""),
                "run_id": str(row.get("source_run_id") or ""),
                "item_id": str(row.get("item_id") or ""),
                "artifact_id": artifact_id,
            },
        )
    return _to_inbox(db, wb, row)


# ── one result, delivered (an automation's artifact or a prompt step) ──


def deliver_text(
    db: Any, principal: Any, target: str, *, key: str, title: str, body: str,
    refs: list[str], generator: str, origin_words: str, used_item_id: str = "",
) -> dict[str, Any]:
    """Put one text result where ``target`` says, once per ``key``.

    The same paths an automation's result takes: a project_updates row with
    its source refs, an Inbox note, a Needs you item, or a prepared send (he
    presses Send). ``today`` files nothing: Today reads the result itself.
    ``key`` is the result's own stable ref (``program_step:<id>``): a second
    delivery of the same key makes nothing new. ``origin_words`` is the
    Markdown line under a note ("From the program [...](...)"). A failure
    raises; the caller keeps the result readable where it is."""
    who = _delivery_principal(principal)
    target = str(target or "inbox")
    if target.startswith(PROJECT_UPDATES_PREFIX):
        project_id = target[len(PROJECT_UPDATES_PREFIX):]
        if not str(body or "").strip():
            return {"target": target, "outcome": "failed", "error": "The engine returned no text."}
        update_id, outcome = _write_project_update(
            db, who, project_id, body=body, refs=refs, generator=generator, used_item_id=used_item_id)
        return {"target": target, "outcome": outcome, "update_id": update_id, "project_id": project_id}
    if target == "today":
        return {"target": "today", "outcome": "shown"}
    if target == "needs_you":
        made = _add_read_item(db, who, title, key)
        return {"target": "needs_you", "outcome": "added" if made else "kept",
                **({"action_item_id": made} if made else {})}
    note_id = result_note_id(key)
    filed = _file_note(db, note_id, title, f"{str(body or '').rstrip()}\n\n---\n{origin_words}",
                       inbox=not target.startswith(DESTINATION_PREFIX))
    if target.startswith(DESTINATION_PREFIX):
        destination_id = target[len(DESTINATION_PREFIX):]
        outcome, send_id = _prepare_send(db, who, destination_id, f"note:{note_id}", None)
        return {"target": target, "outcome": outcome, "note_id": note_id, "send_id": send_id}
    return {"target": "inbox", "outcome": "noted" if filed is not None else "kept", "note_id": note_id,
            "filed": bool(filed)}


def _remember_project_update(db: Any, artifact_id: Any, update_id: Any, project_id: Any) -> bool:
    """Link a delivered artifact to its exact, project-validated update."""
    clean_artifact_id = str(artifact_id or "").strip()
    clean_update_id = str(update_id or "").strip()
    clean_project_id = str(project_id or "").strip()
    if not clean_artifact_id or not clean_update_id or not clean_project_id:
        return False
    update = db.project_updates.get_update(clean_update_id)
    if update is None or str(update.get("project_id") or "") != clean_project_id:
        return False
    with db._connection() as conn:
        row = conn.execute(
            "SELECT structured_json FROM artifacts WHERE id = ?",
            (clean_artifact_id,),
        ).fetchone()
        if row is None:
            return False
        try:
            metadata = json.loads(row["structured_json"] or "{}")
        except (TypeError, ValueError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        metadata["project_update_id"] = clean_update_id
        conn.execute(
            "UPDATE artifacts SET structured_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(metadata, sort_keys=True), utc_now_iso(), clean_artifact_id),
        )
    return True


def _write_project_update(
    db: Any, principal: Any, project_id: str, *, body: str, refs: list[str], generator: str,
    used_item_id: str = "",
) -> tuple[str, str]:
    """``(update_id, "written")``: the project's one update for this result.

    A tool-capable engine already used the application's update producer
    during the run (``run_trace`` of ``used_item_id`` names the row it
    wrote): that row is the result; no second revision is made. Otherwise
    one update is written from ``body`` with the refs the run looked at,
    else ``refs``."""
    from .project_service import ProjectService
    from .project_update_service import ProjectUpdateService
    from .run_trace import use_by_item

    looked: list[str] = []
    if used_item_id:
        try:
            used = use_by_item(db, [used_item_id]).get(used_item_id, {})
            looked = [str(entry.get("ref") or "") for entry in used.get("looked_at", [])]
            for entry in used.get("wrote", []):
                ref = str(entry.get("ref") or "")
                if not ref.startswith("project_update:"):
                    continue
                existing_id = ref.split(":", 1)[1].strip()
                existing = db.project_updates.get_update(existing_id)
                if existing is not None and str(existing.get("project_id") or "") == project_id:
                    return existing_id, "written"
        except Exception:
            looked = []
    service = ProjectUpdateService(db, project_service=ProjectService(db))
    update = service.write_agent_update(
        principal, project_id, body_md=body, source_refs=looked or list(refs), generator=generator,
    )
    return str(update.get("id") or ""), "written"


def _to_project_updates(
    db: Any, principal: Any, wb: Any, row: dict[str, Any], project_id: str,
) -> dict[str, Any]:
    """Put one automation result in the project's one update ledger."""
    body = str(row.get("result") or "").strip()
    base = {"artifact_id": row["artifact_id"], "target": str(wb.output_target)}
    from .run_trace import use_by_item

    item_id = str(row.get("item_id") or "")
    try:
        wrote = any(str(entry.get("ref") or "").startswith("project_update:")
                    for entry in use_by_item(db, [item_id]).get(item_id, {}).get("wrote", []))
    except Exception:
        wrote = False
    if not body and not wrote:
        return {**base, "outcome": "failed", "error": "The update engine returned no text."}
    update_id, outcome = _write_project_update(
        db, principal, project_id, body=body, refs=sources_of(wb), generator=f"agent:automation:{wb.id}",
        used_item_id=item_id,
    )
    _remember_project_update(db, row["artifact_id"], update_id, project_id)
    return {**base, "outcome": outcome, "update_id": update_id, "project_id": project_id}


def inbox_directory_id(db: Any) -> Optional[str]:
    """The Inbox a result note is filed in (Betterment A6).

    The seeded Inbox, else a live drawer named Inbox. A desk that never had
    one (an unseeded, fresh desk) gets it, with the seed's own id, so a later
    seed finds it and adds no second one. An Inbox he deleted is not brought
    back: the note stays on the floor.
    """
    seeded = db.directories.get(INBOX_DIRECTORY_ID, include_deleted=True)
    if seeded is not None and not seeded.deleted:
        return INBOX_DIRECTORY_ID
    named = db.directories.find_by_normalized_name("Inbox")
    if named is not None:
        return str(named.id)
    if seeded is not None:
        return None
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    _changed("directory", INBOX_DIRECTORY_ID)
    return INBOX_DIRECTORY_ID


def _file_note(db: Any, note_id: str, title: str, body: str, *, inbox: bool = True) -> Optional[bool]:
    """Write the result note once. ``None``: it was there already; else
    whether it was filed in the Inbox."""
    if db.notes.get(note_id, include_deleted=True) is not None:
        return None
    db.notes.upsert(note_id=note_id, title=str(title or "Result"), body_markdown=body)
    filed = False
    inbox_id = inbox_directory_id(db) if inbox else None
    if inbox_id:
        db.directory_memberships.upsert(primitive_id=f"note:{note_id}", directory_id=inbox_id)
        filed = True
    _changed("note", note_id)
    return filed


def _to_inbox(db: Any, wb: Any, row: dict[str, Any]) -> dict[str, Any]:
    note_id = result_note_id(str(row["artifact_id"]))
    body = (
        f"{str(row['result'] or '').rstrip()}\n\n---\n"
        f"From the automation [{wb.name or 'Automation'}](/?open=workbench:{wb.id})."
    )
    filed = _file_note(db, note_id, str(row["title"] or wb.name or "Result"), body)
    if filed is None:
        return {"artifact_id": row["artifact_id"], "target": "inbox", "outcome": "kept", "note_id": note_id}
    return {"artifact_id": row["artifact_id"], "target": "inbox", "outcome": "noted",
            "note_id": note_id, "filed": filed}


def _add_read_item(db: Any, principal: Any, title: str, source_ref: str) -> Optional[str]:
    """One Door item "Read the new result", owned by the owner and due
    today, so Needs you counts it (the same rule the agent follow-through
    uses: delivery/follow_through.py). ``None`` when the source has one."""
    from .door_service import DoorService
    from .follow_through_service import FollowThroughService

    door = DoorService(FollowThroughService(db), None, None, None, db=db)  # type: ignore[arg-type]
    if door.has_item_for_source(source_ref):
        return None
    item = door.add_item(
        principal, f"Read the new result: {title}", owner="me",
        due=datetime.now().astimezone().date().isoformat(),
        source_type="automation_result", source_ref=source_ref,
    )
    return str(item["id"])


def _to_needs_you(db: Any, principal: Any, wb: Any, row: dict[str, Any]) -> dict[str, Any]:
    made = _add_read_item(db, principal, str(row["title"] or wb.name), f"artifact:{row['artifact_id']}")
    if made is None:
        return {"artifact_id": row["artifact_id"], "target": "needs_you", "outcome": "kept"}
    return {"artifact_id": row["artifact_id"], "target": "needs_you", "outcome": "added",
            "action_item_id": made}


def _prepare_send(
    db: Any, principal: Any, destination_id: str, document_ref: str,
    automation_origin: Mapping[str, Any] | None,
) -> tuple[str, str]:
    """``(outcome, send_id)``: ``kept`` when the document has a live send to
    the destination, else ``prepared``. Prepare only: the bytes are frozen
    in a ``prepared`` send; nothing leaves until he presses Send."""
    with db._connection() as conn:
        seen = conn.execute(
            "SELECT id FROM channel_sends WHERE document_ref=? AND destination_id=? AND state!='discarded'",
            (document_ref, destination_id),
        ).fetchone()
    if seen is not None:
        return "kept", str(seen["id"])
    from .. import operations
    from .channel_service import ChannelService

    # The hub's installed registry owns the normal channel service.  This
    # internal delivery needs the same operation descriptors and kernel path,
    # while carrying source-owned automation provenance into this one frozen
    # prepare effect.  Bind a narrow registry over the trusted service rather
    # than asking ``for_runtime`` (which deliberately returns the installed
    # live instance and would drop the origin).
    from ..runtime.composition import notify_desk_changed

    registry = operations.bind_available({
        "channel_service": ChannelService(
            db, on_changed=notify_desk_changed, automation_origin=automation_origin,
        ),
    })
    result, _kernel = registry.invoke_receipted(
        principal, "channel.prepare", {"document_ref": document_ref, "destination_id": destination_id},
    )
    send = (result or {}).get("send") or {}
    return "prepared", str(send.get("id") or "")


def _to_destination(
    db: Any, principal: Any, destination_id: str, artifact_id: str,
    *, automation_origin: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    outcome, send_id = _prepare_send(db, principal, destination_id, f"artifact:{artifact_id}", automation_origin)
    return {"artifact_id": artifact_id, "target": DESTINATION_PREFIX + destination_id,
            "outcome": outcome, "send_id": send_id}


def _changed(kind: str, obj_id: str) -> None:
    try:
        from holdspeak.runtime.composition import notify_desk_changed

        notify_desk_changed(kind, obj_id, "create")
    except Exception:
        pass
