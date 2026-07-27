"""The tool-call gate, hub side (HS-104-02).

Receive a hook's redacted proposal, hold it, let the desk decide from
the shade, and answer the polling hook. The proposal record is never
authority: these routes flip states and write audit rows; only the
live hook waiting on the answer can let the call proceed.

Both capability-bearing paths route through
:func:`holdspeak.agent_capabilities.require_capability` — the ledger
census pins them (`gate_routes.receive` needs ``tool_hooks``,
`gate_routes.decide` needs ``blocking``, both on the
``claude-code-hooks`` adapter).

The one decision chokepoint lives in :mod:`holdspeak.db.gate` (the
repository's private transition method); these routes call
``decide``/``expire_due``/``invalidate_all_held``, which all pass
through it. A second code path that flips proposal state is a census
failure (tests/unit/test_gate_chokepoint.py).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....agent_capabilities import Capability, require_capability
from ....db.gate import APPROVED, DENIED, HELD
from .... import kernel
from ....kernel.model import KernelRefused
from ....kernel.runtime import _as_principal, _service
from ....logging_config import get_logger
from ...context import WebContext

log = get_logger("web.routes.gate")

_REASON_MAX_CHARS = 200


def build_gate_router(ctx: WebContext) -> APIRouter:
    from ....db import get_database

    router = APIRouter()

    @router.post("/api/principals/agents")
    async def api_issue_agent_principal(request: Request) -> Any:
        """Owner-only mint used by trusted spawn and lifecycle hooks."""
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        identity = str(body.get("identity") or "").strip()
        if not identity:
            return JSONResponse({"error": "identity is required"}, status_code=400)
        credential = request.app.state.agent_credentials.issue(identity)
        return JSONResponse(
            {
                "principal": credential.principal.name,
                "identity": credential.principal.identity,
                "credential": credential.token,
            },
            status_code=201,
        )

    @router.delete("/api/principals/agents/{identity}")
    async def api_revoke_agent_principal(identity: str, request: Request) -> Any:
        revoked = request.app.state.agent_credentials.revoke(identity)
        return JSONResponse(
            {"principal": "agent", "identity": identity, "revoked": revoked}
        )

    @router.delete("/api/principals/self")
    async def api_revoke_self(request: Request) -> Any:
        principal = request.state.principal
        revoked = request.app.state.agent_credentials.revoke(principal.identity)
        return JSONResponse(
            {
                "principal": principal.name,
                "identity": principal.identity,
                "revoked": revoked,
            }
        )

    @router.post("/api/gate/proposals")
    async def api_gate_propose(request: Request) -> Any:
        # web.routes.system.gate_routes.receive — the ledger consumer.
        require_capability("claude-code-hooks", Capability.TOOL_HOOKS)
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        proposal_id = str(body.get("id") or "").strip()
        tool = str(body.get("tool") or "").strip()
        args_sha256 = str(body.get("args_sha256") or "").strip()
        if not proposal_id or not tool or not args_sha256:
            return JSONResponse(
                {"error": "id, tool, and args_sha256 are required"}, status_code=400
            )
        cwd = str(body.get("cwd") or "")
        try:
            ttl = float(body.get("ttl_seconds") or 0.0)
        except (TypeError, ValueError):
            ttl = 0.0
        if ttl <= 0.0:
            from ....coder_gate import DEFAULT_TTL_SECONDS

            ttl = DEFAULT_TTL_SECONDS
        gate = get_database().gate
        gate.expire_due()
        principal = request.state.principal
        with _as_principal(principal):
            handle = kernel.submit(
                {
                    "request_schema": 1,
                    "request_id": proposal_id,
                    "idempotency_key": f"gate:{proposal_id}",
                    "operation": {"name": "tool.call", "version": 1},
                    "subject_refs": [],
                    "target": {"ref": f"gate:{proposal_id}"},
                    "arguments": {
                        "proposal_id": proposal_id,
                        "tool": tool,
                        "args_sha256": args_sha256,
                        "args_head": str(body.get("args_head") or ""),
                        "cwd": cwd,
                        "ttl_seconds": ttl,
                    },
                    "placement": "hub:local",
                }
            )
        refusal_receipt = handle.get("receipt") or {}
        if refusal_receipt.get("outcome") == "idempotency_payload_mismatch":
            return JSONResponse(
                {
                    "error": "args_mismatch",
                    "state": "invalidated",
                    "reason": "a re-arrival changed the arguments; the original hold was revoked",
                },
                status_code=409,
            )
        proposal = gate.get(proposal_id)
        if proposal is None:
            return JSONResponse(handle, status_code=409)
        return JSONResponse(_wire(proposal))

    @router.get("/api/gate/proposals/{proposal_id}")
    async def api_gate_read(proposal_id: str, request: Request) -> Any:
        gate = get_database().gate
        gate.expire_due()
        proposal = gate.get(proposal_id)
        if proposal is None:
            return JSONResponse({"error": "unknown_proposal"}, status_code=404)
        principal = request.state.principal
        if principal.name == "agent" and proposal.session_key != principal.identity:
            return JSONResponse(
                {
                    "error": "principal_scope_required",
                    "principal": principal.name,
                    "principal_identity": principal.identity,
                    "missing_right": "agent.read:other_session",
                },
                status_code=403,
            )
        return JSONResponse(_wire(proposal))

    @router.get("/api/gate/proposals")
    async def api_gate_list(state: str = HELD) -> Any:
        gate = get_database().gate
        gate.expire_due()
        return JSONResponse(
            {"proposals": [_wire(p) for p in gate.list_state(state)], "state": state}
        )

    @router.post("/api/gate/proposals/{proposal_id}/decide")
    async def api_gate_decide(proposal_id: str, request: Request) -> Any:
        # web.routes.system.gate_routes.decide — the ledger consumer.
        require_capability("claude-code-hooks", Capability.BLOCKING)
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        decision = str(body.get("decision") or "").strip()
        if decision not in (APPROVED, DENIED):
            return JSONResponse(
                {"error": f"decision must be {APPROVED}|{DENIED}"}, status_code=400
            )
        reason = str(body.get("reason") or "").strip()[:_REASON_MAX_CHARS] or None
        gate = get_database().gate
        proposal = gate.get(proposal_id)
        if proposal is None:
            return JSONResponse({"error": "unknown_proposal"}, status_code=404)
        operation_id = str(proposal.operation.get("kernel_operation_id") or "")
        if not operation_id:
            return JSONResponse({"error": "proposal_not_kernel_admitted"}, status_code=409)
        principal = request.state.principal
        try:
            with _as_principal(principal):
                projected = kernel.read([f"operation:{operation_id}"], "state", "committed")
                standing = projected["objects"][0]["operation"]
                _service().decide(
                    operation_id,
                    "approve" if decision == APPROVED else "reject",
                    int(standing["revision"]),
                    principal,
                    reason=reason or "",
                )
        except (KernelRefused, IndexError) as exc:
            current = gate.get(proposal_id)
            return JSONResponse(
                {
                    "error": "already_decided",
                    "state": current.state if current is not None else "unknown",
                    "requested": decision,
                },
                status_code=409,
            )
        return JSONResponse(_wire(gate.get(proposal_id)))

    @router.post("/api/gate/usage")
    async def api_gate_usage(request: Request) -> Any:
        # web.routes.system.gate_routes.usage — the ledger consumer
        # (HS-104-05): reported figures land only for an adapter the
        # ledger vouches usage_tokens for.
        require_capability("claude-code-hooks", Capability.USAGE_TOKENS)
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        session_key = request.state.principal.identity
        try:
            get_database().gate.report_usage(
                session_key=session_key,
                model=str(body.get("model") or ""),
                input_tokens=int(body.get("input_tokens") or 0),
                output_tokens=int(body.get("output_tokens") or 0),
                cache_read_tokens=int(body.get("cache_read_tokens") or 0),
                cache_creation_tokens=int(body.get("cache_creation_tokens") or 0),
            )
        except (TypeError, ValueError):
            return JSONResponse({"error": "figures must be integers"}, status_code=400)
        return JSONResponse({"success": True})

    @router.get("/api/sessions/{session_key}/receipt")
    async def api_session_receipt(session_key: str) -> Any:
        # web.routes.system.gate_routes.receipt — the render call
        # site; the reported/estimated tiers inside build_receipt go
        # through require_capability (census-pinned).
        from ....session_receipts import build_receipt

        return JSONResponse(build_receipt(session_key, db=get_database()))

    @router.get("/api/gate/audit")
    async def api_gate_audit(limit: int = 100) -> Any:
        entries = get_database().gate.audit_entries(limit=max(1, min(limit, 500)))
        return JSONResponse({"entries": entries})

    @router.get("/api/gate/config")
    async def api_gate_config() -> Any:
        from ....coder_gate import load_gate_config

        return JSONResponse(load_gate_config().to_dict())

    return router


def invalidate_held_on_startup() -> int:
    """Restart honesty (called from the web server's startup): every
    pre-restart ``held`` row flips ``invalidated``; the polling hook
    reads deny-with-reason; nothing decided pre-restart is re-served."""
    from ....db import get_database

    flipped = get_database().gate.invalidate_all_held(
        reason="hub restarted while the proposal was held"
    )
    if flipped:
        recovered = _service().recover_invalidated(flipped)
        log.info(
            f"gate: invalidated {len(flipped)} held proposal(s) on startup; "
            f"kernel terminalized {recovered}"
        )
    return len(flipped)


def _wire(proposal: Any) -> dict[str, Any]:
    payload = proposal.to_dict()
    # The shade renders the redacted preview and age; the full
    # arguments never existed hub-side to leak.
    return payload
