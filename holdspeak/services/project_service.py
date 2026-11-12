"""Transport-neutral project and relationship operations (HS-123-05).

HS-158-02 graduation: every accepted write increments projects.revision
exactly once, appends a project_changes row and a ServiceEventLedger event
in the same transaction (DOM-003, DOM-004, API-004).  Optional
expected_revision / command_id enforce optimistic concurrency (API-001)
and idempotent replay (API-002, DOM-010).  Absent params = legacy behavior
(API-006).  HS-173-08 / 158 S-1: the four legacy-wrapping methods
(add/remove_resource, associate/disassociate_meeting) folded from three
separate transactions into one atomic transaction each.

HS-158-03: item commands under the revision law (create/update/transition/
list).  Items are Project-OWNED records (SS5.3), not citizens (SS3.2).
changed_refs carries ``project:<id>``; the item id rides in the result
payload.  Event kind is ``project.updated`` (SS10 has no item event kind).
"""
from __future__ import annotations

from dataclasses import asdict
from .room_binding import room_binding

import logging
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from holdspeak.timestamps import utc_now_iso
from typing import Any, Optional

from ..db.core import Database
from ..db.relationships import qualified_ref
from ..logging_config import get_logger
from ..meeting_aftercare import compute_project_since_last_meeting
from ..principals import Principal, PrincipalKind
from ..project_contracts import (
    CommandResultEnvelope,
    ProjectError,
    ProjectErrorCode,
    ResultKind,
    generate_pchg_id,
    generate_pcmd_id,
    generate_pitem_id,
    generate_psrc_id,
)
from ..refs import format as format_ref, parse as parse_ref
from .errors import ConflictError, NotFound, ServiceError, ValidationError
from .project_definitions import (  # noqa: F401  re-exported: the same objects, one owner (project_definitions)
    _ABSENT_SECTION, _ASK_STOP_CODE, aware_iso, _CHANGE_KIND_PHRASES, _COMMITMENT_SETTLED, _count_unit,
    _DETAILS_SCHEMAS, _format_age, _is_number_or_none, _is_str, _is_str_or_none, ITEM_DEFAULT_LIFECYCLE,
    ITEM_LIFECYCLES, ITEM_TYPES, local_now, local_week_bounds, localize, plain_reason, _PLAIN_REASON_PATTERNS,
    PLAIN_REASONS, _POSTURE_MAX, _POSTURE_REASON_MAX, PROJECT_LIFECYCLES, PROVENANCE_KINDS,
    _PROVIDER_TO_CONNECTOR, _receipt_project, _RECEIPT_SCOPE, ROOM_CHANGES_CAP, ROOM_FOCUS_CAP,
    _ROOM_UPDATES_CAP, ROOM_WRITE_METHODS, _SERVICE_OBSERVED_OPERATIONS, _SERVICE_OBSERVED_PREFIXES,
    SEVERITY_LEVELS, _SEVERITY_ORDER, SEVERITY_RANK, _SLUG_MAX, snapshot_entities, _source_watch_identity,
    _STATE_SEVERITY, _SUBJECT_TO_QUERY_KIND, _TOKEN_ORDER_PREFIXES, token_sort_key, _top_level, utc_z,
    validate_details, validate_lifecycle, validate_optional_ref, validate_severity, _wall, _WEEK_DAYS,
)
from . import project_room_reads as room_reads
from .project_setup_service import CADENCE_PRESETS
from .service_event_ledger import ServiceEventLedger

_log = get_logger("services.project_service")


class _CommandRaced(Exception):
    """PHILO-9-02 (law 9): another caller recorded this command_id first.

    Raised inside the write transaction, under the write lock, before any
    write: the transaction rolls back with nothing written, and the call is
    answered again through the replay path (the winner's recorded response,
    or ``idempotency_conflict`` for a different request).
    """


def _serialized_command(method: Any) -> Any:
    """Answer a lost same-key race through the replay path (PHILO-9-02, law 9)."""
    import functools

    @functools.wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return method(self, *args, **kwargs)
        except _CommandRaced:
            return method(self, *args, **kwargs)

    return wrapper


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash of a command's request payload (API-002)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _envelope_to_dict(env: CommandResultEnvelope) -> dict[str, Any]:
    """Serialize an envelope to a JSON-safe dict for storage/response."""
    return {
        "result_kind": env.result_kind.value,
        "project_id": env.project_id,
        "project_revision": env.project_revision,
        "changed_refs": [str(r) for r in env.changed_refs],
    }


def _custody_identity() -> str:
    """A DURABLE identity for the desk that holds a saved ask (HS-200-41 F1).

    Custody asks "is this the same DESK?".  Two nearby answers were tried and
    both answer a different question:

    - ``RefinementCoordinator.host_id`` is ``refhost_<uuid4>``, minted per
      PROCESS (`refinement_coordinator.py:45`), so custody read ``elsewhere``
      on the same desk after every restart — and the face printed the raw
      uuid, breaking the no-raw-ids rule as well.
    - ``runtime_identity.database_identity`` digests the database path plus
      its device and INODE.  That is correct for its own purpose and stays
      untouched — HS-200-02 needs a REPLACED file to read as a different
      database — but an inode answers "is this the same FILE?".  Recreate the
      file and it flips, so custody was nondeterministic across a restart and
      would have claimed SAVED ON ANOTHER DESK after a restore from backup,
      on the very machine that saved the ask.

    So custody keys on ``config.machine_identity()``: minted once, persisted
    beside the hub's other durable settings, never regenerated.  It survives a
    restart, a database restore and a schema reconcile.  It is opaque and
    never leaves the hub — the DTO carries the ``here``/``elsewhere`` verdict
    and never this token.

    An identity the hub cannot establish is ``""``, and an empty custody stamp
    draws no token at all.  Identity failure is never load-bearing: an unknown
    desk says nothing rather than guessing ``here``.
    """
    try:
        from ..config import machine_identity

        return str(machine_identity() or "")
    except Exception:  # pragma: no cover - identity is never load-bearing
        return ""


class _ProjectObserver:
    def __init__(self, delegate: Any) -> None:
        self._delegate = delegate

    def on_event(self, event: Any) -> None:
        if event.service == "ProjectService" and event.method in {"people_preparation", "cached_needs_you"}:
            from dataclasses import replace
            event = replace(event, args_summary="{}", result_summary='{"people":"redacted"}')
        self._delegate.on_event(event)


@observe_service
class ProjectService:
    """The durable project boundary; routes only parse and serialize."""

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None,
                 review_available: bool | None = None,
                 delta_service: Any = None) -> None:
        self._db = db
        self._observer = _ProjectObserver(observer or NullObserver())
        self._ledger = ServiceEventLedger(db)
        # S52: the Room's review section is a capability flag, not a held
        # command service.  The review row is read through
        # ``DeltaRepository.get_open_review``; this service never holds or
        # calls ProjectDeltaService.  ``review_available`` says whether the
        # review domain exists on this desk (a bare service: absent).
        # ``delta_service=`` is the legacy spelling kept for callers that
        # still compose it: a non-None value (even a falsey stand-in) means
        # available; the object is not retained.  An explicit boolean wins.
        if review_available is None:
            review_available = delta_service is not None
        self._review_available = bool(review_available)

    def people_preparation(self, principal: Principal, project_id: str, *, people_service: Any = None) -> dict[str, Any]:
        from ..operations import OperationOwnerRequired
        from ..principals import PrincipalKind
        from .room_people_service import room_people_preparation
        from ..runtime.composition import service

        if principal.kind is not PrincipalKind.OWNER:
            raise OperationOwnerRequired("project.people")
        people = people_service if people_service is not None else service("people_service", lambda: None)
        return room_people_preparation(self, people, project_id, principal)

    def people_preparation_sources(self, project_id: str) -> dict[str, Any]:
        """The project's open commitments and watches for its People projection."""
        self._require_project(project_id)
        return {"commitments": room_reads.people_commitments(self._db, project_id),
                "watches": self._db.automations.list_project_watches(project_id)}

    # ── reads (unchanged) ────────────────────────────────────────────

    def list_projects(
        self, principal: Principal, filters: dict[str, Any] | None = None,
        *, include_archived: bool | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        if include_archived is None:
            include_archived = bool(filters.get("include_archived", False))
        return [self._project_payload(project) for project in self._db.projects.list_projects(
            include_archived=bool(include_archived)
        )]

    def get_project(self, principal: Principal, project_id: str) -> dict[str, Any]:
        return self._project_payload(self._require_project(project_id))

    def briefing_facts(self, principal: Principal) -> dict[str, list[dict[str, Any]]]:
        """The Room's meeting decisions and commitments, once per identity.

        The brief consumes the same section readers as ``room`` without
        building another Room (Needs you already read each Room for coverage).
        """
        decisions = {}
        commitments = {}
        for project in self.list_projects(principal):
            rows = self._read_room_decisions(project["id"])["items"]
            for row in rows:
                if row.get("kind") == "decision" and row.get("source_type") == "meeting":
                    decisions[row["id"]] = row
            by_commitment = {row["commitment_id"]: row for row in rows if row.get("commitment_id")}
            for row in self._read_room_commitments(project["id"])["items"]:
                if row.get("kind") != "action":
                    continue
                decision = by_commitment.get(row["id"], {})
                commitments[row["id"]] = {
                    **row, "at": decision.get("at"),
                    "ref": (f"decision:{decision['source_id']}" if decision.get("source_id") else
                            f"action_item:{row['action_item_id']}" if row.get("action_item_id") else
                            f"commitment:{row['id']}"),
                }
        return {"decisions": list(decisions.values()), "commitments": list(commitments.values())}

    def list_briefings(self, principal: Principal, project_id: str, limit: int = 50) -> dict[str, Any]:
        self._require_project(project_id)
        clean_limit = max(1, min(int(limit), 200))
        annotations = self._db.activity.list_activity_annotations(
            source_connector_id="meeting_context", annotation_type="meeting_context_briefing",
            limit=max(clean_limit * 4, 100),
        )
        rows = [{"id": ann.id, "title": ann.title, "value": ann.value,
                 "created_at": ann.created_at.isoformat(), "updated_at": ann.updated_at.isoformat()}
                for ann in annotations if isinstance(ann.value, dict) and ann.value.get("project_id") == project_id]
        return {"project_id": project_id, "briefings": rows[:clean_limit]}

    def list_meetings(self, principal: Principal, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return self._db.projects.get_project_meetings(project_id, limit=limit, offset=offset)

    def list_resources(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [row.to_dict() for row in self._db.project_relationships.list_for_project(project_id)]

    def _project_resource_ref(self, resource_ref: str) -> str:
        """The one ref name a Project keeps for a resource.

        A desk decision is `desk_decision:<id>` (the name memory, Send and
        grounding read). The Desk window names it `decision:<id>`; that name
        is taken here and written as the one name, so a decision filed from
        any face is found in its Project. A meeting decision keeps
        `decision:<id>`.
        """
        ref = qualified_ref(resource_ref)
        kind, _, resource_id = ref.partition(":")
        if (
            kind == "decision"
            and self._db.desk_decisions.get(resource_id) is not None
            and self._db.decisions.get(resource_id) is None
        ):
            return f"desk_decision:{resource_id}"
        return ref

    def _validate_repository_binding(self, principal: Principal, resource_ref: str) -> None:
        """Allow the owner to file one registered local Delivery Source.

        Repository bindings are the durable authority used by Hand to agent;
        an agent or launch must not be able to widen its own Project's local
        repository.  Validation reads the same persisted registry as the
        delivery context and never registers, imports or saves a source.
        """
        kind, _, source_id = resource_ref.partition(":")
        if kind != "repository":
            return
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise ServiceError(
                "owner_required",
                "Only the owner can bind a local repository to a Project.",
                context={"status": 403},
            )
        from ..delivery.registry import DeliveryRegistry

        registry = DeliveryRegistry.read_only_snapshot()
        if registry.get(source_id) is None:
            raise NotFound("delivery source", source_id)

    @staticmethod
    def _project_resource_ref_names(ref: str) -> tuple[str, ...]:
        """The names a stored row can carry for ``ref`` (old rows: `decision:`)."""
        kind, _, resource_id = ref.partition(":")
        if kind == "desk_decision":
            return (ref, f"decision:{resource_id}")
        return (ref,)

    def list_resource_relationships(self, principal: Principal, resource_ref: str) -> dict[str, Any]:
        ref = qualified_ref(resource_ref)
        placement = self._db.directory_memberships.get(ref)
        projects: dict[str, Any] = {}
        for name in self._project_resource_ref_names(self._project_resource_ref(ref)):
            for row in self._db.project_relationships.list_for_resource(name):
                projects.setdefault(row.project_id, row)
        return {"resource_ref": ref, "zone": placement.to_dict() if placement else None,
                "knowledge": [row.to_dict() for row in self._db.knowledge_memberships.list_for_resource(ref)],
                "projects": [row.to_dict() for row in projects.values()],
                "explanations": {"zone": "Where this object lives; exactly one Zone or the Desk root.",
                                 "knowledge": "Reusable collections this object informs; membership does not move it.",
                                 "projects": "Work this object supports; a relationship does not file or copy it."}}

    def list_meeting_projects(self, principal: Principal, meeting_id: str) -> list[dict[str, Any]]:
        self._require_meeting(meeting_id)
        return self._db.projects.get_meeting_projects(meeting_id)

    def since_last_meeting(self, principal: Principal, project_id: str) -> dict[str, Any]:
        self._require_project(project_id)
        return compute_project_since_last_meeting(self._db, project_id) or {}

    def summary(self, principal: Principal, project_id: str) -> dict[str, Any]:
        self._require_project(project_id)
        return self._db.projects.get_project_summary(project_id)

    def list_action_items(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [{"id": item.id, "task": item.task, "owner": item.owner, "due": item.due,
                 "status": item.status, "review_state": item.review_state,
                 "source_timestamp": item.source_timestamp, "meeting_id": item.meeting_id,
                 "meeting_title": item.meeting_title, "meeting_date": item.meeting_date.isoformat(),
                 "created_at": item.created_at.isoformat(),
                 "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                 "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None}
                for item in self._db.projects.get_project_action_items(project_id)]

    def list_artifacts(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [{"id": item.id, "meeting_id": item.meeting_id, "artifact_type": item.artifact_type,
                 "title": item.title, "body_markdown": item.body_markdown, "confidence": item.confidence,
                 "status": item.status, "plugin_id": item.plugin_id, "created_at": item.created_at.isoformat()}
                for item in self._db.projects.get_project_artifacts(project_id)]

    # ── the desk's NEEDS YOU (PHILO-9-01, F13) ────────────────────────

    def proposal_needs(self, *, project_id: str | None) -> list[dict[str, Any]]:
        """The open proposals as NEEDS YOU rows: one Project's, or (``None``)
        those from meetings in no Project (PHILO-15 08, B03).

        A deferred row stays out until its stamp passes (PHILO-15 08).
        """
        from .proposal_bridge_service import is_deferred

        if project_id is not None:
            proposals = self._db.proposals.list_proposals(
                project_id=project_id, state="proposed",
            )
        else:
            proposals = [
                prop for prop in self._db.proposals.list_proposals(state="proposed")
                if not prop.project_id
                and not self._db.projects.get_meeting_projects(prop.meeting_id)
            ]
        needs: list[dict[str, Any]] = []
        for prop in proposals:
            if is_deferred(prop):
                continue
            # Resolve meeting title AND its start for provenance.
            # HS-200-16: the caption reads `from <meeting> <MM-DD>`; that
            # date is the MEETING's, never the proposal row's write time.
            # On a same-day desk the two agree, so the difference was
            # invisible until a two-working-day walk: a meeting read the
            # next morning was captioned with today's date while the
            # review wing and recall both said yesterday's.
            meeting_title = ""
            meeting_started_at = ""
            try:
                mtg = self._db.meetings.get_meeting(prop.meeting_id)
                meeting_title = (mtg.title or "") if mtg else ""
                if mtg is not None and getattr(mtg, "started_at", None) is not None:
                    meeting_started_at = mtg.started_at.isoformat()
            except Exception:
                pass
            why_parts = ["PROPOSED"]
            if meeting_title:
                why_parts.append(meeting_title)
            needs.append({
                "source": "proposal",
                "kind": "proposal",
                "title": prop.text,
                "why": " · ".join(why_parts),
                "since": prop.created_at,
                "url": None,
                "verb": "confirm",
                "verbHref": f"/api/proposals/{prop.id}/confirm",
                "severity": "info",
                "binding": room_binding(asdict(prop)),
                "proposal_id": prop.id,
                "proposal_kind": prop.kind,
                "host": prop.model_host,
                "speaker_label": prop.speaker_label,
                "due_hint": prop.due_hint,
                "owner_hint": prop.owner_hint,
                "original_text": prop.original_text,
                "meeting_id": prop.meeting_id,
                "action_item_id": prop.action_item_id,
                "meeting_title": meeting_title,
                "meeting_started_at": meeting_started_at,
                "created_at": prop.created_at,
            })
        return needs

    def bind_needs_you_cache(self, cache: Any) -> None:
        self._room_needs_you_cache = cache

    def cached_needs_you(self, principal: Principal, *, fresh: bool = False, door_upcoming: Any = None,
                         direction: str | None = None, person: str | None = None,
                         project: str | None = None, week: bool = False) -> dict[str, Any]:
        """The owner's cached HTTP view; private rows never enter observed output."""
        from ..operations import OperationOwnerRequired
        from .needs_you_membership import compose, filter_answer
        if principal.kind is not PrincipalKind.OWNER:
            raise OperationOwnerRequired("desk.needs_you.owner_view")
        data = self._room_needs_you_cache.get(force=fresh)
        return filter_answer(compose(self._db, principal, data), direction=direction, person=person,
                             project=project, week=week)

    def needs_you(
        self,
        principal: Principal,
        *,
        door_upcoming: Any = None,
        direction: str | None = None,
        person: str | None = None,
        project: str | None = None,
        week: bool = False,
    ) -> dict[str, Any]:
        """What needs the owner: ONE rule, ONE count, every face.

        The answer is the R1-R3 membership (``needs_you_membership``): Door
        cards, Room rows, meeting-path blockers and failed summaries. ``count``
        is the number the bell, the Chair, the Dock, the Brief, notifications,
        the palette, the system shade and MCP all show.

        PHILO-9-01 (F13): the HTTP route applied the heartbeat's muted
        projects and MCP ``desk.needs_you`` did not, so the two counts
        differed with a muted project. Both transports reach this method
        through the declared ``desk.needs_you`` operation now. ``door_upcoming``
        is the hub's calendar read (``DoorService._upcoming``), held by the
        transport; ``None`` when the process has none.

        Betterment D2: ``direction``, ``person``, ``project`` and ``week``
        narrow the rows (``needs_you_membership.filter_answer``); the number
        stays the desk's one number.
        """
        from .needs_you_aggregate import build_aggregate, shared_last_known
        from .needs_you_membership import compose, filter_answer, withhold_people_content

        aggregate = build_aggregate(
            list_projects=self.list_projects,
            room=self.room,
            principal=principal,
            door_upcoming=door_upcoming,
            last_known=shared_last_known(lambda: self._db),
            unfiled_proposals=lambda: self.proposal_needs(project_id=None),
        )
        # The one rule (needs_you_membership): the Door's asking columns, the
        # Room rows, the meeting-path blockers and the failed summaries. The
        # heartbeat's muted projects are applied by the rule.
        # This method is OBSERVED: its result is summarized into the
        # plaintext ``pipeline_events`` table. People content must never pass
        # through it, so the commitments are counted here and their text is
        # withheld. The owner's cached HTTP view composes the full rows through
        # cached_needs_you; _ProjectObserver redacts that whole result.
        return withhold_people_content(filter_answer(
            compose(self._db, principal, aggregate),
            direction=direction, person=person, project=project, week=week,
        ))

    # ── room projection (HS-158-04, SS6.2) ────────────────────────────

    def room(self, principal: Principal, project_id: str) -> dict[str, Any]:
        """Coherent, revision-stamped room projection (SS6.2, HS-158-04).

        Returns one dict with every section the first useful render needs.
        Per-section fault isolation (NFR-003): each sub-read is wrapped;
        a failure degrades that section without failing the response.
        404 only when the project itself is missing.

        observed_at is derived from project.updated_at (fully deterministic:
        two reads with no writes in between produce byte-identical payloads).

        Focus ordering (DB-005): severity DESC NULLS LAST, due_at ASC
        NULLS LAST, sort_key ASC NULLS LAST, created_at ASC, id ASC.
        """
        project = self._require_project(project_id)
        room_fields = self._db.projects.get_project_room_fields(project_id)

        # Orientation: identity + SS5.1 fields + revision + is_archived
        orientation = self._project_payload(project)
        revision = 0
        if room_fields:
            orientation["purpose"] = room_fields["purpose"]
            orientation["outcome_text"] = room_fields["outcome_text"]
            orientation["owner_ref"] = room_fields["owner_ref"]
            orientation["lifecycle"] = room_fields["lifecycle"]
            orientation["posture"] = room_fields["posture"]
            orientation["posture_reason"] = room_fields["posture_reason"]
            orientation["start_at"] = room_fields["start_at"]
            orientation["target_at"] = room_fields["target_at"]
            orientation["review_cadence_json"] = room_fields["review_cadence_json"]
            orientation["next_review_at"] = room_fields["next_review_at"]
            orientation["template_key"] = room_fields["template_key"]
            orientation["modules_json"] = room_fields["modules_json"]
            orientation["revision"] = room_fields["revision"]
            orientation["last_review_id"] = room_fields["last_review_id"]
            orientation["last_review_at"] = room_fields["last_review_at"]
            revision = room_fields["revision"] or 0

        # observed_at: derived from project.updated_at for full determinism
        observed_at = project.updated_at.isoformat()

        # HS-169-04: the four questions' wire data
        target_at = (room_fields or {}).get("target_at")
        room_read_at = (room_fields or {}).get("room_read_at")

        # HS-169-04: build sources first so nextCheckAt can be hoisted
        sources_section = self._room_section(
            "sources", lambda: self._read_room_sources(project_id))
        # Top-level nextCheckAt: from sources section when ok
        next_check_at = (
            sources_section.get("nextCheckAt")
            if sources_section.get("state") == "ok"
            else None
        )

        # Betterment P3: this week's material, read once for the state and
        # the Now wing (the health reason and This week say the same thing).
        try:
            week = self._room_week(principal, project_id)
        except Exception as exc:
            _log.warning("room week material failed for %s: %s", project_id, exc)
            week = None
        decisions_section = self._room_section(
            "decisions", lambda: self._read_room_decisions(project_id))

        return {
            "project_id": project_id,
            "revision": revision,
            "observed_at": observed_at,
            "nextCheckAt": next_check_at,
            "project": orientation,
            "items": self._room_section(
                "items", lambda: self._read_room_items(project_id)),
            "meetings": self._room_section(
                "meetings", lambda: self._read_room_meetings(
                    principal, project_id, project)),
            "resources": self._room_section(
                "resources", lambda: self._read_room_resources(project_id)),
            "changes": self._room_section(
                "changes", lambda: self._read_room_changes(project_id)),
            "review": (
                self._room_section(
                    "review", lambda: self._read_room_review(project_id))
                if self._review_available
                else dict(_ABSENT_SECTION)
            ),
            # HS-169-04: the four questions (additive)
            "needsYou": self._room_section(
                "needsYou", lambda: self._read_room_needs_you(project_id)),
            "sources": sources_section,
            "health": self._room_section(
                "health", lambda: self._read_room_health(project_id, target_at, week)),
            # Betterment P3: the Now wing (the head's second line, This week).
            "now": self._room_section(
                "now", lambda: self._read_room_now(project_id, target_at, week, decisions_section)),
            "sinceRead": self._room_section(
                "sinceRead", lambda: self._read_room_since_read(project_id, room_read_at)),
            "decisions": decisions_section,
            "commitments": self._room_section(
                "commitments", lambda: self._read_room_commitments(project_id)),
            "target": self._room_section(
                "target", lambda: self._read_room_target(target_at)),
            # PHILO-9-01 (F6): the updates and the steward read what exists.
            "updates": self._room_section(
                "updates", lambda: self._read_room_updates(principal, project_id)),
            "steward": self._room_section(
                "steward", lambda: self._read_room_steward(project_id)),
            # HS-174-04: pipeline receipts scoped to this project.
            "receipts": self._room_section(
                "receipts", lambda: self._read_room_receipts(project_id)),
            # Programs (2026-10-28, §9b): the Room's Programs fold, worst first.
            "programs": self._room_section(
                "programs", lambda: self._read_room_programs(project_id)),
        }

    # ── room sub-readers (fault-isolated) ────────────────────────────

    def _read_room_programs(self, project_id: str) -> dict[str, Any]:
        from .program_service import ProgramService

        return {"programs": ProgramService(self._db).for_project(project_id)}

    @staticmethod
    def _room_section(name: str, fn: Any) -> dict[str, Any]:
        """Run *fn* and tag the result with state=ok, or return degraded."""
        try:
            result = fn()
            result["state"] = "ok"
            return result
        except Exception as exc:
            _log.warning("room section %s degraded: %s", name, exc)
            return {"state": "degraded", "error_code": f"{name}_read_failed"}

    def _read_room_items(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_items(self._db, project_id)

    def _read_room_meetings(
        self, principal: Principal, project_id: str, project: Any,
    ) -> dict[str, Any]:
        """Meetings summary: count + latest."""
        count = project.meeting_count
        latest_list = self.list_meetings(principal, project_id, limit=1)
        return {
            "count": count,
            "latest": latest_list[0] if latest_list else None,
        }

    def _read_room_resources(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_resources(self._db, project_id)

    def _read_room_changes(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_changes(self._db, project_id)

    _ROOM_UPDATES_CAP = _ROOM_UPDATES_CAP  # project_definitions

    def _read_room_updates(self, principal: Principal, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_updates(self._db, principal, project_id)

    def _read_room_steward(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_steward(self._db, project_id)

    def _read_room_review(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_review(self._db, project_id, review_available=self._review_available)

    # ── HS-169-04 room sub-readers (the four questions) ──────────────

    # The snapshot reader and the needs-you words live in project_definitions.
    _entities = staticmethod(snapshot_entities)
    _SEVERITY_ORDER = _SEVERITY_ORDER
    _CHANGE_KIND_PHRASES = _CHANGE_KIND_PHRASES
    _PLAIN_REASON_PATTERNS = _PLAIN_REASON_PATTERNS
    PLAIN_REASONS = PLAIN_REASONS
    _plain_reason = staticmethod(plain_reason)

    _fold_watch_duplicates = staticmethod(room_reads._fold_watch_duplicates)

    def _read_room_needs_you(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_needs_you(
            self._db, project_id, review_available=self._review_available,
            proposal_needs=self.proposal_needs, resolve_review_people=self._resolve_review_people)

    def _room_matching_meeting_items(self, project_id: str) -> list[dict[str, Any]]:
        return room_reads._room_matching_meeting_items(self._db, project_id)

    def _overdue_milestones(self, project_id: str, now: datetime) -> list[tuple[dict[str, Any], int]]:
        return room_reads._overdue_milestones(self._db, project_id, now)

    def _room_overdue_milestone_items(self, project_id: str, now: datetime) -> list[dict[str, Any]]:
        return room_reads._room_overdue_milestone_items(self._db, project_id, now)

    _COMMITMENT_SETTLED = _COMMITMENT_SETTLED  # project_definitions

    def _room_commitment_items(self, project_id: str, now: datetime) -> list[dict[str, Any]]:
        return room_reads._room_commitment_items(self._db, project_id, now)

    def _room_meeting_action_items(self, project_id: str, now: datetime) -> list[dict[str, Any]]:
        return room_reads._room_meeting_action_items(self._db, project_id, now)

    _nudge_target = staticmethod(room_reads._nudge_target)

    def _room_nudge_destination(self, project_id: str, action_id: str, source_ref: str) -> dict[str, Any] | None:
        return room_reads._room_nudge_destination(self._db, project_id, action_id, source_ref)

    def _get_github_owner_login(self) -> str | None:
        return room_reads._get_github_owner_login(self._db)

    # The merge words live in project_definitions.
    _STATE_SEVERITY = _STATE_SEVERITY
    _TOKEN_ORDER_PREFIXES = _TOKEN_ORDER_PREFIXES
    _token_sort_key = staticmethod(token_sort_key)

    def _meeting_calendar_tokens(
        self, project_id: str, *, now: datetime | None = None,
    ) -> list[str]:
        return room_reads._meeting_calendar_tokens(self._db, project_id, now=now)

    def _read_room_sources(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_sources(self._db, project_id)

    def _annotate_source_freshness(self, sources: list[dict[str, Any]]) -> str | None:
        return room_reads._annotate_source_freshness(self._db, sources)

    def _read_room_health(
        self, project_id: str, target_at: str | None, week: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return room_reads._read_room_health(
            self._db, project_id, target_at, week, resolve_review_people=self._resolve_review_people)

    _WEEK_DAYS = _WEEK_DAYS  # project_definitions

    def _room_week(self, principal: Principal, project_id: str) -> dict[str, Any]:
        return room_reads._room_week(self._db, principal, project_id)

    def _read_room_now(
        self,
        project_id: str,
        target_at: str | None,
        week: dict[str, Any] | None,
        decisions_section: dict[str, Any],
    ) -> dict[str, Any]:
        return room_reads._read_room_now(self._db, project_id, target_at, week, decisions_section)

    def _load_ci_history(self, project_id: str) -> list[dict[str, Any]] | None:
        return room_reads._load_ci_history(self._db, project_id)

    def _count_overdue_commitments(self, project_id: str) -> int:
        return room_reads._count_overdue_commitments(self._db, project_id)

    def _resolve_review_people(
        self,
        project_id: str,
        per_reviewer: list[dict[str, Any]],
        threshold_days: float = 2.0,
    ) -> list[dict[str, Any]]:
        """Resolve reviewer logins to People relationships for bottleneck rows.

        Only RESOLVED reviewers whose median exceeds the threshold appear.
        Unresolved reviewers are counted in overall median but get no row
        (no raw login on the face).
        """
        people_svc = getattr(self, "_people_service", None)
        if people_svc is None:
            # Try to construct from the DB if available
            try:
                from holdspeak.services.people_service import PeopleService
                people_svc = PeopleService(self._db)
            except Exception:
                return []

        result: list[dict[str, Any]] = []
        for reviewer in per_reviewer:
            login = reviewer.get("login", "")
            median_days = reviewer.get("median_days", 0.0)
            count = reviewer.get("count", 0)
            if median_days < threshold_days:
                continue
            try:
                resolved = people_svc.resolve_relationship_by_watch_identity(login)
                if not resolved or resolved.get("state") != "ready":
                    continue
                relationship = resolved.get("relationship")
                if not relationship:
                    continue
                rel_id = relationship.get("id")
                display_name = relationship.get("display_name") or ""
                if not rel_id or not display_name:
                    continue
                result.append({
                    "relationship_id": rel_id,
                    "display_name": display_name,
                    "login": login,
                    "median_days": median_days,
                    "count": count,
                })
            except Exception:
                logging.getLogger(__name__).debug("review people: resolver skipped one reviewer", exc_info=True)
                continue
        return result

    def _enrich_people_with_nudge_state(
        self,
        project_id: str,
        people: list[dict[str, Any]],
        pr_entities: list[dict[str, Any]],
    ) -> None:
        return room_reads._enrich_people_with_nudge_state(self._db, project_id, people, pr_entities)

    def _read_room_since_read(self, project_id: str, room_read_at: str | None) -> dict[str, Any]:
        return room_reads._read_room_since_read(self._db, project_id, room_read_at)

    def _read_room_decisions(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_decisions(self._db, project_id)

    def _read_room_commitments(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_commitments(self._db, project_id)

    _read_room_target = staticmethod(room_reads._read_room_target)

    def _read_room_receipts(self, project_id: str) -> dict[str, Any]:
        return room_reads._read_room_receipts(self._db, project_id)

    # ── read marker (HS-169-04) ─────────────────────────────────────

    def mark_room_read(self, principal: Principal, project_id: str) -> dict[str, Any]:
        """Set the per-project read marker to now."""
        self._require_project(project_id)
        now_iso = utc_now_iso()
        self._db.projects.set_room_read_at(project_id, now_iso)
        return {"readAt": now_iso}

    # ── HS-200-41: the saved ask (return to unfinished work) ─────────
    #
    # A Room ask survives nothing today: its words live in browser state, the
    # kernel journals a payload hash, and `ask_results` keeps the answer
    # without the question.  These five methods make the QUESTION durable and
    # make a late answer claimable instead of re-runnable.
    #
    # Ownership (ruling B2): ProjectService already owns Room state, so a saved
    # Room ask is Room state.  AskService keeps its one property — it persists
    # nothing, which is what keeps it replayable — and gains no durable rows;
    # the dispatch it performs is injected here as a callable so this boundary
    # stays transport-neutral and so a test can prove that NOTHING dispatched.

    def save_ask(
        self,
        principal: Principal,
        project_id: str,
        payload: dict[str, Any],
        *,
        host_id: str = "",
        lease_epoch: int = 0,
    ) -> dict[str, Any]:
        """Persist an unfinished Room ask and mint its invocation identity.

        The row is written BEFORE anything is dispatched (ruling B3), so the
        answer that lands while the tab is gone has a key back to it.
        """
        self._require_project(project_id)
        purpose = str(payload.get("purpose") or "").strip()
        if not purpose:
            raise ValidationError("ask purpose is required", code="ask_task_purpose_required")
        state = str(payload.get("state") or "saved")
        if state not in {"saved", "failed", "incomplete"}:
            raise ValidationError(
                "an ask can only be saved in a state it can reach",
                code="ask_task_state_invalid",
            )
        grounding = payload.get("grounding")
        if grounding is not None and not isinstance(grounding, dict):
            raise ValidationError("grounding must be an object", code="ask_task_grounding_invalid")
        # The target's own words, quoted; never a sentence composed here (B5).
        stopped_reason = str(payload.get("stopped_reason") or payload.get("stoppedReason") or "")
        stopped_code = str(payload.get("stopped_code") or payload.get("stoppedCode") or "")
        invocation_id = "ask_" + uuid.uuid4().hex
        task = self._db.project_ask_tasks.create(
            task_id="asktask_" + uuid.uuid4().hex,
            project_id=project_id,
            invocation_id=invocation_id,
            purpose=purpose,
            lens=str(payload.get("lens") or "Project"),
            recipe_key=str(payload.get("recipe_key") or payload.get("recipeKey") or ""),
            grounding=grounding,
            state=state,
            stopped_reason=stopped_reason,
            stopped_code=stopped_code,
            # HS-200-41 F1: custody is stamped with a STABLE MACHINE identity,
            # never the process lease.  `RefinementCoordinator.host_id` is
            # `refhost_<uuid4>` minted per process
            # (`refinement_coordinator.py:45`), so custody stamped with it
            # flipped to `elsewhere` on every restart — the exact event this
            # story exists for.  HS-200-02's `database_identity` is derived
            # from the resolved path plus device+inode, so it survives a
            # restart and honestly differs on another machine.  The lease id
            # still rides `dispatch_host_id`, where it belongs.
            custody_host_id=_custody_identity(),
            custody_lease_epoch=int(lease_epoch or 0),
        )
        return {"task": self._ask_task_dto(task, host_id=host_id)}

    def list_unfinished_asks(
        self,
        principal: Principal,
        *,
        limit: int = 20,
        cursor: str | None = None,
        project_id: str | None = None,
        host_id: str = "",
    ) -> dict[str, Any]:
        """The deliberately small, keyset-paged Resume projection.

        Mirrors ``RefinementThoughtService.list_unfinished``: a signed
        high-water cursor over ``(resume_order DESC, id DESC)``, bounded limit.
        ``discarded`` never appears (ruling B6), and neither does ``accepted``.
        """
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1 or limit > 50:
            raise ValidationError(
                "limit must be between 1 and 50", code="ask_task_list_limit_invalid",
            )
        token = self._decode_ask_cursor(cursor) if cursor else None
        repo = self._db.project_ask_tasks
        high = int(token["high"]) if token else repo.high_water(project_id=project_id)
        after = (int(token["last_resume_order"]), str(token["last_id"])) if token else None
        page, more = repo.page_unfinished(
            limit=limit, high=high, after=after, project_id=project_id,
        )
        next_cursor = None
        if more and page:
            last = page[-1]
            next_cursor = self._encode_ask_cursor({
                "v": 1, "state": "unfinished", "high": high,
                "last_resume_order": last.resume_order, "last_id": last.id,
            })
        return {
            "items": [self._ask_task_dto(task, host_id=host_id) for task in page],
            "next_cursor": next_cursor,
        }

    async def resume_ask(
        self,
        principal: Principal,
        task_id: str,
        *,
        dispatcher: Any = None,
        host_id: str = "",
        lease_epoch: int = 0,
    ) -> dict[str, Any]:
        """Return to one unfinished ask — claiming a late answer, never re-running it.

        The order is the whole law (ruling B3):

        1. Read ``ask_results`` for this invocation identity FIRST.  If the
           answer arrived while the owner was away, settle the task
           ``accepted``, hand back the answer, and dispatch NOTHING.  A second
           Resume takes this same branch, so a double Resume cannot double-spend.
        2. Only with no result does a resume dispatch, under the SAME
           ``invocation_id``, so the kernel's ``operation_id`` UNIQUE refuses a
           duplicate operation rather than a new guard inventing one.
        """
        task = self._require_ask_task(task_id)
        if task.state == "discarded":
            raise ConflictError(
                "this ask was discarded", code="ask_task_discarded",
                context={"task_id": task.id},
            )
        repo = self._db.project_ask_tasks

        claimed = repo.find_ask_result(task.invocation_id)
        if claimed is not None:
            settled = repo.settle(task.id, state="accepted") or task
            return {
                "task": self._ask_task_dto(settled, host_id=host_id),
                "answer": claimed,
                "claimed": True,
                "dispatched": False,
            }

        if dispatcher is None:
            # No transport was supplied: hand back the saved material so the
            # caller can run it under this identity. Nothing was dispatched.
            return {
                "task": self._ask_task_dto(task, host_id=host_id),
                "answer": None,
                "claimed": False,
                "dispatched": False,
            }

        if not repo.claim_dispatch(task.id, str(host_id or ""), int(lease_epoch or 0)):
            raise ConflictError(
                "this ask is already being resumed", code="ask_task_resume_in_flight",
                context={"task_id": task.id, "reason": "still_running"},
            )
        # Betterment Q1: one identity is one kernel operation.  A run that
        # ended without an answer cannot run again under its identity (the
        # kernel replays its failure), so the retry gets its own.
        # A run still going is never doubled.
        run_state = repo.invocation_run_state(task.invocation_id)
        if run_state == "running":
            repo.release_dispatch(task.id)
            raise ConflictError(
                "this ask is still running", code="ask_task_still_running",
                context={"task_id": task.id, "reason": "still_running"},
            )
        if run_state == "ended":
            task = repo.rotate_invocation(task.id, "ask_" + uuid.uuid4().hex) or task
        try:
            answer = await dispatcher(self._ask_task_dto(task, host_id=host_id))
        except ServiceError as exc:
            # The target's own words, stored verbatim (ruling B5).  The code
            # is the face reason token when the refusal names one, so the
            # row says why in words (Betterment Q1).
            reason = exc.context.get("reason") if isinstance(exc.context, dict) else None
            repo.settle(
                task.id, state="failed", stopped_reason=str(exc.detail),
                stopped_code=str(reason) if isinstance(reason, str) and reason else str(exc.code),
            )
            raise
        except Exception:
            repo.release_dispatch(task.id)
            raise
        settled = repo.settle(task.id, state="accepted") or task
        return {
            "task": self._ask_task_dto(settled, host_id=host_id),
            "answer": answer,
            "claimed": False,
            "dispatched": True,
        }

    _ASK_STOP_CODE = _ASK_STOP_CODE  # project_definitions

    def record_ask_stop(
        self,
        principal: Principal,
        task_id: str,
        code: str,
        *,
        host_id: str = "",
    ) -> dict[str, Any]:
        """Record WHY a saved ask stopped, from a refusal CODE and nothing else.

        `save_ask` writes the row before dispatch (ruling B3), so a failure the
        BROWSER observed — the ordinary one, an engine that is not ready — had
        no way back into the record and the ratified `WAITING ON THE ENGINE`
        token could not be drawn.  This closes that, without letting a caller
        put words in the store.

        Ruling B5 is the whole design here.  The caller sends only the bounded
        refusal code it was already handed (`code` in the /api/ask refusal
        body, minted by ``inference_targets.target_refusal``); it may not send
        a reason.  The server resolves the code against ITS OWN live placement
        and stores the target's ``readiness_reason`` verbatim — the same words
        ``ask_service.py`` raises through ``target_unavailable``.  A code the
        server cannot currently corroborate stores the CODE and no reason;
        nothing the caller wrote is ever echoed back into the row.

        Narrow by construction: only ``saved`` -> ``failed``.  A row in any
        other state is refused, an already-``failed`` row is a no-op (so a
        retry is not an error), and the invocation identity is never touched —
        a failed ask is exactly the one the owner comes back to.
        """
        code = str(code or "").strip()
        if not self._ASK_STOP_CODE.match(code):
            raise ValidationError(
                "a stop code is a token, not a sentence",
                code="ask_task_stop_code_invalid",
            )
        task = self._require_ask_task(task_id)
        if task.state == "failed":
            # Idempotent: a repeat changes nothing, and never overwrites the
            # reason already quoted onto the row.
            return {"task": self._ask_task_dto(task, host_id=host_id), "changed": False}
        if task.state != "saved":
            raise ConflictError(
                "only a saved ask can be recorded as stopped",
                code="ask_task_not_stoppable",
                context={"task_id": task.id, "state": task.state},
            )
        settled = self._db.project_ask_tasks.settle(
            task.id, state="failed",
            stopped_reason=self._resolve_stop_reason(code),
            stopped_code=code,
        ) or task
        return {"task": self._ask_task_dto(settled, host_id=host_id), "changed": True}

    def _resolve_stop_reason(self, code: str) -> str:
        """The target's OWN words for this code, or nothing at all.

        Read from the live placement this hub would use, never from the
        caller.  The reason is stored only when the destination still reports
        the state the code names — if the engine came back in the meantime the
        server has no words to quote, and quoting none is the honest answer.
        """
        try:
            from ..inference_targets import resolve_placement
            target = resolve_placement(self._db).target
        except Exception:  # a hub that cannot resolve a target has no words
            return ""
        if f"inference_target_{target.readiness_state}" != code:
            return ""
        return str(getattr(target, "readiness_reason", "") or "")

    def discard_ask(
        self, principal: Principal, task_id: str, *, host_id: str = "",
    ) -> dict[str, Any]:
        """Discard is a STATE, never a DELETE (ruling B6)."""
        task = self._require_ask_task(task_id)
        settled = self._db.project_ask_tasks.settle(task.id, state="discarded") or task
        return {"task": self._ask_task_dto(settled, host_id=host_id)}

    def recover_ask_tasks_on_startup(self) -> list[str]:
        """Settle asks whose dispatching process is gone. Dispatches nothing.

        Reconcile-from-proof only, the discipline of
        ``recover_refinements_on_startup``: a lease that a live
        ``refinement_hosts`` row still backs is not abandonment.
        """
        return self._db.project_ask_tasks.reconcile_orphans()

    # ── ask-task helpers ─────────────────────────────────────────────

    def _require_ask_task(self, task_id: str) -> Any:
        task = self._db.project_ask_tasks.get(task_id)
        if task is None:
            raise NotFound("ask task", task_id)
        return task

    @staticmethod
    def _ask_task_dto(task: Any, *, host_id: str = "") -> dict[str, Any]:
        """The wire shape. Empty facts are ABSENT, never drawn as nothing (A.8)."""
        dto: dict[str, Any] = {
            "id": task.id,
            "projectId": task.project_id,
            "invocationId": task.invocation_id,
            "purpose": task.purpose,
            "lens": task.lens,
            "state": task.state,
            "savedAt": task.saved_at,
            "updatedAt": task.updated_at,
            "resumeOrder": task.resume_order,
        }
        if task.recipe_key:
            dto["recipeKey"] = task.recipe_key
        if task.grounding:
            dto["grounding"] = task.grounding
        if task.stopped_reason:
            dto["stoppedReason"] = task.stopped_reason
        if task.stopped_code:
            dto["stoppedCode"] = task.stopped_code
        if task.settled_at:
            dto["settledAt"] = task.settled_at
        # Custody (ruling B7, corrected by F1): `here` on the machine that
        # holds the row, `elsewhere` otherwise.  THIS DEVICE stays the egress
        # word.  The identity itself NEVER leaves the hub: it is an opaque
        # minted token and the face has no business printing one (canon
        # `raw-ids`).  The wire carries the verdict, not the id.
        if task.custody_host_id:
            dto["custody"] = (
                "here" if task.custody_host_id == _custody_identity() else "elsewhere"
            )
        return dto

    def _ask_cursor_secret(self) -> bytes:
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT value FROM kernel_meta WHERE key='ask_task_cursor_secret'"
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT OR IGNORE INTO kernel_meta (key, value) "
                    "VALUES ('ask_task_cursor_secret', ?)",
                    (uuid.uuid4().hex + uuid.uuid4().hex,),
                )
                row = conn.execute(
                    "SELECT value FROM kernel_meta WHERE key='ask_task_cursor_secret'"
                ).fetchone()
        return str(row["value"]).encode()

    def _encode_ask_cursor(self, value: dict[str, Any]) -> str:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        sig = hmac.new(self._ask_cursor_secret(), raw, hashlib.sha256).hexdigest()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=") + "." + sig

    def _decode_ask_cursor(self, token: str) -> dict[str, Any]:
        try:
            body, sig = str(token).split(".", 1)
            raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
            if not hmac.compare_digest(
                hmac.new(self._ask_cursor_secret(), raw, hashlib.sha256).hexdigest(), sig
            ):
                raise ValueError("signature")
            value = json.loads(raw)
            if value.get("v") != 1 or value.get("state") != "unfinished":
                raise ValueError("shape")
            if any(value.get(key) is None for key in ("high", "last_resume_order", "last_id")):
                raise ValueError("shape")
            return value
        except Exception as exc:
            raise ValidationError(
                "ask cursor is invalid", code="ask_task_cursor_invalid",
            ) from exc

    # ── writes (graduated to revision law) ───────────────────────────

    @_serialized_command
    def create_project(
        self, principal: Principal, payload: dict[str, Any] | None = None,
        *, command_id: Optional[str] = None, **fields: Any,
    ) -> dict[str, Any]:
        # PHILO-9-01: ``project.create`` passes its declared fields by name;
        # the route's body dict and the named fields are one payload.
        payload = {**(payload or {}), **fields}
        name = str(payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Project name is required")
        threshold = self._threshold(payload.get("detection_threshold", 0.4))

        # Idempotency check (API-002)
        req_hash = _request_hash(payload)
        replay = self._check_idempotency(command_id, req_hash, "create_project")
        if replay is not None:
            return replay

        project_id = f"proj-{uuid.uuid4().hex[:12]}"
        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        new_revision = 1  # first revision for a new project

        with self._command_txn(command_id) as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, name, description, keywords_json, team_members_json,
                    context_json, detection_threshold, revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id, name,
                    str(payload.get("description") or ""),
                    json.dumps(self._strings(payload.get("keywords")), ensure_ascii=False),
                    json.dumps(self._strings(payload.get("team_members")), ensure_ascii=False),
                    json.dumps(payload.get("context") or {}, ensure_ascii=False),
                    threshold,
                    new_revision,
                    now_iso, now_iso,
                ),
            )

            # Change log (DOM-003)
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            project_ref = format_ref("project", project_id)
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.created",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, _request_hash({"name": name}),
                    json.dumps({"name": name}),
                    now_iso,
                ),
            )

            # Service event (API-004)
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.created",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "name": name},
                refs=[project_ref],
            )

            # Command ledger (API-002)
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.CREATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "create_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    @_serialized_command
    def create_from_setup(
        self, principal: Principal, setup_payload: dict[str, Any],
        *, command_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Atomic Project creation from a setup interview (ACT-004).

        ONE transaction:
        - Create the Project row (name, purpose, outcome_text, lifecycle)
        - Activate selected+passed proposals as WatchSpec@1 rows in
          connector_watches (state='active', baseline_state='established')
        - Create watch_rules for each activated watch
        - Create project_sources bindings (semantic_role from proposal)
        - Record change + event + command

        All-or-nothing: any failure rolls back to zero Project/Watch rows.
        Baseline established WITHOUT events (ACT-005: ledger silence).
        Blank path: zero proposals is lawful (INT-002).
        """
        name = str(setup_payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Project name is required")

        req_hash = _request_hash(setup_payload)
        replay = self._check_idempotency(command_id, req_hash, "create_from_setup")
        if replay is not None:
            return replay

        project_id = f"proj-{uuid.uuid4().hex[:12]}"
        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        new_revision = 1
        proposals = setup_payload.get("proposals") or []

        with self._command_txn(command_id) as conn:
            # 1. Create the Project row
            conn.execute(
                """
                INSERT INTO projects (
                    id, name, description, keywords_json, team_members_json,
                    context_json, detection_threshold, revision,
                    purpose, outcome_text, lifecycle,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id, name,
                    str(setup_payload.get("description") or ""),
                    json.dumps([], ensure_ascii=False),
                    json.dumps([], ensure_ascii=False),
                    json.dumps({}, ensure_ascii=False),
                    0.4,  # default threshold
                    new_revision,
                    str(setup_payload.get("purpose") or ""),
                    str(setup_payload.get("outcome_text") or ""),
                    str(setup_payload.get("lifecycle") or "active"),
                    now_iso, now_iso,
                ),
            )

            # 2. Activate selected+passed proposals as Watch rows
            # (``_arm_source_watch_in_txn``: the watch, its rules, the binding).
            activated_watches: list[dict[str, Any]] = []
            for proposal in proposals:
                spec = proposal.get("spec") or {}
                if isinstance(spec, str):
                    spec = json.loads(spec)
                activated_watches.append(self._arm_source_watch_in_txn(conn, project_id, spec, now_iso))

            # 5. Change log (DOM-003)
            project_ref = format_ref("project", project_id)
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.created",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, _request_hash({"name": name}),
                    json.dumps({
                        "name": name,
                        "source": "setup",
                        "watches_activated": len(activated_watches),
                    }),
                    now_iso,
                ),
            )

            # 6. Service event (API-004)
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.created",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "name": name,
                    "source": "setup",
                    "watches_activated": len(activated_watches),
                },
                refs=[project_ref],
            )

            # 7. Command ledger (API-002)
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.CREATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "create_from_setup",
                req_hash, envelope,
            )

            # S-1: mark the setup session completed inside the same
            # transaction so a crash cannot leave a dangling active
            # session whose re-finalize would create a duplicate.
            if session_id:
                self._db.automations.complete_session_in_transaction(
                    conn, session_id=session_id, project_id=project_id,
                )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        result["activated_watches"] = activated_watches
        return result

    @_serialized_command
    def _arm_source_watch_in_txn(self, conn: Any, project_id: str, spec: dict[str, Any],
                                 now_iso: str, *, test_state: str = "passed",
                                 baseline_state: str = "established") -> dict[str, Any]:
        """One armed watch and its Room source binding, on THIS connection (ACT-004).

        Carved from ``create_from_setup`` (PHILO-9-02) so a suggested source
        arms its watch through the same rows: the watch, its rules and the
        ``project_sources`` binding.
        """
        from .watch_service import compute_arm_time as _compute_arm_time

        watch_id = f"watch_{uuid.uuid4().hex[:12]}"
        watch_name = spec.get("name", "Untitled watch")
        connector_id, query_kind, query_json = _source_watch_identity(spec)
        trigger = spec.get("trigger") or CADENCE_PRESETS.get("normal", {})
        mode = spec.get("mode", "yolo")

        # Insert via sanctioned repo helper (M-1: no third door)
        stored_test_state = str(spec.get("test_state") or test_state or "not_checked")
        self._db.automations.create_watch_in_transaction(
            conn,
            watch_id=watch_id,
            connector_id=connector_id,
            query_kind=query_kind,
            name=watch_name,
            query_json=query_json,
            enabled=True,
            schema_version="WatchSpec@1",
            project_id=project_id,
            intent=spec.get("intent", ""),
            subject_kind=query_kind,
            trigger_kind=trigger.get("kind", "poll"),
            trigger_json=json.dumps(trigger, sort_keys=True, separators=(",", ":")),
            mode=mode,
            state="active",
            revision=1,
            baseline_state=baseline_state,  # ACT-005: baseline without events
            test_state=stored_test_state,  # carried from the Door's real source check
            created_at=now_iso,
            updated_at=now_iso,
            # HS-200-43: ARM the row in the same transaction that
            # creates it, due now. Without this the watch is
            # unschedulable forever -- `list_due_watches` refuses a
            # NULL. `baseline_state='established'` above is written
            # before any snapshot exists, so it is not evidence of a
            # baseline; if the caller's `baseline_watch` raises, the
            # first scheduled run establishes the baseline silently
            # (F1) rather than discovering the whole source.
            next_evaluation_at=_compute_arm_time(),
        )

        # 3. Create watch_rules via sanctioned repo helper
        rules = spec.get("rules", [])
        for ordinal, rule in enumerate(rules):
            rule_id = f"wrule_{uuid.uuid4().hex[:12]}"
            self._db.automations.create_rule_in_transaction(
                conn,
                rule_id=rule_id,
                watch_id=watch_id,
                ordinal=ordinal,
                condition_schema="WatchCondition@1",
                condition_json=json.dumps(
                    rule.get("condition", {}),
                    sort_keys=True, separators=(",", ":"),
                ),
                action_schema="WatchAction@1",
                action_json=json.dumps(
                    rule.get("actions", []),
                    sort_keys=True, separators=(",", ":"),
                ),
                enabled=True,
                revision=0,
                created_at=now_iso,
                updated_at=now_iso,
            )

        # 4. Create project_sources binding
        source_id = generate_psrc_id()
        semantic_role = spec.get("subject", {}).get("kind", "general")
        conn.execute(
            """
            INSERT INTO project_sources (
                id, project_id, source_ref, label, semantic_role,
                enabled, revision, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id, project_id,
                format_ref("watch", watch_id),
                watch_name,
                semantic_role,
                1, 0, now_iso, now_iso,
            ),
        )

        return {"watch_id": watch_id, "name": watch_name, "source_id": source_id}

    @_serialized_command
    def add_source_watch(
        self, principal: Principal, project_id: str, *, suggestion_id: str,
        resource_ref: str, spec: dict[str, Any], command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """A suggested source becomes a watched source: ONE transaction (PHILO-9-02; F17).

        The Room files the source (a ``project_resources`` row, relationship
        ``source``), arms its watch (the watch, its rules and its
        ``project_sources`` binding, the rows ``create_from_setup`` writes),
        and the suggestion turns ``accepted`` -- all together or none: a
        suggestion is never ``accepted`` with nothing added. A suggestion that
        is no longer pending refuses ``suggestion_not_pending``.
        """
        self._require_project(project_id)
        ref_str = str(resource_ref).strip()
        req_hash = _request_hash({"project_id": project_id, "suggestion_id": suggestion_id,
                                  "resource_ref": ref_str, "action": "add_source_watch"})
        replay = self._check_idempotency(command_id, req_hash, "add_source_watch")
        if replay is not None:
            return replay
        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)
        with self._command_txn(command_id) as conn:
            accepted = conn.execute(
                "UPDATE source_suggestions SET status='accepted' WHERE id=? AND project_id=? AND status='pending'",
                (suggestion_id, project_id),
            ).rowcount
            if accepted != 1:
                raise ConflictError("The suggestion is not pending", code="suggestion_not_pending",
                                    context={"status": 409})
            new_revision = self._get_revision(conn, project_id) + 1
            conn.execute("UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                         (new_revision, now_iso, project_id))
            prior = conn.execute(
                "SELECT created_at FROM project_resources WHERE project_id=? AND resource_ref=?",
                (project_id, ref_str),
            ).fetchone()
            conn.execute(
                """INSERT INTO project_resources
                   (project_id, resource_ref, relationship, source, confidence,
                    created_at, last_modified, deleted)
                   VALUES (?, ?, 'source', 'suggested', 1.0, ?, ?, 0)
                   ON CONFLICT(project_id, resource_ref) DO UPDATE SET
                     relationship='source', source='suggested', last_modified=excluded.last_modified, deleted=0""",
                (project_id, ref_str, prior[0] if prior else now_iso, now_iso),
            )
            # Codex Astra r1 finding 6: nothing tested or baselined this
            # source; the watch says so ("" = untested, "pending" = the first
            # scheduled read takes the baseline), never "passed"/"established".
            watch = self._arm_source_watch_in_txn(conn, project_id, spec, now_iso,
                                                  test_state="", baseline_state="pending")
            conn.execute(
                """INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind, target_ref, actor_ref,
                    command_id, before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (generate_pchg_id(project_id=project_id, project_revision=new_revision, ordinal=0),
                 project_id, new_revision, "project.resource.linked", ref_str,
                 f"principal:{principal.identity}", cmd_id, None, None,
                 json.dumps({"resource_ref": ref_str, "watch_id": watch["watch_id"],
                             "suggestion_id": suggestion_id}), now_iso),
            )
            self._ledger.append_in_transaction(
                conn, principal, event_type="project.resource.linked", producer="ProjectService",
                subject_ref=project_ref, source_revision=str(new_revision),
                facts={"project_id": project_id, "resource_ref": ref_str, "watch_id": watch["watch_id"]},
                refs=[project_ref, ref_str],
            )
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.LINKED, project_id=project_id, project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            filed = conn.execute(
                "SELECT * FROM project_resources WHERE project_id=? AND resource_ref=?", (project_id, ref_str),
            ).fetchone()
            suggestion = dict(conn.execute("SELECT * FROM source_suggestions WHERE id=?", (suggestion_id,)).fetchone())
            result = {
                "suggestion": suggestion,
                "resource": {**self._db.project_relationships._row(filed).to_dict(), **_envelope_to_dict(envelope)},
                "watch": watch,
            }
            self._record_command(conn, cmd_id, project_id, "add_source_watch", req_hash, envelope, result=result)
        return result

    @_serialized_command
    def add_source_watches(
        self, principal: Principal, project_id: str, specs: list[dict[str, Any]],
        *, command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """PHILO-17 U10: sources added to a project that exists (the Room's Add source).

        The same rows ``create_from_setup`` writes for each source (the watch,
        its rules, the ``project_sources`` binding), in ONE transaction with
        the revision, one ``watch.created`` change per watch and its event.
        """
        self._require_project(project_id)
        if not specs:
            raise ValidationError("At least one source is required")
        req_hash = _request_hash({"project_id": project_id, "specs": specs, "action": "add_source_watches"})
        replay = self._check_idempotency(command_id, req_hash, "add_source_watches")
        if replay is not None:
            return replay
        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)
        with self._command_txn(command_id) as conn:
            # Astra r1 on #1068: a source the project already watches is never
            # armed twice (hidden duplicate polling); all of them: refused.
            watched = {
                (str(r[0]), str(r[1]), str(r[2])) for r in conn.execute(
                    "SELECT connector_id, query_kind, query_json FROM connector_watches"
                    " WHERE project_id=? AND state != 'retired'", (project_id,)).fetchall()
            }
            fresh: list[dict[str, Any]] = []
            for spec in specs:
                identity = _source_watch_identity(spec)
                if identity not in watched:
                    watched.add(identity)
                    fresh.append(spec)
            if not fresh:
                raise ConflictError("Already watched", code="already_watched", context={"status": 409})
            new_revision = self._get_revision(conn, project_id) + 1
            conn.execute("UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                         (new_revision, now_iso, project_id))
            activated: list[dict[str, Any]] = []
            for ordinal, spec in enumerate(fresh):
                watch = self._arm_source_watch_in_txn(conn, project_id, spec, now_iso)
                activated.append(watch)
                watch_ref = format_ref("watch", watch["watch_id"])
                conn.execute(
                    """INSERT INTO project_changes (
                        id, project_id, project_revision, change_kind, target_ref, actor_ref,
                        command_id, before_hash, after_hash, summary_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (generate_pchg_id(project_id=project_id, project_revision=new_revision, ordinal=ordinal),
                     project_id, new_revision, "watch.created", watch_ref,
                     f"principal:{principal.identity}", cmd_id, None, None,
                     json.dumps({"watch_id": watch["watch_id"], "name": watch["name"]}), now_iso),
                )
                self._ledger.append_in_transaction(
                    conn, principal, event_type="watch.created", producer="ProjectService",
                    subject_ref=project_ref, source_revision=str(new_revision),
                    facts={"project_id": project_id, "watch_id": watch["watch_id"]},
                    refs=[project_ref, watch_ref],
                )
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED, project_id=project_id, project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            result = {"project_id": project_id, "activated_watches": activated, **_envelope_to_dict(envelope)}
            self._record_command(conn, cmd_id, project_id, "add_source_watches", req_hash, envelope, result=result)
        return result

    def update_project(
        self, principal: Principal, project_id: str, patch: dict[str, Any],
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        self._require_project(project_id)

        # Idempotency check
        req_hash = _request_hash({"project_id": project_id, **patch})
        replay = self._check_idempotency(command_id, req_hash, "update_project")
        if replay is not None:
            return replay

        fields: dict[str, Any] = {}
        if "name" in patch:
            name = str(patch["name"] or "").strip()
            if not name:
                raise ValidationError("Project name cannot be empty")
            fields["name"] = name
        if "description" in patch:
            fields["description"] = str(patch["description"] or "")
        if "keywords" in patch:
            fields["keywords"] = self._strings(patch["keywords"])
        if "team_members" in patch:
            fields["team_members"] = self._strings(patch["team_members"])
        if "context" in patch:
            fields["context"] = patch["context"] or {}
        if "detection_threshold" in patch:
            fields["detection_threshold"] = self._threshold(patch["detection_threshold"])

        # ── Room fields (HS-158-02, SRS §5.1) ────────────────────────
        if "purpose" in patch:
            fields["purpose"] = str(patch["purpose"]).strip() if patch["purpose"] else None
        if "outcome_text" in patch:
            fields["outcome_text"] = str(patch["outcome_text"]).strip() if patch["outcome_text"] else None
        if "owner_ref" in patch:
            owner_ref_val = patch["owner_ref"]
            if owner_ref_val is not None:
                owner_ref_str = str(owner_ref_val).strip()
                if not owner_ref_str:
                    owner_ref_val = None
                else:
                    try:
                        parse_ref(owner_ref_str)
                    except Exception as exc:
                        raise ValidationError(
                            f"owner_ref is not a valid qualified ref: {exc}",
                            code="invalid_owner_ref",
                        ) from exc
                    owner_ref_val = owner_ref_str
            fields["owner_ref"] = owner_ref_val
        if "lifecycle" in patch:
            lc = str(patch["lifecycle"] or "").strip().lower()
            if lc == "archived":
                raise ValidationError(
                    "lifecycle 'archived' cannot be set via update; use archive_project",
                    code="invalid_lifecycle",
                )
            if lc not in PROJECT_LIFECYCLES:
                raise ValidationError(
                    f"lifecycle must be one of {sorted(PROJECT_LIFECYCLES)}, got {lc!r}",
                    code="invalid_lifecycle",
                )
            fields["lifecycle"] = lc
        if "posture" in patch:
            posture_val = str(patch["posture"]).strip() if patch["posture"] else None
            if posture_val and len(posture_val) > _POSTURE_MAX:
                raise ValidationError(
                    f"posture exceeds {_POSTURE_MAX} characters",
                    code="posture_too_long",
                )
            fields["posture"] = posture_val
        if "posture_reason" in patch:
            reason_val = str(patch["posture_reason"]).strip() if patch["posture_reason"] else None
            if reason_val and len(reason_val) > _POSTURE_REASON_MAX:
                raise ValidationError(
                    f"posture_reason exceeds {_POSTURE_REASON_MAX} characters",
                    code="posture_reason_too_long",
                )
            fields["posture_reason"] = reason_val
        for date_key in ("start_at", "target_at", "next_review_at"):
            if date_key in patch:
                date_val = patch[date_key]
                if date_val is not None:
                    date_str = str(date_val).strip()
                    if not date_str:
                        date_val = None
                    else:
                        try:
                            datetime.fromisoformat(date_str)
                        except (ValueError, TypeError) as exc:
                            raise ValidationError(
                                f"{date_key} is not valid ISO-8601: {date_str!r}",
                                code=f"invalid_{date_key}",
                            ) from exc
                        date_val = date_str
                fields[date_key] = date_val
        if "review_cadence_json" in patch:
            cadence = patch["review_cadence_json"]
            if cadence is not None:
                if not isinstance(cadence, dict):
                    raise ValidationError(
                        "review_cadence_json must be a dict",
                        code="invalid_review_cadence",
                    )
                if "every_days" in cadence:
                    try:
                        every = int(cadence["every_days"])
                    except (TypeError, ValueError) as exc:
                        raise ValidationError(
                            "review_cadence_json.every_days must be a positive integer",
                            code="invalid_review_cadence",
                        ) from exc
                    if every < 1:
                        raise ValidationError(
                            "review_cadence_json.every_days must be a positive integer",
                            code="invalid_review_cadence",
                        )
            fields["review_cadence_json"] = cadence
        if "template_key" in patch:
            tk = str(patch["template_key"]).strip() if patch["template_key"] else None
            if tk and len(tk) > _SLUG_MAX:
                raise ValidationError(
                    f"template_key exceeds {_SLUG_MAX} characters",
                    code="template_key_too_long",
                )
            fields["template_key"] = tk
        if "modules_json" in patch:
            mods = patch["modules_json"]
            if mods is not None:
                if not isinstance(mods, list):
                    raise ValidationError(
                        "modules_json must be a list of short slugs",
                        code="invalid_modules",
                    )
                cleaned: list[str] = []
                for m in mods:
                    slug = str(m).strip()
                    if len(slug) > _SLUG_MAX:
                        raise ValidationError(
                            f"modules_json entry exceeds {_SLUG_MAX} characters",
                            code="invalid_modules",
                        )
                    cleaned.append(slug)
                mods = cleaned
            fields["modules_json"] = mods

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        with self._command_txn(command_id) as conn:
            # Revision check (API-001)
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1

            # Apply the legacy field updates
            updates: list[str] = []
            params: list[Any] = []
            for key, value in fields.items():
                if key == "name":
                    updates.append("name = ?")
                    params.append(value)
                elif key == "description":
                    updates.append("description = ?")
                    params.append(value)
                elif key == "keywords":
                    updates.append("keywords_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "team_members":
                    updates.append("team_members_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "context":
                    updates.append("context_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "detection_threshold":
                    updates.append("detection_threshold = ?")
                    params.append(max(0.0, min(1.0, float(value))))
                # ── Room columns (HS-158-02) ─────────────────────────
                elif key in ("purpose", "outcome_text", "owner_ref",
                             "lifecycle", "posture", "posture_reason",
                             "start_at", "target_at", "next_review_at",
                             "template_key"):
                    updates.append(f"{key} = ?")
                    params.append(value)
                elif key == "review_cadence_json":
                    updates.append("review_cadence_json = ?")
                    params.append(
                        json.dumps(value, ensure_ascii=False) if value is not None else None
                    )
                elif key == "modules_json":
                    updates.append("modules_json = ?")
                    params.append(
                        json.dumps(value, ensure_ascii=False) if value is not None else None
                    )

            updates.append("revision = ?")
            params.append(new_revision)
            updates.append("updated_at = ?")
            params.append(now_iso)
            params.append(project_id)
            if updates:
                conn.execute(
                    f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                    params,
                )

            # Change log
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, _request_hash(fields),
                    json.dumps({"fields": list(fields.keys())}),
                    now_iso,
                ),
            )

            # Event
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "fields": list(fields.keys())},
                refs=[project_ref],
            )

            # Command
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "update_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    @_serialized_command
    def archive_project(
        self, principal: Principal, project_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        self._require_project(project_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id, "action": "archive"})
        replay = self._check_idempotency(command_id, req_hash, "archive_project")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        with self._command_txn(command_id) as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET is_archived = 1, lifecycle = 'archived', "
                "revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.archived",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"lifecycle": "archived"}),
                    now_iso,
                ),
            )

            # HS-167 M-2: pause active/tested watches bound to this
            # project and disable unattended policy — in the SAME
            # transaction — so an archived project never evaluates.
            from holdspeak.db.automations import AutomationRepository as _WatchRepo
            _WatchRepo.pause_project_watches_in_txn(conn, project_id, now_iso)

            policy = self._db.steward_policies.get_policy_for_project_in_transaction(
                conn, project_id,
            )
            if policy and policy.get("unattended_enabled"):
                self._db.steward_policies.update_policy_in_transaction(
                    conn, policy["id"], unattended_enabled=0,
                )
            # PHILO-9-02 (the steward beat, section 4; Muad'Dib r1 C1): archive
            # WRITES the policy's terms (unattended off), so its admitted
            # operation becomes the policy's recorded owner operation, in this
            # same transaction: a snapshot never pairs these terms with an
            # older operation.
            from holdspeak.services import project_kernel as _project_kernel

            running = _project_kernel.current()
            if policy and running is not None and running.name == "project.archive" and not running.replay:
                conn.execute("UPDATE steward_policies SET configure_operation_id=? WHERE id=?",
                             (running.operation_id, policy["id"]))

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.archived",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id},
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.ARCHIVED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "archive_project",
                req_hash, envelope,
            )

        return True

    @_serialized_command
    def restore_project(
        self, principal: Principal, project_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Restore an archived Project (DOM-011).

        If the project is not archived, returns a no_change result
        (API-002's honest reply).

        Watches paused by archive_project are NOT auto-resumed here —
        the owner resumes deliberately after restoring.
        """
        project = self._require_project(project_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id, "action": "restore"})
        replay = self._check_idempotency(command_id, req_hash, "restore_project")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        if not project.is_archived:
            # Not archived -- no-op per API-002
            with self._command_txn(command_id) as conn:
                current_rev = self._get_revision(conn, project_id)
                envelope = CommandResultEnvelope(
                    result_kind=ResultKind.NO_CHANGE,
                    project_id=project_id,
                    project_revision=current_rev,
                )
                self._record_command(
                    conn, cmd_id, project_id, "restore_project",
                    req_hash, envelope,
                )
            result = self._project_payload(project)
            result.update(_envelope_to_dict(envelope))
            return result

        with self._command_txn(command_id) as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET is_archived = 0, lifecycle = 'active', "
                "revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.restored",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"lifecycle": "active"}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.restored",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id},
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.RESTORED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "restore_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    @_serialized_command
    def add_resource(
        self, principal: Principal, project_id: str,
        resource_ref: str, payload: dict[str, Any] | None = None,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
        relationship: Optional[str] = None,
    ) -> dict[str, Any]:
        self._require_project(project_id)
        body = dict(payload or {})
        if relationship is not None:
            body["relationship"] = relationship
        ref_str = self._project_resource_ref(resource_ref)
        self._validate_repository_binding(principal, ref_str)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "resource_ref": ref_str, **body})
        from .conductor_launch import launch_id_of, record_own, refuse

        launch = launch_id_of(principal)
        replay = self._check_idempotency(command_id, req_hash, "add_resource")
        if replay is not None and launch is not None:
            # A replay answers the ORIGINAL caller; it never answers (or
            # transfers ownership to) a launch (Astra round 1 on #903).
            refuse(ref_str, "a launch replays no other caller's command")
        if replay is not None:
            # PHILO-9-01 round three (Codex Astra r2, R1-2): the replay answers
            # the ORIGINAL response, recorded whole with the command -- never
            # one rebuilt from the row as it is now. A command recorded before
            # this change holds only its envelope: that one is answered as the
            # row plus the envelope, as round two did.
            if "resource_ref" in replay:
                return replay
            row = self._db.project_relationships.get(project_id, ref_str, include_deleted=True)
            return {**row.to_dict(), **replay} if row is not None else replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        # HS-173-08 / 158 S-1: single transaction for revision bump +
        # resource upsert + change row + event + command.
        relation = str(body.get("relationship") or "member").strip().lower()
        if relation not in {"member", "source", "output", "related"}:
            raise ValueError(f"unknown project relationship: {relation}")

        with self._command_txn(command_id) as conn:
            if launch is not None:
                # Conductor K6: only a NEW membership is the launch's. An
                # existing live one stays its owner's: refused, in the same
                # transaction that would write it (no race).
                live = conn.execute(
                    "SELECT 1 FROM project_resources WHERE project_id=? AND resource_ref=? AND deleted=0",
                    (project_id, ref_str),
                ).fetchone()
                if live is not None:
                    refuse(ref_str, f"{ref_str} is already in this Project; a launch adds only new resources")
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Inline the resource upsert (was repo layer's own transaction).
            prior = conn.execute(
                "SELECT created_at FROM project_resources "
                "WHERE project_id=? AND resource_ref=?",
                (project_id, ref_str),
            ).fetchone()
            conn.execute(
                """INSERT INTO project_resources
                   (project_id, resource_ref, relationship, source, confidence,
                    created_at, last_modified, deleted)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                   ON CONFLICT(project_id, resource_ref) DO UPDATE SET
                     relationship=excluded.relationship, source=excluded.source,
                     confidence=excluded.confidence, last_modified=excluded.last_modified,
                     deleted=excluded.deleted""",
                (project_id, ref_str, relation, "manual", 1.0,
                 prior[0] if prior else now_iso, now_iso),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.resource.linked",
                    ref_str,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"resource_ref": ref_str}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.resource.linked",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "resource_ref": ref_str},
                refs=[project_ref, ref_str],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.LINKED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            # The response, read in the same transaction, is recorded WITH the
            # command (the existing result_json column), so a replay answers
            # exactly it (Codex Astra r2, R1-2).
            filed = conn.execute(
                "SELECT * FROM project_resources WHERE project_id=? AND resource_ref=?",
                (project_id, ref_str),
            ).fetchone()
            result = self._db.project_relationships._row(filed).to_dict()
            result.update(_envelope_to_dict(envelope))
            self._record_command(
                conn, cmd_id, project_id, "add_resource",
                req_hash, envelope, result=result,
            )

        if launch is not None:
            record_own(principal, f"resource:{project_id}:{ref_str}")
        return result

    @_serialized_command
    def remove_resource(
        self, principal: Principal, project_id: str, resource_ref: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        self._require_project(project_id)
        ref_str = self._project_resource_ref(resource_ref)
        # Conductor K6: a launch removes only a membership it added (HTTP,
        # MCP and the kernel all reach this one method).
        from .conductor_launch import require_own

        require_own(principal, f"resource:{project_id}:{ref_str}")

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "resource_ref": ref_str, "action": "remove"})
        replay = self._check_idempotency(command_id, req_hash, "remove_resource")
        if replay is not None:
            # Codex Astra r2 (R1-2): the original answer, a no-op's false
            # included. A command recorded before this change has no
            # ``removed``: it answers True, as before.
            return bool(replay.get("removed", True))

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        # HS-173-08 / 158 S-1: single transaction for revision bump +
        # resource soft-delete + change row + event + command.
        with self._command_txn(command_id) as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Inline the resource soft-delete (was repo layer's own transaction).
            names = self._project_resource_ref_names(ref_str)
            cur = conn.execute(
                "UPDATE project_resources SET deleted=1, last_modified=? "
                f"WHERE project_id=? AND resource_ref IN ({','.join('?' * len(names))}) "
                "AND deleted=0",
                (now_iso, project_id, *names),
            )
            deleted = bool(cur.rowcount)

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.resource.unlinked",
                    ref_str,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"resource_ref": ref_str}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.resource.unlinked",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "resource_ref": ref_str},
                refs=[project_ref, ref_str],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UNLINKED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "remove_resource",
                req_hash, envelope,
                result={**_envelope_to_dict(envelope), "removed": deleted},
            )

        return deleted

    @_serialized_command
    def associate_meeting(
        self, principal: Principal, project_id: str, meeting_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        """Associate a meeting with a project.

        Meeting association event decision: SRS SS10 does NOT define a
        project.meeting.linked event kind.  We emit project.updated with
        the meeting ref in changed_refs/summary, since the association
        is a project mutation (it changes the project's meeting set) but
        is not a resource link (meetings have their own association table).
        """
        self._require_project(project_id)
        self._require_meeting(meeting_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "meeting_id": meeting_id,
                                  "action": "associate"})
        replay = self._check_idempotency(command_id, req_hash, "associate_meeting")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)
        meeting_ref = format_ref("meeting", meeting_id)

        # HS-173-08 / 158 S-1: single transaction for revision bump +
        # meeting association + change row + event + command.
        mid = str(meeting_id).strip()
        pid = str(project_id).strip()

        with self._command_txn(command_id) as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Inline meeting association (was repo layer's own transaction).
            conn.execute(
                """INSERT INTO meeting_projects
                   (meeting_id, project_id, source, confidence, detected_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(meeting_id, project_id) DO UPDATE SET
                     source = excluded.source,
                     confidence = MAX(meeting_projects.confidence, excluded.confidence),
                     detected_at = excluded.detected_at""",
                (mid, pid, "manual", 1.0, now_iso),
            )
            conn.execute(
                """INSERT INTO project_resources
                   (project_id, resource_ref, relationship, source, confidence,
                    created_at, last_modified, deleted)
                   VALUES (?, ?, 'member', ?, ?, ?, ?, 0)
                   ON CONFLICT(project_id, resource_ref) DO UPDATE SET
                     source=excluded.source,
                     confidence=MAX(project_resources.confidence, excluded.confidence),
                     last_modified=excluded.last_modified, deleted=0""",
                (pid, f"meeting:{mid}", "manual", 1.0, now_iso, now_iso),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    meeting_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"meeting_associated": meeting_id}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "meeting_associated": meeting_id,
                },
                refs=[project_ref, meeting_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(
                    parse_ref(project_ref),
                    parse_ref(meeting_ref),
                ),
            )
            self._record_command(
                conn, cmd_id, project_id, "associate_meeting",
                req_hash, envelope,
            )

        # HS-175-04: ensure the Room's meeting Watch exists after link
        try:
            from holdspeak.services.watch_service import ensure_meeting_watch
            ensure_meeting_watch(self._db, project_id, why="meeting linked")
        except Exception:
            _log.warning("ensure_meeting_watch failed for project %s", project_id)

        return True

    @_serialized_command
    def disassociate_meeting(
        self, principal: Principal, project_id: str, meeting_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        """Disassociate a meeting from a project.

        Same event decision as associate_meeting: project.updated.
        """
        self._require_project(project_id)
        self._require_meeting(meeting_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "meeting_id": meeting_id,
                                  "action": "disassociate"})
        replay = self._check_idempotency(command_id, req_hash, "disassociate_meeting")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)
        meeting_ref = format_ref("meeting", meeting_id)

        # HS-173-08 / 158 S-1: single transaction for revision bump +
        # meeting disassociation + change row + event + command.
        mid = str(meeting_id).strip()
        pid = str(project_id).strip()

        with self._command_txn(command_id) as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Inline meeting disassociation (was repo layer's own transaction).
            conn.execute(
                "DELETE FROM meeting_projects "
                "WHERE meeting_id = ? AND project_id = ?",
                (mid, pid),
            )
            conn.execute(
                "UPDATE project_resources SET deleted=1, last_modified=? "
                "WHERE project_id=? AND resource_ref=?",
                (now_iso, pid, f"meeting:{mid}"),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    meeting_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"meeting_disassociated": meeting_id}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "meeting_disassociated": meeting_id,
                },
                refs=[project_ref, meeting_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(
                    parse_ref(project_ref),
                    parse_ref(meeting_ref),
                ),
            )
            self._record_command(
                conn, cmd_id, project_id, "disassociate_meeting",
                req_hash, envelope,
            )

        return True

    # ── item commands (HS-158-03) ──────────────────────────────────────

    @_serialized_command
    def create_item(
        self, principal: Principal, project_id: str,
        payload: dict[str, Any] | None = None,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
        **fields: Any,
    ) -> dict[str, Any]:
        """Create a typed item under a project (SYS-030, DOM-001).

        Items are Project-OWNED records (SS5.3); they increment the
        project's revision (not citizens, not in CITIZEN_TYPES).
        PHILO-9-01: ``project.item.create`` passes its fields by name.
        """
        payload = {**(payload or {}), **fields}
        self._require_project(project_id)

        item_type = str(payload.get("item_type") or "").strip()
        if item_type not in ITEM_TYPES:
            raise ValidationError(
                f"Unknown item_type: {item_type!r}; "
                f"must be one of {sorted(ITEM_TYPES)}",
                code="validation",
            )

        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValidationError("Item title is required", code="validation")

        severity = self._validate_severity(payload.get("severity"))
        lifecycle = str(payload.get("lifecycle") or "").strip() or ITEM_DEFAULT_LIFECYCLE[item_type]
        self._validate_lifecycle(item_type, lifecycle)

        owner_ref = self._validate_optional_ref(payload.get("owner_ref"), "owner_ref")
        created_by_ref = self._validate_optional_ref(
            payload.get("created_by_ref") or f"principal:{principal.identity}",
            "created_by_ref",
        )
        due_at = payload.get("due_at")
        sort_key = payload.get("sort_key")
        if sort_key is not None:
            try:
                sort_key = float(sort_key)
            except (TypeError, ValueError) as exc:
                raise ValidationError("sort_key must be a number", code="validation") from exc
        summary = payload.get("summary")

        # Validate and serialize details_json (DB-004)
        details = payload.get("details") or {}
        details_json = self._validate_details(item_type, details)

        provenance = str(payload.get("provenance_kind") or "owner").strip()
        if provenance not in PROVENANCE_KINDS:
            raise ValidationError(
                f"provenance_kind must be one of {sorted(PROVENANCE_KINDS)}",
                code="validation",
            )

        # Idempotency check
        req_hash = _request_hash({
            "project_id": project_id, "item_type": item_type,
            "title": title, **{k: v for k, v in payload.items()
                                if k not in ("command_id",)},
        })
        replay = self._check_idempotency(command_id, req_hash, "create_item")
        if replay is not None:
            return replay

        item_id = generate_pitem_id()
        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        with self._command_txn(command_id) as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )
            new_revision = current_rev + 1

            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            conn.execute(
                """
                INSERT INTO project_items (
                    id, project_id, item_type, title, summary, lifecycle,
                    severity, owner_ref, due_at, sort_key, details_json,
                    provenance_kind, source_observation_id, created_by_ref,
                    revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    item_id, project_id, item_type, title, summary,
                    lifecycle, severity, owner_ref, due_at, sort_key,
                    details_json, provenance, payload.get("source_observation_id"),
                    created_by_ref, now_iso, now_iso,
                ),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None,
                    _request_hash({"item_id": item_id, "item_type": item_type}),
                    json.dumps({
                        "action": "item.created",
                        "item_id": item_id,
                        "item_type": item_type,
                        "title": title,
                    }),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "action": "item.created",
                    "item_id": item_id,
                    "item_type": item_type,
                },
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "create_item",
                req_hash, envelope,
            )

        item = self._db.projects.get_project_item(item_id)
        result = dict(item) if item else {"id": item_id}
        result.update(_envelope_to_dict(envelope))
        result["item_id"] = item_id
        return result

    def create_item_in_transaction(
        self, conn: Any, principal: Principal, project_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a typed item inside the caller's transaction (S-2 fix).

        Conn-accepting sibling of create_item, following the 159 M-1
        pattern (conn-threading).  The caller owns the connection and
        the transaction boundary; this method does validation (pure
        Python) then all DB writes on the provided conn.

        Preconditions (caller's job):
        - project_id exists (no _require_project read here)
        - idempotency is the caller's concern

        Returns the same result dict shape as create_item.
        """
        item_type = str(payload.get("item_type") or "").strip()
        if item_type not in ITEM_TYPES:
            raise ValidationError(
                f"Unknown item_type: {item_type!r}; "
                f"must be one of {sorted(ITEM_TYPES)}",
                code="validation",
            )

        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValidationError("Item title is required", code="validation")

        severity = self._validate_severity(payload.get("severity"))
        lifecycle = str(payload.get("lifecycle") or "").strip() or ITEM_DEFAULT_LIFECYCLE[item_type]
        self._validate_lifecycle(item_type, lifecycle)

        owner_ref = self._validate_optional_ref(payload.get("owner_ref"), "owner_ref")
        created_by_ref = self._validate_optional_ref(
            payload.get("created_by_ref") or f"principal:{principal.identity}",
            "created_by_ref",
        )
        due_at = payload.get("due_at")
        sort_key = payload.get("sort_key")
        if sort_key is not None:
            try:
                sort_key = float(sort_key)
            except (TypeError, ValueError) as exc:
                raise ValidationError("sort_key must be a number", code="validation") from exc
        summary = payload.get("summary")

        # Validate and serialize details_json (DB-004)
        details = payload.get("details") or {}
        details_json = self._validate_details(item_type, details)

        provenance = str(payload.get("provenance_kind") or "owner").strip()
        if provenance not in PROVENANCE_KINDS:
            raise ValidationError(
                f"provenance_kind must be one of {sorted(PROVENANCE_KINDS)}",
                code="validation",
            )

        item_id = generate_pitem_id()
        cmd_id = generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        current_rev = self._get_revision(conn, project_id)
        new_revision = current_rev + 1

        conn.execute(
            "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
            (new_revision, now_iso, project_id),
        )

        conn.execute(
            """
            INSERT INTO project_items (
                id, project_id, item_type, title, summary, lifecycle,
                severity, owner_ref, due_at, sort_key, details_json,
                provenance_kind, source_observation_id, created_by_ref,
                revision, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                item_id, project_id, item_type, title, summary,
                lifecycle, severity, owner_ref, due_at, sort_key,
                details_json, provenance, payload.get("source_observation_id"),
                created_by_ref, now_iso, now_iso,
            ),
        )

        change_id = generate_pchg_id(
            project_id=project_id,
            project_revision=new_revision,
            ordinal=0,
        )
        req_hash = _request_hash({
            "project_id": project_id, "item_type": item_type,
            "title": title, **{k: v for k, v in payload.items()
                                if k not in ("command_id",)},
        })
        conn.execute(
            """
            INSERT INTO project_changes (
                id, project_id, project_revision, change_kind,
                target_ref, actor_ref, command_id,
                before_hash, after_hash, summary_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                change_id, project_id, new_revision,
                "project.updated",
                project_ref,
                f"principal:{principal.identity}",
                cmd_id, None,
                _request_hash({"item_id": item_id, "item_type": item_type}),
                json.dumps({
                    "action": "item.created",
                    "item_id": item_id,
                    "item_type": item_type,
                    "title": title,
                }),
                now_iso,
            ),
        )

        self._ledger.append_in_transaction(
            conn, principal,
            event_type="project.updated",
            producer="ProjectService",
            subject_ref=project_ref,
            source_revision=str(new_revision),
            facts={
                "project_id": project_id,
                "action": "item.created",
                "item_id": item_id,
                "item_type": item_type,
            },
            refs=[project_ref],
        )

        envelope = CommandResultEnvelope(
            result_kind=ResultKind.UPDATED,
            project_id=project_id,
            project_revision=new_revision,
            changed_refs=(parse_ref(project_ref),),
        )
        self._record_command(
            conn, cmd_id, project_id, "create_item",
            req_hash, envelope,
        )

        result = _envelope_to_dict(envelope)
        result["item_id"] = item_id
        return result

    @_serialized_command
    def update_item(
        self, principal: Principal, project_id: str, item_id: str,
        patch: dict[str, Any],
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update mutable fields on an item (SYS-031, DOM-006)."""
        self._require_project(project_id)
        existing = self._db.projects.get_project_item(item_id)
        if existing is None or existing["project_id"] != project_id:
            raise NotFound("project_item", item_id)

        item_type = existing["item_type"]

        # Build validated fields
        fields: dict[str, Any] = {}
        if "title" in patch:
            title = str(patch["title"] or "").strip()
            if not title:
                raise ValidationError("Item title cannot be empty", code="validation")
            fields["title"] = title
        if "summary" in patch:
            fields["summary"] = patch["summary"]
        if "severity" in patch:
            fields["severity"] = self._validate_severity(patch["severity"])
        if "owner_ref" in patch:
            fields["owner_ref"] = self._validate_optional_ref(patch["owner_ref"], "owner_ref")
        if "due_at" in patch:
            fields["due_at"] = patch["due_at"]
        if "sort_key" in patch:
            sk = patch["sort_key"]
            if sk is not None:
                try:
                    sk = float(sk)
                except (TypeError, ValueError) as exc:
                    raise ValidationError("sort_key must be a number", code="validation") from exc
            fields["sort_key"] = sk
        if "details" in patch:
            fields["details_json"] = self._validate_details(item_type, patch["details"] or {})

        # Lifecycle via update is allowed but NOT for completing milestones (DOM-007)
        if "lifecycle" in patch:
            new_lc = str(patch["lifecycle"]).strip()
            self._validate_lifecycle(item_type, new_lc)
            if item_type == "milestone" and new_lc == "reached":
                raise ValidationError(
                    "Milestones cannot be completed through a field update; "
                    "use the transition verb (DOM-007)",
                    code="validation",
                )
            fields["lifecycle"] = new_lc

        if not fields:
            raise ValidationError("No updatable fields supplied", code="validation")

        # Idempotency
        req_hash = _request_hash({"project_id": project_id, "item_id": item_id, **patch})
        replay = self._check_idempotency(command_id, req_hash, "update_item")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        with self._command_txn(command_id) as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )
            new_revision = current_rev + 1

            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            # Update item fields
            item_updates: list[str] = []
            item_params: list[Any] = []
            for key, value in fields.items():
                item_updates.append(f"{key} = ?")
                item_params.append(value)
            item_updates.append("revision = revision + 1")
            item_updates.append("updated_at = ?")
            item_params.append(now_iso)
            item_params.append(item_id)
            conn.execute(
                f"UPDATE project_items SET {', '.join(item_updates)} WHERE id = ?",
                item_params,
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None,
                    _request_hash(fields),
                    json.dumps({
                        "action": "item.updated",
                        "item_id": item_id,
                        "fields": list(fields.keys()),
                    }),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "action": "item.updated",
                    "item_id": item_id,
                    "fields": list(fields.keys()),
                },
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "update_item",
                req_hash, envelope,
            )

        item = self._db.projects.get_project_item(item_id)
        result = dict(item) if item else {"id": item_id}
        result.update(_envelope_to_dict(envelope))
        result["item_id"] = item_id
        return result

    @_serialized_command
    def transition_item(
        self, principal: Principal, project_id: str, item_id: str,
        verb: str, payload: dict[str, Any] | None = None,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Explicit lifecycle verb on an item (DOM-007).

        The verb IS the target lifecycle state.  DOM-007 is satisfied
        because a milestone can ONLY reach "reached" through this method
        (update_item refuses it), and this method requires an explicit
        verb from the caller -- narrative prose cannot invoke it.
        """
        self._require_project(project_id)
        existing = self._db.projects.get_project_item(item_id)
        if existing is None or existing["project_id"] != project_id:
            raise NotFound("project_item", item_id)

        body = payload or {}
        item_type = existing["item_type"]
        verb = str(verb).strip()
        self._validate_lifecycle(item_type, verb)

        current_lc = existing["lifecycle"]
        if current_lc == verb:
            # No-op: already in that state
            with self._db._connection() as conn:
                current_rev = self._get_revision(conn, project_id)
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.NO_CHANGE,
                project_id=project_id,
                project_revision=current_rev,
            )
            result = dict(existing)
            result.update(_envelope_to_dict(envelope))
            result["item_id"] = item_id
            return result

        # Idempotency
        req_hash = _request_hash({
            "project_id": project_id, "item_id": item_id,
            "verb": verb, **body,
        })
        replay = self._check_idempotency(command_id, req_hash, "transition_item")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = utc_now_iso()
        project_ref = format_ref("project", project_id)

        with self._command_txn(command_id) as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )
            new_revision = current_rev + 1

            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            conn.execute(
                "UPDATE project_items SET lifecycle = ?, revision = revision + 1, "
                "updated_at = ? WHERE id = ?",
                (verb, now_iso, item_id),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({
                        "action": "item.transitioned",
                        "item_id": item_id,
                        "from": current_lc,
                        "to": verb,
                    }),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "action": "item.transitioned",
                    "item_id": item_id,
                    "from": current_lc,
                    "to": verb,
                },
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "transition_item",
                req_hash, envelope,
            )

        item = self._db.projects.get_project_item(item_id)
        result = dict(item) if item else {"id": item_id}
        result.update(_envelope_to_dict(envelope))
        result["item_id"] = item_id
        return result

    def list_items(
        self, principal: Principal, project_id: str,
        *, item_type: Optional[str] = None,
        limit: int = 200, offset: int = 0,
    ) -> dict[str, Any]:
        """List items for a project, bounded and deterministically ordered.

        Order: item_type ASC, sort_key ASC NULLS LAST, created_at ASC, id ASC.
        Pagination via limit/offset (sibling convention).
        """
        self._require_project(project_id)
        clean_limit = max(1, min(int(limit), 1000))
        clean_offset = max(0, int(offset))

        with self._db._connection() as conn:
            if item_type:
                if item_type not in ITEM_TYPES:
                    raise ValidationError(
                        f"Unknown item_type filter: {item_type!r}",
                        code="validation",
                    )
                rows = conn.execute(
                    """
                    SELECT * FROM project_items
                    WHERE project_id = ? AND item_type = ?
                    ORDER BY sort_key IS NULL, sort_key ASC,
                             created_at ASC, id ASC
                    LIMIT ? OFFSET ?
                    """,
                    (project_id, item_type, clean_limit, clean_offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM project_items
                    WHERE project_id = ?
                    ORDER BY item_type ASC,
                             sort_key IS NULL, sort_key ASC,
                             created_at ASC, id ASC
                    LIMIT ? OFFSET ?
                    """,
                    (project_id, clean_limit, clean_offset),
                ).fetchall()

        return {
            "items": [dict(r) for r in rows],
            "limit": clean_limit,
            "offset": clean_offset,
        }

    # ── item validation helpers (project_definitions) ──────────────────

    _validate_severity = staticmethod(validate_severity)
    _validate_lifecycle = staticmethod(validate_lifecycle)
    _validate_optional_ref = staticmethod(validate_optional_ref)
    _validate_details = staticmethod(validate_details)

    # ── internal helpers ─────────────────────────────────────────────

    def _require_project(self, project_id: str) -> Any:
        return room_reads.require_project(self._db, project_id)

    def _require_meeting(self, meeting_id: str) -> Any:
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            raise NotFound("meeting", meeting_id)
        return meeting

    @staticmethod
    def _strings(value: Any) -> list[str]:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value or []

    @staticmethod
    def _threshold(value: Any) -> float:
        try:
            threshold = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("detection_threshold must be between 0 and 1") from exc
        if not 0.0 <= threshold <= 1.0:
            raise ValidationError("detection_threshold must be between 0 and 1")
        return threshold

    @staticmethod
    def _project_payload(project: Any) -> dict[str, Any]:
        return {"id": project.id, "name": project.name, "description": project.description,
                "keywords": project.keywords, "team_members": project.team_members, "context": project.context,
                "detection_threshold": project.detection_threshold, "is_archived": project.is_archived,
                "meeting_count": project.meeting_count, "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()}

    def _get_revision(self, conn: Any, project_id: str) -> int:
        """Read the current revision inside an open transaction."""
        row = conn.execute(
            "SELECT revision FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise NotFound("project", project_id)
        return int(row["revision"])

    def _command_txn(self, command_id: Optional[str]) -> Any:
        """The write transaction of an idempotent command (PHILO-9-02, law 9).

        ``_check_idempotency`` reads the command BEFORE the write; two callers
        with one ``command_id`` could both find it absent and both write (two
        revisions and change rows; Codex Astra r3 on PR #680, finding 3). The
        write transaction therefore takes the write lock first (``BEGIN
        IMMEDIATE``) and looks again: a command another caller recorded
        meanwhile raises :class:`_CommandRaced` before anything is written,
        and :func:`_serialized_command` answers through the replay path.
        """
        from contextlib import contextmanager

        @contextmanager
        def txn() -> Any:
            with self._db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                row = None if command_id is None else conn.execute(
                    "SELECT status FROM project_commands WHERE id=?", (command_id,),
                ).fetchone()
                if row is not None and row[0] == "completed":
                    raise _CommandRaced(command_id)
                yield conn

        return txn()

    def _check_idempotency(
        self, command_id: Optional[str], req_hash: str, command_kind: str,
    ) -> Optional[dict[str, Any]]:
        """API-002: if command_id is given, check for replay or conflict.

        Returns stored result dict on replay, None on new command.
        Raises ConflictError on hash mismatch.
        """
        if command_id is None:
            return None
        existing = self._db.projects.get_project_command(command_id)
        if existing is None:
            return None
        if existing["status"] == "completed" and existing["request_hash"] == req_hash:
            # Replay: return stored result
            if existing["result_json"]:
                return json.loads(existing["result_json"])
            return {"result_kind": "no_change", "project_id": existing["project_id"]}
        if existing["request_hash"] != req_hash:
            raise ConflictError(
                "idempotency conflict: same command_id with different request hash",
                code="idempotency_conflict",
                context={"command_id": command_id},
            )
        # Pending command with same hash -- proceed (could be a retry after crash)
        return None

    def _record_command(
        self,
        conn: Any,
        command_id: str,
        project_id: str,
        command_kind: str,
        request_hash: str,
        envelope: CommandResultEnvelope,
        *,
        result: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record a completed command in the idempotency ledger.

        ``result``: the whole response to replay (PHILO-9-01 round three);
        by default the envelope alone, as before.
        """
        # PHILO-9-02 round three (ruling A): the one answer per command, and
        # the admitted operation running this call ends in THIS transaction.
        from holdspeak.services import project_kernel

        project_kernel.answered(
            conn, command_id=command_id, project_id=project_id, command_kind=command_kind,
            request_hash=request_hash, answer=result if result is not None else _envelope_to_dict(envelope),
        )
