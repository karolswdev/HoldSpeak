"""Principal-aware desk actuator proposal boundary."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
import re
from typing import Any, Callable

from ..principals import Principal
from .errors import NotFound, ValidationError

_REPO = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


@observe_service
class ActuatorProposalService:
    """Own desk proposal validation, provenance, and lifecycle delegation.

    The injected lifecycle collaborator owns connector execution and is deliberately
    transport-neutral: it receives a proposal and broadcaster, never a request.
    """
    def __init__(self, db: Any, config_provider: Callable[[], Any], broadcast: Callable[[str, Any], None], lifecycle: Any, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._config_provider = config_provider
        self._broadcast = broadcast
        self._lifecycle = lifecycle
        self._observer = observer or NullObserver()

    def _source_binding(self, payload: Any) -> tuple[str, dict[str, Any]]:
        raw = str(getattr(payload, "source_ref", "") or "").strip()
        if not raw: return "", {}
        from ..db.relationships import qualified_ref
        source_ref = qualified_ref(raw); kind, identifier = source_ref.split(":", 1)
        source = {"meeting": self._db.meetings.get_meeting, "note": self._db.notes.get,
                  "artifact": self._db.plugins.get_artifact}.get(kind)
        if source is None: raise ValidationError("source_ref must identify a Meeting, Note, or Artifact")
        value = source(identifier)
        if value is None: raise ValidationError(f"Unknown {kind.title()} source: {identifier}")
        label = str(value.title or identifier).strip()[:160]
        return source_ref, {"_source": {"ref": source_ref, "label": label or identifier}}

    def _propose(self, principal: Principal, payload: Any, *, target: str) -> dict[str, Any]:
        text = str(getattr(payload, "text", "") or "").strip()
        if not text: raise ValidationError("text is required")
        config = self._config_provider(); meeting = config.meeting
        configured = {"slack": meeting.slack_webhook_url, "webhook": meeting.companion_webhook_url,
                      "github": meeting.companion_github_repo}[target]
        repo = ""
        if target == "github":
            repo = str(getattr(payload, "repo", "") or "").strip() or str(configured or "").strip()
            if not repo: raise ValidationError("No GitHub repo (set companion_github_repo on the host, or pass repo)")
            if not _REPO.match(repo): raise ValidationError("repo must be of the form owner/name")
        elif not configured:
            label = "Slack" if target == "slack" else "Webhook"
            raise ValidationError(f"{label} is not configured on the host")
        source_ref, source_payload = self._source_binding(payload)
        title = str(getattr(payload, "title", "") or "").strip()
        if target == "github":
            title = title or text.splitlines()[0][:72]
            preview = f"Open a GitHub issue in {repo}: “{title}”"
            body = text; key_material = f"{repo}|{title}|{text}"; action = "create_issue"
            from ..plugins.builtin.github_issue_actuator import GithubIssueActuator as plugin
            proposal_payload = {"repo": repo, "title": title, "body": text, **source_payload}
        else:
            body = f"*{title}*\n{text}" if title else text; preview = body; key_material = body; action = "post_message"
            from ..plugins.builtin.webhook_post_actuator import WebhookPostActuator as plugin
            proposal_payload = {"body": {"text": body}, **source_payload}
        key = hashlib.sha256(key_material.encode()).hexdigest()[:16]
        proposal = self._db.actuators.record_proposal(meeting_id=None, origin="desk", window_id=source_ref or f"companion:{target}",
            plugin_id=plugin.id, plugin_version=plugin.version, idempotency_key=f"companion-{target}:{source_ref + ':' if source_ref else ''}{key}",
            target=target, action=action, preview=preview, payload=proposal_payload, reversible=False,
            required_capabilities=["actuator"], control_mode=config.control_mode,
            fixed_destination=bool(target != "github" or (configured and repo == configured)))
        self._broadcast("actuator_proposed", {"id": proposal.id, "meeting_id": proposal.meeting_id,
            "plugin_id": proposal.plugin_id, "status": proposal.status, "target": proposal.target,
            "action": proposal.action, "preview": proposal.preview, "reversible": bool(proposal.reversible)})
        proposal = self._lifecycle.apply(proposal, target)
        return {"success": True, "proposal": self._lifecycle.serialize(proposal)}

    def propose_slack(self, principal: Principal, payload: Any) -> dict[str, Any]: return self._propose(principal, payload, target="slack")
    def propose_webhook(self, principal: Principal, payload: Any) -> dict[str, Any]: return self._propose(principal, payload, target="webhook")
    def propose_github(self, principal: Principal, payload: Any) -> dict[str, Any]: return self._propose(principal, payload, target="github")

    def _decide(self, principal: Principal, proposal_id: str, payload: Any, *, target: str) -> dict[str, Any]:
        updated, error, status = self._lifecycle.decide(proposal_id, payload, target)
        if error:
            if status == 404: raise NotFound("proposal", proposal_id)
            raise ValidationError(error)
        return {"success": True, "proposal": self._lifecycle.serialize(updated)}
    def decide_slack(self, principal: Principal, proposal_id: str, payload: Any) -> dict[str, Any]: return self._decide(principal, proposal_id, payload, target="slack")
    def decide_webhook(self, principal: Principal, proposal_id: str, payload: Any) -> dict[str, Any]: return self._decide(principal, proposal_id, payload, target="webhook")
    def decide_github(self, principal: Principal, proposal_id: str, payload: Any) -> dict[str, Any]: return self._decide(principal, proposal_id, payload, target="github")
