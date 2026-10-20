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
- ``destination:<id>``: ``channel.prepare`` only. He presses Send;
- ``today`` (Betterment daily D9): nothing is filed. The newest result is
  Today's Prepared block (``prepared_for_today``).

An automation with no instruction keeps the old queue run.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from ..logging_config import get_logger
from ..timestamps import local_now, utc_now_iso
from .errors import ValidationError

log = get_logger("services.automation_runs")

#: The context marker of an occurrence item (``workbench_items.context_json``).
OCCURRENCE = "occurrence"
#: The per-item time limit for an HTTP engine (seconds).
HTTP_ITEM_SECONDS = 60.0
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


def occurrence_id(workbench_id: str, key: str) -> str:
    return "wbocc_" + hashlib.sha256(f"{workbench_id}:{key}".encode()).hexdigest()[:20]


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


def materialize_hand_items(db: Any, wb: Any) -> list[Any]:
    """Create or read one occurrence item for every eligible source item."""
    from ..timestamps import utc_now_iso

    items: list[Any] = []
    instruction = str(getattr(wb, "instruction", "") or "").strip()
    for source in hand_sources(db, wb):
        item_id = hand_item_id(wb.id, source["ref"])
        context = {
            OCCURRENCE: True,
            "agent_hand": {
                "source_ref": source["ref"],
                "kind": source["kind"],
                "id": source["id"],
                "status": "pending",
            },
        }
        # Materialisation itself is a race with another Run press.  Insert
        # only when absent under the database write lock; an existing row's
        # launch context is immutable to this step.
        with db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing_row = conn.execute("SELECT id FROM workbench_items WHERE id=?", (item_id,)).fetchone()
            if existing_row is None:
                now = utc_now_iso()
                conn.execute(
                    """INSERT INTO workbench_items
                       (id, workbench_id, title, body, priority, status,
                        grounding_json, context_json, created_at, last_modified)
                       VALUES (?, ?, ?, ?, 3, 'pending', ?, ?, ?, ?)""",
                    (item_id, wb.id, source["title"], instruction,
                     json.dumps({"refs": [source["ref"]]}, sort_keys=True),
                     json.dumps(context, sort_keys=True), now, now),
                )
        existing = db.workbench_items.get(item_id, include_parked=True)
        if existing is None:
            continue
        items.append(existing)
    return items


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
    return [{
        "workbench_id": str(row["workbench_id"]),
        "name": str(row["name"] or "Automation"),
        "new_count": int(row["new_count"]),
        "newest_at": row["newest_at"],
    } for row in rows]


def prepared_for_today(db: Any, principal: Any) -> Optional[dict[str, Any]]:
    """Betterment daily D9: Today's Prepared block, or None.

    The newest done result of a live automation whose Put it in is Today
    (Morning prep), with its automation's name, the engine it runs on (the
    With line's name) and what its agent looked at. None when no such
    automation has a done result: Today then draws no block at all."""
    sync_agent_results(db)
    with db._connection() as conn:
        row = conn.execute(
            """SELECT w.id AS workbench_id FROM workbench_items i
               JOIN workbenches w ON w.id = i.workbench_id
               WHERE w.deleted = 0 AND w.output_target = 'today' AND i.parked = 0 AND i.status = 'done'
                 AND json_extract(i.context_json, '$.occurrence') = 1
               ORDER BY COALESCE(i.completed_at, i.created_at) DESC, i.id DESC LIMIT 1""",
        ).fetchone()
    if row is None:
        return None
    workbench_id = str(row["workbench_id"])
    wb = db.workbenches.get(workbench_id)
    result = next((r for r in results_of(db, workbench_id, limit=5) if r["status"] == "done"), None)
    if wb is None or result is None:
        return None
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
    if target.startswith(PROJECT_UPDATES_PREFIX):
        return _to_project_updates(db, _delivery_principal(principal), wb, row,
                                   target[len(PROJECT_UPDATES_PREFIX):])
    if target == "needs_you":
        return _to_needs_you(db, principal, wb, row)
    if target == "today":
        # Betterment daily D9: Today reads the newest result itself.
        return {"artifact_id": artifact_id, "target": "today", "outcome": "shown"}
    if target.startswith(DESTINATION_PREFIX):
        return _to_destination(db, principal, target[len(DESTINATION_PREFIX):], artifact_id)
    return _to_inbox(db, wb, row)


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


def _to_project_updates(
    db: Any, principal: Any, wb: Any, row: dict[str, Any], project_id: str,
) -> dict[str, Any]:
    """Put one automation result in the project's one update ledger."""
    from .project_service import ProjectService
    from .project_update_service import ProjectUpdateService
    from .run_trace import use_by_item

    item_id = str(row.get("item_id") or "")
    refs: list[str] = []
    try:
        used = use_by_item(db, [item_id]).get(item_id, {})
        refs = [str(entry.get("ref") or "") for entry in used.get("looked_at", [])]
        # A tool-capable update already used the application's update
        # producer. Reuse that row as the automation result; do not create a
        # second project_updates revision for the same run.
        for entry in used.get("wrote", []):
            ref = str(entry.get("ref") or "")
            if not ref.startswith("project_update:"):
                continue
            existing_id = ref.split(":", 1)[1].strip()
            existing = db.project_updates.get_update(existing_id)
            if existing is not None and str(existing.get("project_id") or "") == project_id:
                _remember_project_update(db, row["artifact_id"], existing_id, project_id)
                return {"artifact_id": row["artifact_id"], "target": str(wb.output_target),
                        "outcome": "written", "update_id": existing_id,
                        "project_id": project_id}
    except Exception:
        refs = []
    if not refs:
        refs = sources_of(wb)
    body = str(row.get("result") or "").strip()
    if not body:
        return {"artifact_id": row["artifact_id"], "target": str(wb.output_target),
                "outcome": "failed", "error": "The update engine returned no text."}
    service = ProjectUpdateService(db, project_service=ProjectService(db))
    update = service.write_agent_update(
        principal, project_id, body_md=body, source_refs=refs,
        generator=f"agent:automation:{wb.id}",
    )
    _remember_project_update(db, row["artifact_id"], update.get("id"), project_id)
    return {"artifact_id": row["artifact_id"], "target": str(wb.output_target),
            "outcome": "written", "update_id": str(update.get("id") or ""),
            "project_id": project_id}


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
