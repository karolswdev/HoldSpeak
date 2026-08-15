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
from ....speech_session import (
    MIC_INTERVAL_CLOSED,
    OUTCOME_INDETERMINATE,
    SpeechProviderFailure,
    SpeechSessionRefused,
    browser_mic_sessions,
)
from ...context import WebContext
from ...runtime_support import error_500

from .voice_support import (
    _BROWSER_MIC_OWNER,
    _claim_browser_audio_floor,
    _mic_interval_closed,
    _release_browser_audio_floor,
    _resolve_config,
    _resolve_server,
    _route_principal,
)

log = get_logger("web.routes.system")


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

    @router.post("/api/dictation/mic/open")
    async def api_mic_open(request: Request) -> Any:
        """Open ONE admitted open-mic interval for this authenticated identity.

        HS-131-09: the click-to-toggle mic is one authority lifetime, so it admits
        exactly one ``dictation.session`` here and every utterance in the interval
        is a trusted child of it. The response carries an OPAQUE server-issued
        handle; the client cannot name a parent.
        """
        try:
            interval = browser_mic_sessions().open(_route_principal(request))
        except SpeechSessionRefused as exc:
            return JSONResponse(
                {
                    "success": False,
                    "reason": exc.reason,
                    "error": "The microphone session was not admitted. Nothing is being captured.",
                },
                status_code=403,
            )
        return {
            "success": True,
            "mic_session": interval.handle,
            "expires_at": interval.ceiling_at,
            "inactivity_expires_at": interval.lease_until,
        }

    @router.post("/api/dictation/mic/close")
    async def api_mic_close(request: Request) -> Any:
        """Close the interval: the parent is cancelled and closed, not left live."""
        closed = browser_mic_sessions().close(
            _route_principal(request), reason="browser_mic_stopped"
        )
        return {"success": True, "closed": bool(closed)}

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
        (corrections, learning loop, journaling). The response carries ``text``
        (corrected), ``raw`` (original), and ``egress_boundary``.

        HS-131-09: the utterance's OWN admitted speech session is the kernel
        admission — every transcription and every pipeline model call is a
        receipted child of it, and a refusal comes from THAT admission. The
        ``egress_boundary`` is read from the deployment revision the session
        froze, so the label and the receipts name the same destination.
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

        # HS-131-09 (Sol round 2): there is no separate browser-pipeline
        # admission any more. The utterance's OWN speech session is the
        # admission — it parents and authorizes every model call below — and the
        # egress label is read from the revision that session FROZE, not from a
        # parallel operation that could refuse a valid session or default to
        # "local" whenever the kernel errored.
        egress_boundary = "local"
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
        # HS-131-09: with the pipeline on, classify/rewrite are real model calls,
        # so the utterance's parent must stay OPEN through them and they must run
        # as its children. The admitted seam hands that authority back; the raw
        # path (no pipeline) keeps the closes-immediately seam.
        admitted = None
        transcribe = ctx.on_transcribe_admitted if pipeline else None
        if pipeline and transcribe is None:
            # The pipeline reaches a model. Without the admitted seam there is no
            # authority to run it under, and an unadmitted dispatch is never the
            # fallback.
            return JSONResponse(
                {
                    "success": False,
                    "error": "The dictation pipeline is unavailable in this runtime. "
                    "Nothing was processed. Retry without the pipeline.",
                },
                status_code=503,
            )
        try:
            if transcribe is not None:
                admitted = transcribe(
                    audio,
                    principal=_route_principal(request),
                    mic_handle=str(request.query_params.get("mic_session", "") or ""),
                )
                text = str(admitted.text)
                egress_boundary = str(admitted.provider.egress_boundary)
            else:
                text = ctx.on_transcribe(
                    audio,
                    principal=_route_principal(request),
                    mic_handle=str(request.query_params.get("mic_session", "") or ""),
                )
        except SpeechSessionRefused as exc:
            # Inside an interval that just hit a fence: the client is told by name
            # and closes the interval (Sol Amendment 3).
            return _mic_interval_closed(
                exc.reason,
                "The microphone session closed. Click the mic again to continue; "
                "your audio is kept in the browser for Retry.",
            )
        except Exception as exc:
            log.error(f"speak-to-fill transcription failed: {exc}")
            return JSONResponse(
                {"success": False, "error": "Transcription failed. Your audio is kept in the browser for Retry."},
                status_code=502,
            )

        if not pipeline:
            return {"success": True, "text": text}

        # HS-118-08: full pipeline path -- corrections, learning, journaling.
        # HS-131-09: run under the utterance's OWN admission, so every classify and
        # rewrite is a receipted child; the parent then closes with the honest
        # outcome (failed when the pipeline raised).
        raw_text = text
        outcome = "succeeded"
        failure_body: dict[str, Any] | None = None
        failure_status = 0
        terminal = ""
        try:
            from ....dictation_runner import process_transcript

            corrected = await process_transcript(
                raw_text=raw_text,
                source="browser",
                context=None,
                config=getattr(ctx, "_config", None) or _resolve_config(ctx),
                server=_resolve_server(ctx),
                admission=None if admitted is None else admitted.provider,
            )
        except SpeechSessionRefused as exc:
            # A control refusal is never DIR-F-003 degradation. Nothing may turn
            # it into a successful raw transcript after the admitted child said
            # this session/capability/revision was not authorized or no longer live.
            outcome = "refused"
            failure_status = 422
            failure_body = {
                "success": False,
                "error": exc.reason,
                "reason": exc.reason,
                "refusal": exc.reason,
                "failure_category": "speech_session_refused",
            }
        except SpeechProviderFailure as exc:
            outcome = "failed"
            failure_status = 502
            failure_body = {
                "success": False,
                "error": f"{exc.contract}:{exc.reason}",
                "reason": exc.reason,
                "failure_category": "speech_provider_failure",
            }
        except Exception as exc:
            log.warning(f"Browser pipeline processing failed, returning raw: {exc}")
            corrected = raw_text
            outcome = "failed"
        finally:
            if admitted is not None:
                terminal = admitted.close(outcome)

        terminal_marker = (
            {"session_terminal": OUTCOME_INDETERMINATE}
            if terminal == OUTCOME_INDETERMINATE
            else {}
        )
        if failure_body is not None:
            return JSONResponse(
                {**failure_body, **terminal_marker}, status_code=failure_status
            )
        return {
            "success": True,
            "text": corrected,
            "raw": raw_text,
            "egress_boundary": egress_boundary,
            **terminal_marker,
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


    @router.websocket("/ws/dictation/stream")
    async def ws_dictation_stream(websocket: WebSocket) -> None:
        """HS-119-01: streaming transcription for the click-to-toggle mic.

        The client sends raw 16 kHz mono 16-bit PCM chunks as binary frames.
        The server transcribes each chunk and sends back JSON events:
          {"type": "partial", "text": "..."}   — progressive Whisper result
          {"type": "final",   "text": "..."}   — pipeline-processed final text
          {"type": "error",   "error": "..."}  — named failure

        The client signals end-of-stream by sending a JSON text frame:
          {"type": "end"}
        """
        from .... import web_auth
        from ....principals import derive_owner, agent_credentials, UNAUTHENTICATED, PrincipalRight

        provided = web_auth.extract_request_token(
            authorization=websocket.headers.get("authorization"),
            header_token=websocket.headers.get("x-holdspeak-token"),
        ) or web_auth.extract_websocket_token(
            websocket.headers.get("sec-websocket-protocol")
        )
        principal = derive_owner(provided, ctx.web_auth_token)
        if principal is None:
            principal = agent_credentials.derive(provided)
        principal = principal or UNAUTHENTICATED
        if not principal.permits(PrincipalRight.OWNER):
            await websocket.close(code=1008, reason="auth_required")
            return

        offered = {
            item.strip()
            for item in str(websocket.headers.get("sec-websocket-protocol") or "").split(",")
        }
        selected = web_auth.WEBSOCKET_PROTOCOL if web_auth.WEBSOCKET_PROTOCOL in offered else None
        await websocket.accept(subprotocol=selected)

        if ctx.on_transcribe is None:
            await websocket.send_json({"type": "error", "error": "Transcription unavailable."})
            await websocket.close()
            return

        if not _claim_browser_audio_floor(ctx):
            await websocket.send_json({"type": "error", "error": "Audio floor held by another source."})
            await websocket.close()
            return

        import io
        import wave
        import numpy as np

        # HS-131-09: ONE admitted interval for this socket's whole lifetime. Every
        # partial and the final utterance are trusted children of it — never one
        # session per streamed chunk, which would be admission per frame.
        try:
            interval = browser_mic_sessions().open(principal)
        except SpeechSessionRefused as exc:
            await websocket.send_json(
                {"type": "error", "error": "The microphone session was not admitted.",
                 "reason": exc.reason}
            )
            _release_browser_audio_floor(ctx)
            await websocket.close()
            return
        mic_handle = interval.handle

        def transcribe(chunk: Any) -> str:
            return str(
                ctx.on_transcribe(chunk, principal=principal, mic_handle=mic_handle) or ""
            )

        all_chunks: list[bytes] = []
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break

                if "bytes" in message and message["bytes"]:
                    chunk_bytes = message["bytes"]
                    all_chunks.append(chunk_bytes)
                    audio = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                    if len(audio) < 1600:
                        continue
                    try:
                        partial_text = transcribe(audio)
                        await websocket.send_json({"type": "partial", "text": partial_text or ""})
                    except SpeechSessionRefused as exc:
                        # The interval hit a fence mid-stream: named, closed, and
                        # the client must click again (Sol Amendment 3).
                        await websocket.send_json(
                            {"type": "error", "error": "The microphone session closed.",
                             "mic_interval": MIC_INTERVAL_CLOSED, "reason": exc.reason}
                        )
                        break
                    except Exception as exc:
                        log.debug(f"Streaming partial transcription failed: {exc}")

                elif "text" in message and message["text"]:
                    try:
                        payload = json.loads(message["text"])
                    except Exception:
                        continue
                    if payload.get("type") == "end":
                        break

            if all_chunks:
                combined = b"".join(all_chunks)
                audio = np.frombuffer(combined, dtype=np.int16).astype(np.float32) / 32768.0
                try:
                    raw_text = transcribe(audio)
                except SpeechSessionRefused as exc:
                    await websocket.send_json(
                        {"type": "error", "error": "The microphone session closed.",
                         "mic_interval": MIC_INTERVAL_CLOSED, "reason": exc.reason}
                    )
                    return
                except Exception as exc:
                    log.error(f"Final transcription failed: {exc}")
                    await websocket.send_json({"type": "error", "error": "Transcription failed."})
                    return

                final_text = raw_text or ""
                try:
                    from ....dictation_runner import process_transcript
                    # HS-131-09: the final pass's classify/rewrite are children of
                    # THIS socket's interval parent — the same authority the
                    # utterance transcribed under, never unwrapped runtime work.
                    corrected = await process_transcript(
                        raw_text=final_text,
                        source="browser",
                        context=None,
                        config=getattr(ctx, "_config", None) or _resolve_config(ctx),
                        server=_resolve_server(ctx),
                        admission=interval.session.provider(),
                    )
                    final_text = corrected
                except SpeechSessionRefused as exc:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": exc.reason,
                            "reason": exc.reason,
                            "failure_category": "speech_session_refused",
                        }
                    )
                    return
                except SpeechProviderFailure as exc:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": f"{exc.contract}:{exc.reason}",
                            "reason": exc.reason,
                            "failure_category": "speech_provider_failure",
                        }
                    )
                    return
                except Exception as exc:
                    log.warning(f"Pipeline processing failed, returning raw: {exc}")

                await websocket.send_json({"type": "final", "text": final_text})
            else:
                await websocket.send_json({"type": "final", "text": ""})

        except WebSocketDisconnect:
            pass
        except Exception as exc:
            log.debug(f"Streaming dictation error: {exc}")
        finally:
            # The socket closing IS the interval ending: the parent is cancelled
            # and closed here, never left holding authority.
            browser_mic_sessions().close(principal, reason="browser_mic_stream_closed")
            _release_browser_audio_floor(ctx)

    return router
