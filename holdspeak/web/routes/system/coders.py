"""The coder board: which live coding session receives a spoken answer.

Bodies moved verbatim from routes/system.py (HS-79-02, the Phase-63 discipline).
HS-87-01 adds the attach verb: a read-only peek into a session's tmux pane.
"""
from __future__ import annotations

import asyncio
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.system")
from ._shared import _normalize_runtime_status_payload

_COMPANION_TARGET_MAX_AGE_SECONDS = 120
_COMPANION_OVERVIEW_MAX_AGE_SECONDS = 30 * 60


def _coder_frame(ctx: WebContext, key: str) -> None:
    """One `scope:"coder"` frame on the one bus — arming moved, a grant
    expired, an awaiting flag flipped; every surface hears the same
    motion (the HS-86-03 frame shape, coder scope)."""
    if ctx.broadcast is None:
        return
    try:
        ctx.broadcast(
            "intel_status",
            {
                "state": "ready",
                "scope": "coder",
                "capability": {
                    "kind": "coder",
                    "id": key,
                    "name": key.split(":", 1)[0],
                },
            },
        )
    except Exception as exc:
        log.debug(f"coder frame dropped: {exc}")


def _session_age_seconds(stamp: Optional[str], now: datetime) -> Optional[int]:
    """Seconds since an ISO-8601 session timestamp, or None if unparseable."""
    if not isinstance(stamp, str) or not stamp.strip():
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0, int((now - parsed).total_seconds()))




def build_coders_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/coders/status")
    async def api_companion_status() -> Any:
        """Return one debug snapshot for the AIPI agent companion loop."""
        from ....agent_context import (
            DEFAULT_STALE_AGENT_SESSION_SECONDS,
            get_recent_awaiting_agent_session,
            list_recent_awaiting_agent_sessions,
        )
        from ....agent_device import AGENT_QUERY_NAMES, build_agent_identity_payload
        from ....config import Config
        from ....meeting_session import _device_descriptor_to_dict

        try:
            state = ctx.get_state() or {}
        except Exception as e:
            log.error(f"get_state failed: {e}")
            state = {}

        runtime_error: str | None = None
        if ctx.on_get_status is not None:
            try:
                raw_payload = ctx.on_get_status()
                if isinstance(raw_payload, dict):
                    runtime_payload = _normalize_runtime_status_payload(raw_payload, state)
                else:
                    runtime_payload = _normalize_runtime_status_payload(
                        {"runtime_status": raw_payload},
                        state,
                    )
            except Exception as e:
                log.error(f"on_get_status failed: {e}")
                runtime_error = str(e)
                runtime_payload = _normalize_runtime_status_payload({}, state)
        else:
            runtime_payload = _normalize_runtime_status_payload({}, state)

        devices = [
            _device_descriptor_to_dict(descriptor)
            for descriptor in ctx.device_registry.active()
        ]
        device_connected = bool(devices)

        agent_error: str | None = None
        try:
            session = get_recent_awaiting_agent_session(
                max_age_seconds=_COMPANION_TARGET_MAX_AGE_SECONDS
            )
            agent_sessions = list_recent_awaiting_agent_sessions(
                max_age_seconds=_COMPANION_OVERVIEW_MAX_AGE_SECONDS,
                limit=8,
            )
        except Exception as e:
            log.error(f"agent companion status failed: {e}")
            agent_error = str(e)
            session = None
            agent_sessions = []
        agent_waiting = bool(session and session.awaiting_response)
        tmux_reply_available = bool(
            session
            and session.awaiting_response
            and getattr(session, "tmux_pane", None)
        )

        dictation_error: str | None = None
        try:
            dictation_cfg = Config.load().dictation
            pipeline_enabled = bool(dictation_cfg.pipeline.enabled)
            pipeline_stages = list(dictation_cfg.pipeline.stages)
            target_profile_override = dictation_cfg.pipeline.target_profile_override
            runtime_backend = dictation_cfg.runtime.backend
        except Exception as e:
            log.error(f"dictation config load failed: {e}")
            dictation_error = str(e)
            pipeline_enabled = False
            pipeline_stages = []
            target_profile_override = None
            runtime_backend = None

        text_injection_known = "text_injection_enabled" in runtime_payload
        text_injection_enabled = (
            bool(runtime_payload.get("text_injection_enabled"))
            if text_injection_known
            else None
        )
        agent_identity = build_agent_identity_payload(
            session,
            text_injection_enabled=text_injection_enabled,
        )
        if session is not None and not any(
            item.agent == session.agent and item.session_id == session.session_id
            for item in agent_sessions
        ):
            agent_sessions.insert(0, session)
        selected_agent_key = (
            (session.agent, session.session_id) if session is not None else None
        )
        agent_session_items = []
        selected_index: int | None = None
        status_now = datetime.now(timezone.utc)
        for index, item in enumerate(agent_sessions):
            item_key = (item.agent, item.session_id)
            selected = item_key == selected_agent_key
            if selected:
                selected_index = index
            age_seconds = _session_age_seconds(item.updated_at, status_now)
            # Pinned sessions are intentionally kept; never badge them stale.
            stale = (
                not item.pinned
                and age_seconds is not None
                and age_seconds > DEFAULT_STALE_AGENT_SESSION_SECONDS
            )
            agent_session_items.append(
                {
                    "index": index,
                    "selected": selected,
                    "pinned": item.pinned,
                    "stale": stale,
                    "age_seconds": age_seconds,
                    "session": item.to_dict(),
                    "identity": build_agent_identity_payload(
                        item,
                        text_injection_enabled=text_injection_enabled,
                    ),
                }
            )

        blockers: list[str] = []
        if not device_connected:
            blockers.append("no_device_connected")
        if not agent_waiting:
            blockers.append("no_agent_waiting")
        if not pipeline_enabled:
            blockers.append("dictation_pipeline_disabled")
        if text_injection_enabled is False and not tmux_reply_available:
            blockers.append("text_injection_unavailable")
        elif text_injection_enabled is None and not tmux_reply_available:
            blockers.append("text_injection_status_unknown")
        if agent_error:
            blockers.append("agent_status_unavailable")
        if dictation_error:
            blockers.append("dictation_config_unavailable")
        if runtime_error:
            blockers.append("runtime_status_unavailable")

        return JSONResponse(
            {
                "status": "ok",
                "ready_for_agent_reply": not blockers,
                "blockers": blockers,
                "checks": {
                    "device_connected": device_connected,
                    "agent_waiting": agent_waiting,
                    "dictation_pipeline_enabled": pipeline_enabled,
                    "text_injection_enabled": text_injection_enabled,
                    "tmux_reply_available": tmux_reply_available,
                    "target_confidence": (
                        agent_identity["target_confidence"] if agent_identity else None
                    ),
                },
                "devices": {
                    "connected": device_connected,
                    "count": len(devices),
                    "items": devices,
                    "query_names": sorted(AGENT_QUERY_NAMES),
                },
                "agent": {
                    "awaiting_response": agent_waiting,
                    "session": session.to_dict() if session else None,
                    "identity": agent_identity,
                    "sessions": {
                        "count": len(agent_session_items),
                        "selected_index": selected_index,
                        "items": agent_session_items,
                    },
                    "max_age_seconds": _COMPANION_TARGET_MAX_AGE_SECONDS,
                    "overview_max_age_seconds": _COMPANION_OVERVIEW_MAX_AGE_SECONDS,
                    "stale_threshold_seconds": DEFAULT_STALE_AGENT_SESSION_SECONDS,
                    "error": agent_error,
                },
                "dictation": {
                    "pipeline_enabled": pipeline_enabled,
                    "stages": pipeline_stages,
                    "target_profile_override": target_profile_override,
                    "runtime_backend": runtime_backend,
                    "error": dictation_error,
                },
                "runtime": {
                    "status": runtime_payload.get("status"),
                    "mode": runtime_payload.get("mode"),
                    "meeting_active": runtime_payload.get("meeting_active"),
                    "meeting_id": runtime_payload.get("meeting_id"),
                    "voice_state": runtime_payload.get("voice_state"),
                    "text_injection_enabled": text_injection_enabled,
                    "text_injection_error": runtime_payload.get("text_injection_error"),
                    "tmux_reply_available": tmux_reply_available,
                    "target_transport": (
                        agent_identity["target_transport"] if agent_identity else None
                    ),
                    "error": runtime_error,
                },
                "companion": {
                    "query_names": sorted(AGENT_QUERY_NAMES),
                    "voice_reply_max_age_seconds": _COMPANION_TARGET_MAX_AGE_SECONDS,
                    "stale_threshold_seconds": DEFAULT_STALE_AGENT_SESSION_SECONDS,
                },
            }
        )

    def _companion_agent_target(payload: Optional[dict[str, Any]]) -> tuple[str, str] | JSONResponse:
        """Pull a required (agent, session_id) pair from a control-route body."""
        body = payload if isinstance(payload, dict) else {}
        agent = body.get("agent")
        session_id = body.get("session_id")
        if not isinstance(agent, str) or not agent.strip():
            return JSONResponse({"error": "agent is required"}, status_code=400)
        if not isinstance(session_id, str) or not session_id.strip():
            return JSONResponse({"error": "session_id is required"}, status_code=400)
        return agent, session_id

    @router.get("/api/coders/sessions")
    async def api_coders_sessions(
        agent: Optional[str] = None, include_ended: bool = True
    ) -> Any:
        """The live coder set (HSM-17-02) in the HSM-17-01 shape.

        Every session the hooks reported, newest first — not just the ones
        waiting on a reply — each carrying its raw `lifecycle`, the pending
        `question` (secret-filtered at ingest), and the decayed effective
        `state` (working | waiting | idle | ended). Sessions past the dead
        window fall out of the live set entirely; `include_ended=false` also
        drops fresh tombstones.
        """
        from ....agent_context import (
            DEFAULT_LIFECYCLE_DEAD_SECONDS,
            LIFECYCLE_ENDED,
            effective_state,
            list_agent_sessions,
        )
        from ....agent_device import build_agent_identity_payload

        try:
            now = datetime.now(timezone.utc)
            items: list[dict[str, Any]] = []
            for session in list_agent_sessions(agent=agent):
                age = _session_age_seconds(session.updated_at, now)
                if age is not None and age > DEFAULT_LIFECYCLE_DEAD_SECONDS:
                    continue
                state = effective_state(session, now=now)
                if state == LIFECYCLE_ENDED and not include_ended:
                    continue
                payload = session.to_dict()
                payload["state"] = state
                items.append(
                    {
                        "session": payload,
                        "age_seconds": age,
                        "identity": build_agent_identity_payload(session),
                    }
                )
            return JSONResponse({"sessions": items, "count": len(items)})
        except Exception as e:
            return error_500("coders sessions", e, log)

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

    @router.post("/api/coders/select")
    async def api_companion_select(payload: Optional[dict[str, Any]] = None) -> Any:
        """Select a specific waiting session as AI PI's active reply target."""
        from ....agent_context import select_awaiting_agent_session

        target = _companion_agent_target(payload)
        if isinstance(target, JSONResponse):
            return target
        agent, session_id = target
        session = select_awaiting_agent_session(agent, session_id)
        if session is None:
            return JSONResponse(
                {"success": False, "error": "unknown_session", "session": None},
                status_code=404,
            )
        return JSONResponse({"success": True, "session": session.to_dict()})

    @router.post("/api/coders/dismiss")
    async def api_companion_dismiss(payload: Optional[dict[str, Any]] = None) -> Any:
        """Clear a waiting session's captured response (non-destructive)."""
        from ....agent_context import clear_agent_session_response

        target = _companion_agent_target(payload)
        if isinstance(target, JSONResponse):
            return target
        agent, session_id = target
        session = clear_agent_session_response(agent=agent, session_id=session_id)
        return JSONResponse(
            {
                "success": session is not None,
                "session": session.to_dict() if session else None,
            }
        )

    @router.post("/api/coders/pin")
    async def api_companion_pin(payload: Optional[dict[str, Any]] = None) -> Any:
        """Pin or unpin a waiting session as the sticky reply target."""
        from ....agent_context import pin_agent_session

        target = _companion_agent_target(payload)
        if isinstance(target, JSONResponse):
            return target
        agent, session_id = target
        body = payload if isinstance(payload, dict) else {}
        pinned = bool(body.get("pinned", True))
        session = pin_agent_session(agent, session_id, pinned)
        if session is None:
            return JSONResponse(
                {"success": False, "error": "unknown_session", "session": None},
                status_code=404,
            )
        return JSONResponse({"success": True, "session": session.to_dict()})

    @router.post("/api/coders/clear-stale")
    async def api_companion_clear_stale(payload: Optional[dict[str, Any]] = None) -> Any:
        """Clear all non-pinned waiting sessions older than the threshold."""
        from ....agent_context import (
            DEFAULT_STALE_AGENT_SESSION_SECONDS,
            clear_stale_agent_sessions,
        )

        body = payload if isinstance(payload, dict) else {}
        raw_age = body.get("max_age_seconds")
        try:
            max_age_seconds = int(raw_age) if raw_age is not None else DEFAULT_STALE_AGENT_SESSION_SECONDS
        except (TypeError, ValueError):
            return JSONResponse({"error": "max_age_seconds must be an integer"}, status_code=400)
        if max_age_seconds < 0:
            return JSONResponse({"error": "max_age_seconds must be >= 0"}, status_code=400)
        cleared = clear_stale_agent_sessions(max_age_seconds=max_age_seconds)
        return JSONResponse(
            {"success": True, "cleared": cleared, "max_age_seconds": max_age_seconds}
        )


    return router
