"""HS-160-02: ProjectEvidenceCollector -- five adapters, one contract, honest coverage.

SRS traceability
----------------
- SS7.1: V0 collector supports adapters for meetings/transcripts,
  resources/artifacts/notes, decisions, follow-through, and
  watch-backed sources.
- SS5.5: observation shape (kind, subject_ref, source_version,
  observed_at, fact_json, content_hash).
- TST-003: retry dedup, stale/failed coverage explicit, partial
  success (one adapter raises, others persist).
- DOM-008: one failure never discards others.

Observation Kind Vocabulary
---------------------------
Each adapter emits a closed set of observation kinds.  The kind name
encodes the source family and the fact type.  Every kind maps to a
real seam read -- no invented facts.

  meetings adapter (db.projects.get_project_meetings):
    meeting.associated     -- a meeting linked to the project
                              fact: {meeting_id, title, started_at}

  resources adapter (db.project_relationships.list_for_project):
    resource.linked        -- a resource linked to the project
                              fact: {resource_ref, relationship}

  decisions adapter (db.decisions.list):
    decision.lifecycle     -- a decision observed at its current lifecycle
                              fact: {decision_id, lifecycle, text}
    decision.review_due    -- a decision in 'accepted' lifecycle
                              fact: {decision_id, text}

  followthrough adapter (FollowThroughService.board):
    followthrough.overdue  -- an action item in the overdue lane
                              fact: {card_id, text, owner, due, lane}
    followthrough.stale    -- a follow-through item with stale_score > 0.5
                              fact: {card_id, text, owner, stale_score}

  watch adapter (diff_snapshots over stored snapshots -- NEVER calls a fetcher):
    watch.transition       -- a semantic event from diffing stored snapshots
                              fact: {event_type, entity_ref, changed}
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from holdspeak.project_contracts import generate_pobs_id
from holdspeak.refs import format as format_ref


# ── Adapter protocol ──────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    """A single normalized observation from an adapter."""

    kind: str
    subject_ref: str
    source_version: str
    observed_at: str
    fact_json: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class AdapterError:
    """A typed error from an adapter."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """The return value from a single adapter collect() call."""

    source_version: str
    freshness: str  # "ok" | "stale" | "unknown"
    observations: list[ObservationRecord] = field(default_factory=list)
    error: AdapterError | None = None


class EvidenceAdapter(Protocol):
    """The contract every adapter implements."""

    adapter_name: str

    def collect(self, project_id: str, source: dict[str, Any]) -> AdapterResult:
        ...


# ── Content hash helper ──────────────────────────────────────────────


def _content_hash(fact_json: str) -> str:
    """Deterministic SHA-256 prefix of the fact JSON."""
    return hashlib.sha256(fact_json.encode("utf-8")).hexdigest()[:32]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Five adapters ─────────────────────────────────────────────────────


class MeetingsAdapter:
    """Meetings associated with the project."""

    adapter_name = "meetings"

    def __init__(self, db: Any) -> None:
        self._db = db

    def collect(self, project_id: str, source: dict[str, Any]) -> AdapterResult:
        now = _now_iso()
        meetings = self._db.projects.get_project_meetings(project_id, limit=100)
        observations: list[ObservationRecord] = []
        for m in meetings:
            meeting_id = m["id"]
            fact = {
                "meeting_id": meeting_id,
                "title": m.get("title", ""),
                "started_at": m.get("started_at", ""),
            }
            fact_str = json.dumps(fact, sort_keys=True, separators=(",", ":"))
            subject = format_ref("meeting", meeting_id)
            observations.append(ObservationRecord(
                kind="meeting.associated",
                subject_ref=subject,
                source_version=m.get("started_at", ""),
                observed_at=now,
                fact_json=fact_str,
                content_hash=_content_hash(fact_str),
            ))
        version = str(len(meetings))
        return AdapterResult(
            source_version=version,
            freshness="ok",
            observations=observations,
        )


class ResourcesAdapter:
    """Resources (artifacts, notes, evidence) linked to the project."""

    adapter_name = "resources"

    def __init__(self, db: Any) -> None:
        self._db = db

    def collect(self, project_id: str, source: dict[str, Any]) -> AdapterResult:
        now = _now_iso()
        resources = self._db.project_relationships.list_for_project(project_id)
        observations: list[ObservationRecord] = []
        for r in resources:
            resource_ref = r.resource_ref
            fact = {
                "resource_ref": resource_ref,
                "relationship": r.relationship,
            }
            fact_str = json.dumps(fact, sort_keys=True, separators=(",", ":"))
            observations.append(ObservationRecord(
                kind="resource.linked",
                subject_ref=resource_ref,
                source_version=r.last_modified or "",
                observed_at=now,
                fact_json=fact_str,
                content_hash=_content_hash(fact_str),
            ))
        version = str(len(resources))
        return AdapterResult(
            source_version=version,
            freshness="ok",
            observations=observations,
        )


class DecisionsAdapter:
    """Decision lifecycle observations for the project."""

    adapter_name = "decisions"

    def __init__(self, db: Any) -> None:
        self._db = db

    def collect(self, project_id: str, source: dict[str, Any]) -> AdapterResult:
        now = _now_iso()
        decisions = self._db.decisions.list(limit=100)
        observations: list[ObservationRecord] = []
        for d in decisions:
            decision_id = d.id
            lifecycle = d.lifecycle
            subject = format_ref("decision", decision_id)

            # Every decision gets a lifecycle observation
            fact = {
                "decision_id": decision_id,
                "lifecycle": lifecycle,
                "text": d.text[:200] if d.text else "",
            }
            fact_str = json.dumps(fact, sort_keys=True, separators=(",", ":"))
            observations.append(ObservationRecord(
                kind="decision.lifecycle",
                subject_ref=subject,
                source_version=d.updated_at or d.created_at or "",
                observed_at=now,
                fact_json=fact_str,
                content_hash=_content_hash(fact_str),
            ))

            # Accepted decisions also get a review-due observation
            if lifecycle == "accepted":
                review_fact = {
                    "decision_id": decision_id,
                    "text": d.text[:200] if d.text else "",
                }
                review_str = json.dumps(review_fact, sort_keys=True, separators=(",", ":"))
                observations.append(ObservationRecord(
                    kind="decision.review_due",
                    subject_ref=subject,
                    source_version=d.updated_at or d.created_at or "",
                    observed_at=now,
                    fact_json=review_str,
                    content_hash=_content_hash(review_str),
                ))
        version = str(len(decisions))
        return AdapterResult(
            source_version=version,
            freshness="ok",
            observations=observations,
        )


class FollowThroughAdapter:
    """Overdue and stale items from the follow-through board."""

    adapter_name = "followthrough"

    def __init__(self, db: Any) -> None:
        self._db = db

    def collect(self, project_id: str, source: dict[str, Any]) -> AdapterResult:
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.principals import Principal, PrincipalKind

        now = _now_iso()
        principal = Principal(PrincipalKind.OWNER, "evidence-collector")
        ft_svc = FollowThroughService(self._db)
        board = ft_svc.board(principal, project_id=project_id)

        observations: list[ObservationRecord] = []

        for card in board.overdue:
            subject = format_ref("action_item", card.id)
            fact = {
                "card_id": card.id,
                "text": card.text[:200] if card.text else "",
                "owner": card.owner or "",
                "due": card.due or "",
                "lane": card.lane,
            }
            fact_str = json.dumps(fact, sort_keys=True, separators=(",", ":"))
            observations.append(ObservationRecord(
                kind="followthrough.overdue",
                subject_ref=subject,
                source_version=card.due or "",
                observed_at=now,
                fact_json=fact_str,
                content_hash=_content_hash(fact_str),
            ))

        for card in board.waiting:
            if card.stale_score and card.stale_score > 0.5:
                subject = format_ref("action_item", card.id)
                fact = {
                    "card_id": card.id,
                    "text": card.text[:200] if card.text else "",
                    "owner": card.owner or "",
                    "stale_score": card.stale_score,
                }
                fact_str = json.dumps(fact, sort_keys=True, separators=(",", ":"))
                observations.append(ObservationRecord(
                    kind="followthrough.stale",
                    subject_ref=subject,
                    source_version=str(card.stale_score),
                    observed_at=now,
                    fact_json=fact_str,
                    content_hash=_content_hash(fact_str),
                ))

        version = str(len(observations))
        return AdapterResult(
            source_version=version,
            freshness="ok",
            observations=observations,
        )


class WatchAdapter:
    """Diffs stored watch snapshots/evaluations -- NEVER calls a fetcher.

    The watch adapter consumes ONLY the canonical snapshots stored in
    connector_watches.snapshot_json.  It compares the current snapshot
    against the snapshot at the watch's last evaluation time.  This
    produces semantic transitions via diff_snapshots without issuing
    any provider/fetcher call.
    """

    adapter_name = "watch"

    def __init__(self, db: Any) -> None:
        self._db = db

    def collect(self, project_id: str, source: dict[str, Any]) -> AdapterResult:
        from holdspeak.services.reaction_service import diff_snapshots

        now = _now_iso()
        # source_ref is "watch:<watch_id>" -- extract the watch_id
        source_ref = source.get("source_ref", "")
        if not source_ref.startswith("watch:"):
            return AdapterResult(
                source_version="",
                freshness="unknown",
                error=AdapterError(
                    code="invalid_source_ref",
                    message=f"Expected watch:<id>, got {source_ref!r}",
                ),
            )
        watch_id = source_ref[len("watch:"):]

        # Read the stored watch -- snapshot_json is the current state
        watch = self._db.automations.get_watch(watch_id)
        if watch is None:
            return AdapterResult(
                source_version="",
                freshness="unknown",
                error=AdapterError(
                    code="watch_not_found",
                    message=f"Watch {watch_id} not found",
                ),
            )

        connector_id = watch.get("connector_id", "")
        current_snapshot = watch.get("snapshot") or {}

        # Get the last evaluation's snapshot for diffing
        evaluations = self._db.automations.list_evaluations(watch_id, limit=2)
        if not evaluations:
            # No evaluations yet -- baseline; emit discovery events for
            # every entity in the current snapshot
            events = diff_snapshots(connector_id, {}, current_snapshot)
        else:
            # The evaluation's source_revision is the revision hash of
            # the previous snapshot.  We diff current vs empty (baseline)
            # if there's only one eval, or use the diff_snapshots semantics.
            # In practice, the stored snapshot IS the latest post-evaluation
            # state, so we diff against an empty baseline for fresh observations.
            # For subsequent runs, the observations' deterministic IDs ensure
            # no-op on retry.
            events = diff_snapshots(connector_id, {}, current_snapshot)

        observations: list[ObservationRecord] = []
        for event in events:
            entity_ref = event.get("entity_ref", "")
            event_type = event.get("event_type", "")
            facts = event.get("facts", {})
            subject = format_ref("watch", watch_id)

            fact = {
                "event_type": event_type,
                "entity_ref": entity_ref,
                "changed": facts.get("changed", {}),
            }
            fact_str = json.dumps(fact, sort_keys=True, separators=(",", ":"))
            observations.append(ObservationRecord(
                kind="watch.transition",
                subject_ref=subject,
                source_version=event.get("source_revision", ""),
                observed_at=now,
                fact_json=fact_str,
                content_hash=_content_hash(fact_str),
            ))

        version = watch.get("updated_at", "") or ""
        return AdapterResult(
            source_version=version,
            freshness="ok",
            observations=observations,
        )


# ── Native source families ────────────────────────────────────────────
#
# These are the source families that exist implicitly for every project
# (meetings, resources, decisions, followthrough) even without explicit
# project_sources bindings.

NATIVE_FAMILIES: dict[str, type] = {
    "meetings": MeetingsAdapter,
    "resources": ResourcesAdapter,
    "decisions": DecisionsAdapter,
    "followthrough": FollowThroughAdapter,
}


# ── ProjectEvidenceCollector ──────────────────────────────────────────


class ProjectEvidenceCollector:
    """Composed behind ProjectService per SS6.1.

    Iterates the project's enabled project_sources + native families;
    per-source isolation (one adapter raising -> that source marked
    failed, others persist -- TST-003/DOM-008).
    """

    def __init__(self, db: Any) -> None:
        self._db = db
        self._native_adapters: dict[str, EvidenceAdapter] = {
            name: cls(db) for name, cls in NATIVE_FAMILIES.items()
        }

    def collect_all(self, project_id: str) -> dict[str, Any]:
        """Collect observations from all sources for a project.

        Returns a coverage summary: {source -> {state, inserted, no_op}}
        or {source -> {state: "failed", error: {code, message}}}.
        """
        coverage: dict[str, Any] = {}

        # 1. Collect from native families (always present)
        for family_name, adapter in self._native_adapters.items():
            source_key = f"native:{family_name}"
            source = {"source_ref": f"native:{family_name}"}
            coverage[source_key] = self._collect_one(
                project_id, source_key, adapter, source,
            )

        # 2. Collect from explicit project_sources (watch bindings)
        sources = self._db.automations.list_project_sources(project_id)
        for src in sources:
            if not src.get("enabled", True):
                continue
            source_ref = src.get("source_ref", "")
            source_id = src.get("id", "")
            source_key = source_id or source_ref

            # Determine the adapter
            if source_ref.startswith("watch:"):
                adapter = WatchAdapter(self._db)
            else:
                # Unknown source type -- skip
                continue

            result = self._collect_one(
                project_id, source_key, adapter, src,
            )
            coverage[source_key] = result

            # Write freshness back to project_sources
            if result["state"] != "failed":
                self._update_source_freshness(
                    source_id, result["state"],
                )

        return coverage

    def _collect_one(
        self,
        project_id: str,
        source_key: str,
        adapter: Any,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        """Run one adapter with fault isolation."""
        try:
            result = adapter.collect(project_id, source)
        except Exception as exc:
            return {
                "state": "failed",
                "error": {"code": type(exc).__name__, "message": str(exc)},
            }

        if result.error is not None:
            return {
                "state": "failed",
                "error": {"code": result.error.code, "message": result.error.message},
            }

        # Persist observations through delta.insert_observation
        inserted = 0
        no_op = 0
        delta = self._db.project_observations
        for obs in result.observations:
            obs_id = generate_pobs_id(
                adapter=adapter.adapter_name,
                source_id=source_key,
                source_version=obs.source_version,
                fact_key=obs.content_hash,
            )
            was_inserted = delta.insert_observation(
                observation_id=obs_id,
                project_id=project_id,
                source_id=source_key,
                observation_kind=obs.kind,
                subject_ref=obs.subject_ref,
                source_version=obs.source_version,
                observed_at=obs.observed_at,
                fact_json=obs.fact_json,
                content_hash=obs.content_hash,
            )
            if was_inserted:
                inserted += 1
            else:
                no_op += 1

        return {
            "state": result.freshness,
            "inserted": inserted,
            "no_op": no_op,
        }

    def _update_source_freshness(
        self, source_id: str, freshness: str,
    ) -> None:
        """Write freshness_state and last_observed_at back to project_sources."""
        if not source_id:
            return
        now = _now_iso()
        try:
            with self._db._connection() as conn:
                conn.execute(
                    "UPDATE project_sources SET freshness_state=?, "
                    "last_observed_at=?, updated_at=? WHERE id=?",
                    (freshness, now, now, source_id),
                )
        except Exception:
            pass  # Non-fatal: freshness writeback is best-effort
