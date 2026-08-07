"""Transport-neutral meeting aftercare and proposal operations."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
from typing import Any, Callable

from ..config import Config
from ..db.core import Database
from ..meeting_aftercare import build_followup_draft, compute_meeting_aftercare
from ..plugins.builtin.github_issue_actuator import GithubIssueActuator, build_github_issue_proposal
from ..plugins.builtin.webhook_post_actuator import WebhookPostActuator
from ..principals import Principal
from ..slack_export import EXPORT_KINDS, slack_message_for
from .errors import ConflictError, NotFound, ValidationError


@observe_service
class MeetingAftercareService:
    """Own aftercare projections and the durable proposal lifecycle."""

    def __init__(self, db: Database, notify: Callable[[str, Any], None] | None = None, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._notify = notify
        self._observer = observer or NullObserver()

    def _emit(self, topic: str, value: Any) -> None:
        if self._notify:
            self._notify(topic, value)

    @staticmethod
    def proposal_payload(proposal: Any) -> dict[str, Any]:
        from ..operation_policy import OperationDescriptor, commitment_labels, operation_for_proposal
        operation = getattr(proposal, "operation", None) or operation_for_proposal(proposal).to_dict()
        descriptor = OperationDescriptor(operation_id=str(operation.get("operation_id") or f"actuator:{proposal.id}"), family=str(operation.get("family") or "external_write"), effect_class=str(operation.get("effect_class") or f"{proposal.target}/{proposal.action}"), actor=str(operation.get("actor") or "owner"), destination=str(operation.get("destination") or proposal.target), data_classes=tuple(operation.get("data_classes") or []), project_scope=operation.get("project_scope"), resource_scope=operation.get("resource_scope"), fixed_destination=bool(operation.get("fixed_destination")), consequence=str(operation.get("consequence") or "execute_now"), version=int(operation.get("version") or 1))
        return {"id": proposal.id, "origin": getattr(proposal, "origin", "meeting"), "meeting_id": proposal.meeting_id, "window_id": proposal.window_id, "plugin_id": proposal.plugin_id, "plugin_version": proposal.plugin_version, "status": proposal.status, "review_decision": getattr(proposal, "review_decision", "unreviewed"), "authorization_state": getattr(proposal, "authorization_state", "proposed"), "execution_state": getattr(proposal, "execution_state", "not_started"), "target": proposal.target, "action": proposal.action, "preview": proposal.preview, "payload": proposal.payload, "reversible": proposal.reversible, "required_capabilities": proposal.required_capabilities, "decided_by": proposal.decided_by, "authority": {"payload_hash": proposal.approved_payload_hash, "destination": proposal.approved_destination, "preview_hash": proposal.approved_preview_hash, "preview_renderer_version": proposal.preview_renderer_version, "effect_class": proposal.effect_class, "policy_version": proposal.policy_version} if proposal.approved_payload_hash else None, "operation": operation, "policy_snapshot": getattr(proposal, "policy_snapshot", {}), "grant_id": getattr(proposal, "grant_id", None), "commitment": commitment_labels(descriptor), "result": proposal.result, "error": proposal.error, "created_at": proposal.created_at, "decided_at": proposal.decided_at, "executed_at": proposal.executed_at}

    def get_aftercare(self, principal: Principal, meeting_id: str) -> dict[str, Any]:
        digest = compute_meeting_aftercare(self._db, meeting_id)
        if digest is None:
            raise NotFound("meeting", meeting_id)
        digest["slack_configured"] = bool(Config.load().meeting.slack_webhook_url)
        return digest

    def get_followup_draft(self, principal: Principal, meeting_id: str) -> dict[str, Any]:
        digest = compute_meeting_aftercare(self._db, meeting_id)
        if digest is None:
            raise NotFound("meeting", meeting_id)
        return {"meeting_id": meeting_id, "markdown": build_followup_draft(digest), "is_empty": digest["is_empty"]}

    def list_proposals(self, principal: Principal, meeting_id: str, status: str | None = None) -> dict[str, Any]:
        if self._db.meetings.get_meeting(meeting_id) is None:
            raise NotFound("meeting", meeting_id)
        return {"meeting_id": meeting_id, "proposals": [self.proposal_payload(p) for p in self._db.actuators.list_proposals(meeting_id, status=status)]}

    def _proposed_event(self, proposal: Any) -> dict[str, Any]:
        return {"id": proposal.id, "meeting_id": proposal.meeting_id, "plugin_id": proposal.plugin_id, "status": proposal.status, "target": proposal.target, "action": proposal.action, "preview": proposal.preview, "reversible": bool(proposal.reversible), "created_at": proposal.created_at.isoformat() if hasattr(proposal.created_at, "isoformat") else proposal.created_at}

    def _result_event(self, proposal: Any) -> dict[str, Any]:
        return {"id": proposal.id, "meeting_id": proposal.meeting_id, "status": proposal.status, "target": proposal.target, "action": proposal.action, "preview": proposal.preview, "reversible": bool(proposal.reversible), "policy": getattr(proposal, "policy_snapshot", {}), "error": proposal.error}

    def _execute_slack(self, proposal: Any, actor: str) -> Any:
        from ..plugins.actuator_executor import ActuatorExecutor
        from ..slack_export import build_slack_connector
        url = Config.load().meeting.slack_webhook_url
        if not url:
            updated = self._db.actuators.transition_proposal(proposal.id, to_status="failed", actor=actor, detail="slack export: no webhook URL configured at execution time", error="Slack is not configured (meeting.slack_webhook_url is empty)")
            self._emit("actuator_result", self._result_event(updated))
            return updated
        executor = ActuatorExecutor(self._db, connector=build_slack_connector(url), allow_actuators=True, actor=actor, on_result=lambda event: self._emit("actuator_result", event))
        return executor.execute(proposal.id)

    def decide_proposal(self, principal: Principal, meeting_id: str, proposal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        decision = str(payload.get("decision") or "").strip().lower()
        if decision not in {"approved", "rejected"}:
            raise ValidationError(f"Invalid decision: {payload.get('decision')!r}")
        proposal = self._db.actuators.get_proposal(proposal_id)
        if proposal is None or proposal.origin != "meeting" or proposal.meeting_id != meeting_id:
            raise NotFound("proposal", proposal_id)
        try:
            policy_snapshot = None
            if decision == "approved":
                from ..operation_policy import operation_for_proposal, resolve_policy
                grant_id = payload.get("grant_id")
                grant_record = self._db.actuators.get_grant(grant_id) if grant_id else None
                captured = dict(getattr(proposal, "policy_snapshot", {}) or {})
                if captured.get("outcome") == "refused":
                    raise ValueError("captured operation policy refuses this unregistered effect")
                policy = resolve_policy(operation_for_proposal(proposal, actor=str(payload.get("decided_by") or "web-user").strip() or "web-user"), mode=str(captured.get("mode") or "neutral"), source=str(captured.get("source") or "config"), grant=grant_record.to_dict() if grant_record else None, explicit_authorization=not bool(grant_id))
                if grant_id and policy.authority_basis != "scoped_grant":
                    raise ValueError("scoped grant is not active for this exact operation and mode")
                if policy.outcome != "allowed":
                    raise ValueError("captured operation policy does not authorize this effect")
                policy_snapshot = policy.to_dict()
            actor = str(payload.get("decided_by") or "web-user").strip() or "web-user"
            updated = self._db.actuators.transition_proposal(proposal_id, to_status=decision, actor=actor, policy_snapshot=policy_snapshot, grant_id=payload.get("grant_id"))
        except ValueError as exc:
            raise ValidationError(str(exc), code="illegal_transition") from exc
        if decision == "rejected": self._emit("actuator_result", self._result_event(updated))
        if decision == "approved" and updated.target == "slack": updated = self._execute_slack(updated, actor)
        return {"success": True, "proposal": self.proposal_payload(updated)}

    def file_issue(self, principal: Principal, meeting_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        repo = str(payload.get("repo") or "").strip()
        if not repo: raise ValidationError("A target repo (owner/name) is required")
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None: raise NotFound("meeting", meeting_id)
        item = self._db.meetings.get_action_item(payload.get("action_item_id"))
        if item is None or item.meeting_id != meeting_id: raise NotFound("action item", str(payload.get("action_item_id") or ""))
        if item.review_state != "accepted": raise ValidationError("Only an accepted action item can be filed as an issue")
        spec = build_github_issue_proposal(task=item.task, owner=item.owner, due=item.due, meeting_title=meeting.title or "meeting", repo=repo)
        proposal = self._db.actuators.record_proposal(meeting_id=meeting_id, window_id=f"{meeting_id}:aftercare", plugin_id=GithubIssueActuator.id, plugin_version=GithubIssueActuator.version, idempotency_key=f"aftercare-issue:{meeting_id}:{item.id}", target=spec["target"], action=spec["action"], preview=spec["preview"], payload=spec["payload"], reversible=spec["reversible"], required_capabilities=spec["required_capabilities"], control_mode=Config.load().control_mode, fixed_destination=False)
        self._emit("actuator_proposed", self._proposed_event(proposal))
        return {"success": True, "proposal": self.proposal_payload(proposal)}

    def export_slack(self, principal: Principal, meeting_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        what = str(payload.get("what") or "").strip().lower()
        if what not in EXPORT_KINDS: raise ValidationError(f"Unknown export kind: {what!r} (expected 'digest' or 'followup')")
        digest = compute_meeting_aftercare(self._db, meeting_id)
        if digest is None: raise NotFound("meeting", meeting_id)
        config = Config.load()
        if not config.meeting.slack_webhook_url: raise ValidationError("Slack is not configured (set the webhook URL in Settings first)")
        if digest.get("is_empty"): raise ValidationError("This meeting has nothing open, decided, or changed to send")
        text = slack_message_for(digest, what); content_key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        proposal = self._db.actuators.record_proposal(meeting_id=meeting_id, window_id=f"{meeting_id}:aftercare", plugin_id=WebhookPostActuator.id, plugin_version=WebhookPostActuator.version, idempotency_key=f"slack-export:{meeting_id}:{what}:{content_key}", target="slack", action="post_message", preview=text, payload={"body": {"text": text}}, reversible=False, required_capabilities=["actuator"], control_mode=config.control_mode, fixed_destination=True)
        self._emit("actuator_proposed", self._proposed_event(proposal))
        # Fixed-destination posture authorization is deliberately captured at creation.
        policy = dict(getattr(proposal, "policy_snapshot", {}) or {})
        if proposal.status == "proposed" and policy.get("outcome") == "allowed" and policy.get("authority_basis") == "control_posture":
            proposal = self._db.actuators.transition_proposal(proposal.id, to_status="approved", actor=f"control-posture:{policy.get('mode') or 'unknown'}", detail="configured operation authorized by captured control posture", policy_snapshot=policy)
            proposal = self._execute_slack(proposal, f"control-posture:{policy.get('mode') or 'unknown'}")
        return {"success": True, "proposal": self.proposal_payload(proposal)}
