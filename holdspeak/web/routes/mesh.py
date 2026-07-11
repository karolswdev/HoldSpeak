"""Mesh routes: discovery (HSM-15-10) + the mesh inbox (HSM-15-03).

``GET /api/mesh/info`` is a single lightweight, **unauthenticated** identify
endpoint. A companion that has just discovered this server on the LAN (via
Bonjour) needs to confirm WHO it found and whether pairing will need a token —
and it must do so *before* it has the token. So this endpoint is deliberately
reachable without auth (the server's off-loopback auth gate exempts it) and
returns only non-sensitive identity: ``{name, version, requiresToken}``. It
NEVER returns the token or any secret.

``GET /api/mesh/inbox`` is the mesh queue's one window (normal auth applies):
everything in flight on this hub (the deferred intel queue + the MIR plugin-run
queue) plus everything pending the human nod (actuator proposals across meeting
AND desk origins), in one envelope a companion's Queue HUD polls. Aggregation
only — the underlying queues and the decision routes are untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..context import WebContext

# The off-loopback auth gate in `MeetingWebServer._create_app` exempts this path
# so a not-yet-paired companion can identify the server before it has a token.
MESH_INFO_PATH = "/api/mesh/info"


def build_mesh_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get(MESH_INFO_PATH)
    async def api_mesh_info() -> Any:
        """Identify this server to a freshly-discovered (unpaired) companion.

        Returns ONLY non-sensitive identity. No token, no secrets.
        """
        from ... import __version__
        from ...config import Config
        from ...mesh import resolve_device_name

        try:
            configured = Config.load().mesh.device_name
        except Exception:
            configured = ""
        return JSONResponse(
            {
                "name": resolve_device_name(configured),
                "version": __version__,
                "requiresToken": bool(ctx.mesh_requires_token),
            }
        )

    @router.get("/api/mesh/inbox")
    async def api_mesh_inbox() -> Any:
        """Everything in flight + everything pending approval, one envelope.

        Jobs are the IN-FLIGHT rows (queued/running) from the two real queues;
        failures ride the counts, not the job list (the HUD's blocked-footer
        vocabulary). Proposals are every `proposed` row across meeting + desk
        origins — the fields a companion needs to render and DECIDE (origin +
        target pick the existing decision route; the payload never rides).
        """
        try:
            from ...db import get_database
            from ...intel_queue import build_runtime_queue_frame

            db = get_database()

            jobs: list[dict[str, Any]] = []
            intel_frame = build_runtime_queue_frame(db)
            for job in intel_frame["jobs"]:
                if str(job.get("status") or "") in ("queued", "running"):
                    jobs.append({
                        "kind": "intel",
                        "id": str(job.get("id") or ""),
                        "label": str(job.get("label") or ""),
                        "status": str(job.get("status") or "queued"),
                        "meeting_id": job.get("meeting_id"),
                        "attempts": int(job.get("attempts") or 0),
                    })
            for job in db.plugins.list_plugin_run_jobs(status="queued", limit=20):
                jobs.append({
                    "kind": "plugin",
                    # The DB id is an INTEGER; the wire id is a kind-prefixed
                    # string so rows are string-typed AND unique across lanes.
                    "id": f"plugin:{job.id}",
                    "label": job.plugin_id,
                    "status": job.status,
                    "meeting_id": job.meeting_id,
                    "attempts": int(job.attempts or 0),
                })

            from ...operation_policy import commitment_labels, operation_for_proposal

            proposals = []
            for p in db.actuators.list_pending_proposals(limit=50):
                operation = operation_for_proposal(p)
                proposals.append({
                    "id": p.id,
                    "origin": p.origin,
                    "meeting_id": p.meeting_id,
                    "target": p.target,
                    "action": p.action,
                    "preview": p.preview,
                    "status": p.status,
                    "review_decision": p.review_decision,
                    "authorization_state": p.authorization_state,
                    "execution_state": p.execution_state,
                    "operation": operation.to_dict(),
                    "commitment": commitment_labels(operation),
                    "created_at": p.created_at,
                })

            return JSONResponse({
                "jobs": jobs,
                "proposals": proposals,
                "counts": {
                    "queued": int(intel_frame.get("queued") or 0),
                    "running": int(intel_frame.get("running") or 0),
                    "failed": int(intel_frame.get("failed") or 0),
                    "pending_approvals": len(proposals),
                },
            })
        except Exception as exc:
            from ...logging_config import get_logger
            from ..runtime_support import error_500

            return error_500(exc, get_logger("web.routes.mesh"), "Failed to build the mesh inbox")

    # ── The mesh-edge relay wire (HS-85-01) ─────────────────────────────
    # A node's WORKER speaks these three routes (normal auth applies): claim
    # stamps the node's liveness on every poll — the mesh's only heartbeat —
    # and returns the oldest queued job addressed to that node; complete/fail
    # post the run's outcome verbatim. Enqueue has no route: only the hub's
    # own relay provider (HS-85-02) writes jobs.

    @router.post("/api/mesh/relay/claim")
    async def api_mesh_relay_claim(payload: dict[str, Any]) -> Any:
        node = str((payload or {}).get("node") or "").strip()
        if not node:
            return JSONResponse({"error": "node must be a non-empty string"}, status_code=400)
        try:
            from ...db import get_database

            job = get_database().mesh_relay.claim_next(node)
            return JSONResponse({"job": job.to_dict() if job is not None else None})
        except Exception as exc:
            from ...logging_config import get_logger
            from ..runtime_support import error_500

            return error_500(exc, get_logger("web.routes.mesh"), "Failed to claim relay work")

    @router.post("/api/mesh/relay/{job_id}/complete")
    async def api_mesh_relay_complete(job_id: str, payload: dict[str, Any]) -> Any:
        result = (payload or {}).get("result")
        if not isinstance(result, str) or not result.strip():
            return JSONResponse({"error": "result must be a non-empty string"}, status_code=400)
        try:
            from ...db import get_database

            ok = get_database().mesh_relay.complete(job_id, result=result)
            if not ok:
                # the answer arrived after the deadline (or for an unknown id) —
                # refuse it by name so a late worker learns the truth
                return JSONResponse(
                    {"error": f"relay job {job_id} is not completable (expired, failed, or unknown)"},
                    status_code=409,
                )
            return JSONResponse({"success": True})
        except Exception as exc:
            from ...logging_config import get_logger
            from ..runtime_support import error_500

            return error_500(exc, get_logger("web.routes.mesh"), "Failed to complete relay work")

    @router.post("/api/mesh/relay/{job_id}/fail")
    async def api_mesh_relay_fail(job_id: str, payload: dict[str, Any]) -> Any:
        error = str((payload or {}).get("error") or "").strip()
        if not error:
            return JSONResponse({"error": "error must be a non-empty string"}, status_code=400)
        try:
            from ...db import get_database

            ok = get_database().mesh_relay.fail(job_id, error=error)
            if not ok:
                return JSONResponse(
                    {"error": f"relay job {job_id} is not failable (already terminal or unknown)"},
                    status_code=409,
                )
            return JSONResponse({"success": True})
        except Exception as exc:
            from ...logging_config import get_logger
            from ..runtime_support import error_500

            return error_500(exc, get_logger("web.routes.mesh"), "Failed to record relay failure")

    return router
