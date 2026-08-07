"""Action-item and actuator data models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from .mixins import Serializable

# Validation constants shared across the persistence layer.
VALID_ACTION_ITEM_STATUSES = frozenset({"pending", "done", "dismissed"})
VALID_ACTION_ITEM_REVIEW_STATES = frozenset({"pending", "accepted"})
# Phase 37 (HS-37-02): the actuator-proposal lifecycle.
VALID_ACTUATOR_PROPOSAL_STATUSES = frozenset(
    {"proposed", "approved", "executed", "rejected", "failed"}
)


@dataclass
class ActionItemSummary(Serializable):
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
class ActuatorProposalRecord(Serializable):
    """A proposed external side effect awaiting human approval (Phase 37).

    ``payload`` is the exact machine representation of the side effect -- the
    parity source-of-truth the guarded executor (HS-37-04) checks before
    acting. Timestamps are ISO strings. ``status`` is one of
    ``VALID_ACTUATOR_PROPOSAL_STATUSES``.
    """

    id: str
    meeting_id: Optional[str]   # None for origin='desk' (v5 -- no sentinel meeting)
    origin: str                 # 'meeting' | 'desk' (v5, Phase 72)
    window_id: str
    plugin_id: str
    plugin_version: str
    idempotency_key: str
    status: str
    review_decision: str
    authorization_state: str
    execution_state: str
    target: str
    action: str
    preview: str
    payload: dict[str, Any]
    reversible: bool
    required_capabilities: list[str]
    decided_by: Optional[str]
    approved_payload_hash: Optional[str]
    approved_destination: Optional[str]
    approved_preview_hash: Optional[str]
    preview_renderer_version: Optional[str]
    effect_class: Optional[str]
    policy_version: Optional[str]
    operation: dict[str, Any]
    policy_snapshot: dict[str, Any]
    grant_id: Optional[str]
    result: Optional[dict[str, Any]]
    error: Optional[str]
    created_at: str
    decided_at: Optional[str]
    executed_at: Optional[str]
    updated_at: str


@dataclass
class AuthorityGrantRecord(Serializable):
    """A revocable actor/effect/destination/data/scope/time/count grant."""

    id: str
    actor: str
    operation_family: str
    effect_class: str
    destination: str
    data_classes: list[str]
    project_scope: Optional[str]
    resource_scope: Optional[str]
    issued_at: str
    expires_at: str
    max_uses: int
    remaining_uses: int
    revoked_at: Optional[str]
    revoke_reason: Optional[str]
    binding_hash: str
    control_mode: str

    @property
    def state(self) -> str:
        if self.revoked_at:
            return "revoked"
        try:
            if datetime.fromisoformat(self.expires_at) <= datetime.now():
                return "expired"
        except ValueError:
            return "expired"
        if self.remaining_uses <= 0:
            return "exhausted"
        return "active"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "actor": self.actor,
            "operation_family": self.operation_family,
            "effect_class": self.effect_class, "destination": self.destination,
            "data_classes": list(self.data_classes),
            "project_scope": self.project_scope, "resource_scope": self.resource_scope,
            "issued_at": self.issued_at, "expires_at": self.expires_at,
            "max_uses": self.max_uses, "remaining_uses": self.remaining_uses,
            "revoked_at": self.revoked_at, "revoke_reason": self.revoke_reason,
            "binding_hash": self.binding_hash, "control_mode": self.control_mode,
            "state": self.state,
        }


@dataclass
class ActuatorProposalAuditEntry(Serializable):
    """One recorded status transition of an actuator proposal (Phase 37)."""

    id: int
    proposal_id: str
    actor: str
    from_status: Optional[str]
    to_status: str
    detail: Optional[str]
    created_at: str


@dataclass
class DictationCorrectionRecord(Serializable):
    """A persisted dictation correction (Phase 40, HS-40-02).

    The durable form of ``plugins.dictation.corrections.Correction``: ``kind`` is
    ``"intent"``/``"target"``, ``gist`` is the bounded context gist the correction
    applies to, ``value`` is the corrected block id / target profile. Gist-only +
    secret-rejected at write time (the ``CorrectionStore`` enforces this before
    persisting), so a stored row never carries a secret.
    """

    id: int
    kind: str
    gist: str
    value: str
    created_at: str
