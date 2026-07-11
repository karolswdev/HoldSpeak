"""The desk actuator relay — /api/desk/actuators/* (Phase 72, was /api/companion/*).

HSM-14: the iPad desk routes a connector send through the HOST's actuator
framework. The desk holds NO credential; it proposes arbitrary text, the host
executes with the credential joined in memory at execution time. Same
propose → approve → execute as Phase 61.

Moved out of ``meetings.py`` and off the ``/api/companion/*`` prefix, which
this repo now reserves for exactly one concept (nothing — the coder session
picker lives at ``/api/coders/*``, this relay lives here, and "companion" as
a concept name is retired from the API surface). Handler behavior is
byte-identical to the moved routes.

Desk proposals are owner-typed (v5, Phase 72): `origin='desk'` with
`meeting_id=NULL`. The old `_COMPANION_MEETING_ID` sentinel meeting (a fake
row that satisfied the proposals FK) is gone; the v5 migration re-types the
old rows and deletes the sentinel.
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...web_requests import _CompanionSlackRequest, _ProposalDecisionRequest
from ..context import WebContext
from ..runtime_support import error_500
from .actuator_shared import (
    decide_proposal,
    execute_github_proposal,
    execute_slack_proposal,
    execute_webhook_proposal,
    proposal_to_dict,
)

log = get_logger("web.routes.desk_actuators")

_COMPANION_GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def build_desk_actuators_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/desk/actuators/status")
    async def api_desk_actuators_status() -> Any:
        """Which desk connectors are configured (HS-77-03).

        Booleans only — the URLs are credentials and never ride a payload.
        This lived on /api/coders/status as a residual conflation (a coder
        is a live coding session; connector config is the actuator
        domain's); the domain owns its own status now.
        """
        try:
            from ...config import Config

            mc = Config.load().meeting
            return {
                "slack_configured": bool(mc.slack_webhook_url),
                "webhook_configured": bool(mc.companion_webhook_url),
                "github_configured": bool(mc.companion_github_repo),
            }
        except Exception:
            return {
                "slack_configured": False,
                "webhook_configured": False,
                "github_configured": False,
            }

    @router.post("/api/desk/actuators/slack/propose")
    async def api_desk_slack_propose(payload: _CompanionSlackRequest) -> Any:
        """Propose sending arbitrary desk text to Slack (HSM-14).

        A non-meeting-scoped sibling of the aftercare Slack export: the iPad
        drops a generated card onto its Slack connector, and that becomes a
        `proposed` actuator proposal here. The preview IS the exact message
        body; the webhook URL is never accepted from or returned to the
        desk — it stays on the host, joined at execution time only.
        """
        import hashlib

        from ...config import Config

        text = str(payload.text or "").strip()
        if not text:
            return JSONResponse({"success": False, "error": "text is required"}, status_code=400)
        if not Config.load().meeting.slack_webhook_url:
            return JSONResponse(
                {"success": False, "error": "Slack is not configured on the host (set the webhook URL in Settings first)"},
                status_code=400,
            )
        try:
            from ...db import get_database
            from ...plugins.builtin.webhook_post_actuator import WebhookPostActuator

            db = get_database()
            body = f"*{payload.title.strip()}*\n{text}" if (payload.title or "").strip() else text
            content_key = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            proposal = db.actuators.record_proposal(
                meeting_id=None,
                origin="desk",
                window_id="companion:slack",
                plugin_id=WebhookPostActuator.id,
                plugin_version=WebhookPostActuator.version,
                idempotency_key=f"companion-slack:{content_key}",
                target="slack",
                action="post_message",
                preview=body,
                payload={"body": {"text": body}},
                reversible=False,
                required_capabilities=["actuator"],
            )
            ctx.broadcast(
                "actuator_proposed",
                {
                    "id": proposal.id,
                    "meeting_id": proposal.meeting_id,
                    "plugin_id": proposal.plugin_id,
                    "status": proposal.status,
                    "target": proposal.target,
                    "action": proposal.action,
                    "preview": proposal.preview,
                    "reversible": bool(proposal.reversible),
                },
            )
            return JSONResponse({"success": True, "proposal": proposal_to_dict(proposal)})
        except Exception as e:
            return error_500(e, log, "Failed to propose desk Slack send")

    @router.post("/api/desk/actuators/slack/{proposal_id}/decision")
    async def api_decide_desk_slack(
        proposal_id: str, payload: _ProposalDecisionRequest
    ) -> Any:
        """Approve (→ execute) or reject a desk Slack proposal (HSM-14).

        Mirrors the meeting decision route but scoped to desk proposals.
        Approving a `slack` proposal executes immediately through the full
        guarded executor (status gate, payload parity, manifest allow-list),
        with the webhook URL injected in memory by the connector — never on the
        proposal, never returned.
        """
        try:
            from ...db import get_database

            updated, err, status = decide_proposal(
                ctx, get_database(), proposal_id,
                decision=payload.decision,
                actor=(payload.decided_by or "companion").strip() or "companion",
                belongs=lambda p: p.origin == "desk" and p.target == "slack",
                executors={"slack": execute_slack_proposal},
                grant_id=payload.grant_id,
            )
            if err is not None:
                return JSONResponse({"success": False, "error": err}, status_code=status)
            return JSONResponse({"success": True, "proposal": proposal_to_dict(updated)})
        except Exception as e:
            return error_500(e, log, "Failed to decide desk Slack proposal")

    @router.post("/api/desk/actuators/webhook/propose")
    async def api_desk_webhook_propose(payload: _CompanionSlackRequest) -> Any:
        """Propose sending arbitrary desk text to a generic webhook (HSM-14).

        The generic sibling of the Slack propose — same shape, target `webhook`,
        gated on `meeting.companion_webhook_url`. No credential crosses.
        """
        import hashlib

        from ...config import Config

        text = str(payload.text or "").strip()
        if not text:
            return JSONResponse({"success": False, "error": "text is required"}, status_code=400)
        if not Config.load().meeting.companion_webhook_url:
            return JSONResponse(
                {"success": False, "error": "Webhook is not configured on the host (set companion_webhook_url first)"},
                status_code=400,
            )
        try:
            from ...db import get_database
            from ...plugins.builtin.webhook_post_actuator import WebhookPostActuator

            db = get_database()
            body = f"*{payload.title.strip()}*\n{text}" if (payload.title or "").strip() else text
            content_key = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            proposal = db.actuators.record_proposal(
                meeting_id=None, origin="desk", window_id="companion:webhook",
                plugin_id=WebhookPostActuator.id, plugin_version=WebhookPostActuator.version,
                idempotency_key=f"companion-webhook:{content_key}",
                target="webhook", action="post_message", preview=body,
                payload={"body": {"text": body}}, reversible=False, required_capabilities=["actuator"],
            )
            ctx.broadcast("actuator_proposed", {
                "id": proposal.id, "meeting_id": proposal.meeting_id, "plugin_id": proposal.plugin_id,
                "status": proposal.status, "target": proposal.target, "action": proposal.action,
                "preview": proposal.preview, "reversible": bool(proposal.reversible),
            })
            return JSONResponse({"success": True, "proposal": proposal_to_dict(proposal)})
        except Exception as e:
            return error_500(e, log, "Failed to propose desk webhook send")

    @router.post("/api/desk/actuators/webhook/{proposal_id}/decision")
    async def api_decide_desk_webhook(proposal_id: str, payload: _ProposalDecisionRequest) -> Any:
        """Approve (→ execute) or reject a desk Webhook proposal (HSM-14)."""
        try:
            from ...db import get_database

            updated, err, status = decide_proposal(
                ctx, get_database(), proposal_id,
                decision=payload.decision,
                actor=(payload.decided_by or "companion").strip() or "companion",
                belongs=lambda p: p.origin == "desk" and p.target == "webhook",
                executors={"webhook": execute_webhook_proposal},
                grant_id=payload.grant_id,
            )
            if err is not None:
                return JSONResponse({"success": False, "error": err}, status_code=status)
            return JSONResponse({"success": True, "proposal": proposal_to_dict(updated)})
        except Exception as e:
            return error_500(e, log, "Failed to decide desk webhook proposal")

    @router.post("/api/desk/actuators/github/propose")
    async def api_desk_github_propose(payload: _CompanionSlackRequest) -> Any:
        """Propose filing a desk card as a GitHub issue (HSM-14).

        target `github`, action `create_issue`; the payload carries `{repo, title,
        body}` — exactly what the Phase-38 `gh issue create` connector consumes on
        approval. The repo is the request's or the host's `companion_github_repo`.
        """
        import hashlib

        from ...config import Config

        text = str(payload.text or "").strip()
        if not text:
            return JSONResponse({"success": False, "error": "text is required"}, status_code=400)
        repo = str(payload.repo or "").strip() or str(Config.load().meeting.companion_github_repo or "").strip()
        if not repo:
            return JSONResponse(
                {"success": False, "error": "No GitHub repo (set companion_github_repo on the host, or pass repo)"},
                status_code=400,
            )
        if not _COMPANION_GITHUB_REPO_RE.match(repo):
            return JSONResponse(
                {"success": False, "error": "repo must be of the form owner/name"},
                status_code=400,
            )
        try:
            from ...db import get_database
            from ...plugins.builtin.github_issue_actuator import GithubIssueActuator

            db = get_database()
            title = str(payload.title or "").strip() or (text.splitlines()[0][:72] if text else "Desk issue")
            preview = f"Open a GitHub issue in {repo}: “{title}”"
            content_key = hashlib.sha256(f"{repo}|{title}|{text}".encode("utf-8")).hexdigest()[:16]
            proposal = db.actuators.record_proposal(
                meeting_id=None, origin="desk", window_id="companion:github",
                plugin_id=GithubIssueActuator.id, plugin_version=GithubIssueActuator.version,
                idempotency_key=f"companion-github:{content_key}",
                target="github", action="create_issue", preview=preview,
                payload={"repo": repo, "title": title, "body": text}, reversible=False,
                required_capabilities=["actuator"],
            )
            ctx.broadcast("actuator_proposed", {
                "id": proposal.id, "meeting_id": proposal.meeting_id, "plugin_id": proposal.plugin_id,
                "status": proposal.status, "target": proposal.target, "action": proposal.action,
                "preview": proposal.preview, "reversible": bool(proposal.reversible),
            })
            return JSONResponse({"success": True, "proposal": proposal_to_dict(proposal)})
        except Exception as e:
            return error_500(e, log, "Failed to propose desk GitHub issue")

    @router.post("/api/desk/actuators/github/{proposal_id}/decision")
    async def api_decide_desk_github(proposal_id: str, payload: _ProposalDecisionRequest) -> Any:
        """Approve (→ file the issue) or reject a desk GitHub proposal (HSM-14)."""
        try:
            from ...db import get_database

            updated, err, status = decide_proposal(
                ctx, get_database(), proposal_id,
                decision=payload.decision,
                actor=(payload.decided_by or "companion").strip() or "companion",
                belongs=lambda p: p.origin == "desk" and p.target == "github",
                executors={"github": execute_github_proposal},
                grant_id=payload.grant_id,
            )
            if err is not None:
                return JSONResponse({"success": False, "error": err}, status_code=status)
            return JSONResponse({"success": True, "proposal": proposal_to_dict(updated)})
        except Exception as e:
            return error_500(e, log, "Failed to decide desk GitHub proposal")

    return router
