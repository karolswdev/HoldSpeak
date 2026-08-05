"""The voice lane: wake type, hub transcribe, the preview one-shots, the command test.

Bodies moved verbatim from routes/system.py (HS-79-02, the Phase-63 discipline).
"""
from __future__ import annotations

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


_BROWSER_MIC_OWNER = "browser_mic"


def _resolve_config(ctx: WebContext) -> Any:
    """Load the runtime config for pipeline processing."""
    from ....config import Config
    return Config.load()


def _resolve_server(ctx: WebContext) -> Any:
    """Build a server-like namespace the dictation pipeline can read."""
    from types import SimpleNamespace
    return SimpleNamespace(
        dictation_corrections=ctx.corrections,
        dictation_telemetry=ctx.telemetry,
        dictation_journal=ctx.journal,
    )


def _admit_browser_pipeline(request: Any) -> tuple[bool, str]:
    """Admit the browser pipeline operation through the kernel.

    Returns (admitted, egress_boundary). If the kernel refuses, admitted
    is False and the caller must not process. Best-effort: if the kernel
    is not available, returns (True, "local").
    """
    try:
        from ....kernel.runtime import _service
        from ....principals import UNAUTHENTICATED

        principal = getattr(getattr(request, "state", None), "principal", UNAUTHENTICATED)
        broker = _service()

        import uuid

        operation_id = "op_" + uuid.uuid4().hex
        invocation_id = "browser_pipeline_" + uuid.uuid4().hex
        handle = broker.submit(
            {
                "request_schema": 1,
                "request_id": str(uuid.uuid4()),
                "idempotency_key": invocation_id,
                "operation": {"name": "inference.run", "version": 1},
                "target": {},
                "arguments": {
                    "invocation_id": invocation_id,
                    "definition_ref": "program:browser-mic-pipeline-v1",
                    "definition_revision": "1",
                    "grounding_refs": [],
                    "requested_target_id": "this_machine",
                    "deadline_at": __import__("time").time() + 30,
                    "input_snapshot": {"source": "browser"},
                },
            },
            principal,
        )
        state = handle.get("state", "")
        if state == "refused":
            reason = handle.get("reason", "kernel refused the operation")
            return False, "none"
        # Derive boundary from the admitted operation
        boundary = handle.get("egress_boundary", "local")
        return True, str(boundary) if boundary else "local"
    except Exception:
        # Kernel not available -- admit by default (local Whisper is safe)
        return True, "local"


def _claim_browser_audio_floor(ctx: WebContext) -> bool:
    """Claim the audio floor for the browser mic, returning True if granted."""
    session = getattr(ctx, "voice_session", None)
    if session is None:
        return True  # no arbiter -- nothing to contend with
    return session.acquire(_BROWSER_MIC_OWNER, lease_seconds=30.0)


def _release_browser_audio_floor(ctx: WebContext) -> None:
    """Release the browser mic's audio floor claim."""
    session = getattr(ctx, "voice_session", None)
    if session is not None:
        session.release(_BROWSER_MIC_OWNER)


def build_voice_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.post("/api/dictation/wake/type")
    async def api_wake_type(payload: dict[str, Any]) -> Any:
        """HS-60: type a stored wake preview, exactly once.

        The token was minted server-side when the preview was created; the
        runtime types ONLY its own stored text and burns the token. Client
        text is never accepted here.
        """
        if ctx.on_wake_type is None:
            return JSONResponse(
                {"success": False, "error": "Wake typing is unavailable in this runtime. Nothing was typed. Start the desktop runtime and retry."},
                status_code=503,
            )
        token = str((payload or {}).get("token", "")).strip()
        if not token:
            return JSONResponse(
                {"success": False, "error": "A preview token is required."},
                status_code=400,
            )
        typed = ctx.on_wake_type(token)
        if typed is None:
            return JSONResponse(
                {"success": False, "error": "Unknown or already used preview token."},
                status_code=404,
            )
        return {"success": True, "typed": typed}

    @router.post("/api/dictation/transcribe")
    async def api_transcribe(request: Request) -> Any:
        """HS-78-01: speak-to-fill -- browser-captured audio in, text out.

        Accepts one WAV (16 kHz mono, 16-bit PCM) body and runs the
        runtime's OWN transcriber (one model, one lock) + the dictation
        punctuation pass. The audio is never persisted and nothing
        egresses (local Whisper); the route rides the same
        loopback/token posture as every other route. Size-capped.

        HS-118-08: the ``pipeline`` field in the JSON body (or, for raw
        audio bodies, a query parameter) gates the full dictation pipeline
        (corrections, learning loop, journaling). The kernel admits the
        operation BEFORE inference; if refused, an error is returned. The
        response carries ``text`` (corrected), ``raw`` (original), and
        ``egress_boundary`` (derived from the kernel admission).
        """
        if ctx.on_transcribe is None:
            return JSONResponse(
                {"success": False, "error": "Transcription is unavailable in this runtime. Your audio is kept in the browser for Retry. Start the desktop runtime."},
                status_code=503,
            )

        # Read pipeline flag from query params (for octet-stream bodies)
        pipeline = request.query_params.get("pipeline", "").lower() in ("true", "1")

        raw = await request.body()
        if not raw:
            return JSONResponse(
                {"success": False, "error": "An audio body is required."}, status_code=400
            )
        if len(raw) > 16_000_000:  # ~8 minutes of 16 kHz mono 16-bit
            return JSONResponse(
                {"success": False, "error": "Audio too large (cap: 16 MB)."}, status_code=413
            )

        # HS-118-08: kernel admission BEFORE inference.
        egress_boundary = "local"
        if pipeline:
            try:
                admitted, egress_boundary = _admit_browser_pipeline(request)
                if not admitted:
                    return JSONResponse(
                        {"success": False, "error": "Kernel refused the browser pipeline operation."},
                        status_code=403,
                    )
            except Exception as exc:
                log.debug(f"Kernel admission skipped for browser pipeline: {exc}")

        try:
            import io
            import wave

            import numpy as np

            with wave.open(io.BytesIO(raw)) as wf:
                if wf.getnchannels() != 1 or wf.getframerate() != 16000 or wf.getsampwidth() != 2:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "Expected WAV: 16 kHz, mono, 16-bit PCM.",
                        },
                        status_code=400,
                    )
                frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception:
            return JSONResponse(
                {"success": False, "error": "Not a readable WAV body."}, status_code=400
            )
        try:
            text = ctx.on_transcribe(audio)
        except Exception as exc:
            log.error(f"speak-to-fill transcription failed: {exc}")
            return JSONResponse(
                {"success": False, "error": "Transcription failed. Your audio is kept in the browser for Retry."},
                status_code=502,
            )

        if not pipeline:
            return {"success": True, "text": text}

        # HS-118-08: full pipeline path -- corrections, learning, journaling.
        raw_text = text
        try:
            from ....dictation_runner import process_transcript

            corrected = await process_transcript(
                raw_text=raw_text,
                source="browser",
                context=None,
                config=getattr(ctx, "_config", None) or _resolve_config(ctx),
                server=_resolve_server(ctx),
            )
        except Exception as exc:
            log.warning(f"Browser pipeline processing failed, returning raw: {exc}")
            corrected = raw_text

        return {
            "success": True,
            "text": corrected,
            "raw": raw_text,
            "egress_boundary": egress_boundary,
        }

    @router.post("/api/dictation/preview/type")
    async def api_preview_type(payload: dict[str, Any]) -> Any:
        """HS-75-01: type a stored hold-key preview, exactly once.

        The token was minted server-side when the preview armed; the
        runtime types ONLY its own stored text and burns the token. Client
        text is never accepted here (the wake/type contract).
        """
        if ctx.on_preview_type is None:
            return JSONResponse(
                {"success": False, "error": "Preview typing is unavailable in this runtime. Nothing was typed. Start the desktop runtime and retry."},
                status_code=503,
            )
        token = str((payload or {}).get("token", "")).strip()
        if not token:
            return JSONResponse(
                {"success": False, "error": "A preview token is required."},
                status_code=400,
            )
        typed = ctx.on_preview_type(token)
        if typed is None:
            return JSONResponse(
                {"success": False, "error": "Unknown or already used preview token."},
                status_code=404,
            )
        return {"success": True, "typed": typed}

    @router.post("/api/dictation/preview/discard")
    async def api_preview_discard(payload: dict[str, Any]) -> Any:
        """HS-75-01: burn a stored preview without typing."""
        if ctx.on_preview_discard is None:
            return JSONResponse(
                {"success": False, "error": "Preview discard is unavailable in this runtime. The preview is unchanged. Start the desktop runtime and retry."},
                status_code=503,
            )
        token = str((payload or {}).get("token", "")).strip()
        if not token:
            return JSONResponse(
                {"success": False, "error": "A preview token is required."},
                status_code=400,
            )
        if not ctx.on_preview_discard(token):
            return JSONResponse(
                {"success": False, "error": "Unknown or already used preview token."},
                status_code=404,
            )
        return {"success": True}

    @router.post("/api/commands/test")
    async def api_test_voice_command(payload: dict[str, Any]) -> Any:
        """HS-52-05: fire one voice command action from the board, to verify it.

        Egress kinds (open_url / launch_app / shell) run on the host through the same
        bounded connector the dispatcher uses (the browser cannot open a terminal). The
        `type_text` kind types into whatever app has focus when the keyword is spoken, so
        there is nothing to run here; it returns a preview instead of firing.
        """
        from ....config import VoiceMacroAction, VoiceMacroError

        try:
            action = VoiceMacroAction(
                kind=str((payload or {}).get("kind", "")),
                payload=str((payload or {}).get("payload", "")),
            )
        except VoiceMacroError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

        if action.kind == "type_text":
            return JSONResponse({
                "ok": True,
                "tested": False,
                "preview": action.preview(),
                "note": "types into the focused app",
            })

        from ....plugins.actuators import ActuatorProposal
        from ....plugins.voice_macro_connector import build_voice_macro_connector

        proposal = ActuatorProposal(
            target="voice_macro",
            action=action.kind,
            preview=action.preview(),
            payload={"kind": action.kind, "payload": action.payload},
            reversible=False,
            required_capabilities=(),
        )
        try:
            connector = build_voice_macro_connector(action)
            result = connector(proposal)
            return JSONResponse({"ok": True, "tested": True, "result": result})
        except Exception as exc:  # a failed command is reported inline, not as a 5xx
            return JSONResponse({"ok": False, "error": f"{type(exc).__name__}: {exc}"})


    return router
