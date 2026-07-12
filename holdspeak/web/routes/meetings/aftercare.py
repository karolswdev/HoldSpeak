"""Meeting aftercare routes: digest, follow-up draft, and the actuator
propose -> approve -> execute endpoints (proposals, decision, file-issue,
Slack export).
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import (
    _AftercareFileIssueRequest,
    _ProposalDecisionRequest,
    _SlackExportRequest,
)
from ...runtime_support import error_500
from ...context import WebContext
from .. import actuator_shared

log = get_logger("web.routes.meetings")

# A companion-supplied GitHub repo must be `owner/name` — same shape the host
# config path validates (system.py `_GITHUB_REPO_RE`). A malformed repo from an
# iPad would otherwise land in the proposal payload and the `gh issue create`
# argv unchecked.

# HSM-14: the runner the companion GitHub connector uses for `gh issue create`.
# None = production `subprocess.run` (the host's local, authenticated `gh`); tests
# inject a fake so the suite never shells out.


def build_aftercare_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/meetings/{meeting_id}/aftercare")
    async def api_get_meeting_aftercare(meeting_id: str) -> Any:
        """Read-only aftercare digest for one meeting (HS-49-01).

        Aggregates what's still open (by owner), what was decided, and a real
        diff against the chronologically previous meeting. Pure read — no writes,
        no side effects. Returns `is_empty` so the surface can stay quiet when
        there is nothing open, nothing decided, and nothing changed.
        """
        try:
            from ....db import get_database
            from ....meeting_aftercare import compute_meeting_aftercare

            db = get_database()
            digest = compute_meeting_aftercare(db, meeting_id)
            if digest is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)
            # HS-61-02: the capability flag the Send-to-Slack buttons gate on.
            # A bool only — the webhook URL is a credential and never rides
            # an aftercare response.
            from ....config import Config

            digest["slack_configured"] = bool(
                Config.load().meeting.slack_webhook_url
            )
            return JSONResponse(digest)
        except Exception as e:
            return error_500(e, log, "Failed to load meeting aftercare")

    @router.get("/api/meetings/{meeting_id}/followup-draft")
    async def api_get_meeting_followup_draft(meeting_id: str) -> Any:
        """A local, copyable follow-up draft for one meeting (HS-49-04).

        Assembled deterministically from the aftercare digest — decisions, open
        items by owner, and the since-last-meeting delta. Preview + copy only:
        nothing is sent and no connector is opened. Honest when there's little to
        say (no padding). Pure read; 404 for an unknown meeting.
        """
        try:
            from ....db import get_database
            from ....meeting_aftercare import build_followup_draft, compute_meeting_aftercare

            db = get_database()
            digest = compute_meeting_aftercare(db, meeting_id)
            if digest is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "markdown": build_followup_draft(digest),
                    "is_empty": digest["is_empty"],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to build meeting follow-up draft")

    # Phase 72: the actuator-lifecycle helpers live in actuator_shared (one
    # implementation for the meeting routes AND the desk relay). These local
    # names keep the existing call sites; ctx is bound here.
    # Phase 72: the lifecycle lives in actuator_shared; only the dict shape
    # is consumed here (the decision route calls decide_proposal directly).
    _proposal_to_dict = actuator_shared.proposal_to_dict

    @router.get("/api/meetings/{meeting_id}/proposals")
    async def api_get_meeting_proposals(
        meeting_id: str,
        status: Optional[str] = None,
    ) -> Any:
        """List actuator proposals for one meeting (HS-37-03).

        A pure DB read — viewing a proposal performs **no** side effect.
        """
        try:
            from ....db import get_database

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)

            proposals = db.actuators.list_proposals(meeting_id, status=status)
            return JSONResponse(
                {
                    "meeting_id": meeting_id,
                    "proposals": [_proposal_to_dict(p) for p in proposals],
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to load meeting proposals")

    @router.post("/api/meetings/{meeting_id}/proposals/{proposal_id}/decision")
    async def api_decide_meeting_proposal(
        meeting_id: str,
        proposal_id: str,
        payload: _ProposalDecisionRequest,
    ) -> Any:
        """Approve or reject an actuator proposal (HS-37-03).

        Approving only flips DB state to `approved` (+ `decided_by` + an audit
        entry); it performs **no** side effect — execution is HS-37-04. Rejecting
        is terminal. Illegal decisions (e.g. on an already-executed proposal)
        return 400.
        """
        try:
            from ....db import get_database

            # Phase 72: the ONE decision lifecycle (validate -> scope-check ->
            # audited transition -> terminal-rejection broadcast -> execute-on-
            # approve). Slack executes on approval (HS-61-01 consent reasoning,
            # see actuator_shared.execute_slack_proposal); other targets keep
            # the Phase-37 behavior (approval flips state only).
            updated, err, status = actuator_shared.decide_proposal(
                ctx, get_database(), proposal_id,
                decision=payload.decision,
                actor=(payload.decided_by or "web-user").strip() or "web-user",
                belongs=lambda p: p.origin == "meeting" and p.meeting_id == meeting_id,
                executors={"slack": actuator_shared.execute_slack_proposal},
                grant_id=payload.grant_id,
            )
            if err is not None:
                return JSONResponse({"success": False, "error": err}, status_code=status)
            return JSONResponse({"success": True, "proposal": _proposal_to_dict(updated)})
        except Exception as e:
            return error_500(e, log, "Failed to decide meeting proposal")

    @router.post("/api/meetings/{meeting_id}/aftercare/file-issue")
    async def api_aftercare_file_issue(
        meeting_id: str, payload: _AftercareFileIssueRequest
    ) -> Any:
        """Turn an accepted action item into a GitHub-issue actuator proposal (HS-49-03).

        Closing the loop reuses the existing propose -> approve -> execute flow:
        this records a `proposed` proposal only. Nothing leaves the machine here —
        Secure and Normal still require a bounded authority decision, while YOLO
        refuses this ad-hoc destination because it is not host-configured. The
        executor also requires `allow_actuators`, the per-project allow-list, and
        a host-injected connector. No new write primitive; idempotent per
        (meeting, action item).
        """
        repo = str(payload.repo or "").strip()
        if not repo:
            return JSONResponse(
                {"success": False, "error": "A target repo (owner/name) is required"},
                status_code=400,
            )
        try:
            from ....config import Config
            from ....db import get_database
            from ....plugins.builtin.github_issue_actuator import (
                GithubIssueActuator,
                build_github_issue_proposal,
            )

            db = get_database()
            meeting = db.meetings.get_meeting(meeting_id)
            if meeting is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)

            item = db.meetings.get_action_item(payload.action_item_id)
            if item is None or item.meeting_id != meeting_id:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )
            # Only a human-reviewed (accepted) action can be filed — this is the
            # "take what I just accepted and track it" seam, not auto-filing.
            if item.review_state != "accepted":
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Only an accepted action item can be filed as an issue",
                    },
                    status_code=400,
                )

            spec = build_github_issue_proposal(
                task=item.task,
                owner=item.owner,
                due=item.due,
                meeting_title=meeting.title or "meeting",
                repo=repo,
            )
            proposal = db.actuators.record_proposal(
                meeting_id=meeting_id,
                window_id=f"{meeting_id}:aftercare",
                plugin_id=GithubIssueActuator.id,
                plugin_version=GithubIssueActuator.version,
                idempotency_key=f"aftercare-issue:{meeting_id}:{item.id}",
                target=spec["target"],
                action=spec["action"],
                preview=spec["preview"],
                payload=spec["payload"],
                reversible=spec["reversible"],
                required_capabilities=spec["required_capabilities"],
                control_mode=Config.load().control_mode,
                fixed_destination=False,
            )
            # HS-56-03: the live in-meeting path already broadcasts proposals;
            # the aftercare path now does too, with the identical wire-safe
            # shape (the human preview only — never the machine payload).
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
                    "created_at": proposal.created_at.isoformat()
                    if hasattr(proposal.created_at, "isoformat")
                    else proposal.created_at,
                },
            )
            return JSONResponse(
                {"success": True, "proposal": _proposal_to_dict(proposal)}
            )
        except Exception as e:
            return error_500(e, log, "Failed to file aftercare issue")

    @router.post("/api/meetings/{meeting_id}/export/slack")
    async def api_export_meeting_to_slack(
        meeting_id: str, payload: _SlackExportRequest
    ) -> Any:
        """Propose sending one aftercare artifact to Slack (HS-61-01).

        Records a `proposed` actuator proposal whose preview IS the exact
        message text Slack would receive — nothing is sent here; execution
        happens only when the proposal is approved (the decision endpoint).
        Refuses up front when no webhook URL is configured (the feature is
        invisible then), when `what` is unknown, or when the meeting's
        aftercare is empty (no padding gets sent to a channel).

        Wire safety: the stored payload carries only the message body. The
        webhook URL is a credential — it stays in config, joined to the POST
        in memory at execution time only.
        """
        import hashlib

        from ....config import Config
        from ....slack_export import EXPORT_KINDS, slack_message_for

        what = str(payload.what or "").strip().lower()
        if what not in EXPORT_KINDS:
            return JSONResponse(
                {
                    "success": False,
                    "error": f"Unknown export kind: {what!r} (expected 'digest' or 'followup')",
                },
                status_code=400,
            )
        config = Config.load()
        if not config.meeting.slack_webhook_url:
            return JSONResponse(
                {
                    "success": False,
                    "error": "Slack is not configured (set the webhook URL in Settings first)",
                },
                status_code=400,
            )
        try:
            from ....db import get_database
            from ....meeting_aftercare import compute_meeting_aftercare
            from ....plugins.builtin.webhook_post_actuator import WebhookPostActuator

            db = get_database()
            digest = compute_meeting_aftercare(db, meeting_id)
            if digest is None:
                return JSONResponse({"error": "Meeting not found"}, status_code=404)
            if digest.get("is_empty"):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "This meeting has nothing open, decided, or changed to send",
                    },
                    status_code=400,
                )

            text = slack_message_for(digest, what)
            # Identical content dedupes to the existing proposal; edited
            # aftercare (a new item, a corrected decision) re-proposes.
            content_key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            proposal = db.actuators.record_proposal(
                meeting_id=meeting_id,
                window_id=f"{meeting_id}:aftercare",
                plugin_id=WebhookPostActuator.id,
                plugin_version=WebhookPostActuator.version,
                idempotency_key=f"slack-export:{meeting_id}:{what}:{content_key}",
                target="slack",
                action="post_message",
                preview=text,
                payload={"body": {"text": text}},
                reversible=False,  # a posted message cannot be unsent
                required_capabilities=["actuator"],
                control_mode=config.control_mode,
                fixed_destination=True,
            )
            # The same wire-safe shape every proposal broadcast uses (the
            # human preview only — never the machine payload).
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
                    "created_at": proposal.created_at.isoformat()
                    if hasattr(proposal.created_at, "isoformat")
                    else proposal.created_at,
                },
            )
            proposal = actuator_shared.apply_control_posture(
                ctx,
                db,
                proposal,
                executors={"slack": actuator_shared.execute_slack_proposal},
            )
            return JSONResponse(
                {"success": True, "proposal": _proposal_to_dict(proposal)}
            )
        except Exception as e:
            return error_500(e, log, "Failed to propose Slack export")

    return router
