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
        try:
            ref = qualified_ref(raw.strip())
        except ValueError as exc:
            raise ValidationError(f"Unknown source: {raw.strip()} ({exc})") from None
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
    if event is not None:
        body = f"{body}\n\n{_event_block(event)}"
    return db.workbench_items.upsert(
        item_id=clean_id,
        workbench_id=wb.id,
        title=str(title or occurrence_title(wb)),
        body=body,
        grounding={"refs": sources_of(wb)} if sources_of(wb) else {},
        context={**(context or {}), OCCURRENCE: True},
    )


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
                profile_id = str(entry.get("profile_id") or "")
                if profile_id.startswith("legacy-"):
                    row = conn.execute(
                        "SELECT kind, base_url FROM profiles WHERE id=?",
                        (profile_id.removeprefix("legacy-"),),
                    ).fetchone()
                    if row is not None and str(row["kind"]) == "cliCommand":
                        endpoints.append(row["base_url"])
                    continue
                row = conn.execute(
                    """SELECT d.kind, d.endpoint FROM model_profile_binding_heads h
                       JOIN model_profile_binding_revisions b
                         ON b.binding_id = h.binding_id AND b.revision = h.revision
                       JOIN deployment_revisions d ON d.id = b.deployment_revision_id
                       WHERE h.profile_id = ?""",
                    (profile_id,),
                ).fetchone()
                if row is not None and str(row["kind"]) == "cli_engine":
                    endpoints.append(row["endpoint"])
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


def results_of(db: Any, workbench_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """The occurrence results, newest first: one per run."""
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT i.id, i.title, i.status, i.result, i.result_artifact_id, i.completed_at,
                      i.created_at, a.status AS artifact_status
               FROM workbench_items i LEFT JOIN artifacts a ON a.id = i.result_artifact_id
               WHERE i.workbench_id = ? AND i.parked = 0
                 AND json_extract(i.context_json, '$.occurrence') = 1
               ORDER BY COALESCE(i.completed_at, i.created_at) DESC, i.id DESC LIMIT ?""",
            (workbench_id, max(1, int(limit))),
        ).fetchall()
    results = []
    for row in rows:
        failed = str(row["status"]) == "failed"
        results.append({
            "item_id": str(row["id"]),
            "title": str(row["title"] or ""),
            "status": str(row["status"]),
            "artifact_id": row["result_artifact_id"],
            "new": str(row["artifact_status"] or "") == "new",
            "error": str(row["result"] or "").removeprefix("Error: ") if failed else None,
            "completed_at": row["completed_at"],
        })
    return results


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
    return outcomes


def _deliver_one(db: Any, principal: Any, wb: Any, row: dict[str, Any]) -> dict[str, Any]:
    target = str(wb.output_target or "inbox")
    artifact_id = str(row["artifact_id"])
    if target == "needs_you":
        return _to_needs_you(db, principal, wb, row)
    if target.startswith(DESTINATION_PREFIX):
        return _to_destination(db, principal, target[len(DESTINATION_PREFIX):], artifact_id)
    return _to_inbox(db, wb, row)


def _to_inbox(db: Any, wb: Any, row: dict[str, Any]) -> dict[str, Any]:
    note_id = "note_result_" + hashlib.sha256(str(row["artifact_id"]).encode()).hexdigest()[:16]
    if db.notes.get(note_id, include_deleted=True) is not None:
        return {"artifact_id": row["artifact_id"], "target": "inbox", "outcome": "kept", "note_id": note_id}
    body = (
        f"{str(row['result'] or '').rstrip()}\n\n---\n"
        f"From the automation [{wb.name or 'Automation'}](/?open=workbench:{wb.id})."
    )
    db.notes.upsert(note_id=note_id, title=str(row["title"] or wb.name or "Result"), body_markdown=body)
    filed = False
    directory = db.directories.get(INBOX_DIRECTORY_ID)
    if directory is not None:
        # The Inbox exists on a seeded desk. A desk without it keeps the note
        # on the floor; this never makes or restores the Inbox.
        db.directory_memberships.upsert(primitive_id=f"note:{note_id}", directory_id=INBOX_DIRECTORY_ID)
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
