"""Activity, project, artifact, profile, and journal data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

from .mixins import Serializable

VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES = frozenset(
    {"candidate", "armed", "dismissed", "started"}
)


@dataclass
class ProjectSummary(Serializable):
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
class ArtifactSummary(Serializable):
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
    # 'meeting' | 'run' (v6, Phase 74). Run-born rows have no meeting anchor:
    # meeting_id stores NULL and reads back "" here.
    origin: str = "meeting"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "origin": self.origin,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "body_markdown": self.body_markdown,
            "structured_json": dict(self.structured_json),
            "confidence": self.confidence,
            "status": self.status,
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "sources": list(self.sources),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class ActivityRecord(Serializable):
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
class ActivityImportCheckpoint(Serializable):
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
class ActivityProjectRule(Serializable):
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
class ActivityEnrichmentConnectorState(Serializable):
    """Persisted state for an optional activity enrichment connector."""

    id: str
    enabled: bool
    settings: dict[str, Any]
    last_run_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityAnnotation(Serializable):
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
class ActivityMeetingCandidate(Serializable):
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
class DictationJournalRecord(Serializable):
    """One persisted dictation-journal entry (Phase 45, HS-45-01).

    The durable afterlife of a single dictation/dry-run pipeline run: what was
    said (``transcript``), how it routed (``intent``/``block_id``/``confidence``),
    where it was headed (``target_profile``), what got typed (``final_text``), and
    how long each stage took (``stage_ms``/``total_ms``/``rewrite_pass_ms``).
    ``source`` is ``"dictation"`` (a real spoken run) or ``"dry_run"`` (the
    no-mic web path). ``corrected``/``correction_id`` are unset here and set by
    HS-45-03 when the user fixes the entry in the moment. Transcript + final text
    are secret-filtered before persistence, so a stored row never carries a secret.
    """

    id: int
    created_at: str
    source: str
    transcript: str
    final_text: str
    project_root: Optional[str] = None
    intent: Optional[str] = None
    block_id: Optional[str] = None
    target_profile: Optional[str] = None
    stage_ms: dict[str, float] = field(default_factory=dict)
    total_ms: float = 0.0
    rewrite_pass_ms: list[float] = field(default_factory=list)
    confidence: Optional[float] = None
    warnings: list[str] = field(default_factory=list)
    corrected: bool = False
    correction_id: Optional[int] = None
