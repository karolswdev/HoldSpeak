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
        """Resolve a steering key to a session-like target.

        Two key shapes (HS-89-02): a `pane:%N` key resolves DIRECTLY to
        that raw tmux pane (attach to ANY pane, beyond the hook registry —
        a hand-started pane is first-class); every other key is an
        `agent:session_id` resolved against the registry. A JSONResponse
        when the key is malformed or the session is gone.
        """
        if key.startswith("pane:"):
            pane_id = key[len("pane:"):].strip()
            if not pane_id:
                return JSONResponse(
                    {"error": "key must be pane:%N"}, status_code=400
                )
            # A synthetic session over the raw pane — `resolve_pane_target`
            # reads `tmux_pane`, so the whole spine (arm pins %N, steer/keys
            # re-verify it) works unchanged. Fresh `updated_at`: a raw pane
            # is never "stale" the way a registry record can be.
            from types import SimpleNamespace

            return SimpleNamespace(
                agent="pane",
                session_id=pane_id,
                awaiting_response=False,
                question=None,
                updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                tmux_pane=pane_id,
                last_assistant_text=None,
            )

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

    @router.get("/api/coders/steering/panes")
    async def api_coder_panes() -> Any:
        """Every tmux pane on the machine (HS-89-02) — the discovery behind
        attach-to-any-pane. Read-only (no grant): the desk lists panes with
        their session/window/command/title so a human can watch any of them
        free, then arm the one they mean by its `pane:%N` key. No tmux
        server is an honest empty list."""
        from .... import coder_steering

        try:
            result = await asyncio.to_thread(coder_steering.list_panes)
            return JSONResponse(result)
        except Exception as e:
            return error_500("steering panes", e, log)

    # --- cross-machine steering (HS-89-03) ---------------------------------
    #
    # Relay a steering verb to a CONFIGURED node's own steering routes. The
    # node executes against its OWN tmux and enforces its OWN consent + audit
    # (the machine that types owns the record). A quiet node refuses by name
    # (502 node_offline); the node's own typed refusal rides through as 409.

    async def _relay(node: str, verb: str, key: str, *, method: str = "POST", body: Any = None):
        from .... import coder_steering_relay

        result = await asyncio.to_thread(
            coder_steering_relay.relay, node, verb, key, method=method, body=body
        )
        return JSONResponse(result, status_code=coder_steering_relay.relay_http_code(result))

    @router.get("/api/coders/relay/{node}/peek")
    async def api_relay_peek(
        node: str, key: str, lines: int = 200, last_hash: Optional[str] = None
    ) -> Any:
        verb = f"peek?lines={lines}" + (f"&last_hash={last_hash}" if last_hash else "")
        return await _relay(node, verb, key, method="GET")

    @router.post("/api/coders/relay/{node}/arm")
    async def api_relay_arm(node: str, payload: Optional[dict[str, Any]] = None) -> Any:
        body = payload if isinstance(payload, dict) else {}
        key = str(body.get("key", "")).strip()
        if not key:
            return JSONResponse({"error": "key is required"}, status_code=400)
        ttl = {"ttl_seconds": body["ttl_seconds"]} if "ttl_seconds" in body else {}
        return await _relay(node, "arm", key, body=ttl)

    @router.post("/api/coders/relay/{node}/disarm")
    async def api_relay_disarm(node: str, payload: Optional[dict[str, Any]] = None) -> Any:
        body = payload if isinstance(payload, dict) else {}
        key = str(body.get("key", "")).strip()
        if not key:
            return JSONResponse({"error": "key is required"}, status_code=400)
        return await _relay(node, "disarm", key, body={})

    @router.post("/api/coders/relay/{node}/steer")
    async def api_relay_steer(node: str, payload: Optional[dict[str, Any]] = None) -> Any:
        body = payload if isinstance(payload, dict) else {}
        key = str(body.get("key", "")).strip()
        if not key:
            return JSONResponse({"error": "key is required"}, status_code=400)
        forwarded = {k: v for k, v in body.items() if k != "key"}
        return await _relay(node, "steer", key, body=forwarded)

    @router.post("/api/coders/relay/{node}/keys")
    async def api_relay_keys(node: str, payload: Optional[dict[str, Any]] = None) -> Any:
        body = payload if isinstance(payload, dict) else {}
        key = str(body.get("key", "")).strip()
        if not key:
            return JSONResponse({"error": "key is required"}, status_code=400)
        return await _relay(node, "keys", key, body={"keys": body.get("keys")})

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
        raw_r = grounding.get("rails")
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
        rails_refs = [x for x in raw_r if isinstance(x, dict)] if isinstance(raw_r, list) else []
        expand = str(grounding.get("expand") or "summary").strip() or "summary"
        if expand not in GROUNDING_EXPANDS:
            return JSONResponse(
                {"error": f"expand {expand!r} is not one of {list(GROUNDING_EXPANDS)}"},
                status_code=400,
            )
        if len(meeting_ids) + len(artifact_ids) + len(rails_refs) > GROUNDING_MAX_REFS:
            return JSONResponse(
                {"error": f"grounding is capped at {GROUNDING_MAX_REFS} refs"},
                status_code=400,
            )
        blocks, unknown = hydrate_refs(
            get_database(), meeting_ids, artifact_ids, expand
        )
        # HS-88-01: rails objects ground through the same block type,
        # CLI-mediated per repo — a receipt, folded in after desk objects.
        if rails_refs:
            from ....grounding_rails import hydrate_rails_refs

            r_blocks, r_unknown = hydrate_rails_refs(rails_refs)
            blocks = list(blocks) + r_blocks
            unknown = list(unknown) + r_unknown
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

    @router.post("/api/coders/{key}/keys")
    async def api_coder_keys(
        key: str, payload: Optional[dict[str, Any]] = None
    ) -> Any:
        """Send a KEY sequence through THE chokepoint (HS-89-01).

        Full key control: `C-c` to interrupt a runaway, arrows/`Escape`/
        `Tab` to drive a TUI — not just literal text. The body is
        `{"keys": [...]}` where each item is a named key (a string like
        `"C-c"`, or `{"key": "C-c"}`) or a literal run (`{"literal": "…"}`).
        Named keys are held to an allow-list — an unknown key is refused by
        name (409 `unknown_key`), never sent. Unarmed is a typed 409 (the
        desk shows ARM); a revoking refusal broadcasts its frame. Delivered
        or refused, every key sequence is audited.
        """
        from .... import coder_steering

        try:
            session = _registry_session(key)
        except Exception as e:
            return error_500("coder keys", e, log)
        if isinstance(session, JSONResponse):
            return session
        body = payload if isinstance(payload, dict) else {}
        target = coder_steering.resolve_pane_target(session)
        result = await asyncio.to_thread(
            coder_steering.deliver_keys,
            key,
            body.get("keys"),
            current_target=target,
            agent=session.agent,
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

    @router.post("/api/coders/{key}/keep-note")
    async def api_coder_keep_note(
        key: str, payload: Optional[dict[str, Any]] = None
    ) -> Any:
        """Classify (HS-87-05): keep the session's current ask as a desk
        note. The body is the ask; a lineage line names the session, the
        agent, and the moment — so the filed note opens, ropes, and
        traces like any primitive (no new store). An override title/body
        lets the composer name it (with the mic, per canon)."""
        from datetime import datetime, timezone

        from ....db import get_database
        from ..primitives._shared import _new_id  # the primitives id minter

        try:
            session = _registry_session(key)
        except Exception as e:
            return error_500("coder keep-note", e, log)
        if isinstance(session, JSONResponse):
            return session
        body = payload if isinstance(payload, dict) else {}
        ask = str(
            body.get("body")
            or getattr(session, "question", None)
            or getattr(session, "last_assistant_text", None)
            or ""
        )
        if not ask.strip():
            return JSONResponse(
                {"error": "nothing to keep — the session has no current ask"},
                status_code=400,
            )
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        title = str(body.get("title") or "").strip() or f"From {session.agent} · {key}"
        lineage = f"> kept from session `{key}` ({session.agent}) at {ts}"
        note_body = f"{lineage}\n\n{ask}"
        try:
            note = await asyncio.to_thread(
                get_database().notes.upsert,
                note_id=_new_id("note"),
                title=title,
                body_markdown=note_body,
                tags=["session", session.agent],
            )
            return JSONResponse({"note": note.to_dict()}, status_code=201)
        except Exception as e:
            return error_500("coder keep-note", e, log)

    return router
