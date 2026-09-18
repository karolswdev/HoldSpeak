"""HS-172-07 / HS-200-14 — Room People projection.

HS-172-07 collected distinct owner identities from a Room's Watch snapshot
entities, resolved each through the People resolver, and returned resolved
people with per-Room counts.

HS-200-14 makes that projection USEFUL for preparation, inside the same
boundary:

* the population is every person the Project NAMES -- an owner on one of
  its commitments (story 12's records), an identity on one of its Watches
  (172-07), or a relationship the ledger links to it (``project_refs``);
* each linked person carries their open commitments (source span linked)
  and their observable work facts (PRs waiting, assignments), each with
  the source it came from -- nothing inferred, nothing scored;
* an owner string two people could be meant by is AMBIGUOUS, listed with
  its candidates, and NEVER attributed (AC1);
* a locked, unconfigured or unavailable ledger is NAMED in the payload
  (``state``), never drawn as an empty section (AC5).

No writes.  No raw logins in the payload (Article III): an unresolved
Watch identity stays out (172-07 law); an unresolved RECORD owner is shown
under the owner string the plaintext record already carries.  Only
``id`` and ``display_name`` cross from the People store, in memory, for
the authenticated owner -- the same two fields 172-07 crosses.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .project_service import ProjectService

#: The ledger states the projection can name.  ``ready`` is the only one
#: that resolves anybody; the rest turn every named person into a gap.
LEDGER_STATES = ("ready", "locked", "unconfigured", "unavailable")

#: Per-owner link states.  The last three mirror LEDGER_STATES: an owner
#: under an unreadable ledger is typed with the ledger's OWN state, so a
#: row never says LOCKED under a head that says NOT SET UP (counsel P2-ii).
LINK_STATES = ("linked", "ambiguous", "not_linked", "locked", "unconfigured", "unavailable")

#: Owner strings that name the owner himself, never a person on the ledger
#: (people_service._RESERVED_OWNER_ALIASES).  Skipped from the population
#: (counsel P2-i): a `me` row would be a person the ledger refuses to link.
RESERVED_OWNERS = frozenset({"me", "remote", "you"})

#: Watch states whose snapshot is a live observation.  A paused or retired
#: Watch's facts are OMITTED and the omission named (counsel P2-v).
LIVE_WATCH_STATES = frozenset({"active", "tested", ""})


def _extract_identities(project_service: ProjectService, project_id: str) -> dict[str, dict[str, Any]]:
    """Extract distinct identities from Watch entities with per-identity counts.

    Returns ``{identity: {"prs_waiting": N, "assignments_open": N,
    "assignments_overdue": N, "_raw": str, "_sources": {watch_id: {...}}}}``.
    GitHub PR entities: reviewRequests (list of logins waiting on review).
    Jira issue entities: assignee field.

    HS-200-14: ``_sources`` records WHICH Watch each count came from, so the
    face can put a source chip on every fact.
    """
    watches = project_service._db.automations.list_project_watches(project_id)
    identities: dict[str, dict[str, Any]] = {}
    now = datetime.now(timezone.utc)

    def _bucket(raw: str) -> dict[str, Any]:
        key = raw.lower()
        if key not in identities:
            identities[key] = {
                "prs_waiting": 0,
                "assignments_open": 0,
                "assignments_overdue": 0,
                "_raw": raw,
                "_sources": {},
            }
        return identities[key]

    def _source(bucket: dict[str, Any], watch: dict[str, Any]) -> dict[str, Any]:
        watch_id = str(watch.get("id") or "")
        sources = bucket["_sources"]
        if watch_id not in sources:
            sources[watch_id] = {
                "watch_id": watch_id,
                "connector_id": str(watch.get("connector_id") or ""),
                "label": _watch_label(watch),
                "state": _watch_state(watch),
                "prs_waiting": 0,
                "assignments_open": 0,
                "assignments_overdue": 0,
            }
        return sources[watch_id]

    for watch in watches:
        connector_id = watch.get("connector_id", "")
        query_kind = watch.get("query_kind", "")
        snapshot = watch.get("snapshot")
        if not snapshot:
            continue
        entities = ProjectService._entities(snapshot)
        live = _watch_state(watch) in LIVE_WATCH_STATES
        if not live:
            # A revoked source still NAMES its people (the identity is a
            # fact the Watch observed) but contributes no count: the row
            # carries the source with its state instead of a number.
            for entity in entities:
                if connector_id == "gh" and query_kind == "pull_requests":
                    for login in (entity.get("review_requests") or entity.get("reviewRequests") or []):
                        login_str = str(login).strip()
                        if login_str:
                            _source(_bucket(login_str), watch)
                elif connector_id == "jira" and query_kind == "issues":
                    assignee = str(entity.get("assignee") or "").strip()
                    if assignee:
                        _source(_bucket(assignee), watch)
            continue

        if connector_id == "gh" and query_kind == "pull_requests":
            for entity in entities:
                state = str(entity.get("state", "")).lower()
                if state != "open":
                    continue
                review_requests = (
                    entity.get("review_requests")
                    or entity.get("reviewRequests")
                    or []
                )
                for login in review_requests:
                    login_str = str(login).strip()
                    if not login_str:
                        continue
                    bucket = _bucket(login_str)
                    bucket["prs_waiting"] += 1
                    _source(bucket, watch)["prs_waiting"] += 1

        elif connector_id == "jira" and query_kind == "issues":
            for entity in entities:
                assignee = str(entity.get("assignee") or "").strip()
                if not assignee:
                    continue
                bucket = _bucket(assignee)
                bucket["assignments_open"] += 1
                source = _source(bucket, watch)
                source["assignments_open"] += 1

                # Check overdue
                due_at = entity.get("due_at") or entity.get("dueDate")
                if due_at:
                    try:
                        due_str = str(due_at).replace("Z", "+00:00")
                        if "T" in due_str:
                            due_str = due_str.split("T")[0]
                        due_dt = datetime.fromisoformat(due_str)
                        if due_dt.replace(tzinfo=None) < now.replace(tzinfo=None):
                            bucket["assignments_overdue"] += 1
                            source["assignments_overdue"] += 1
                    except (ValueError, TypeError):
                        pass

    return identities


def _watch_state(watch: dict[str, Any]) -> str:
    """`paused` / `retired` from the row's state, or `disabled` when the
    legacy flag is off; empty for a live Watch."""
    state = str(watch.get("state") or "").strip().lower()
    if state in ("paused", "retired"):
        return state
    enabled = watch.get("enabled", 1)
    if enabled in (0, False, "0"):
        return "disabled"
    return state if state not in LIVE_WATCH_STATES else ""


def _watch_label(watch: dict[str, Any]) -> str:
    """The Watch's own name (what the SOURCES section already shows)."""
    name = str(watch.get("name") or "").strip()
    if name:
        return name
    query = watch.get("query") or {}
    if isinstance(query, dict):
        repo = query.get("repository")
        if repo:
            return str(repo)
        projects = query.get("projects")
        if isinstance(projects, list) and projects:
            return ", ".join(str(p) for p in projects)
    return str(watch.get("connector_id") or "watch")


def _facts_for(counts: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Observable work facts, one per (live Watch, kind), each with its
    source -- and the sources OMITTED because the Watch is paused, retired
    or disabled, each with its state (never a silent gap)."""
    facts: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    for source in counts.get("_sources", {}).values():
        chip = {
            "kind": "watch",
            "watch_id": source["watch_id"],
            "connector_id": source["connector_id"],
            "label": source["label"],
        }
        if source.get("state"):
            omitted.append(dict(chip, state=source["state"]))
            continue
        for kind in ("prs_waiting", "assignments_open", "assignments_overdue"):
            n = int(source.get(kind) or 0)
            if n > 0:
                facts.append({"kind": kind, "count": n, "source": chip})
    return facts, omitted


def _read_room_commitments(project_service: ProjectService, project_id: str) -> list[dict[str, Any]]:
    """OPEN commitments on the Project's decisions, with their source span.

    The lifecycle vocabulary is follow_through_service's: `Done`/`Dismiss`
    write ``closed`` (follow_through_service.py:401), `Reopen` writes
    ``open`` (:448).  Only ``open`` counts (counsel P0: ``!= 'completed'``
    matched nothing the real verb writes, so a Done commitment stayed open
    in PEOPLE forever).

    Story 12's chain: ``decisions`` (source_meeting_id) -> ``decision_commitments``
    (owner, due_at) -> ``action_items`` (task); the confirmed proposal, when
    one exists, carries the transcript span (``segment_index``).
    """
    with project_service._db._connection() as conn:
        rows = conn.execute(
            """SELECT c.id, c.owner, c.due_at, c.status,
                      ai.task AS text,
                      d.source_meeting_id AS meeting_id,
                      m.title AS meeting_title,
                      p.segment_index AS segment_index,
                      p.span_start AS span_start,
                      p.span_end AS span_end
               FROM decision_commitments c
               JOIN decisions d ON d.id = c.decision_id
               JOIN meeting_projects mp
                    ON mp.meeting_id = d.source_meeting_id
                   AND mp.project_id = ?
               LEFT JOIN action_items ai ON ai.id = c.action_item_id
               LEFT JOIN meetings m ON m.id = d.source_meeting_id
               LEFT JOIN follow_through_proposals p
                    ON p.commitment_id = c.id AND p.state = 'confirmed'
               WHERE c.status = 'open'
                 AND d.deleted = 0
               ORDER BY c.due_at ASC NULLS LAST, c.created_at ASC""",
            (project_id,),
        ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        source: dict[str, Any] = {
            "kind": "meeting",
            "meeting_id": row["meeting_id"],
            "label": row["meeting_title"] or "Meeting",
        }
        if row["segment_index"] is not None:
            source["segment_index"] = int(row["segment_index"])
        if row["span_start"] is not None:
            source["span_start"] = float(row["span_start"])
        if row["span_end"] is not None:
            source["span_end"] = float(row["span_end"])
        items.append({
            "id": row["id"],
            "text": row["text"] or "",
            "due_at": row["due_at"],
            "owner": str(row["owner"] or "").strip(),
            "source": source,
        })
    return items


def _ledger_state(people_service: Any) -> str:
    if people_service is None:
        return "unavailable"
    reader = getattr(people_service, "readiness_state", None)
    if not callable(reader):
        return "unavailable"
    try:
        state = str(reader() or "unavailable")
    except Exception:
        return "unavailable"
    if state == "ready":
        return "ready"
    if state == "locked":
        return "locked"
    if state == "unconfigured":
        return "unconfigured"
    return "unavailable"


def room_people_preparation(
    project_service: ProjectService,
    people_service: Any,
    project_id: str,
    principal: Any = None,
) -> dict[str, Any]:
    """The Room's PEOPLE projection (HS-200-14).

    Returns::

        {
          "state": "ready" | "locked" | "unconfigured" | "unavailable",
          "expected": M,              # people the Project names
          "resolved": N,              # of them, linked to a ledger entry
          "gaps": {"ambiguous": a, "not_linked": b, "unreadable": c},
          "people": [ ...linked rows... ],       # 172-07 shape + commitments + facts
          "unresolved": [ ...gap rows... ],      # owner string + link + candidates
        }

    ``people`` keeps 172-07's row shape (``relationship_id``,
    ``display_name``, the three counts absent at zero) so the shade's
    PEOPLE lane keeps reading it unchanged, and adds ``link``,
    ``commitments`` and ``facts``.
    """
    project_service._require_project(project_id)

    state = _ledger_state(people_service)
    commitments = _read_room_commitments(project_service, project_id)
    identities = _extract_identities(project_service, project_id)

    # Owners the Project's own records name, grouped by owner string.
    owners: dict[str, dict[str, Any]] = {}
    for item in commitments:
        owner = item["owner"]
        if not owner or owner.casefold() in RESERVED_OWNERS:
            continue
        key = owner.casefold()
        owners.setdefault(key, {"owner": owner, "commitments": []})
        owners[key]["commitments"].append(item)

    linked: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []

    def _row(rel_id: str, display_name: str) -> dict[str, Any]:
        if rel_id not in linked:
            linked[rel_id] = {
                "relationship_id": rel_id,
                "display_name": display_name,
                "link": "linked",
                "commitments": [],
                "facts": [],
                "omitted_sources": [],
            }
        return linked[rel_id]

    if state != "ready":
        for bucket in owners.values():
            unresolved.append({
                "owner": bucket["owner"],
                "link": state,
                "candidates": [],
                "commitments": bucket["commitments"],
            })
        # Watch identities cannot be named (no ledger to resolve them
        # against, and a raw login never crosses); they are not counted.
        expected = len(unresolved)
        return {
            "state": state,
            "expected": expected,
            "resolved": 0,
            "gaps": {"ambiguous": 0, "not_linked": 0, "unreadable": expected},
            "people": [],
            "unresolved": unresolved,
        }

    # 1. Record owners, through the candidate resolver (never a guess).
    for bucket in owners.values():
        result = people_service.resolve_owner_candidates(bucket["owner"])
        if result.get("state") != "ready":
            unresolved.append({
                "owner": bucket["owner"], "link": "unavailable",
                "candidates": [], "commitments": bucket["commitments"],
            })
            continue
        relationship = result.get("relationship")
        if result.get("link") == "linked" and relationship:
            rel_id = str(relationship.get("id") or "")
            display = str(relationship.get("display_name") or "")
            if rel_id and display:
                _row(rel_id, display)["commitments"].extend(bucket["commitments"])
                continue
        unresolved.append({
            "owner": bucket["owner"],
            "link": "ambiguous" if result.get("link") == "ambiguous" else "not_linked",
            "candidates": [
                {"relationship_id": c.get("id"), "display_name": c.get("display_name")}
                for c in result.get("candidates") or []
                if c.get("id") and c.get("display_name")
            ],
            "commitments": bucket["commitments"],
        })

    # 2. Watch identities (172-07): resolved ones carry their facts; an
    #    unresolved login stays out of the payload entirely.
    for _key, counts in identities.items():
        raw = counts.get("_raw", _key)
        has_count = any(int(counts.get(k) or 0) > 0 for k in ("prs_waiting", "assignments_open", "assignments_overdue"))
        has_omitted = any(src.get("state") for src in counts.get("_sources", {}).values())
        if not has_count and not has_omitted:
            continue
        resolved = people_service.resolve_relationship_by_watch_identity(raw)
        if not resolved or resolved.get("state") != "ready":
            continue
        relationship = resolved.get("relationship")
        if not relationship:
            continue
        rel_id = str(relationship.get("id") or "")
        display = str(relationship.get("display_name") or "")
        if not rel_id or not display:
            continue
        row = _row(rel_id, display)
        for kind in ("prs_waiting", "assignments_open", "assignments_overdue"):
            n = int(counts.get(kind) or 0)
            if n > 0:
                row[kind] = row.get(kind, 0) + n
        facts, omitted = _facts_for(counts)
        row["facts"].extend(facts)
        row["omitted_sources"].extend(omitted)

    # 3. Relationships the ledger links to this Project (project_refs).
    if principal is not None:
        try:
            for relationship in people_service.list_relationships(principal):
                refs = relationship.get("project_refs") or []
                if project_id not in [str(r) for r in refs]:
                    continue
                rel_id = str(relationship.get("id") or "")
                display = str(relationship.get("display_name") or "")
                if rel_id and display:
                    _row(rel_id, display)
        except Exception:
            # A ledger that turned unavailable mid-read: the people already
            # resolved stand; nothing is invented for the rest.
            pass

    people = sorted(linked.values(), key=lambda r: r["display_name"].lower())
    unresolved.sort(key=lambda r: r["owner"].lower())
    gaps = {
        "ambiguous": sum(1 for r in unresolved if r["link"] == "ambiguous"),
        "not_linked": sum(1 for r in unresolved if r["link"] == "not_linked"),
        "unreadable": sum(1 for r in unresolved if r["link"] not in ("ambiguous", "not_linked")),
    }
    return {
        "state": state,
        "expected": len(people) + len(unresolved),
        "resolved": len(people),
        "gaps": gaps,
        "people": people,
        "unresolved": unresolved,
    }


def room_people(
    project_service: ProjectService,
    people_service: Any,
    project_id: str,
) -> list[dict[str, Any]]:
    """HS-172-07's list: the LINKED people with at least one non-zero count.

    Kept for the shade's PEOPLE lane and every 172-07 consumer; it is the
    ``people`` half of :func:`room_people_preparation` filtered to rows
    that carry a Watch count.
    """
    projection = room_people_preparation(project_service, people_service, project_id)
    result: list[dict[str, Any]] = []
    for row in projection["people"]:
        if not any(k in row for k in ("prs_waiting", "assignments_open", "assignments_overdue")):
            continue
        entry: dict[str, Any] = {
            "relationship_id": row["relationship_id"],
            "display_name": row["display_name"],
        }
        for kind in ("prs_waiting", "assignments_open", "assignments_overdue"):
            if row.get(kind, 0) > 0:
                entry[kind] = row[kind]
        result.append(entry)
    return result
