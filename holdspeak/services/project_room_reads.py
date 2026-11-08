"""The Room's reads: pure queries over the repositories a Project service holds.

Each function takes the database (``db``) it reads and answers the same dict
the ``ProjectService._read_room_*`` method answered before the move
(2026-11-08).  ``ProjectService`` keeps a thin method of the same name and
signature that calls the function here, so every caller and test is
unchanged.

One way only: this module imports the repositories' types, the Project
vocabulary (``project_definitions``) and the service errors.  It never
imports ``project_service``.  A read that needs a collaborator the service
holds (the review flag, the proposal rows, the People resolver) takes it as
a keyword argument.  Sibling services that a read used before the move are
still imported inside the read, as before.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from holdspeak.timestamps import local_wall

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from .errors import NotFound
from .project_definitions import (
    _CHANGE_KIND_PHRASES, _COMMITMENT_SETTLED, _count_unit, _format_age, _receipt_project,
    _ROOM_UPDATES_CAP, _SERVICE_OBSERVED_OPERATIONS, _SERVICE_OBSERVED_PREFIXES, _SEVERITY_ORDER,
    _STATE_SEVERITY, _wall, _WEEK_DAYS, aware_iso, local_now, local_week_bounds, plain_reason as _plain_reason,
    ROOM_CHANGES_CAP, ROOM_FOCUS_CAP, ROOM_WRITE_METHODS, snapshot_entities, token_sort_key, utc_z,
)
from .steward_serialization_service import _serialize_run

# The same logger name the reads logged under inside the service.
_log = get_logger("services.project_service")


def require_project(db: Any, project_id: str) -> Any:
    """The project row, or ``NotFound`` (the one implementation; the service delegates here)."""
    project = db.projects.get_project(project_id)
    if project is None:
        raise NotFound("project", project_id)
    return project


def _read_room_items(db: Any, project_id: str) -> dict[str, Any]:
    """Focus block: bounded top-N items + total counts per type."""
    with db._connection() as conn:
        count_rows = conn.execute(
            "SELECT item_type, COUNT(*) as cnt FROM project_items "
            "WHERE project_id = ? GROUP BY item_type",
            (project_id,),
        ).fetchall()
        totals_by_type = {row["item_type"]: row["cnt"] for row in count_rows}
        total = sum(totals_by_type.values())

        # Focus: bounded, deterministically ordered (DB-005)
        # HS-158-03: explicit CASE rank for severity (highest first,
        # nulls last) instead of free-text DESC over the column.
        focus_rows = conn.execute(
            """
            SELECT * FROM project_items WHERE project_id = ?
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 0
                    WHEN 'high'     THEN 1
                    WHEN 'medium'   THEN 2
                    WHEN 'low'      THEN 3
                    ELSE 999
                END ASC,
                due_at IS NULL, due_at ASC,
                sort_key IS NULL, sort_key ASC,
                created_at ASC,
                id ASC
            LIMIT ?
            """,
            (project_id, ROOM_FOCUS_CAP),
        ).fetchall()
    return {
        "focus": [dict(r) for r in focus_rows],
        "totals_by_type": totals_by_type,
        "total": total,
    }


def _read_room_resources(db: Any, project_id: str) -> dict[str, Any]:
    """Resources summary: count + latest linked."""
    resource_objs = db.project_relationships.list_for_project(
        project_id)
    count = len(resource_objs)
    return {
        "count": count,
        "latest": resource_objs[0].to_dict() if resource_objs else None,
    }


def _read_room_changes(db: Any, project_id: str) -> dict[str, Any]:
    """Recent changes, bounded, newest first."""
    changes = db.projects.list_project_changes(
        project_id, limit=ROOM_CHANGES_CAP)
    return {"recent": changes}


def _read_room_updates(db: Any, principal: Principal, project_id: str) -> dict[str, Any]:
    """PHILO-9-01 (F6): the Room's updates, newest first, each with its deliveries.

    Before this the section was ``absent · not_yet_built`` after an update
    was drafted and published. Counts are per lifecycle; ``recent`` is
    bounded; every listed update carries its ``deliveries`` (the owner's
    copy-and-confirm record, oldest first).
    """
    from .project_update_service import attach_deliveries

    rows = db.project_updates.list_updates(project_id, limit=1000)
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("lifecycle") or "draft")
        counts[key] = counts.get(key, 0) + 1
    fields = ("id", "project_id", "lifecycle", "draft_revision", "generator",
              "created_at", "updated_at", "published_at", "review_id")
    recent = attach_deliveries(db, [
        {key: row.get(key) for key in fields}
        for row in rows[: _ROOM_UPDATES_CAP]
    ])
    # PHILO-9-01 round two (Codex Astra r1, P4): the newest PUBLISHED
    # update, read on its own -- newer drafts must not push it out of view.
    latest_published = None
    with db._connection() as conn:
        pub = conn.execute(
            "SELECT * FROM project_updates WHERE project_id = ? AND lifecycle = 'published' "
            "ORDER BY published_at DESC, created_at DESC, id DESC LIMIT 1",
            (project_id,),
        ).fetchone()
    if pub is not None:
        latest_published = attach_deliveries(db, [{key: dict(pub).get(key) for key in fields}])[0]
    # The project Room's NEW marker belongs to the automation result that
    # delivered an update.  Owner-created drafts have no artifact link and
    # must not make the Room claim that a result is new.
    from .automation_runs import results_of

    automation_id = next(
        (
            str(wb.id)
            for wb in db.workbenches.list()
            if str(wb.output_target or "") == f"project_updates:{project_id}"
        ),
        "",
    )
    latest_result = None
    for result in (results_of(db, automation_id) if automation_id else []):
        if str(result.get("status") or "") != "done":
            continue
        artifact_id = str(result.get("artifact_id") or "").strip()
        if not artifact_id:
            continue
        if result.get("program"):
            # 2026-11-08: a run that is a Program names its delivered update itself.
            update_id = str(result.get("update_id") or "")
            update = db.project_updates.get_update(update_id) if update_id else None
            latest_result = {
                "artifact_id": artifact_id,
                "update_id": update_id if update is not None and str(update.get("project_id") or "") == project_id
                else None,
                "new": bool(result.get("new")),
            }
            break
        artifact = db.plugins.get_artifact(artifact_id)
        if artifact is None:
            continue
        metadata = artifact.structured_json if isinstance(artifact.structured_json, dict) else {}
        raw_update_id = str(metadata.get("project_update_id") or "").strip()
        update_id = raw_update_id
        if update_id:
            update = db.project_updates.get_update(update_id)
            if update is None or str(update.get("project_id") or "") != project_id:
                update_id = ""
        latest_result = {
            "artifact_id": artifact_id,
            "update_id": update_id or None,
            "new": bool(result.get("new")),
        }
        break
    automation = None
    target = f"project_updates:{project_id}"
    for wb in db.workbenches.list():
        if str(wb.output_target or "") != target:
            continue
        try:
            when = json.loads(wb.when_json or "{}") if wb.when_json else {}
        except (TypeError, ValueError):
            when = {}
        engine_label, engine_profile = "Engine not read", None
        if principal.kind is PrincipalKind.OWNER:
            from .inference_assignment_service import InferenceAssignmentService
            effective = InferenceAssignmentService(db).resolve_effective(
                principal, capability_id="workbench.item", subject_kind="workbench", subject_id=wb.id,
            )
            entries = (effective.get("assignment") or {}).get("entries") or []
            if effective.get("status") == "assigned" and entries:
                engine_label = str(entries[0].get("label") or "Selected engine")
                engine_profile = str(entries[0].get("profile_id") or "") or None
            else:
                engine_label = "Engine not set" if effective.get("status") == "no_assignment" else "Check engine"
        automation = {
            "id": str(wb.id),
            "name": str(wb.name or "Project update"),
            "instruction": str(wb.instruction or ""),
            "schedule": str(wb.schedule or "") or None,
            "schedule_enabled": bool(wb.schedule_enabled),
            "when_kind": str(when.get("kind") or "manual"),
            "profile_id": engine_profile,
            "engine_label": engine_label,
            "latest_result": latest_result,
        }
        break
    return {
        "count": len(rows),
        "counts": counts,
        "recent": recent,
        "latest_published": latest_published,
        "automation": automation,
    }


def _read_room_steward(db: Any, project_id: str) -> dict[str, Any]:
    """PHILO-9-01 (F6): the Room's steward — its policy switch and its latest run.

    Before this the section was ``absent · not_yet_built`` after a run
    completed.
    """
    runs = db.steward_runs.list_runs(project_id, limit=1)
    policy = db.steward_policies.get_policy_for_project(project_id)
    return {
        "latest_run": _serialize_run(runs[0]) if runs else None,
        "enabled": bool(policy.get("enabled")) if policy else False,
        "unattended_enabled": bool(policy.get("unattended_enabled")) if policy else False,
    }


def _read_room_review(db: Any, project_id: str, *, review_available: bool) -> dict[str, Any]:
    """Review section: pending_count, last_accepted_at, open_review_id.

    HS-160-05: the review section graduates from absent to real.
    Shape: {state:'ok', last_accepted_at, pending_count, open_review_id}.
    Art VI: zeros are zeros, not absence -- the domain exists now.
    """
    room_fields = db.projects.get_project_room_fields(project_id)
    last_accepted_at = (room_fields or {}).get("last_review_at")

    open_review_id = None
    pending_count = 0

    if review_available:
        try:
            # S52: the repository owns the open-review selector; the
            # Room never reaches into ProjectDeltaService for a read.
            open_review = db.project_observations.get_open_review(project_id)
            if open_review is not None:
                open_review_id = open_review["id"]
                proposals = db.project_observations.list_proposals(
                    project_id,
                    review_window_key=open_review_id,
                    lifecycle="open",
                )
                pending_count = len(proposals)
        except Exception:
            # Fault isolation: if delta reads fail, we still return
            # the section with what we have.
            pass

    return {
        "last_accepted_at": last_accepted_at,
        "pending_count": pending_count,
        "open_review_id": open_review_id,
    }


def _fold_watch_duplicates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entity, one row, whatever the number of Watches that read it."""
    folded: list[dict[str, Any]] = []
    first_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        entity_id = str(row.get("entity_id") or "").strip()
        if not entity_id:
            folded.append(row)
            continue
        key = (str(row.get("source") or ""), entity_id)
        kept = first_by_key.get(key)
        if kept is None:
            first_by_key[key] = row
            folded.append(row)
            continue
        watch_id = str(row.get("watchId") or "")
        if watch_id and watch_id != kept.get("watchId"):
            others = kept.setdefault("watchIds", [str(kept.get("watchId") or "")])
            if watch_id not in others:
                others.append(watch_id)
    return folded


def _read_room_needs_you(
    db: Any, project_id: str, *, review_available: bool,
    proposal_needs: Callable[..., list[dict[str, Any]]],
    resolve_review_people: Callable[..., list[dict[str, Any]]],
) -> dict[str, Any]:
    """NEEDS YOU: items derived from Watch snapshots + Delta review."""
    watches = db.automations.list_project_watches(project_id)
    needs: list[dict[str, Any]] = []
    now = local_wall()

    for watch in watches:
        connector_id = watch.get("connector_id", "")
        snapshot = watch.get("snapshot")
        if not snapshot:
            continue
        entities = snapshot_entities(snapshot)
        query_kind = watch.get("query_kind", "")
        watch_id = str(watch.get("id") or "")
        rows_before = len(needs)

        if connector_id == "gh" and query_kind == "pull_requests":
            # PRs whose review_requests name the owner or review_decision = changes_requested.
            # Also: a PR with failing checks that the owner authored or
            # is asked to review gets a CHECKS FAILING row (the base-branch
            # CI row is the branch_ci kind; PR-level failing checks are a
            # needs-you row ONLY when the PR is the owner's or awaits their
            # review -- otherwise it is a source token only).
            owner_login = _get_github_owner_login(db, )
            for entity in entities:
                # Handle both raw (reviewRequests) and normalized (review_requests) field names
                review_requests = entity.get("review_requests") or entity.get("reviewRequests") or []
                review_decision = (
                    entity.get("review_decision") or entity.get("reviewDecision") or ""
                ).lower()
                updated_at_str = entity.get("updated_at") or entity.get("updatedAt") or ""
                entity_id = entity.get("id") or entity.get("number") or ""
                entity_title = entity.get("title") or ""
                checks = str(entity.get("checks") or "").lower()

                waiting_on_owner = (
                    (owner_login and owner_login.lower() in [r.lower() for r in review_requests])
                    or review_decision == "changes_requested"
                )
                if waiting_on_owner:
                    age_str = _format_age(updated_at_str, now)
                    # PR-level failing checks on a PR awaiting the owner's review
                    if checks == "failing":
                        needs.append({
                            "source": "github",
                            "title": f"#{entity_id} {entity_title}".strip(),
                            "why": f"CHECKS FAILING · {age_str}" if age_str else "CHECKS FAILING",
                            "since": updated_at_str,
                            "url": entity.get("url"),
                            "verb": "open",
                            "severity": "danger",
                        })
                    else:
                        needs.append({
                            "source": "github",
                            "title": f"#{entity_id} {entity_title}".strip(),
                            "why": f"WAITING ON YOUR REVIEW · {age_str}" if age_str else "WAITING ON YOUR REVIEW",
                            "since": updated_at_str,
                            "url": entity.get("url"),
                            "verb": "open",
                            "severity": "warning",
                        })

        elif connector_id == "gh" and query_kind == "branch_ci":
            # CI on the base branch
            for entity in entities:
                conclusion = str(entity.get("conclusion") or "").lower()
                if conclusion in ("failure", "timed_out", "cancelled"):
                    base_branch = entity.get("branch") or "main"
                    needs.append({
                        "source": "github",
                        "title": f"CI failing on {base_branch}",
                        "why": "CI RED",
                        "since": entity.get("updated_at") or "",
                        "url": entity.get("url"),
                        "verb": "open",
                        "severity": "danger",
                    })

        elif connector_id == "gh" and query_kind == "issues":
            # Conductor R4: a GitHub issues Watch's open issues, the
            # same row shape as a Jira issue row (the canvas K2e rows:
            # `#418 Title`, `ISSUE · OPEN 2 D`), so Hand to agent takes them.
            for entity in entities:
                if str(entity.get("state") or "").lower() not in ("", "open"):
                    continue
                number = str(entity.get("number") or entity.get("id") or "")
                if not number:
                    continue
                opened = str(entity.get("created_at") or entity.get("createdAt") or "")
                days = None
                try:
                    opened_dt = datetime.fromisoformat(opened.replace("Z", "+00:00"))
                    if opened_dt.tzinfo is None:
                        opened_dt = opened_dt.astimezone()
                    # Elapsed time on aware instants: the naive wall clocks
                    # lost an hour on the day the clocks went back (2 D read 1 D).
                    current = now if now.tzinfo else now.astimezone()
                    days = max(0, (current - opened_dt).days)
                except (ValueError, TypeError):
                    pass
                needs.append({
                    "source": "github",
                    "kind": "issue",
                    "entity_id": str(entity.get("id") or number),
                    "title": f"#{number} {entity.get('title') or ''}".strip(),
                    "why": f"ISSUE · OPEN {days} D" if days is not None else "ISSUE · OPEN",
                    "since": opened,
                    "url": entity.get("url"),
                    "verb": "open",
                    "severity": "info",
                })

        elif connector_id == "jira" and query_kind == "issues":
            # Jira entities from an OVERDUE-kind watch
            query = watch.get("query") or {}
            # An overdue watch has due_within_days in its query or its template is due_risk
            for entity in entities:
                due_at = entity.get("due_at") or entity.get("dueDate")
                if not due_at:
                    continue
                try:
                    due_dt = datetime.fromisoformat(str(due_at).replace("Z", "+00:00").split("T")[0])
                    overdue_days = (now.replace(tzinfo=None) - due_dt.replace(tzinfo=None)).days
                except (ValueError, TypeError):
                    continue
                if overdue_days > 0:
                    jira_id = entity.get("key") or entity.get("id") or ""
                    jira_title = entity.get("summary") or entity.get("title") or ""
                    needs.append({
                        "source": "jira",
                        # Conductor R4: an issue row names its entity, so
                        # Hand to agent can take it (issue:<watch>.<id>).
                        "kind": "issue",
                        "entity_id": str(entity.get("id") or jira_id),
                        "title": f"{jira_id} {jira_title}".strip(),
                        "why": f"OVERDUE · {_count_unit(overdue_days, 'DAY')}",
                        "since": due_at,
                        # HS-200-15: the due date is the ranking's
                        # observable fact, named as itself.
                        "due_at": str(due_at),
                        "url": entity.get("url"),
                        "verb": "open",
                        "severity": "danger",
                    })

        # HS-200-11: the row names the Watch it was read from, so a brief
        # can cite the source by id, never by provider kind (counsel P2 vi).
        for row in needs[rows_before:]:
            row.setdefault("watchId", watch_id)
    # Owner, 2026-10-25 ("why is the list of open issues so long"): two
    # Watches on one project (Jira due risk + Jira delivery flow) read the
    # same issues, and the Room showed every issue twice. One entity is
    # ONE row: the first Watch's row stays and names the others in
    # ``watchIds``; the count is the number of things, not of reads.
    needs = _fold_watch_duplicates(needs)
    # Delta proposals pending
    if review_available:
        try:
            review_data = _read_room_review(db, project_id, review_available=review_available)
            pending = review_data.get("pending_count", 0)
            if pending > 0:
                needs.append({
                    "source": "delta",
                    # PHILO-9-01 (F22): one proposal is singular.
                    "title": f"{pending} proposal{'' if pending == 1 else 's'} waiting",
                    "why": "DECISION PENDING",
                    "since": "",
                    "url": None,
                    "verb": "decide",
                    "severity": "info",
                })
        except Exception:
            pass

    # HS-172-03: follow-through proposals (intel-extracted decisions/actions).
    try:
        needs.extend(proposal_needs(project_id=project_id))
    except Exception:
        pass

    # PHILO-9-01 (F2, the Q3 ruling): a milestone still planned after its
    # date is an attention row, and it turns the Room's health.
    try:
        needs.extend(_room_overdue_milestone_items(db, project_id, now))
    except Exception as exc:
        _log.warning("room overdue milestones failed for %s: %s", project_id, exc)

    # HS-200-13 (AC3): the Room's open commitments are attention items.
    # HS-200-15 built the `commitment` source, the `CMT` emblem and the
    # due-driven rank class against synthetic rows; this is the real
    # producer.  Each row carries its typed unknowns and ONE lawful next
    # action (name an owner, set a date, or -- only when both are known
    # -- mark it done).  Nothing here can complete a commitment (AC4).
    try:
        needs.extend(_room_commitment_items(db, project_id, now))
    except Exception as exc:
        _log.warning("room commitments as attention failed for %s: %s", project_id, exc)

    # Inventory 2026-10-03 (UX-CANON A.10): a Room read "Clear here /
    # Nothing open" while its meeting had an open action with no owner
    # (the Chair showed the same action as needing an owner). The Room's
    # meetings' open actions are open here.
    try:
        needs.extend(_room_meeting_action_items(db, project_id, now))
    except Exception as exc:
        _log.warning("room meeting actions as attention failed for %s: %s", project_id, exc)

    # Betterment P5: meetings that mention a new project's own words are
    # offered in NEEDS YOU until the owner files them.  This is a producer
    # read from the real transcript index; it does not create a meeting
    # association or claim that the match was accepted.  The Add verb on
    # the face calls the existing project.link route.
    try:
        needs.extend(_room_matching_meeting_items(db, project_id))
    except Exception as exc:
        _log.warning("room matching meetings failed for %s: %s", project_id, exc)

    # HS-173: review bottleneck items (resolved reviewers whose median
    # exceeds the threshold get a NEEDS YOU row).
    try:
        from holdspeak.services.room_health_service import review_wait as _review_wait
        from datetime import timezone as _tz
        now_utc = datetime.now(_tz.utc)

        # Gather all PR entities from watches (already iterated above)
        all_pr_entities: list[dict[str, Any]] = []
        for watch in watches:
            cid = watch.get("connector_id", "")
            qk = watch.get("query_kind", "")
            snap = watch.get("snapshot")
            if cid == "gh" and qk == "pull_requests" and snap:
                all_pr_entities.extend(snapshot_entities(snap))

        if all_pr_entities:
            review_signal = _review_wait(all_pr_entities, now_utc)
            bottleneck_people = resolve_review_people(
                project_id, review_signal.get("per_reviewer", []))
            for person in bottleneck_people:
                median_d = person.get("median_days", 0)
                pr_count = person.get("count", 0)
                display = person.get("display_name", "")
                needs.append({
                    "source": "github",
                    "kind": "review_bottleneck",
                    "title": display,
                    "why": f"REVIEW BOTTLENECK · {median_d} D MEDIAN · {pr_count} PRS WAITING",
                    "since": "",
                    "url": None,
                    "verb": "nudge",
                    "severity": "warning",
                    "relationship_id": person.get("relationship_id"),
                    "median_days": median_d,
                    "count": pr_count,
                })
    except Exception:
        pass

    # Betterment P3: whose move each row is. An owed item with an owner
    # who is not the owner himself is "theirs" (the Now wing's Waiting
    # on); everything else is his (Needs you). The one is-me rule is the
    # desk's (needs_you_membership.self_check: his names, his aliases,
    # the speaker label, the People on the desk).
    try:
        from .needs_you_membership import _read_people_names, self_check

        is_me = self_check(_read_people_names(None))
        for row in needs:
            owner = str(row.get("owner") or "").strip()
            theirs = (
                row.get("kind") in ("action_item", "commitment")
                and bool(owner) and not is_me(owner)
            )
            row["direction"] = "theirs" if theirs else "mine"
    except Exception as exc:
        _log.warning("room needs-you direction failed for %s: %s", project_id, exc)

    # Sort: danger > warning > info, then by age (oldest first = most urgent)
    needs.sort(key=lambda r: (
        _SEVERITY_ORDER.get(r.get("severity", "info"), 2),
        r.get("since") or "",
    ))

    return {"items": needs, "count": len(needs)}


def _room_matching_meeting_items(db: Any, project_id: str) -> list[dict[str, Any]]:
    """Offer unfiled meetings whose transcript names this project.

    Project words are deliberately bounded to the project name and its
    explicit keywords.  Every result is still a suggestion: only the
    existing ``project.link`` command turns it into a Room meeting.
    """
    project = require_project(db, project_id)
    basis = [str(project.name or ""), *(str(word) for word in (project.keywords or []))]
    words: list[str] = []
    seen_words: set[str] = set()
    for text in basis:
        for word in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{3,}", text.lower()):
            if word not in seen_words:
                seen_words.add(word)
                words.append(word)
    if not words:
        return []

    matches: dict[str, str] = {}
    for word in words:
        try:
            for meeting_id, _segment in db.meetings.search_transcripts(word, limit=50):
                matches.setdefault(str(meeting_id), word)
        except Exception:
            continue

    rows: list[dict[str, Any]] = []
    for meeting_id, word in matches.items():
        try:
            linked = db.projects.get_meeting_projects(meeting_id)
            if any(str(row.get("project_id")) == project_id for row in linked):
                continue
            meeting = db.meetings.get_meeting(meeting_id)
        except Exception:
            continue
        if meeting is None or bool(getattr(meeting, "parked", False)):
            continue
        started = getattr(meeting, "started_at", None)
        rows.append({
            "source": "meeting",
            "kind": "meeting_match",
            "title": f"mentions {word}",
            "why": str(getattr(meeting, "title", "") or "Meeting"),
            "since": started.isoformat() if hasattr(started, "isoformat") else str(started or ""),
            "url": None,
            "verb": "confirm",
            "severity": "info",
            "meeting_id": meeting_id,
            "meeting_title": str(getattr(meeting, "title", "") or "Meeting"),
            "meeting_started_at": started.isoformat() if hasattr(started, "isoformat") else str(started or ""),
        })
    rows.sort(key=lambda row: str(row.get("since") or ""), reverse=True)
    return rows[:20]


def _overdue_milestones(db: Any, project_id: str, now: datetime) -> list[tuple[dict[str, Any], int]]:
    """PHILO-9-01 (F2): each milestone still ``planned`` after its due date, with its days late.

    Only ``planned`` is owed: ``reached``, ``missed`` and ``dropped`` are
    settled by the owner. A due date the service cannot read is not
    counted (never guessed).
    """
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT * FROM project_items WHERE project_id = ? AND item_type = 'milestone' "
            "AND lifecycle = 'planned' AND due_at IS NOT NULL AND due_at != '' "
            "ORDER BY due_at ASC, created_at ASC, id ASC",
            (project_id,),
        ).fetchall()
    today = now.date()
    late: list[tuple[dict[str, Any], int]] = []
    for row in rows:
        item = dict(row)
        try:
            due = datetime.fromisoformat(str(item["due_at"]).replace("Z", "+00:00").split("T")[0]).date()
        except (ValueError, TypeError):
            continue
        days = (today - due).days
        if days > 0:
            late.append((item, days))
    return late


def _room_overdue_milestone_items(db: Any, project_id: str, now: datetime) -> list[dict[str, Any]]:
    """PHILO-9-01 (F2): the Room's past-due milestones as attention rows."""
    return [{
        "source": "item",
        "kind": "milestone",
        "title": str(item.get("title") or "").strip() or "Untitled milestone",
        "why": f"OVERDUE · {_count_unit(days, 'DAY')}",
        "since": str(item["due_at"]),
        "due_at": str(item["due_at"]),
        "url": None,
        "verb": "open",
        "severity": "danger",
        "item_id": str(item["id"]),
        "item_type": "milestone",
    } for item, days in _overdue_milestones(db, project_id, now)]


def _room_commitment_items(db: Any, project_id: str, now: datetime) -> list[dict[str, Any]]:
    """The Room's open commitments as attention rows (HS-200-13 AC3).

    A commitment reaches a Room through its decision: ``decision_commitments
    .decision_id`` -> ``decision_records.source_id`` -> a record whose
    source meeting is linked to the Room (the same walk
    ``_read_room_commitments`` makes), or a record filed on the Room as a
    resource.  The obligation stands whether its decision is current or
    superseded: a superseded decision's commitment is still owed until
    someone says otherwise.
    """
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT c.id AS commitment_id, c.owner, c.due_at, c.status,
                      c.created_at, c.updated_at, c.action_item_id,
                      ai.task AS text, ai.status AS action_status,
                      r.id AS record_id, r.lifecycle AS record_lifecycle,
                      (SELECT p.kind FROM follow_through_proposals p
                        WHERE p.commitment_id = c.id LIMIT 1) AS proposal_kind
               FROM decision_commitments c
               JOIN decision_records r ON r.source_id = c.decision_id AND r.deleted = 0
               LEFT JOIN action_items ai ON ai.id = c.action_item_id
               WHERE (
                   EXISTS (SELECT 1 FROM decision_record_sources s
                           JOIN meeting_projects mp ON mp.project_id = ?
                           WHERE s.record_id = r.id AND s.source_type = 'meeting'
                             AND s.source_ref IN (mp.meeting_id, 'meeting:' || mp.meeting_id))
                   OR EXISTS (SELECT 1 FROM project_resources pr
                              WHERE pr.project_id = ? AND pr.deleted = 0
                                AND pr.resource_ref = 'decision_record:' || r.id)
               )
               ORDER BY c.due_at ASC NULLS LAST, c.created_at ASC""",
            (project_id, project_id),
        ).fetchall()
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    today = now.date()
    for row in rows:
        cid = str(row["commitment_id"])
        if cid in seen:
            continue
        seen.add(cid)
        status = str(row["status"] or "open").lower()
        action_status = str(row["action_status"] or "").lower()
        if status in _COMMITMENT_SETTLED or action_status in _COMMITMENT_SETTLED:
            continue
        # HS-200-12's confirm mints a commitment row for a DECISION-kind
        # proposal too; a decision is not an obligation and is never an
        # attention row (the recall face applies the same rule).
        if str(row["proposal_kind"] or "") == "decision":
            continue
        owner = (row["owner"] or "").strip() or None
        due_at = (row["due_at"] or "").strip() or None
        unknowns: list[str] = []
        if not owner:
            unknowns.append("owner")
        if not due_at:
            unknowns.append("due")
        due_date = None
        if due_at:
            try:
                due_date = datetime.fromisoformat(due_at.replace("Z", "+00:00").split("T")[0]).date()
            except (ValueError, TypeError):
                due_date = None
        overdue_days = (today - due_date).days if due_date is not None else 0
        # The reason token: the most urgent observable fact, once.
        if due_date is not None and overdue_days > 0:
            why, severity = f"OVERDUE · {overdue_days} D", "danger"
        elif due_date is not None and overdue_days == 0:
            why, severity = "DUE TODAY", "warning"
        elif not owner:
            why, severity = "OWNER · UNKNOWN", "warning"
        elif not due_at:
            why, severity = "DUE · UNKNOWN", "info"
        else:
            why, severity = f"WAITING ON {owner.upper()}", "info"
        # ONE lawful next action (story 13 AC3/AC4): an unknown is named
        # before anything can be marked done.
        next_action = "name_owner" if not owner else ("set_date" if not due_at else "mark_done")
        items.append({
            "source": "commitment",
            "kind": "commitment",
            "title": str(row["text"] or "").strip() or "Untitled commitment",
            "why": why,
            "since": str(row["updated_at"] or row["created_at"] or ""),
            "due_at": due_at,
            "url": None,
            "verb": next_action,
            "severity": severity,
            "commitment_id": cid,
            "action_item_id": str(row["action_item_id"] or ""),
            "decision_record_id": str(row["record_id"] or ""),
            "decision_lifecycle": str(row["record_lifecycle"] or "active"),
            "owner": owner,
            "unknowns": unknowns,
            "next_action": next_action,
        })
    return items


def _room_meeting_action_items(db: Any, project_id: str, now: datetime) -> list[dict[str, Any]]:
    """Open actions from the Room's meetings, as attention rows.

    The same set the follow-through board reads for this project
    (``FollowThroughService._action_rows``): actions of the Room's
    meetings that are not parked and not settled. An action that a
    decision commitment owns is left to ``_room_commitment_items`` (one
    obligation, one row). The Desk reads these actions through the
    follow-through board, so the Desk aggregate skips this kind.
    """
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT a.id, a.task, a.owner, a.due, a.status, a.created_at,
                      a.source_ref, a.meeting_id, m.title AS meeting_title
               FROM action_items a
               JOIN meeting_projects mp ON mp.meeting_id = a.meeting_id
               JOIN meetings m ON m.id = a.meeting_id
               WHERE mp.project_id = ? AND m.parked = 0
                 AND NOT EXISTS (SELECT 1 FROM decision_commitments dc
                                 WHERE dc.action_item_id = a.id)
               ORDER BY a.created_at ASC""",
            (project_id,),
        ).fetchall()
    items: list[dict[str, Any]] = []
    today = now.date()
    for row in rows:
        if str(row["status"] or "").lower() in _COMMITMENT_SETTLED:
            continue
        owner = (row["owner"] or "").strip() or None
        due_at = (str(row["due"] or "")).strip() or None
        due_date = None
        if due_at:
            try:
                due_date = datetime.fromisoformat(due_at.replace("Z", "+00:00").split("T")[0]).date()
            except (ValueError, TypeError):
                due_date = None
        overdue_days = (today - due_date).days if due_date is not None else 0
        if due_date is not None and overdue_days > 0:
            why, severity = f"OVERDUE · {overdue_days} D", "danger"
        elif due_date is not None and overdue_days == 0:
            why, severity = "DUE TODAY", "warning"
        elif not owner:
            why, severity = "OWNER · UNKNOWN", "warning"
        elif not due_at:
            why, severity = "DUE · UNKNOWN", "info"
        else:
            why, severity = f"WAITING ON {owner.upper()}", "info"
        source_ref = str(row["source_ref"] or "").strip()
        item = {
            "source": "meeting",
            "kind": "action_item",
            "title": str(row["task"] or "").strip() or "Untitled action",
            "why": why,
            "since": str(row["created_at"] or ""),
            "due_at": due_at,
            # A meeting action may carry a checked external place in
            # source_ref. Preserve only an explicit URL so Now can gate
            # its outbound Nudge on the same real destination.
            "url": (source_ref
                    if source_ref.startswith(("http://", "https://"))
                    else None),
            "verb": "open",
            "severity": severity,
            "action_item_id": str(row["id"]),
            "meeting_id": str(row["meeting_id"] or ""),
            "owner": owner,
        }
        nudge = _room_nudge_destination(db, project_id, str(row["id"]), source_ref)
        if nudge:
            item["nudge"] = nudge
        items.append(item)
    return items


def _nudge_target(source_ref: str, destination: dict[str, Any]) -> bool:
    """Match an action's stored destination to one saved target exactly.

    Waiting on must never infer a recipient from a name or from a provider
    account. Jira requires the site and key, Slack requires the saved
    channel label (including any saved thread suffix), and email requires
    an exact saved To/Cc address.
    """
    raw = str(source_ref or "").strip()
    if not raw or destination.get("state") != "active":
        return False
    channel = str(destination.get("channel") or "")
    try:
        account = json.loads(destination.get("account_json") or "{}")
        target = json.loads(destination.get("target_json") or "{}")
    except (TypeError, ValueError):
        return False
    if not isinstance(account, dict) or not isinstance(target, dict):
        return False

    if channel == "jira":
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        parts = [unquote(part).strip() for part in parsed.path.split("/") if part.strip()]
        try:
            key = parts[parts.index("browse") + 1].split("?", 1)[0].split("#", 1)[0]
        except (ValueError, IndexError):
            return False
        site = str(account.get("site") or "").strip().lower()
        site = site.removeprefix("https://").removeprefix("http://").rstrip("/")
        return bool(site and parsed.hostname.lower() == site
                    and key == str(target.get("key") or "").strip())

    if channel == "slack":
        if raw.lower().startswith("slack://"):
            candidate = raw[8:]
        elif raw.lower().startswith("slack:"):
            candidate = raw[6:]
        else:
            return False
        # A source may name a channel alone or a saved thread on that
        # channel. Keep both pieces exact when the destination stores a
        # thread; a channel-only destination never claims a thread.
        channel_ref, separator, query = candidate.partition("?")
        thread_ref = ""
        if separator:
            values = parse_qs(query, keep_blank_values=False)
            thread_ref = str((values.get("thread_ts") or values.get("thread") or [""])[0]).strip()
        if "|" in channel_ref:
            channel_ref, thread_ref = channel_ref.split("|", 1)
            thread_ref = thread_ref.strip()
        clean = lambda value: str(value or "").strip().lstrip("#").casefold()
        saved_thread = str(target.get("thread_ts") or target.get("thread") or "").strip()
        return bool(clean(channel_ref) and clean(channel_ref) == clean(target.get("channel_label"))
                    and thread_ref == saved_thread)

    if channel == "email":
        candidate = raw[7:] if raw.lower().startswith("mailto:") else raw
        candidate = unquote(candidate.split("?", 1)[0].strip()).casefold()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+", candidate):
            return False
        recipients = [*(target.get("to") or []), *(target.get("cc") or [])]
        return candidate in {
            parseaddr(str(value or ""))[1].strip().casefold() or str(value or "").strip().casefold()
            for value in recipients
        }

    return False


def _room_nudge_destination(db: Any, project_id: str, action_id: str, source_ref: str) -> dict[str, Any] | None:
    """Return a Sendwell source only when the stored item has a saved target."""
    if not source_ref:
        return None
    for destination in db.channel_destinations.list():
        if not _nudge_target(source_ref, destination):
            continue
        try:
            target = json.loads(destination.get("target_json") or "{}")
        except (TypeError, ValueError):
            target = {}
        target_label = str(target.get("key") or target.get("channel_label") or
                           ", ".join(str(value) for value in (target.get("to") or [])) or "")
        return {
            "document_ref": f"project_nudge:{project_id}:{action_id}",
            "destination_id": str(destination.get("id") or ""),
            "destination_name": str(destination.get("name") or ""),
            "channel": str(destination.get("channel") or ""),
            "target": target_label,
            "title": "Review request",
        }
    return None


def _get_github_owner_login(db: Any) -> str | None:
    """Get the GitHub owner login from the connection service."""
    try:
        with db._connection() as conn:
            row = conn.execute(
                "SELECT external_connection_ref FROM watch_provider_connections "
                "WHERE provider_id = 'github' AND state != '' "
                "ORDER BY last_connected_at DESC LIMIT 1"
            ).fetchone()
            if row and row["external_connection_ref"]:
                return row["external_connection_ref"]
    except Exception:
        pass
    return None


def _meeting_calendar_tokens(db: Any, project_id: str, *, now: datetime | None = None,
) -> list[str]:
    """``N THIS WEEK`` and ``NEXT DAY HH:MM`` from the Room's linked
    calendar events (HS-175 counsel C8/C9c).

    Inline query over ``calendar_event_projects`` joined to
    ``calendar_events`` (stored UTC ``...Z``); the week is the hub's
    local week and the NEXT clock is local.  A suppressed link (a
    durable Unlink, if present) does not count.
    """
    tokens: list[str] = []
    current = local_now(now)
    monday, next_monday = local_week_bounds(current)
    week_start, week_end = utc_z(monday), utc_z(next_monday)
    now_z = utc_z(current)
    try:
        with db._connection() as conn:
            week_row = conn.execute(
                """SELECT COUNT(DISTINCT ce.id) AS cnt
                   FROM calendar_event_projects cep
                   JOIN calendar_events ce ON ce.id = cep.calendar_event_id
                   WHERE cep.project_id = ?
                     AND cep.match_source != 'suppressed'
                     AND ce.starts_at >= ? AND ce.starts_at < ?""",
                (project_id, week_start, week_end),
            ).fetchone()
            next_row = conn.execute(
                """SELECT ce.starts_at
                   FROM calendar_event_projects cep
                   JOIN calendar_events ce ON ce.id = cep.calendar_event_id
                   WHERE cep.project_id = ?
                     AND cep.match_source != 'suppressed'
                     AND ce.starts_at > ?
                   ORDER BY ce.starts_at ASC LIMIT 1""",
                (project_id, now_z),
            ).fetchone()
    except Exception as exc:  # pragma: no cover - a missing table on an old DB
        _log.warning("meeting calendar tokens failed for %s: %s", project_id, exc)
        return tokens
    this_week = int(week_row["cnt"]) if week_row else 0
    if this_week:
        tokens.append(f"{this_week} THIS WEEK")
    if next_row and next_row["starts_at"]:
        try:
            next_dt = datetime.fromisoformat(
                str(next_row["starts_at"]).replace("Z", "+00:00")
            )
            if next_dt.tzinfo is None:
                next_dt = next_dt.replace(tzinfo=timezone.utc)
            # Per-instant local conversion (DST-safe), never now's offset.
            local_next = next_dt.astimezone()
            tokens.append(
                f"NEXT {local_next.strftime('%a').upper()} {local_next.strftime('%H:%M')}"
            )
        except (ValueError, TypeError):
            pass
    return tokens


def _read_room_sources(db: Any, project_id: str) -> dict[str, Any]:
    """SOURCES: ONE item per (provider, scope), merged from all watches."""
    watches = db.automations.list_project_watches(project_id)
    # Intermediate: per-watch data, keyed by (provider, scope) for grouping
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for watch in watches:
        # HS-175 counsel C7: a retired Watch is not a source row (the
        # owner said no); folding it into the live row hid Retire.
        if str(watch.get("state") or "") == "retired":
            continue
        connector_id = watch.get("connector_id", "")
        query = watch.get("query") or {}
        snapshot = watch.get("snapshot")
        entities = snapshot_entities(snapshot)
        last_error = watch.get("last_error")
        enabled = watch.get("enabled", True)
        watch_state = str(watch.get("state") or "")
        query_kind = watch.get("query_kind", "")

        # Provider label
        provider = "github" if connector_id == "gh" else connector_id

        # Scope
        scope = query.get("repository") or ""
        if connector_id == "jira":
            projects = query.get("projects") or []
            scope = " + ".join(projects) if projects else query.get("connection_ref", "")
        elif connector_id == "meeting":
            scope = "MEETINGS"

        # Host (egress)
        host = "github.com" if connector_id == "gh" else ""
        if connector_id == "jira":
            ref = query.get("connection_ref", "")
            # connection_ref may be "site.atlassian.net|email" -- host is before |
            site = ref.split("|")[0] if "|" in ref else ref
            host = site.split("//")[-1].split("/")[0] if "//" in site else site

        # State -- HS-175 counsel C7(b): Pause writes ``state='paused'``
        # (watch_service.pause_watch) and leaves ``enabled`` alone, so the
        # row reads ``state`` first; a disabled watch is paused too.
        if watch_state == "paused" or not enabled:
            w_state = "paused"
        elif last_error:
            w_state = "cant_check"
        else:
            w_state = "live"

        # Count tokens (zero-count omitted)
        tokens: list[str] = []
        if connector_id == "gh" and query_kind == "pull_requests":
            open_count = sum(1 for e in entities if str(e.get("state", "")).lower() == "open")
            if open_count:
                tokens.append(f"{open_count} OPEN PRS")
            owner_login = _get_github_owner_login(db, )
            if owner_login:
                waiting = sum(
                    1 for e in entities
                    if owner_login.lower() in [
                        r.lower() for r in (
                            e.get("review_requests") or e.get("reviewRequests") or []
                        )
                    ]
                )
                if waiting:
                    tokens.append(f"{waiting} WAITING ON YOU")
            # PR-level checks failing (source token, not a needsYou row
            # unless the PR is the owner's or awaits their review)
            checks_failing = sum(
                1 for e in entities
                if str(e.get("checks") or "").lower() == "failing"
            )
            if checks_failing:
                tokens.append(f"{checks_failing} CHECKS FAILING")
        elif connector_id == "gh" and query_kind == "branch_ci":
            for entity in entities:
                conclusion = str(entity.get("conclusion") or "").lower()
                if conclusion in ("failure", "timed_out", "cancelled"):
                    tokens.append("CI RED")
                elif conclusion == "success":
                    tokens.append("CI GREEN")
        elif connector_id == "jira" and query_kind == "issues":
            overdue_count = 0
            due_soon_count = 0
            for entity in entities:
                due_at = entity.get("due_at") or entity.get("dueDate")
                if not due_at:
                    continue
                try:
                    due_dt = datetime.fromisoformat(str(due_at).replace("Z", "+00:00").split("T")[0])
                    days = (local_wall().replace(tzinfo=None) - due_dt.replace(tzinfo=None)).days
                except (ValueError, TypeError):
                    continue
                if days > 0:
                    overdue_count += 1
                elif days >= -7:
                    due_soon_count += 1
            if overdue_count:
                tokens.append(f"{overdue_count} OVERDUE")
            if due_soon_count:
                tokens.append(f"{due_soon_count} DUE THIS WEEK")
        # HS-175-04: meeting watch tokens.
        # HS-175 counsel C9(c)/C8: the Watch's entities are RECORDED
        # meetings (started_at in the past) -- they can never yield a
        # future NEXT.  Both tokens read the Room's linked CALENDAR
        # events (calendar_event_projects x calendar_events) in the
        # hub's local week:  ``N THIS WEEK`` = linked events whose
        # starts_at falls in [local Monday, next local Monday);
        # ``NEXT DAY HH:MM`` = the first linked event after now, in
        # local time.  Both absent at zero (A.8).
        elif connector_id == "meeting" and query_kind == "meetings":
            tokens.extend(_meeting_calendar_tokens(db, project_id))

        plain_reason = _plain_reason(last_error)

        # Unknown connectors with no local adapter
        _KNOWN_CONNECTORS = {"gh", "jira", "confluence", "meeting"}
        if connector_id not in _KNOWN_CONNECTORS:
            if not last_error:
                plain_reason = "No local adapter for this source yet"
                w_state = "cant_check"

        entry = {
            "watchId": watch.get("id"),
            "provider": provider,
            "scope": scope,
            "tokens": tokens,
            # C8: SQLite's naive-UTC stamps leave here with an offset so
            # the face prints the viewer's local clock.
            "checkedAt": aware_iso(watch.get("last_success_at")),
            "nextCheckAt": aware_iso(watch.get("next_evaluation_at")),
            "host": host,
            "state": w_state,
            "plainReason": plain_reason,
            "suggested": False,
        }
        groups.setdefault((provider, scope), []).append(entry)

    # Merge groups: one source item per (provider, scope)
    sources: list[dict[str, Any]] = []
    for (_provider, _scope), items in groups.items():
        if len(items) == 1:
            merged = dict(items[0])
            merged["watchIds"] = [merged["watchId"]]
        else:
            # Merge tokens: collect, dedupe by exact label, sort to template order
            all_tokens: list[str] = []
            seen_tokens: set[str] = set()
            for item in items:
                for tok in item["tokens"]:
                    if tok not in seen_tokens:
                        all_tokens.append(tok)
                        seen_tokens.add(tok)
            all_tokens.sort(key=token_sort_key)

            # checkedAt: latest non-null
            checked_vals = [i["checkedAt"] for i in items if i["checkedAt"]]
            merged_checked = max(checked_vals) if checked_vals else None

            # nextCheckAt: soonest non-null
            next_vals = [i["nextCheckAt"] for i in items if i["nextCheckAt"]]
            merged_next = min(next_vals) if next_vals else None

            # state: worst (cant_check > paused > live)
            merged_state = min(
                (i["state"] for i in items),
                key=lambda s: _STATE_SEVERITY.get(s, 2),
            )

            # plainReason: first non-null
            merged_reason = next(
                (i["plainReason"] for i in items if i["plainReason"]),
                None,
            )

            merged = {
                "watchId": items[0]["watchId"],
                "watchIds": [i["watchId"] for i in items],
                "provider": items[0]["provider"],
                "scope": items[0]["scope"],
                "tokens": all_tokens,
                "checkedAt": merged_checked,
                "nextCheckAt": merged_next,
                "host": items[0]["host"],
                "state": merged_state,
                "plainReason": merged_reason,
                "suggested": False,
            }

        # CLEAR: a live source with no tokens after merging
        if not merged["tokens"] and merged["state"] == "live" and _provider in ("github", "jira"):
            merged["tokens"] = ["CLEAR"]

        sources.append(merged)

    # PHILO-15 B60/B69: ONE freshness state per source, from this read,
    # by the rule the attention aggregate reads (``source_freshness``);
    # and a next check that is always ahead: the quiet end while
    # HoldSpeak's quiet hours hold the sweep, else the Watch's own time,
    # or the next sweep when that time has passed.
    quiet_iso = _annotate_source_freshness(db, sources)

    # Top-level nextCheckAt: soonest non-null over live sources
    live_next = [
        s["nextCheckAt"] for s in sources
        if s["state"] == "live" and s["nextCheckAt"]
    ]
    next_check_at = min(live_next) if live_next else None

    return {"items": sources, "count": len(sources), "nextCheckAt": next_check_at,
            "quietUntil": quiet_iso}


def _annotate_source_freshness(db: Any, sources: list[dict[str, Any]]) -> str | None:
    """Write ``freshness``/``freshnessReason`` (and ``quietUntil`` while
    quiet hours hold the sweep) on each source row, and move a past
    ``nextCheckAt`` ahead. Returns the quiet end (aware ISO) or None."""
    from datetime import timezone as _tz

    from .heartbeat_service import read_next_sweep_at, read_quiet_window
    from .needs_you_aggregate import source_freshness

    now_utc = datetime.now(_tz.utc)
    window = read_quiet_window(db, now_utc)
    quiet_iso = window[1].isoformat(timespec="seconds") if window is not None else None
    since_iso = window[0].isoformat(timespec="seconds") if window is not None else None
    nxt_sweep = read_next_sweep_at(db)
    # The loop ticks once a minute: a due check runs within one minute.
    ahead = nxt_sweep if (nxt_sweep is not None and nxt_sweep > now_utc) else (
        now_utc + timedelta(minutes=1)
    ).replace(second=0, microsecond=0)
    for src in sources:
        if quiet_iso:
            src["quietUntil"] = quiet_iso
            src["quietSince"] = since_iso
        state, reason = source_freshness(src)
        src["freshness"] = state
        src["freshnessReason"] = reason
        if src.get("state") != "live":
            continue
        when = src.get("nextCheckAt")
        try:
            parsed = datetime.fromisoformat(str(when).replace("Z", "+00:00")) if when else None
        except (TypeError, ValueError):
            parsed = None
        if parsed is not None and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=_tz.utc)
        if window is not None:
            # A check missed BEFORE quiet hours began is still missed.
            if parsed is not None and parsed < window[0]:
                src["missedCheckAt"] = when
            # Held until the quiet end: never sooner than that.
            if parsed is None or parsed <= window[1]:
                src["nextCheckAt"] = quiet_iso
        elif parsed is None or parsed <= now_utc:
            if parsed is not None:
                # The fact stays: this check was missed (the preparation
                # Brief reads it as STALE); the face shows the next one.
                src["missedCheckAt"] = when
            src["nextCheckAt"] = ahead.isoformat(timespec="seconds")
    return quiet_iso


def _read_room_health(
    db: Any, project_id: str, target_at: str | None, week: dict[str, Any] | None = None, *,
    resolve_review_people: Callable[..., list[dict[str, Any]]],
) -> dict[str, Any]:
    """HEALTH: AT RISK / ON TRACK derivation + HS-173 health signals.

    Betterment P3: ``state`` and ``state_reason`` say where the project
    stands in words, from this week's meeting risks, the risk notes and
    risk items, the owed items past their date and failing CI
    (``room_health_service.project_state``). A risk named this week makes
    the project at risk, so the head never reads "On track" while a
    meeting said the release is blocked.
    """
    from holdspeak.services.room_health_service import (
        ci_health as _ci_health,
        issue_aging as _issue_aging,
        merge_queue_depth as _merge_queue_depth,
        readiness as _readiness,
        review_wait as _review_wait,
    )
    from holdspeak.services.room_people_service import room_people as _room_people

    watches = db.automations.list_project_watches(project_id)
    now = local_wall()

    overdue_count = 0
    ci_failing = False
    review_waiting_days: int | None = None

    # HS-173: collect entities by kind for health derivations
    pr_entities: list[dict[str, Any]] = []
    jira_entities: list[dict[str, Any]] = []
    ci_entities: list[dict[str, Any]] = []
    newest_snapshot_at: str | None = None

    for watch in watches:
        connector_id = watch.get("connector_id", "")
        query_kind = watch.get("query_kind", "")
        snapshot = watch.get("snapshot")
        entities = snapshot_entities(snapshot)

        # Track newest snapshot timestamp for checked_at
        updated_at = watch.get("updated_at") or ""
        if updated_at and (newest_snapshot_at is None or updated_at > newest_snapshot_at):
            newest_snapshot_at = updated_at

        if connector_id == "jira" and query_kind == "issues":
            jira_entities.extend(entities)
            for entity in entities:
                due_at = entity.get("due_at") or entity.get("dueDate")
                if not due_at:
                    continue
                try:
                    due_dt = datetime.fromisoformat(str(due_at).replace("Z", "+00:00").split("T")[0])
                    days = (now.replace(tzinfo=None) - due_dt.replace(tzinfo=None)).days
                except (ValueError, TypeError):
                    continue
                if days > 0:
                    overdue_count += 1

        elif connector_id == "gh" and query_kind == "branch_ci":
            ci_entities.extend(entities)
            for entity in entities:
                conclusion = str(entity.get("conclusion") or "").lower()
                if conclusion in ("failure", "timed_out", "cancelled"):
                    ci_failing = True

        elif connector_id == "gh" and query_kind == "pull_requests":
            pr_entities.extend(entities)
            owner_login = _get_github_owner_login(db, )
            for entity in entities:
                review_requests = entity.get("review_requests") or entity.get("reviewRequests") or []
                if owner_login and owner_login.lower() in [r.lower() for r in review_requests]:
                    updated_at_str = entity.get("updated_at") or entity.get("updatedAt") or ""
                    if updated_at_str:
                        try:
                            updated_dt = datetime.fromisoformat(
                                updated_at_str.replace("Z", "+00:00").rstrip("Z")
                            )
                            age_days = (now - updated_dt.replace(tzinfo=None)).days
                            if review_waiting_days is None or age_days > review_waiting_days:
                                review_waiting_days = age_days
                        except (ValueError, TypeError):
                            pass

    # PHILO-9-01 (F2): a milestone still planned after its date is overdue.
    overdue_milestones = len(_overdue_milestones(db, project_id, now))
    overdue_count += overdue_milestones

    # Target passed
    target_passed = False
    if target_at:
        try:
            target_dt = datetime.fromisoformat(target_at.split("T")[0])
            target_passed = now.replace(tzinfo=None) > target_dt.replace(tzinfo=None)
        except (ValueError, TypeError):
            pass

    # AT RISK when ANY of the inputs is true
    at_risk = (
        overdue_count > 0
        or ci_failing
        or (review_waiting_days is not None and review_waiting_days > 3)
        or target_passed
    )

    # Reason: first true input in order
    reason: str | None = None
    if overdue_count > 0:
        reason = f"{overdue_count} OVERDUE"
    elif ci_failing:
        reason = "CI RED"
    elif review_waiting_days is not None and review_waiting_days > 3:
        reason = f"REVIEW WAITING {_count_unit(review_waiting_days, 'DAY')}"
    elif target_passed:
        reason = "TARGET PASSED"

    # ── HS-173: health signal derivations ────────────────────────
    from datetime import timezone as _tz
    now_utc = datetime.now(_tz.utc)

    review_signal = _review_wait(pr_entities, now_utc)
    issue_signal = _issue_aging(jira_entities, now_utc)

    # CI history: try the latest steward run's OBSERVE step first,
    # fall back to the branch_ci snapshot entities.
    ci_history = _load_ci_history(db, project_id) or ci_entities
    queue_depth = _merge_queue_depth(pr_entities)
    ci_signal = _ci_health(ci_history, queue=queue_depth)

    # Overdue commitments from follow-through
    ft_overdue = _count_overdue_commitments(db, project_id)

    # Blocker count: issues with priority blocker/critical or labels
    # containing "blocker"
    blocker_count = 0
    for entity in jira_entities:
        priority = str(entity.get("priority") or "").lower()
        labels = entity.get("labels") or []
        status = str(entity.get("status") or "").lower()
        if status in ("done", "closed"):
            continue
        if priority in ("blocker", "critical") or any(
            "blocker" in str(lbl).lower() for lbl in labels
        ):
            blocker_count += 1

    release_signal = _readiness(
        review_signal=review_signal,
        ci_signal=ci_signal,
        blocker_count=blocker_count,
        overdue_count=ft_overdue,
    )

    # HS-173: resolve reviewers to people for the bottleneck rows
    people: list[dict[str, Any]] = []
    try:
        people = resolve_review_people(
            project_id, review_signal.get("per_reviewer", []))
    except Exception:
        pass

    # HS-173-04: enrich people rows with nudge state
    try:
        _enrich_people_with_nudge_state(db, project_id, people, pr_entities)
    except Exception:
        pass

    from holdspeak.services.room_health_service import project_state as _project_state

    week = week or {}
    overdue_owed: list[dict[str, Any]] = []
    try:
        for row in (_room_meeting_action_items(db, project_id, now)
                    + _room_commitment_items(db, project_id, now)):
            why = str(row.get("why") or "")
            if why.startswith("OVERDUE · "):
                days = int(why.split("· ", 1)[1].split(" ", 1)[0] or 0)
                ref = (f"action_item:{row['action_item_id']}" if row.get("action_item_id")
                       else f"commitment:{row.get('commitment_id')}")
                overdue_owed.append({"title": row.get("title"), "owner": row.get("owner"),
                                     "days": days, "ref": ref})
    except Exception as exc:
        _log.warning("room health owed items failed for %s: %s", project_id, exc)
    try:
        for item, days in _overdue_milestones(db, project_id, now):
            overdue_owed.append({"title": item.get("title") or "A milestone", "owner": None,
                                 "days": days, "ref": f"project_item:{item['id']}"})
    except Exception as exc:
        _log.warning("room health milestones failed for %s: %s", project_id, exc)
    state = _project_state(
        risks=week.get("risks") or [],
        risk_items=week.get("risk_items") or [],
        overdue_owed=overdue_owed,
        ci_failing=ci_failing,
        broken_dependencies=week.get("broken") or [],
    )
    if state["state"] == "on_track" and at_risk:
        # The older inputs still say at risk, in words.
        jira_overdue = overdue_count - overdue_milestones
        if jira_overdue > 0:
            words = f"{jira_overdue} Jira issue{'' if jira_overdue == 1 else 's'} past the due date"
        elif review_waiting_days is not None and review_waiting_days > 3:
            words = f"a review has waited {review_waiting_days} days for you"
        elif target_passed:
            words = "the target date has passed"
        else:
            words = None
        state = {"state": "at_risk", "reason": words, "ref": None}
    at_risk = at_risk or state["state"] != "on_track"

    return {
        "assessment": "at_risk" if at_risk else "on_track",
        "reason": reason,
        # "state" is the section's own (ok / degraded): the project's is
        # ``project_state``.
        "project_state": state["state"],
        "state_reason": state["reason"],
        "state_ref": state["ref"],
        "inputs": {
            "overdue": overdue_count,
            "overdueMilestones": overdue_milestones,
            "ciFailing": ci_failing,
            "reviewWaitingDays": review_waiting_days,
            "targetPassed": target_passed,
        },
        # HS-173: structured health signals
        "signals": {
            "review_wait": review_signal,
            "issue_aging": issue_signal,
            "ci": ci_signal,
            "release": release_signal,
        },
        "checked_at": newest_snapshot_at,
        "merge_queue_depth": queue_depth,
        "people": people,
    }


def _room_week(db: Any, principal: Principal, project_id: str) -> dict[str, Any]:
    """This week's material for the state and the Now wing (Betterment P3).

    ``risks``: the risk sentences of the project's meetings of the last
    seven days (their summaries and their risk lists, 1:1s left out, as
    the update leaves them out) and the risk lines of the notes filed as
    its sources. ``risk_items``: open risk items. ``broken``: broken
    dependency items. ``meetings_this_week``: linked meetings since the
    local Monday. Each risk keeps its ref and a short source token.
    """
    from .meeting_kind import is_one_on_one, meeting_speakers, title_says_one_on_one
    from .needs_you_membership import _read_people_names
    from .room_health_service import note_risk_lines, risk_sentences

    now = local_wall().replace(tzinfo=None)
    since = now - timedelta(days=_WEEK_DAYS)
    monday, _next = local_week_bounds()
    monday_wall = monday.replace(tzinfo=None)
    people = sorted(_read_people_names(principal) or set())

    risks: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_risk(text: str, ref: str, token: str, source: str) -> None:
        clean = " ".join(str(text or "").split())
        if not clean or clean.casefold() in seen:
            return
        seen.add(clean.casefold())
        risks.append({"text": clean, "ref": ref, "token": token, "source": source, "opens": True})

    meetings = db.projects.get_project_meetings(project_id, limit=200)
    week_ids: dict[str, tuple[str, str]] = {}
    meetings_this_week = 0
    for row in meetings:
        started = _wall(row.get("started_at"))
        if started is None or started < since:
            continue
        if started >= monday_wall:
            meetings_this_week += 1
        meeting_id = str(row.get("id") or "")
        title = str(row.get("title") or "Meeting")
        if not meeting_id or title_says_one_on_one(title):
            continue
        meeting = db.meetings.get_meeting(meeting_id)
        if meeting is None or is_one_on_one(title, meeting_speakers(meeting), people):
            continue
        token = f"MTG {started.strftime('%m-%d')}"
        week_ids[meeting_id] = (title, token)
        summary = str(getattr(getattr(meeting, "intel", None), "summary", "") or "")
        for sentence in risk_sentences(summary):
            add_risk(sentence, f"meeting:{meeting_id}", token, title)
    if week_ids:
        for artifact in db.projects.get_project_artifacts(project_id):
            found = week_ids.get(str(artifact.meeting_id or ""))
            if not found:
                continue
            for entry in (artifact.structured_json or {}).get("risks") or []:
                text = entry.get("risk") if isinstance(entry, dict) else entry
                add_risk(str(text or ""), f"meeting:{artifact.meeting_id}", found[1], found[0])
    for resource in db.project_relationships.list_for_project(project_id):
        kind, _, note_id = str(resource.to_dict().get("resource_ref") or "").partition(":")
        if kind != "note" or not note_id:
            continue
        note = db.notes.get(note_id)
        if note is None:
            continue
        note_title = " ".join(str(getattr(note, "title", "") or "").split()) or "Note"
        for line in note_risk_lines(note_title, str(getattr(note, "body_markdown", "") or "")):
            add_risk(line, f"note:{note_id}", "NOTE", note_title)

    risk_items: list[dict[str, Any]] = []
    broken: list[dict[str, Any]] = []
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT id, item_type, title, lifecycle, severity FROM project_items "
            "WHERE project_id = ? AND item_type IN ('risk', 'dependency')",
            (project_id,),
        ).fetchall()
    for row in rows:
        item = dict(row)
        lifecycle = str(item.get("lifecycle") or "").lower()
        entry = {"title": item.get("title"), "severity": item.get("severity"),
                 "ref": f"project_item:{item['id']}"}
        if item["item_type"] == "risk" and lifecycle in ("open", "at_risk"):
            risk_items.append(entry)
        elif item["item_type"] == "dependency" and lifecycle == "broken":
            broken.append(entry)
    for item in risk_items:
        add_risk(str(item.get("title") or ""), str(item["ref"]), "RISK", "Risk")
    return {
        "risks": risks,
        "risk_items": risk_items,
        "broken": broken,
        "meetings_this_week": meetings_this_week,
    }


def _read_room_now(
    db: Any,
    project_id: str,
    target_at: str | None,
    week: dict[str, Any] | None,
    decisions_section: dict[str, Any],
) -> dict[str, Any]:
    """Betterment P3: the Now wing's reads beside the head's state.

    ``next_date``: the target, or the next planned milestone, whichever
    is first. ``last_update_at``: the newest published update.
    ``meetings_this_week``. ``risks``: this week's risks with their
    sources. ``decided``: the decisions recorded in the last seven days
    (the decision record is the one store the face shows).
    """
    if week is None:
        raise RuntimeError("week material not read")
    today = local_wall().date()
    candidates: list[tuple[str, str]] = []
    if target_at:
        try:
            day = datetime.fromisoformat(str(target_at).split("T")[0]).date()
            if day >= today:
                candidates.append((day.isoformat(), "Target"))
        except (ValueError, TypeError):
            pass
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT title, due_at FROM project_items WHERE project_id = ? "
            "AND item_type = 'milestone' AND lifecycle = 'planned' "
            "AND due_at IS NOT NULL AND due_at != ''",
            (project_id,),
        ).fetchall()
        published = conn.execute(
            "SELECT published_at FROM project_updates WHERE project_id = ? "
            "AND lifecycle = 'published' AND published_at IS NOT NULL "
            "ORDER BY published_at DESC LIMIT 1",
            (project_id,),
        ).fetchone()
    for row in rows:
        try:
            day = datetime.fromisoformat(str(row["due_at"]).replace("Z", "+00:00").split("T")[0]).date()
        except (ValueError, TypeError):
            continue
        if day >= today:
            candidates.append((day.isoformat(), " ".join(str(row["title"] or "").split()) or "Milestone"))
    candidates.sort()
    next_date = {"at": candidates[0][0], "label": candidates[0][1]} if candidates else None

    decided: list[dict[str, Any]] = []
    since = local_wall().replace(tzinfo=None) - timedelta(days=_WEEK_DAYS)
    if decisions_section.get("state") == "ok":
        for item in decisions_section.get("items") or []:
            if str(item.get("kind") or "decision") != "decision":
                continue
            if str(item.get("lifecycle") or "active") not in ("active", "accepted", "current"):
                continue
            at = _wall(item.get("confirmed_at") or item.get("at"))
            if at is None or at < since:
                continue
            source_ref = str(item.get("source_ref") or "")
            if source_ref and not (
                source_ref.startswith("meeting:")
                or source_ref.startswith("decision_record:")
            ):
                source_ref = f"meeting:{source_ref}"
            decided.append({
                "id": item.get("id"),
                "text": item.get("text"),
                "at": item.get("confirmed_at") or item.get("at"),
                "ref": f"decision_record:{item.get('id')}",
                "source": item.get("meeting_title") or "",
                "source_ref": source_ref,
                # 2026-11-08: the Person the decision is committed to (#1891).
                "committed_to": item.get("committed_to"),
            })
    return {
        "next_date": next_date,
        "last_update_at": published["published_at"] if published else None,
        "meetings_this_week": int(week.get("meetings_this_week") or 0),
        "risks": list(week.get("risks") or []),
        "decided": decided,
    }


def _load_ci_history(db: Any, project_id: str) -> list[dict[str, Any]] | None:
    """Load CI history from the latest completed steward run's OBSERVE step.

    Returns a list of CI run dicts, or None when no history is available.
    The steward's OBSERVE phase persists ci_history on the step's
    observed_state_json (HS-173).
    """
    try:
        runs = db.steward_runs.list_runs(
            project_id, state="completed", limit=1)
        if not runs:
            return None
        run_id = runs[0]["id"]
        steps = db.steward_steps.list_steps(
            run_id, phase="observe", limit=1)
        if not steps:
            return None
        observed_raw = steps[0].get("observed_state_json") or "{}"
        if isinstance(observed_raw, str):
            observed = json.loads(observed_raw)
        else:
            observed = observed_raw
        history = observed.get("ci_history")
        if isinstance(history, list) and history:
            return history
    except Exception:
        pass
    return None


def _count_overdue_commitments(db: Any, project_id: str) -> int:
    """Count the Room's open commitments that are past their due date.

    One walk, one rule: the rows are the Room's commitment attention rows
    (``_room_commitment_items``: decision -> source meeting linked to the
    Room, or a decision record filed on the Room; settled rows left out).
    A SQL error is not a count of zero: it surfaces.
    """
    return sum(
        1 for item in _room_commitment_items(db, project_id, local_wall())
        if item["severity"] == "danger"
    )


def _enrich_people_with_nudge_state(
    db: Any,
    project_id: str,
    people: list[dict[str, Any]],
    pr_entities: list[dict[str, Any]],
) -> None:
    """HS-173-04: add nudge={step_id, state, sent_at?} to each person row."""
    if not people:
        return
    # Build a map of login -> latest nudge step for this project.
    prefix = f"nudge:{project_id}:"
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT * FROM steward_steps "
            "WHERE effect_kind = 'github_comment' "
            "AND idempotency_key LIKE ? "
            "ORDER BY created_at DESC LIMIT 500",
            (prefix + "%",),
        ).fetchall()

    # Group by reviewer login, keep the most recent per login.
    nudge_by_login: dict[str, dict[str, Any]] = {}
    for row in rows:
        step = dict(row)
        idem_key = step.get("idempotency_key", "")
        # nudge:{project_id}:{repo}:{pr_number}:{login}
        parts = idem_key.split(":")
        if len(parts) >= 5:
            login = parts[-1]
        else:
            continue
        if login not in nudge_by_login:
            nudge_by_login[login] = {
                "step_id": step["id"],
                "state": step["state"],
                # PHILO-10-02: the card of an UNKNOWN step names the PR to check, after a reload too.
                "pr_number": int(parts[-2]) if parts[-2].isdigit() else None,
                "sent_at": step.get("completed_at") if step["state"] == "sent" else None,
            }

    for person in people:
        login = (person.get("login") or "").lower()
        if login in nudge_by_login:
            person["nudge"] = nudge_by_login[login]


def _read_room_since_read(db: Any, project_id: str, room_read_at: str | None) -> dict[str, Any]:
    """SINCE YOU LOOKED: changes grouped by source in phrases."""
    if room_read_at:
        # Get changes since the read marker via revision lookup
        with db._connection() as conn:
            # Find the revision at or after room_read_at
            row = conn.execute(
                "SELECT MIN(project_revision) as min_rev FROM project_changes "
                "WHERE project_id = ? AND created_at > ?",
                (project_id, room_read_at),
            ).fetchone()
            min_rev = row["min_rev"] if row and row["min_rev"] else None
        if min_rev is not None:
            changes = db.projects.list_project_changes(
                project_id, since_revision=min_rev, limit=100,
            )
        else:
            changes = []
    else:
        changes = []

    # Group changes by source and map kinds to phrases
    groups: dict[str, list[dict[str, Any]]] = {}
    for change in changes:
        kind = change.get("change_kind", "")
        # Determine source label from kind
        if kind.startswith("watch.") or kind.startswith("github."):
            source_label = "GitHub"
        elif kind.startswith("jira."):
            source_label = "Jira"
        else:
            source_label = "Room"

        phrase = _CHANGE_KIND_PHRASES.get(kind, kind.replace("_", " ").replace(".", " "))
        summary = change.get("summary_json")
        detail = ""
        if summary:
            try:
                s = json.loads(summary) if isinstance(summary, str) else summary
                if isinstance(s, dict):
                    if s.get("action"):
                        detail = f" · {s['action']}"
                    elif s.get("name"):
                        detail = f" · {s['name']}"
            except (json.JSONDecodeError, TypeError):
                pass

        entry = {
            "phrase": f"{phrase}{detail}",
            "at": change.get("created_at", ""),
            "url": None,
        }
        groups.setdefault(source_label, []).append(entry)

    # Build summary per group
    result_groups: list[dict[str, Any]] = []
    for source_label, entries in groups.items():
        # Build a short summary like "2 updated · 1 linked"
        kind_counts: dict[str, int] = {}
        for e in entries:
            verb = e["phrase"].split(" · ")[0] if " · " in e["phrase"] else e["phrase"]
            kind_counts[verb] = kind_counts.get(verb, 0) + 1
        summary_parts = [f"{count} {verb}" for verb, count in kind_counts.items()]
        result_groups.append({
            "source": source_label,
            "summary": " · ".join(summary_parts),
            "entries": entries,
        })

    return {
        "readAt": room_read_at,
        "groups": result_groups,
    }


def _read_room_decisions(db: Any, project_id: str) -> dict[str, Any]:
    """DECISIONS: records linked to this project or its meetings.

    HS-172-03: LEFT JOINs confirmed proposals so the face can render
    proposal provenance (source, meeting_title, confirmed_at, was).
    """
    # Find meetings linked to this project
    with db._connection() as conn:
        meeting_rows = conn.execute(
            "SELECT meeting_id FROM meeting_projects WHERE project_id = ?",
            (project_id,),
        ).fetchall()
        meeting_ids = [r["meeting_id"] for r in meeting_rows]
        # Find records sourced from this project's meetings, or filed to
        # the project by either canonical record ref or its retained Desk
        # source ref.  LEFT JOIN confirmed proposals on decision_record_id
        # so proposal provenance stays available for meeting decisions.
        decision_rows = conn.execute(
            """SELECT DISTINCT r.id, r.decision_text, r.created_at, r.lifecycle,
                       r.kind AS record_kind,
                       r.source_type AS record_source_type, r.source_id AS record_source_id,
                       CASE WHEN r.source_type = 'desk'
                            THEN 'decision_record:' || r.id
                            ELSE s.source_ref END AS record_source_ref,
                       p.id AS proposal_id,
                       p.meeting_id AS proposal_meeting_id,
                       p.kind AS proposal_kind,
                       p.original_text AS proposal_original_text,
                       p.owner_hint AS proposal_owner_hint,
                       p.due_hint AS proposal_due_hint,
                       p.text AS proposal_confirmed_text,
                       p.decided_at AS proposal_confirmed_at,
                       p.model_host AS proposal_model_host,
                       p.commitment_id AS proposal_commitment_id,
                       r.owner AS record_owner,
                       dc.due_at AS commitment_due_at,
                       dc.owner AS commitment_owner,
                       dc2.owner AS record_committed_to,
                       ai.status AS action_status,
                       ai.completed_at AS action_completed_at
                FROM decision_records r
                LEFT JOIN decision_record_sources s
                     ON s.record_id = r.id AND s.source_type = 'meeting'
                LEFT JOIN follow_through_proposals p
                     ON p.decision_record_id = r.id
                    AND p.state = 'confirmed'
                LEFT JOIN decision_commitments dc
                     ON dc.id = p.commitment_id
                LEFT JOIN decision_commitments dc2
                     ON dc2.id = 'commitment-' || r.id
                LEFT JOIN action_items ai
                     ON ai.id = dc.action_item_id
                WHERE r.deleted = 0
                AND NOT EXISTS (
                    SELECT 1 FROM desk_decisions dd
                    WHERE r.source_type = 'desk' AND dd.id = r.source_id
                      AND dd.deleted = 0 AND LOWER(dd.status) = 'proposed'
                )
                  AND (
                    EXISTS (
                        SELECT 1
                        FROM decision_record_sources rs
                        JOIN meeting_projects mp ON mp.meeting_id = rs.source_ref
                        WHERE rs.record_id = r.id
                          AND rs.source_type = 'meeting'
                          AND mp.project_id = ?
                    )
                    OR EXISTS (
                        SELECT 1 FROM project_resources pr
                        WHERE pr.project_id = ? AND pr.deleted = 0
                          AND pr.resource_ref = 'decision_record:' || r.id
                    )
                    OR (
                        r.source_type = 'desk' AND EXISTS (
                            SELECT 1 FROM project_resources pr
                            WHERE pr.project_id = ? AND pr.deleted = 0
                              AND pr.resource_ref IN (
                                  'desk_decision:' || r.source_id,
                                  'decision:' || r.source_id
                              )
                        )
                    )
                  )
                ORDER BY r.created_at DESC""",
            (project_id, project_id, project_id),
        ).fetchall()

        # Resolve meeting titles for proposal provenance.
        mtg_titles: dict[str, str] = {}
        for mid in meeting_ids:
            try:
                mtg = conn.execute(
                    "SELECT title FROM meetings WHERE id = ?", (mid,)
                ).fetchone()
                if mtg and mtg["title"]:
                    mtg_titles[mid] = mtg["title"]
            except Exception:
                pass

    items = []
    seen_record_ids: set[str] = set()
    for row in decision_rows:
        rid = row["id"]
        if rid in seen_record_ids:
            continue
        seen_record_ids.add(rid)

        item: dict[str, Any] = {
            "id": rid,
            "text": row["decision_text"],
            "at": row["created_at"],
            "url": None,
            # HS-200-11: current vs superseded rides with the row so a
            # preparation manifest can carry the distinction in (AC2),
            # and a superseded record names its successor (counsel P1-2).
            "lifecycle": str(row["lifecycle"] or "active"),
            # HS-200-16: the RECORD's kind rides with the row.  Confirming
            # an action-kind proposal also writes a decision_records row
            # (proposal_bridge_service.py:588-590), so this section holds
            # commitments too; without the kind every consumer draws them
            # as decisions.  RecallService reads the same column to keep
            # an action out of its CURRENT cards
            # (recall_service.py:193-196); a consumer that cannot drop the
            # row must at least tell the truth about what it is.
            # PHILO-15 08: the record carries its own kind now.
            "kind": str(row["proposal_kind"] or "") or str(row["record_kind"] or "") or "decision",
            # PHILO-14 A2: the record's source identity (a meeting record's
            # source is the `decisions` row its opener reads), so a face
            # opens and dedupes by identity, never by the text.
            "source_type": row["record_source_type"],
            "source_id": row["record_source_id"],
            "source_ref": row["record_source_ref"],
            # 2026-11-08 (#1891): the name the record is committed to, or None.
            "committed_to": str(row["record_committed_to"] or "") or None,
        }
        if item["lifecycle"] == "superseded":
            with db._connection() as succ_conn:
                successor = succ_conn.execute(
                """SELECT new_value FROM decision_record_revisions
                   WHERE record_id = ? AND field_name = 'successor_id'
                   ORDER BY created_at DESC LIMIT 1""",
                    (rid,),
                ).fetchone()
            if successor and successor["new_value"]:
                item["successor_id"] = str(successor["new_value"])

        # HS-172-03: proposal provenance fields.
        proposal_id = row["proposal_id"] if "proposal_id" in row.keys() else None
        if proposal_id:
            prop_meeting_id = row["proposal_meeting_id"] or ""
            item["proposal_id"] = proposal_id
            item["source"] = "meeting"
            item["meeting_title"] = mtg_titles.get(prop_meeting_id, "")
            item["confirmed_at"] = row["proposal_confirmed_at"]
            item["commitment_id"] = row["proposal_commitment_id"]
            # PHILO-15 B70: an action marked done says DONE on its row.
            if str(row["action_status"] or "") == "done":
                item["done"] = True
                item["done_at"] = aware_iso(row["action_completed_at"])

            # Build "was" dict: only fields the owner changed.
            was: dict[str, str] = {}
            orig_text = row["proposal_original_text"] or ""
            conf_text = row["proposal_confirmed_text"] or ""
            if orig_text and conf_text and orig_text != conf_text:
                was["text"] = orig_text
            orig_owner = row["proposal_owner_hint"] or ""
            conf_owner = row["commitment_owner"] or row["record_owner"] or ""
            if orig_owner and conf_owner and orig_owner != conf_owner:
                was["owner"] = orig_owner
            orig_due = row["proposal_due_hint"] or ""
            conf_due = row["commitment_due_at"] or ""
            if orig_due and conf_due and orig_due != conf_due:
                was["due"] = orig_due
            if was:
                item["was"] = was

        items.append(item)
    # PG16: a Program's Skip or merge by rule, proposed and not yet
    # accepted, with its Program and its PR (the Room's proposed fold).
    from .program_decisions import room_proposed

    return {"items": items, "proposed": room_proposed(db, project_id)}


def _read_room_commitments(db: Any, project_id: str) -> dict[str, Any]:
    """COMMITMENTS: via their decision (whose source meeting is linked).

    HS-172-03: joins through decision_records.source_id to reach
    decision_commitments.decision_id (which references decisions.id,
    not decision_records.id).
    """
    # Get the decision record IDs first.
    decisions_data = _read_room_decisions(db, project_id)
    record_ids = [d["id"] for d in decisions_data.get("items", [])]
    if not record_ids:
        return {"items": []}

    with db._connection() as conn:
        # Map decision_records.id -> decision_records.source_id (= decisions.id)
        placeholders = ",".join("?" * len(record_ids))
        source_rows = conn.execute(
            f"SELECT id, source_id FROM decision_records WHERE id IN ({placeholders})",
            record_ids,
        ).fetchall()
        decision_ids = [str(r["source_id"]) for r in source_rows if r["source_id"]]
        if not decision_ids:
            return {"items": []}

        placeholders2 = ",".join("?" * len(decision_ids))
        commitment_rows = conn.execute(
            f"""SELECT c.id, c.owner, c.due_at, c.status, c.action_item_id,
                       ai.task AS text,
                       (SELECT p.kind FROM follow_through_proposals p
                         WHERE p.commitment_id = c.id LIMIT 1) AS proposal_kind
                FROM decision_commitments c
                LEFT JOIN action_items ai ON ai.id = c.action_item_id
                WHERE c.decision_id IN ({placeholders2})
                  AND c.status != 'completed'
                ORDER BY c.due_at ASC NULLS LAST, c.created_at ASC""",
            decision_ids,
        ).fetchall()

    items = []
    for row in commitment_rows:
        items.append({
            "id": row["id"],
            "text": row["text"] or "",
            "dueAt": row["due_at"],
            "owner": row["owner"],
            # HS-200-16, the mirror of the decisions rule: confirming a
            # decision-kind proposal also writes a commitment, so this
            # section holds decisions too.  The kind rides with the row.
            "kind": str(row["proposal_kind"] or "") or "action",
            # PHILO-14 A2: Follow-through keys its card by the action item.
            "action_item_id": row["action_item_id"],
        })
    return {"items": items}


def _read_room_target(target_at: str | None) -> dict[str, Any]:
    """TARGET: days left and passed flag."""
    if not target_at:
        return {"targetAt": None, "daysLeft": None, "passed": False}
    try:
        target_dt = datetime.fromisoformat(target_at.split("T")[0])
        now = local_wall()
        delta = (target_dt.replace(tzinfo=None) - now.replace(tzinfo=None)).days
        return {
            "targetAt": target_at,
            "daysLeft": delta if delta >= 0 else None,
            "passed": delta < 0,
        }
    except (ValueError, TypeError):
        return {"targetAt": target_at, "daysLeft": None, "passed": False}


def _read_room_receipts(db: Any, project_id: str) -> dict[str, Any]:
    """HS-174-04: pipeline receipts scoped to this project (last 10).

    Searches pipeline_events where the project_id appears in
    args_summary.  Each receipt carries origin/caller so the face can
    show the REMOTE badge.  Returns ``{items: [...]}``; empty list
    when none.
    """
    _LIMIT = 10
    # Scoping is a substring match on args_summary (counsel-on-built
    # 174, condition 3).  Project ids are ``proj-<12 hex>``, so a
    # collision needs one id to be a substring of another summary's
    # id -- improbable, not impossible.  The exact form is
    # ``json_extract(args_summary, '$.project_id') = ?``; V0 keeps
    # LIKE because summaries are not guaranteed to be JSON objects.
    # PHILO-9-01 (F7): the Room's RECEIPTS are its WRITES. Every service
    # call is a pipeline event, so the Room's own reads ("READ MEETINGS"
    # x n) filled the list; only the named write methods count now.
    writes = sorted(ROOM_WRITE_METHODS)
    marks = ",".join("?" for _ in writes)
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT event_id, timestamp, service, method, "
            "       origin, caller, caller_identity, "
            "       args_summary, result_summary, error "
            "FROM pipeline_events "
            # PHILO-9-03 (F7; Codex Astra r2 finding 3): a write names its
            # project in its arguments or in its result (a create, a
            # watch's record); _RECEIPT_SCOPE below says which, exactly.
            f"WHERE method IN ({marks}) AND (args_summary LIKE ? OR result_summary LIKE ?) "
            "ORDER BY timestamp DESC LIMIT ?",
            (*writes, f"%{project_id}%", f"%{project_id}%", _LIMIT * 5),
        ).fetchall()
        # PHILO-9-03 (Codex Astra r1 finding 3, r2 finding 3): the LIKE
        # above is only a prefilter. A receipt belongs to this Room when
        # its PRODUCER's project-identity field is this project's id
        # (_RECEIPT_SCOPE) -- never because some value in the payload (a
        # name, a title) happens to equal or contain it.
        rows = [row for row in rows if _receipt_project(
            str(row["method"]), row["args_summary"], row["result_summary"]) == project_id]
        # PHILO-9-03 (F7): the Room's admitted writes outside the observed
        # services (publish, delivery, the steward's run, the review) are
        # kernel receipts, not pipeline events: read them by the target
        # the operation named -- the project, one of its updates or runs.
        kernel_rows = conn.execute(
            "SELECT o.operation_id, o.name, o.principal_kind, o.principal_identity, "
            "       r.state, r.outcome, r.created_at "
            "FROM kernel_operations o JOIN kernel_receipts r ON r.operation_id = o.operation_id "
            "WHERE o.parent_operation_id = '' AND ("
            "   o.target_ref = ? "
            "   OR o.target_ref IN (SELECT 'project_update:' || id FROM project_updates WHERE project_id = ?) "
            "   OR o.target_ref IN (SELECT 'steward_run:' || id FROM steward_runs WHERE project_id = ?)) "
            "ORDER BY r.created_at DESC LIMIT ?",
            (f"project:{project_id}", project_id, project_id, _LIMIT * 3),
        ).fetchall()
    items = []
    for row in rows:
        origin_val = str(row["origin"]) if row["origin"] and row["origin"] != "local" else None
        caller_val = str(row["caller"]) if row["caller"] else None
        items.append({
            "id": str(row["event_id"]),
            "op": str(row["method"]),
            "label": f"{row['service']}.{row['method']}",
            "title": f"{row['service']}.{row['method']}",
            "outcome": "error" if row["error"] else "ok",
            "reason": None,
            "origin": origin_val,
            "caller": caller_val,
            "identity": str(row["caller_identity"]) if row["caller_identity"] else None,
            "at": row["timestamp"],
            "timestamp": row["timestamp"],
        })
    for row in kernel_rows:
        name = str(row["name"])
        # A ProjectService write is already its pipeline event above.
        if name in _SERVICE_OBSERVED_OPERATIONS or name.startswith(_SERVICE_OBSERVED_PREFIXES):
            continue
        state = str(row["state"])
        agent = str(row["principal_kind"]) != "owner"
        items.append({
            "id": str(row["operation_id"]),
            "op": name.removeprefix("project."),
            "label": name,
            "title": name,
            "outcome": "ok" if state == "succeeded" else state,
            # PHILO-9-03 (Codex Astra r1 finding 1): a refused or failed
            # write keeps the kernel's named outcome (e.g.
            # `update_not_published`) so the face can say why.
            "reason": None if state == "succeeded" else (str(row["outcome"] or "") or None),
            "origin": None,
            "caller": str(row["principal_identity"]) if agent else None,
            "identity": str(row["principal_identity"]) or None,
            "at": row["created_at"],
            "timestamp": row["created_at"],
        })
    items.sort(key=lambda item: float(item["timestamp"] or 0), reverse=True)
    return {"items": items[:_LIMIT]}

