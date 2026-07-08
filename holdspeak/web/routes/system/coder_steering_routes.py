"""The steering surface (HS-87-01/02/03): attach, arm, steer, audit.

Carved from `coders.py` (the Phase-79 single-concern budget): the
coder BOARD (who receives a spoken answer) stays there; STEERING
(watch a pane, arm it, type into it under the consent spine) lives
here. Shared with the board: `_coder_frame` and `_session_age_seconds`,
imported from `coders.py` (one owner each, no duplication).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500
from .coders import _coder_frame, _session_age_seconds

log = get_logger("web.routes.system.steering")


def build_coder_steering_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _registry_session(key: str):
        """Resolve `agent:session_id` against the registry; a JSONResponse
        when the key is malformed or the session is gone."""
        from ....agent_context import list_agent_sessions

        agent, _, session_id = key.partition(":")
        if not agent.strip() or not session_id.strip():
            return JSONResponse(
                {"error": "key must be agent:session_id"}, status_code=400
            )
        session = next(
            (
                s
                for s in list_agent_sessions(agent=agent)
                if s.session_id == session_id
            ),
            None,
        )
        if session is None:
            return JSONResponse(
                {"status": "unknown_session", "key": key}, status_code=404
            )
        return session

    def _session_is_stale(session: Any) -> tuple[bool, Optional[int]]:
        from ....agent_context import DEFAULT_RECENT_MAX_AGE_SECONDS

        age = _session_age_seconds(session.updated_at, datetime.now(timezone.utc))
        return (
            bool(age is not None and age > DEFAULT_RECENT_MAX_AGE_SECONDS),
            age,
        )

    def _sweep_and_frame() -> None:
        """Lazy expiry on read (no background timer): expired grants
        broadcast their frame the moment any steering read notices."""
        from .... import coder_steering

        for expired_key in coder_steering.sweep_expired():
            _coder_frame(ctx, expired_key)

    @router.get("/api/coders/{key}/peek")
    async def api_coder_peek(
        key: str, lines: int = 200, last_hash: Optional[str] = None
    ) -> Any:
        """Read-only window into a session's tmux pane (HS-87-01).

        Watching is free — no grant, no keystroke, ever. The pane is
        resolved from the registry record; absences come back as typed
        peek statuses (`no_pane`, `pane_gone`, `tmux_absent`), and a
        registry entry past the recent window is marked `stale`, never
        dropped. The envelope carries the grant state (HS-87-02) so an
        open pull-out renders the countdown without a second poll.
        """
        from .... import coder_steering

        try:
            session = _registry_session(key)
        except Exception as e:
            return error_500("coder peek", e, log)
        if isinstance(session, JSONResponse):
            return session
        stale, _age = _session_is_stale(session)
        _sweep_and_frame()
        grant = coder_steering.active_grants().get(key)
        envelope: dict[str, Any] = {
            "key": key,
            "agent": session.agent,
            "stale": stale,
            "awaiting_response": session.awaiting_response,
            "question": session.question,
            "updated_at": session.updated_at,
            "grant": {
                "armed": grant is not None,
                "expires_in_seconds": grant["expires_in_seconds"] if grant else None,
            },
        }
        target = coder_steering.resolve_pane_target(session)
        if target is None:
            envelope["peek"] = {"status": "no_pane"}
            return JSONResponse(envelope)
        envelope["peek"] = await asyncio.to_thread(
            coder_steering.peek_pane, target, lines=lines, last_hash=last_hash
        )
        return JSONResponse(envelope)

    @router.post("/api/coders/{key}/arm")
    async def api_coder_arm(
        key: str, payload: Optional[dict[str, Any]] = None
    ) -> Any:
        """Arm a session for steering (HS-87-02) — the explicit desk act.

        Pins the pane's `%N` identity at grant time; refuses a stale
        registry record by naming the staleness, and a pane that cannot
        prove itself. Refusals are 409 with a typed status — the UI
        renders them in place, never a toast-shaped apology.
        """
        from .... import coder_steering

        try:
            session = _registry_session(key)
        except Exception as e:
            return error_500("coder arm", e, log)
        if isinstance(session, JSONResponse):
            return session
        stale, age = _session_is_stale(session)
        if stale:
            return JSONResponse(
                {
                    "status": "stale_session",
                    "detail": (
                        f"registry record is {age}s old — a stale session "
                        "cannot be armed"
                    ),
                },
                status_code=409,
            )
        target = coder_steering.resolve_pane_target(session)
        if target is None:
            return JSONResponse(
                {"status": "no_pane", "detail": "this session never saw tmux"},
                status_code=409,
            )
        body = payload if isinstance(payload, dict) else {}
        ttl = coder_steering.clamp_ttl(
            body.get("ttl_seconds", coder_steering.ARM_DEFAULT_TTL_SECONDS)
        )
        result = await asyncio.to_thread(
            coder_steering.arm, key, target, ttl_seconds=ttl
        )
        if result["status"] != "armed":
            return JSONResponse(result, status_code=409)
        _coder_frame(ctx, key)
        return JSONResponse(result)

    @router.post("/api/coders/{key}/disarm")
    async def api_coder_disarm(key: str) -> Any:
        """One tap, immediate, idempotent (HS-87-02)."""
        from .... import coder_steering

        was_armed = coder_steering.disarm(key)
        if was_armed:
            _coder_frame(ctx, key)
        return JSONResponse({"status": "disarmed", "key": key, "was_armed": was_armed})

    @router.get("/api/coders/steering/grants")
    async def api_coder_grants() -> Any:
        """Every live grant (HS-87-02) — the pins' armed state, one read.
        Expired grants sweep (and frame) on the way through."""
        from .... import coder_steering

        _sweep_and_frame()
        return JSONResponse({"grants": coder_steering.active_grants()})

    def _compose_from_body(body: dict[str, Any]):
        """Message + optional grounding → the composed steer (HS-87-04).

        A JSONResponse on any refusal (bad text, bad grounding shape,
        unknown refs, over-cap); otherwise the compose result dict from
        `grounding.compose_steer`. Hydration is the SAME helper the ask
        route uses — one grounding truth.
        """
        from ....db import get_database
        from ....grounding import (
            GROUNDING_EXPANDS,
            GROUNDING_MAX_REFS,
            compose_steer,
            hydrate_refs,
        )

        text = body.get("text")
        if not isinstance(text, str) or not text.strip():
            return JSONResponse({"error": "text is required"}, status_code=400)
        grounding = body.get("grounding")
        if grounding is None:
            return compose_steer(text, [])
        if not isinstance(grounding, dict):
            return JSONResponse(
                {"error": "grounding must be an object"}, status_code=400
            )
        raw_m = grounding.get("meeting_ids")
        raw_a = grounding.get("artifact_ids")
        meeting_ids = (
            [str(x).strip() for x in raw_m if str(x).strip()]
            if isinstance(raw_m, list)
            else []
        )
        artifact_ids = (
            [str(x).strip() for x in raw_a if str(x).strip()]
            if isinstance(raw_a, list)
            else []
        )
        expand = str(grounding.get("expand") or "summary").strip() or "summary"
        if expand not in GROUNDING_EXPANDS:
            return JSONResponse(
                {"error": f"expand {expand!r} is not one of {list(GROUNDING_EXPANDS)}"},
                status_code=400,
            )
        if len(meeting_ids) + len(artifact_ids) > GROUNDING_MAX_REFS:
            return JSONResponse(
                {"error": f"grounding is capped at {GROUNDING_MAX_REFS} refs"},
                status_code=400,
            )
        blocks, unknown = hydrate_refs(
            get_database(), meeting_ids, artifact_ids, expand
        )
        if unknown:
            return JSONResponse(
                {"error": "grounding ids not on this hub", "unknown_ids": unknown},
                status_code=400,
            )
        return compose_steer(text, blocks)

    @router.post("/api/coders/{key}/steer")
    async def api_coder_steer(
        key: str, payload: Optional[dict[str, Any]] = None
    ) -> Any:
        """Deliver one steer through THE chokepoint (HS-87-03/04).

        The steer may carry `grounding` refs (HS-87-04): the hub
        hydrates them through the SAME helper the ask route uses, fences
        them with provenance headers, and caps the context — over-cap
        refuses at compose time (executed == previewed). `preview: true`
        returns the exact composed text WITHOUT sending. An unarmed
        steer is a typed 409 (the desk shows the ARM affordance); a
        revoking refusal broadcasts its frame. Delivered or refused, the
        attempt is audited.
        """
        from .... import coder_steering

        try:
            session = _registry_session(key)
        except Exception as e:
            return error_500("coder steer", e, log)
        if isinstance(session, JSONResponse):
            return session
        body = payload if isinstance(payload, dict) else {}
        composed = _compose_from_body(body)
        if isinstance(composed, JSONResponse):
            return composed
        if composed["status"] == "over_cap":
            return JSONResponse(
                {
                    "status": "grounding_over_cap",
                    "detail": (
                        f"grounded context is {composed['context_bytes']} bytes, "
                        f"over the {composed['cap_bytes']} byte cap"
                    ),
                    "context_bytes": composed["context_bytes"],
                    "cap_bytes": composed["cap_bytes"],
                },
                status_code=409,
            )
        submit = bool(body.get("submit", True))
        if bool(body.get("preview")):
            # Executed == previewed: the SAME composed text the send uses.
            return JSONResponse(
                {
                    "status": "preview",
                    "text": composed["text"],
                    "context_bytes": composed["context_bytes"],
                    "cap_bytes": composed["cap_bytes"],
                    "refs": composed["refs"],
                }
            )
        target = coder_steering.resolve_pane_target(session)
        result = await asyncio.to_thread(
            coder_steering.deliver,
            key,
            composed["text"],
            current_target=target,
            agent=session.agent,
            submit=submit,
            grounding_refs=composed["refs"],
        )
        if result.get("revoked"):
            _coder_frame(ctx, key)  # the disarm is visible everywhere, now
        if result["status"] == "delivered":
            return JSONResponse(result)
        return JSONResponse(result, status_code=409)

    @router.get("/api/coders/steering/audit")
    async def api_coder_steering_audit(
        session_key: Optional[str] = None, limit: int = 50
    ) -> Any:
        """The steering trail (HS-87-03): who/when/session/pane/shape,
        newest first — refusals included. Heads and hashes only; the
        full steer text is never stored."""
        from ....db import get_database

        try:
            entries = await asyncio.to_thread(
                get_database().steering.list, session_key=session_key, limit=limit
            )
            return JSONResponse({"audit": [e.to_dict() for e in entries]})
        except Exception as e:
            return error_500("steering audit", e, log)

    return router
