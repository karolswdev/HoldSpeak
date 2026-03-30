"""Artifact contracts and helpers for MIR synthesis outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_ARTIFACT_STATUSES = frozenset({"draft", "needs_review", "accepted", "rejected"})


def artifact_status_from_confidence(confidence: float) -> str:
    """Map confidence to a conservative default artifact review status."""
    score = max(0.0, min(1.0, float(confidence)))
    if score < 0.55:
        return "needs_review"
    return "draft"


@dataclass(frozen=True)
class ArtifactSourceRef:
    """Reference to source lineage for one synthesized artifact."""

    source_type: str
    source_ref: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source_type": self.source_type,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class ArtifactDraft:
    """Synthesized artifact payload before persistence."""

    artifact_id: str
    meeting_id: str
    artifact_type: str
    title: str
    body_markdown: str
    structured_json: dict[str, Any]
    confidence: float
    status: str
    plugin_id: str
    plugin_version: str
    sources: list[ArtifactSourceRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.artifact_id,
            "meeting_id": self.meeting_id,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "body_markdown": self.body_markdown,
            "structured_json": dict(self.structured_json),
            "confidence": float(self.confidence),
            "status": self.status,
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "sources": [source.to_dict() for source in self.sources],
        }

