"""Infrastructure data models: plugin runs, mesh relay, connectors."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from .mixins import Serializable


@dataclass
class PluginRunSummary(Serializable):
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
class PluginRunJob(Serializable):
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
class PluginRunJobQueueSummary(Serializable):
    """Aggregated deferred plugin-run queue telemetry."""

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    queued_due_jobs: int
    scheduled_retry_jobs: int
    next_retry_at: Optional[datetime] = None


@dataclass(frozen=True)
class ConnectorRun(Serializable):
    """One persisted invocation of a connector pack.

    HS-13-05. Each run row captures the start/finish timestamps,
    the success / error flag, the byte count and per-capability
    counters (annotations / candidates / commands). Rows are
    deleted alongside the connector's other output when the
    operator clicks "Clear annotations" / "Clear candidates" --
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
class MeshRelayJob(Serializable):
    """A mesh-edge relay run (HS-85-01): work addressed to ONE node, claimed by
    that node's worker, executed on ITS OWN provider, result posted back.
    Hub-local rows -- never a synced kind; prompts move only hub <-> the
    executing node."""

    id: str
    node: str
    task_kind: str = "llm"
    system_prompt: str = ""
    user_prompt: str = ""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model_hint: str = ""
    status: str = "queued"  # queued | running | completed | failed
    result: Optional[str] = None
    error: Optional[str] = None
    deadline_at: str = ""
    created_at: str = ""
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None
