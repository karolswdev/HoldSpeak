"""HS-172-03: Proposal bridge -- intel artifacts to follow-through proposals.

After an intel job completes, reads decision_capture and action_owner_enforcer
artifacts and writes PROPOSALS into ``follow_through_proposals``.  Idempotent
per (meeting_id, fingerprint).  Confirm/dismiss go through the kernel.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from ..db.core import Database
from ..db.proposals import Proposal
from ..logging_config import get_logger
from ..principals import Principal
from ..services.observer import current_correlation_id
from ..services.service_event_ledger import ServiceEventLedger

log = get_logger("proposal_bridge")

# The two extractors whose artifacts we read.
_DECISION_PLUGIN = "decision_capture"
_ACTION_PLUGIN = "action_owner_enforcer"


class ProposalBridgeService:
    """Bridge intel artifacts into follow-through proposals."""

    def __init__(self, db: Database) -> None:
        self._db = db

    # ── bridge: artifacts -> proposals ──────────────────────────────

    def bridge_meeting_artifacts(
        self,
        meeting_id: str,
        *,
        model_host: str = "local",
    ) -> list[Proposal]:
        """Read extractor artifacts for a meeting, create proposals.

        Returns the newly created proposals (empty if all were deduped).
        """
        created: list[Proposal] = []

        # Resolve project_id for this meeting.
        project_ids = self._db.projects.get_meeting_projects(meeting_id)
        project_id = project_ids[0]["project_id"] if project_ids else None

        # Read artifacts from the two extractors.
        artifacts = self._db.plugins.list_artifacts(meeting_id, limit=2000)

        for art in artifacts:
            if art.plugin_id == _DECISION_PLUGIN:
                created.extend(
                    self._bridge_decision_artifact(
                        meeting_id, project_id, art, model_host
                    )
                )
            elif art.plugin_id == _ACTION_PLUGIN:
                created.extend(
                    self._bridge_action_artifact(
                        meeting_id, project_id, art, model_host
                    )
                )

        return created

    def _bridge_decision_artifact(
        self,
        meeting_id: str,
        project_id: Optional[str],
        artifact: Any,
        model_host: str,
    ) -> list[Proposal]:
        """Extract decisions from a decision_capture artifact."""
        created: list[Proposal] = []
        structured = self._parse_structured(artifact)
        decisions = structured.get("decisions") or []
        for dec in decisions:
            text = str(dec.get("text") or "").strip()
            if not text:
                continue
            prop = self._db.proposals.create_proposal(
                meeting_id=meeting_id,
                project_id=project_id,
                kind="decision",
                text=text,
                source_artifact_id=artifact.id,
                source_plugin=_DECISION_PLUGIN,
                segment_timestamp=dec.get("source_timestamp"),
                speaker_label=dec.get("speaker"),
                model_host=model_host,
            )
            if prop is not None:
                created.append(prop)
        return created

    def _bridge_action_artifact(
        self,
        meeting_id: str,
        project_id: Optional[str],
        artifact: Any,
        model_host: str,
    ) -> list[Proposal]:
        """Extract action items from an action_owner_enforcer artifact."""
        created: list[Proposal] = []
        structured = self._parse_structured(artifact)
        items = structured.get("action_items") or []
        for item in items:
            text = str(item.get("task") or item.get("text") or "").strip()
            if not text:
                continue
            prop = self._db.proposals.create_proposal(
                meeting_id=meeting_id,
                project_id=project_id,
                kind="action",
                text=text,
                owner_hint=item.get("owner"),
                due_hint=item.get("due"),
                source_artifact_id=artifact.id,
                source_plugin=_ACTION_PLUGIN,
                segment_timestamp=item.get("source_timestamp"),
                speaker_label=item.get("speaker"),
                model_host=model_host,
            )
            if prop is not None:
                created.append(prop)
        return created

    @staticmethod
    def _parse_structured(artifact: Any) -> dict[str, Any]:
        """Parse the artifact's structured_json."""
        raw = getattr(artifact, "structured_json", None) or "{}"
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}

    # ── confirm / dismiss ───────────────────────────────────────────

    def confirm_proposal(
        self,
        principal: Principal,
        proposal_id: str,
        *,
        text: Optional[str] = None,
        owner: Optional[str] = None,
        due: Optional[str] = None,
    ) -> dict[str, Any]:
        """Confirm a proposal: write decision_record + commitment through the kernel."""
        proposal = self._db.proposals.get_proposal(proposal_id)
        if proposal is None or proposal.state != "proposed":
            return {"error": "Proposal not found or already decided"}

        # Confirm in the proposals table.
        confirmed = self._db.proposals.confirm_proposal(
            proposal_id, text=text, owner=owner, due=due,
        )
        if confirmed is None:
            return {"error": "Failed to confirm proposal"}

        final_text = text or proposal.text
        final_owner = owner or proposal.owner_hint
        final_due = due or proposal.due_hint
        now = datetime.now().isoformat()

        result: dict[str, Any] = {
            "proposal_id": proposal_id,
            "state": "confirmed",
            "original_text": proposal.original_text,
        }

        if proposal.kind == "decision":
            # Create a decision_record via the decisions table.
            decision_id = f"dec-{uuid.uuid4().hex[:16]}"
            with self._db._connection() as conn:
                conn.execute(
                    """INSERT INTO decisions
                       (id, text, rationale, decided_at, date_basis,
                        source_timestamp, source_artifact_id,
                        source_meeting_id, project_key, lifecycle,
                        created_at, updated_at, last_modified)
                       VALUES (?, ?, '', ?, 'meeting_date', ?, ?, ?, ?, 'accepted',
                               ?, ?, ?)""",
                    (
                        decision_id, final_text, now,
                        proposal.segment_timestamp,
                        proposal.source_artifact_id or "",
                        proposal.meeting_id,
                        self._project_key(proposal.project_id),
                        now, now, now,
                    ),
                )
                ServiceEventLedger(self._db).append_in_transaction(
                    conn, principal,
                    event_type="proposal.confirmed",
                    producer="ProposalBridgeService",
                    subject_ref=f"proposal:{proposal_id}",
                    source_revision=decision_id,
                    facts={
                        "proposal_id": proposal_id,
                        "decision_id": decision_id,
                        "kind": "decision",
                        "text": final_text,
                        "original_text": proposal.original_text,
                    },
                    refs=[f"proposal:{proposal_id}", f"decision:{decision_id}"],
                    correlation_id=current_correlation_id(),
                    causation_id=f"proposal:{proposal_id}",
                )
            result["decision_id"] = decision_id

        elif proposal.kind == "action":
            # Create an action_item directly.
            action_id = f"action-{uuid.uuid4().hex[:16]}"
            delegated_at = now if final_owner else None
            with self._db._connection() as conn:
                conn.execute(
                    """INSERT INTO action_items
                       (id, meeting_id, task, owner, due, status,
                        review_state, source_timestamp, created_at, delegated_at)
                       VALUES (?, ?, ?, ?, ?, 'open', 'accepted', ?, ?, ?)""",
                    (
                        action_id, proposal.meeting_id, final_text,
                        final_owner, final_due,
                        proposal.segment_timestamp, now, delegated_at,
                    ),
                )
                ServiceEventLedger(self._db).append_in_transaction(
                    conn, principal,
                    event_type="proposal.confirmed",
                    producer="ProposalBridgeService",
                    subject_ref=f"proposal:{proposal_id}",
                    source_revision=action_id,
                    facts={
                        "proposal_id": proposal_id,
                        "action_item_id": action_id,
                        "kind": "action",
                        "text": final_text,
                        "original_text": proposal.original_text,
                        "owner": final_owner,
                        "due": final_due,
                    },
                    refs=[f"proposal:{proposal_id}", f"action_item:{action_id}"],
                    correlation_id=current_correlation_id(),
                    causation_id=f"proposal:{proposal_id}",
                )
            result["action_item_id"] = action_id

        return result

    def dismiss_proposal(
        self,
        principal: Principal,
        proposal_id: str,
    ) -> dict[str, Any]:
        """Dismiss a proposal without creating any record."""
        proposal = self._db.proposals.get_proposal(proposal_id)
        if proposal is None or proposal.state != "proposed":
            return {"error": "Proposal not found or already decided"}

        dismissed = self._db.proposals.dismiss_proposal(proposal_id)
        if dismissed is None:
            return {"error": "Failed to dismiss proposal"}

        # Receipt for the dismissal.
        with self._db._connection() as conn:
            ServiceEventLedger(self._db).append_in_transaction(
                conn, principal,
                event_type="proposal.dismissed",
                producer="ProposalBridgeService",
                subject_ref=f"proposal:{proposal_id}",
                source_revision="",
                facts={
                    "proposal_id": proposal_id,
                    "kind": proposal.kind,
                    "text": proposal.text,
                },
                refs=[f"proposal:{proposal_id}"],
                correlation_id=current_correlation_id(),
                causation_id=f"proposal:{proposal_id}",
            )

        return {"proposal_id": proposal_id, "state": "dismissed"}

    def list_meeting_proposals(
        self,
        meeting_id: str,
        state: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List proposals for a meeting."""
        proposals = self._db.proposals.list_proposals(
            meeting_id=meeting_id, state=state,
        )
        return [self._serialize(p) for p in proposals]

    def list_project_proposals(
        self,
        project_id: str,
        state: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List proposals for a project (via meeting_projects)."""
        proposals = self._db.proposals.list_proposals(
            project_id=project_id, state=state,
        )
        return [self._serialize(p) for p in proposals]

    @staticmethod
    def _serialize(p: Proposal) -> dict[str, Any]:
        return {
            "id": p.id,
            "meeting_id": p.meeting_id,
            "project_id": p.project_id,
            "kind": p.kind,
            "text": p.text,
            "owner_hint": p.owner_hint,
            "due_hint": p.due_hint,
            "source_artifact_id": p.source_artifact_id,
            "source_plugin": p.source_plugin,
            "segment_timestamp": p.segment_timestamp,
            "speaker_label": p.speaker_label,
            "model_host": p.model_host,
            "state": p.state,
            "original_text": p.original_text,
            "created_at": p.created_at,
            "decided_at": p.decided_at,
        }

    @staticmethod
    def _project_key(project_id: Optional[str]) -> Optional[str]:
        """The project_id serves as project_key in the decisions table."""
        return project_id or None
