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
        model_host: str | None = None,
    ) -> list[Proposal]:
        """Read extractor artifacts for a meeting, create proposals.

        Returns the newly created proposals (empty if all were deduped).
        ``model_host`` defaults to the recorded host on the intel job row;
        never resolved from config in the read path.
        """
        created: list[Proposal] = []

        # HS-172-02: read the recorded host from the job row.
        if model_host is None:
            model_host = self._db.intel.get_intel_job_model_host(meeting_id)

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
        """Confirm a proposal: write decision_record + commitment through the kernel.

        Both decision-kind and action-kind create the full chain:
        decisions -> decision_records (+ sources) -> action_items -> decision_commitments
        so the Room's DECISIONS & COMMITMENTS reads see them.
        """
        proposal = self._db.proposals.get_proposal(proposal_id)
        if proposal is None or proposal.state != "proposed":
            return {"error": "Proposal not found or already decided"}

        final_text = text or proposal.text
        final_owner = owner or proposal.owner_hint
        final_due = due or proposal.due_hint
        now = datetime.now().isoformat()

        decision_id = f"dec-{uuid.uuid4().hex[:16]}"
        record_id = f"record-{uuid.uuid4().hex[:16]}"
        record_source_id = f"record-source-{uuid.uuid4().hex[:16]}"
        action_id = f"action-{uuid.uuid4().hex[:16]}"
        commitment_id = f"commitment-{uuid.uuid4().hex[:16]}"

        with self._db._connection() as conn:
            # 1. decisions row (raw meeting decision, lifecycle=accepted).
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

            # 2. decision_records row (the durable canon the Room reads).
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, rationale, alternatives, owner,
                    review_date, lifecycle, source_type, source_id,
                    created_at, updated_at)
                   VALUES (?, ?, '', '', ?, '', 'active', 'meeting', ?,
                           ?, ?)""",
                (record_id, final_text, final_owner, decision_id, now, now),
            )

            # 3. decision_record_sources linking to the meeting.
            conn.execute(
                """INSERT INTO decision_record_sources
                   (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', ?, ?)""",
                (record_source_id, record_id, proposal.meeting_id, now),
            )

            # 4. action_items row.
            delegated_at = now if final_owner else None
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

            # 5. decision_commitments linking decision to action_item.
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 'open', ?, ?)""",
                (commitment_id, decision_id, action_id, final_owner, final_due, now, now),
            )

            # Kernel receipt (Article XI).
            ServiceEventLedger(self._db).append_in_transaction(
                conn, principal,
                event_type="proposal.confirmed",
                producer="ProposalBridgeService",
                subject_ref=f"proposal:{proposal_id}",
                source_revision=record_id,
                facts={
                    "proposal_id": proposal_id,
                    "kind": proposal.kind,
                    "decision_id": decision_id,
                    "decision_record_id": record_id,
                    "action_item_id": action_id,
                    "commitment_id": commitment_id,
                    "text": final_text,
                    "original_text": proposal.original_text,
                    "owner": final_owner,
                    "due": final_due,
                },
                refs=[
                    f"proposal:{proposal_id}",
                    f"decision:{decision_id}",
                    f"decision_record:{record_id}",
                    f"action_item:{action_id}",
                    f"commitment:{commitment_id}",
                ],
                correlation_id=current_correlation_id(),
                causation_id=f"proposal:{proposal_id}",
            )

        # Update the proposal row with the record/commitment ids.
        # owner_hint and due_hint stay as extraction originals for was{}.
        self._db.proposals.confirm_proposal(
            proposal_id,
            text=text,
            decision_record_id=record_id,
            commitment_id=commitment_id,
        )

        # HS-172-03: dirty marker so the needs-you cache refreshes.
        try:
            from .needs_you_aggregate import mark_needs_you_dirty
            mark_needs_you_dirty(self._db)
        except Exception:
            pass

        return {
            "proposal_id": proposal_id,
            "state": "confirmed",
            "original_text": proposal.original_text,
            "decision_id": decision_id,
            "decision_record_id": record_id,
            "action_item_id": action_id,
            "commitment_id": commitment_id,
        }

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

        # HS-172-03: dirty marker so the needs-you cache refreshes.
        try:
            from .needs_you_aggregate import mark_needs_you_dirty
            mark_needs_you_dirty(self._db)
        except Exception:
            pass

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
            "decision_record_id": p.decision_record_id,
            "commitment_id": p.commitment_id,
            "created_at": p.created_at,
            "decided_at": p.decided_at,
        }

    @staticmethod
    def _project_key(project_id: Optional[str]) -> Optional[str]:
        """The project_id serves as project_key in the decisions table."""
        return project_id or None
