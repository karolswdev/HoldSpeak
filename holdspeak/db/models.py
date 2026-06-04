"""Data models for the HoldSpeak persistence layer.

Extracted verbatim from db.py in Phase 31 (HS-31-01) so repositories and the
Database container share them without import cycles.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

# Validation constants shared across the persistence layer.
VALID_ACTION_ITEM_STATUSES = frozenset({"pending", "done", "dismissed"})
VALID_ACTION_ITEM_REVIEW_STATES = frozenset({"pending", "accepted"})
VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES = frozenset(
    {"candidate", "armed", "dismissed", "started"}
)
# Phase 37 (HS-37-02): the actuator-proposal lifecycle.
VALID_ACTUATOR_PROPOSAL_STATUSES = frozenset(
    {"proposed", "approved", "executed", "rejected", "failed"}
)


@dataclass
class MeetingSummary:
    """Lightweight meeting summary for list views."""
    id: str
    started_at: datetime
    ended_at: Optional[datetime]
    title: Optional[str]
    duration_seconds: float
    segment_count: int
    action_item_count: int
    tags: list[str]
    intel_status: str = "disabled"
    intel_status_detail: Optional[str] = None


@dataclass
class IntelJob:
    """Deferred intelligence job metadata."""

    meeting_id: str
    status: str
    transcript_hash: str
    requested_at: datetime
    updated_at: datetime
    attempts: int
    last_error: Optional[str]
    meeting_title: Optional[str] = None
    started_at: Optional[datetime] = None
    intel_status_detail: Optional[str] = None


@dataclass
class IntelQueueSummary:
    """Aggregated deferred-intel queue telemetry."""

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    queued_due_jobs: int
    scheduled_retry_jobs: int
    next_retry_at: Optional[datetime] = None


@dataclass
class IntelJobAttempt:
    """Deferred-intel attempt event for one meeting."""

    meeting_id: str
    attempt: int
    outcome: str
    error: Optional[str]
    retry_at: Optional[datetime]
    created_at: datetime


@dataclass
class ActionItemSummary:
    """Action item with meeting context."""
    id: str
    task: str
    owner: Optional[str]
    due: Optional[str]
    status: str
    review_state: str
    meeting_id: str
    meeting_title: Optional[str]
    meeting_date: datetime
    source_timestamp: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    reviewed_at: Optional[datetime]


@dataclass
class IntentWindowSummary:
    """Persisted MIR intent window with confidence scores."""

    meeting_id: str
    window_id: str
    start_seconds: float
    end_seconds: float
    transcript_hash: str
    transcript_excerpt: str
    profile: str
    threshold: float
    active_intents: list[str]
    intent_scores: dict[str, float]
    override_intents: list[str]
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class PluginRunSummary:
    """Persisted MIR plugin-run record."""

    id: int
    meeting_id: str
    window_id: str
    plugin_id: str
    plugin_version: str
    status: str
    idempotency_key: Optional[str]
    duration_ms: float
    output: Optional[dict[str, Any]]
    error: Optional[str]
    deduped: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class PluginRunJob:
    """Deferred MIR plugin-run queue item."""

    id: int
    meeting_id: str
    window_id: str
    plugin_id: str
    plugin_version: str
    transcript_hash: str
    idempotency_key: str
    context: dict[str, Any]
    status: str
    requested_at: datetime
    updated_at: datetime
    attempts: int
    last_error: Optional[str]


@dataclass
class PluginRunJobQueueSummary:
    """Aggregated deferred plugin-run queue telemetry."""

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    queued_due_jobs: int
    scheduled_retry_jobs: int
    next_retry_at: Optional[datetime] = None


@dataclass
class ProjectSummary:
    """User-defined project knowledge base."""

    id: str
    name: str
    description: str
    keywords: list[str]
    team_members: list[str]
    context: dict[str, Any]
    detection_threshold: float
    is_archived: bool
    meeting_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class ArtifactSummary:
    """Persisted synthesized artifact with lineage sources."""

    id: str
    meeting_id: str
    artifact_type: str
    title: str
    body_markdown: str
    structured_json: dict[str, Any]
    confidence: float
    status: str
    plugin_id: str
    plugin_version: str
    sources: list[dict[str, str]]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityRecord:
    """Normalized local activity record from browser history metadata."""

    id: int
    source_browser: str
    source_profile: str
    source_path_hash: str
    url: str
    normalized_url: str
    title: Optional[str]
    domain: str
    visit_count: int
    first_seen_at: Optional[datetime]
    last_seen_at: Optional[datetime]
    last_visit_raw: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    project_id: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityImportCheckpoint:
    """Per browser/profile import checkpoint for local activity readers."""

    source_browser: str
    source_profile: str
    source_path_hash: str
    last_visit_raw: Optional[str]
    last_imported_at: Optional[datetime]
    last_error: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityProjectRule:
    """User-defined rule for assigning local activity to a project."""

    id: str
    project_id: str
    project_name: Optional[str]
    name: str
    enabled: bool
    priority: int
    match_type: str
    pattern: str
    entity_type: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityEnrichmentConnectorState:
    """Persisted state for an optional activity enrichment connector."""

    id: str
    enabled: bool
    settings: dict[str, Any]
    last_run_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ConnectorRun:
    """One persisted invocation of a connector pack.

    HS-13-05. Each run row captures the start/finish timestamps,
    the success / error flag, the byte count and per-capability
    counters (annotations / candidates / commands). Rows are
    deleted alongside the connector's other output when the
    operator clicks "Clear annotations" / "Clear candidates" —
    run history is part of the pack's output, not a global log.
    """

    id: int
    connector_id: str
    started_at: datetime
    finished_at: datetime
    succeeded: bool
    error: Optional[str]
    output_bytes: int
    annotation_count: int
    candidate_count: int
    command_count: int

    def duration_ms(self) -> int:
        delta = self.finished_at - self.started_at
        return max(0, int(delta.total_seconds() * 1000))

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "connector_id": self.connector_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "succeeded": self.succeeded,
            "error": self.error,
            "output_bytes": self.output_bytes,
            "annotation_count": self.annotation_count,
            "candidate_count": self.candidate_count,
            "command_count": self.command_count,
            "duration_ms": self.duration_ms(),
        }


@dataclass
class ActivityAnnotation:
    """Local enrichment annotation attached to an activity record or entity."""

    id: str
    activity_record_id: Optional[int]
    source_connector_id: str
    annotation_type: str
    title: str
    value: dict[str, Any]
    confidence: float
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityMeetingCandidate:
    """Local candidate for a meeting action derived from activity metadata."""

    id: str
    source_connector_id: str
    source_activity_record_id: Optional[int]
    dedupe_key: str
    title: str
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    meeting_url: Optional[str]
    started_meeting_id: Optional[str]
    confidence: float
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ActuatorProposalRecord:
    """A proposed external side effect awaiting human approval (Phase 37).

    `payload` is the exact machine representation of the side effect — the
    parity source-of-truth the guarded executor (HS-37-04) checks before
    acting. Timestamps are ISO strings. `status` is one of
    `VALID_ACTUATOR_PROPOSAL_STATUSES`.
    """

    id: str
    meeting_id: str
    window_id: str
    plugin_id: str
    plugin_version: str
    idempotency_key: str
    status: str
    target: str
    action: str
    preview: str
    payload: dict[str, Any]
    reversible: bool
    required_capabilities: list[str]
    decided_by: Optional[str]
    result: Optional[dict[str, Any]]
    error: Optional[str]
    created_at: str
    decided_at: Optional[str]
    executed_at: Optional[str]
    updated_at: str


@dataclass
class ActuatorProposalAuditEntry:
    """One recorded status transition of an actuator proposal (Phase 37)."""

    id: int
    proposal_id: str
    actor: str
    from_status: Optional[str]
    to_status: str
    detail: Optional[str]
    created_at: str

