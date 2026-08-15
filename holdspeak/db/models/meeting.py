"""Meeting-domain data models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from .mixins import Serializable


@dataclass
class MeetingSummary(Serializable):
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
    capture_status: str = "finalized"
    capture_failure: Optional[str] = None
    capture_checkpoint_seconds: float = 0.0
    provenance: str = "desktop"


@dataclass
class IntelJob(Serializable):
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
    # HS-131-08: the structured work stop() displaced onto this job (slugs from
    # `holdspeak.meeting_session.intel_plan.DISPLACED_*`). Empty for an ordinary
    # deferred job.
    displaced_work: tuple[str, ...] = ()


@dataclass
class IntelQueueSummary(Serializable):
    """Aggregated deferred-intel queue telemetry."""

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    queued_due_jobs: int
    scheduled_retry_jobs: int
    next_retry_at: Optional[datetime] = None


@dataclass
class IntelJobAttempt(Serializable):
    """Deferred-intel attempt event for one meeting."""

    meeting_id: str
    attempt: int
    outcome: str
    error: Optional[str]
    retry_at: Optional[datetime]
    created_at: datetime


@dataclass
class IntentWindowSummary(Serializable):
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
