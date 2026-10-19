"""One automation = one instruction + sources; each run = one result (Betterment A2).

The stored kind stays ``workbench`` (``docs/internal/betterment/workbench/
RECIPE.md``, slice A2). An automation with an ``instruction`` does not run a
typed queue. Each run makes one *occurrence* item: its title is
"<name>, <date>" (or the event's title), its body is the instruction, and its
grounding is the automation's sources (plus the event's subject). The runner
runs that one item; its artifact starts ``new`` (decision 5) and becomes
``read`` when it is opened. Then the result goes where ``output_target`` says:

- ``inbox`` (the default): one Note, filed in the Inbox, with a link back;
- ``needs_you``: one Door item owned by the owner and due today, so Needs
  you counts it;
- ``destination:<id>``: ``channel.prepare`` only. He presses Send.

An automation with no instruction keeps the old queue run.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from ..logging_config import get_logger
from ..timestamps import local_now
from .errors import ValidationError

log = get_logger("services.automation_runs")

#: The context marker of an occurrence item (``workbench_items.context_json``).
OCCURRENCE = "occurrence"
#: The per-item time limit for an HTTP engine (seconds).
HTTP_ITEM_SECONDS = 60.0
#: The Inbox zone (``holdspeak/seeds/fresh-desk.yaml``).
INBOX_DIRECTORY_ID = "hs-seed-inbox"
OUTPUT_TARGETS = ("inbox", "needs_you")
DESTINATION_PREFIX = "destination:"
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
    """``inbox`` | ``needs_you`` | ``destination:<saved destination id>``."""
    target = str(value or "inbox").strip()
    if target in OUTPUT_TARGETS:
        return target
    if target.startswith(DESTINATION_PREFIX):
        destination_id = target[len(DESTINATION_PREFIX):].strip()
        if destination_id and db.channel_destinations.get(destination_id) is not None:
            return DESTINATION_PREFIX + destination_id
        raise ValidationError(f"Unknown destination: {destination_id or '(none)'}")
    raise ValidationError("output_target must be inbox, needs_you or destination:<id>")


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


def plain_agent(wb: Any) -> Any:
    """The agent of an automation that has an instruction and no recipe."""
    from types import SimpleNamespace

    return SimpleNamespace(
        id="", name=str(wb.name or "Automation"), system_prompt=PLAIN_SYSTEM_PROMPT,
        last_modified="", manual_context="", kb_id=None,
    )


# ── the occurrence item ────────────────────────────────────────────────


def is_occurrence(item: Any) -> bool:
    try:
        context = json.loads(getattr(item, "context_json", "") or "{}")
    except (TypeError, ValueError):
        return False
    return isinstance(context, dict) and bool(context.get(OCCURRENCE))


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


def mint_occurrence(
    db: Any,
    wb: Any,
    *,
    item_id: Optional[str] = None,
    title: Optional[str] = None,
    event: Optional[dict[str, Any]] = None,
    context: Optional[dict[str, Any]] = None,
) -> Any:
    """Add the one item a run of an instruction automation runs.

    A known ``item_id`` (a scheduled minute, a request id, an event) is
    made once: a replayed start finds the item it made and adds none.
    """
    clean_id = str(item_id or ("wbocc_" + uuid.uuid4().hex[:16]))
    existing = db.workbench_items.get(clean_id, include_parked=True)
    if existing is not None:
        return existing
    body = str(wb.instruction or "").strip()
    refs, about = expand_sources(db, sources_of(wb))
    if about:
        body = f"{body}\n\n[ABOUT]\n" + "\n".join(about)
    if event is not None:
        body = f"{body}\n\n{_event_block(event)}"
    return db.workbench_items.upsert(
        item_id=clean_id,
        workbench_id=wb.id,
        title=str(title or occurrence_title(wb)),
        body=body,
        grounding={"refs": refs} if refs else {},
        context={**(context or {}), OCCURRENCE: True},
    )


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


def occurrence_id(workbench_id: str, key: str) -> str:
    return "wbocc_" + hashlib.sha256(f"{workbench_id}:{key}".encode()).hexdigest()[:20]


# ── the per-engine time limit ──────────────────────────────────────────


def _seconds_for(endpoints: list[Any]) -> float:
    from ..intel.cli_engine import parse_cli_endpoint

    seconds = HTTP_ITEM_SECONDS
    for endpoint in endpoints:
        parsed = parse_cli_endpoint(endpoint)
        if parsed is not None:
            seconds = max(seconds, float(parsed[0].timeout_seconds))
    return seconds


def item_seconds(db: Any, route: dict[str, Any]) -> float:
    """The time limit for one item on a frozen route (a scheduled run): 60 s
    for an HTTP engine, the preset's timeout for a CLI engine; the longest
    leg of the chain."""
    ids = [str(entry.get("deployment_revision_id") or "") for entry in route.get("entries") or []]
    endpoints: list[Any] = []
    with db._connection() as conn:
        for revision_id in ids:
            row = conn.execute(
                "SELECT kind, endpoint FROM deployment_revisions WHERE id=?", (revision_id,)
            ).fetchone()
            if row is not None and str(row["kind"]) == "cli_engine":
                endpoints.append(row["endpoint"])
    return _seconds_for(endpoints)


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


def assigned_item_seconds(db: Any, workbench_id: str) -> float:
    """The same limit for a press or an event: read from the engine assigned
    to this automation's ``workbench.item`` job before the run is admitted
    (the admitted deadline is bound into the route bundle and cannot move)."""
    from .inference_assignment_service import InferenceAssignmentService

    service = InferenceAssignmentService(db)
    try:
        capability = service._require_assignable("workbench.item")
        with db._connection() as conn:
            resolved = service._resolve(
                conn, capability, subject_kind="workbench", subject_id=workbench_id,
            )
            entries = list((resolved.get("assignment") or {}).get("entries") or [])
            endpoints: list[Any] = []
            for entry in entries:
                endpoint = cli_endpoint_of(conn, str(entry.get("profile_id") or ""))
                if endpoint:
                    endpoints.append(endpoint)
    except Exception as exc:  # no readable assignment: the run's own admission says why
        log.debug("automation %s: engine limit read failed: %s", workbench_id, exc)
        return HTTP_ITEM_SECONDS
    return _seconds_for(endpoints)


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
    return [{
        "workbench_id": str(row["workbench_id"]),
        "name": str(row["name"] or "Automation"),
        "new_count": int(row["new_count"]),
        "newest_at": row["newest_at"],
    } for row in rows]


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
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT i.id, i.title, i.status, i.result, i.result_artifact_id, i.completed_at,
                      i.created_at, i.claimed_at, i.result_egress_json, a.status AS artifact_status,
                      r.model AS run_model
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
    results = []
    for row in rows:
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
        })
    return results


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


def deliver_run(db: Any, principal: Any, run: Any) -> list[dict[str, Any]]:
    """Put each new occurrence result of one run where its automation says.

    Idempotent: a note, a Door item or a prepared send is made once for one
    result. A failed delivery is logged and returned; it never fails the run.
    """
    run_id = str((run or {}).get("run_id") or "") if isinstance(run, dict) else ""
    if not run_id or (isinstance(run, dict) and run.get("replayed")):
        return []
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT a.id AS artifact_id, i.id AS item_id, i.workbench_id, i.title, i.result
               FROM artifacts a JOIN workbench_items i ON i.id = a.source_item_id
               WHERE a.source_run_id = ? AND i.status = 'done'
                 AND json_extract(i.context_json, '$.occurrence') = 1""",
            (run_id,),
        ).fetchall()
    outcomes = []
    for row in rows:
        wb = db.workbenches.get(str(row["workbench_id"]), include_deleted=True)
        if wb is None:
            continue
        try:
            outcomes.append(_deliver_one(db, _delivery_principal(principal), wb, dict(row)))
        except Exception as exc:  # a result stays readable on the automation
            log.warning("automation %s: delivery of %s failed: %s", wb.id, row["artifact_id"], exc)
            outcomes.append({"artifact_id": row["artifact_id"], "target": wb.output_target,
                             "outcome": "failed", "error": str(exc)})
    _finished_notices(db, rows)
    return outcomes


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
    if target == "needs_you":
        return _to_needs_you(db, principal, wb, row)
    if target.startswith(DESTINATION_PREFIX):
        return _to_destination(db, principal, target[len(DESTINATION_PREFIX):], artifact_id)
    return _to_inbox(db, wb, row)


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


def _to_inbox(db: Any, wb: Any, row: dict[str, Any]) -> dict[str, Any]:
    note_id = result_note_id(str(row["artifact_id"]))
    if db.notes.get(note_id, include_deleted=True) is not None:
        return {"artifact_id": row["artifact_id"], "target": "inbox", "outcome": "kept", "note_id": note_id}
    body = (
        f"{str(row['result'] or '').rstrip()}\n\n---\n"
        f"From the automation [{wb.name or 'Automation'}](/?open=workbench:{wb.id})."
    )
    db.notes.upsert(note_id=note_id, title=str(row["title"] or wb.name or "Result"), body_markdown=body)
    filed = False
    inbox_id = inbox_directory_id(db)
    if inbox_id:
        db.directory_memberships.upsert(primitive_id=f"note:{note_id}", directory_id=inbox_id)
        filed = True
    _changed("note", note_id)
    return {"artifact_id": row["artifact_id"], "target": "inbox", "outcome": "noted",
            "note_id": note_id, "filed": filed}


def _to_needs_you(db: Any, principal: Any, wb: Any, row: dict[str, Any]) -> dict[str, Any]:
    from .door_service import DoorService
    from .follow_through_service import FollowThroughService

    source_ref = f"artifact:{row['artifact_id']}"
    door = DoorService(FollowThroughService(db), None, None, None, db=db)  # type: ignore[arg-type]
    if door.has_item_for_source(source_ref):
        return {"artifact_id": row["artifact_id"], "target": "needs_you", "outcome": "kept"}
    # Owned by the owner and due today, so Needs you counts it (the same
    # rule the agent follow-through uses: delivery/follow_through.py).
    item = door.add_item(
        principal, f"Read the new result: {row['title'] or wb.name}", owner="me",
        due=datetime.now().astimezone().date().isoformat(),
        source_type="automation_result", source_ref=source_ref,
    )
    return {"artifact_id": row["artifact_id"], "target": "needs_you", "outcome": "added",
            "action_item_id": item["id"]}


def _to_destination(db: Any, principal: Any, destination_id: str, artifact_id: str) -> dict[str, Any]:
    document_ref = f"artifact:{artifact_id}"
    with db._connection() as conn:
        seen = conn.execute(
            "SELECT id FROM channel_sends WHERE document_ref=? AND destination_id=? AND state!='discarded'",
            (document_ref, destination_id),
        ).fetchone()
    if seen is not None:
        return {"artifact_id": artifact_id, "target": DESTINATION_PREFIX + destination_id,
                "outcome": "kept", "send_id": str(seen["id"])}
    from .. import operations
    from .channel_service import ChannelService

    # Prepare only: the bytes are frozen in a ``prepared`` send; nothing leaves
    # until he presses Send.
    registry = operations.for_runtime(channel_service=lambda: ChannelService(db))
    result, _kernel = registry.invoke_receipted(
        principal, "channel.prepare", {"document_ref": document_ref, "destination_id": destination_id},
    )
    send = (result or {}).get("send") or {}
    return {"artifact_id": artifact_id, "target": DESTINATION_PREFIX + destination_id,
            "outcome": "prepared", "send_id": str(send.get("id") or "")}


def _changed(kind: str, obj_id: str) -> None:
    try:
        from holdspeak.runtime.composition import notify_desk_changed

        notify_desk_changed(kind, obj_id, "create")
    except Exception:
        pass
