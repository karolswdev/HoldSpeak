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
    _renew_browser_audio_floor,
    _resolve_config,
    _resolve_server,
    _route_principal,
)

log = get_logger("web.routes.system")


def _macros_enabled(config_snapshot: Any) -> bool:
    """True when this configuration has voice macros turned on.

    Off by default, and checking first keeps the streaming final byte-identical
    (no election, no dispatch) for every desk that never configured a macro.
    """
    macros = getattr(getattr(config_snapshot, "dictation", None), "macros", None)
    return macros is not None and bool(getattr(macros, "enabled", False))


def _dispatch_stream_macro(ctx: WebContext, text: str, config_snapshot: Any) -> Any:
    """Fire a configured macro for a streamed dictate-for-delivery utterance.

    The same bounded, guarded connector the hotkey path and the remote relay
    use. A ``type_text`` macro free-types into the focused app through the
    relay hook, exactly as ``/api/dictation/remote`` does; with no relay hook
    the connector's own refusal is recorded and the utterance dictates as prose
    (a macro failure must never block plain dictation).
    """
    from ....dictation_runner import dispatch_voice_command

    def _type(typed: str) -> None:
        if ctx.on_remote_dictation is None:
            raise RuntimeError("voice_macro_direct_gesture_required")
        ctx.on_remote_dictation(typed, target="focused")

    try:
        return dispatch_voice_command(text, config=config_snapshot, type_writer=_type)
    except Exception as exc:  # a macro failure never blocks plain dictation
        log.error(f"Streaming voice-command dispatch failed: {exc}")
        return None


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
        The server ACCUMULATES them and sends back JSON events:
          {"type": "final",   "text": "..."}   — the utterance's one
                                                 transcription (pipeline-processed
                                                 only when this socket asked for
                                                 the pipeline)
          {"type": "error",   "error": "...",  — a NAMED failure: `reason`,
           "reason": "...", "failure_category": "...",
           "mic_interval": "closed"}             `failure_category`, and the
                                                 closed-interval marker travel
                                                 with it (HS-132-05).

        The client signals end-of-stream by sending a JSON text frame:
          {"type": "end"}

        HS-132-05: there is ONE transcription pass per utterance. Each 600 ms
        chunk used to take an independent full Whisper pass — serialized on the
        very ``transcription_lock`` the hotkey needs, with the worst possible
        context window for hallucination — and the "partial" it produced had no
        consumer anywhere in the client. The chunks still arrive as they are
        captured (bounded memory, and each one heartbeats the audio-floor
        lease); only the final, whole utterance is transcribed.

        HS-132-04: the socket declares WHICH kind of utterance it is carrying,
        once, before the audio:
          {"type": "start", "pipeline": false}
        A speak-to-fill (every desk field mic) is the user typing with their
        voice — it transcribes VERBATIM: no intent routing, no enrichment, no
        rewriting, no journal row. Only a dictate-for-delivery surface (the
        Speak room's TALK key) asks for the pipeline, and it runs exactly once
        here — the delivery that follows sends ``raw: true``. Absent start
        frame -> the pipeline runs, byte-identical to before.
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
            await websocket.send_json(
                {
                    "type": "error",
                    "error": "Transcription unavailable.",
                    "reason": "transcription_unavailable",
                    "failure_category": "transcription_unavailable",
                }
            )
            await websocket.close()
            return

        if not _claim_browser_audio_floor(ctx):
            await websocket.send_json(
                {
                    "type": "error",
                    "error": "Audio floor held by another source.",
                    "reason": "audio_floor_held",
                    "failure_category": "audio_floor_held",
                }
            )
            await websocket.close()
            return

        import numpy as np

        # HS-131-09: ONE admitted interval for this socket's whole lifetime. The
        # utterance's transcription is a trusted child of it — never one session
        # per streamed chunk, which would be admission per frame.
        try:
            interval = browser_mic_sessions().open(principal)
        except SpeechSessionRefused as exc:
            await websocket.send_json(
                {"type": "error", "error": "The microphone session was not admitted.",
                 "reason": exc.reason,
                 "failure_category": "speech_session_refused"}
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
        # HS-132-04: the pipeline is opt-OUT on the wire (an older client that
        # never sends a start frame keeps the pipelined final it was written
        # against), and every field mic opts out explicitly.
        run_pipeline = True
        declared = False
        # HS-132-05: a refusal ENDS the utterance. Nothing may transcribe and
        # deliver a final behind an error the client was already told about.
        refused = False
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break

                # HS-132-05: the floor claim is a LEASE and a dictation can run
                # far longer than one. Every frame that lands IS the heartbeat,
                # so the hotkey, the wake listener or a meeting can never seize
                # the mic mid-utterance. A floor that was genuinely lost stops
                # the capture BY NAME rather than letting this socket keep
                # recording into a microphone somebody else owns.
                if not _renew_browser_audio_floor(ctx):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": "The microphone floor was taken by another source.",
                            "mic_interval": MIC_INTERVAL_CLOSED,
                            "reason": "audio_floor_lost",
                            "failure_category": "audio_floor_lost",
                        }
                    )
                    refused = True
                    break

                if "bytes" in message and message["bytes"]:
                    # Accumulated, not transcribed: one utterance, one pass.
                    all_chunks.append(message["bytes"])

                elif "text" in message and message["text"]:
                    try:
                        payload = json.loads(message["text"])
                    except Exception:
                        continue
                    if payload.get("type") == "start":
                        # Declared once, before the audio: a later frame cannot
                        # turn a speak-to-fill back into a pipelined, journaled
                        # utterance after the words were already captured.
                        if not declared:
                            declared = True
                            run_pipeline = bool(payload.get("pipeline", True))
                        continue
                    if payload.get("type") == "end":
                        break

            if refused:
                # The client already has the named refusal; a final now would
                # hand it words from a session that was told it was over.
                return

            if all_chunks:
                combined = b"".join(all_chunks)
                audio = np.frombuffer(combined, dtype=np.int16).astype(np.float32) / 32768.0
                try:
                    raw_text = transcribe(audio)
                except SpeechSessionRefused as exc:
                    await websocket.send_json(
                        {"type": "error", "error": "The microphone session closed.",
                         "mic_interval": MIC_INTERVAL_CLOSED, "reason": exc.reason,
                         "failure_category": "speech_session_refused"}
                    )
                    return
                except Exception as exc:
                    log.error(f"Final transcription failed: {exc}")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "error": "Transcription failed.",
                            "reason": "transcription_failed",
                            "failure_category": "transcription_failed",
                        }
                    )
                    return

                final_text = raw_text or ""
                if not run_pipeline:
                    # A speak-to-fill: the words the user said, unchanged, into
                    # the field. Nothing is classified, enriched, rewritten or
                    # journaled — there is no second author on this utterance.
                    await websocket.send_json({"type": "final", "text": final_text})
                    return

                config_snapshot = getattr(ctx, "_config", None) or _resolve_config(ctx)

                # HS-132-04: a configured, enabled macro keyword FIRES here —
                # once, on the dictate-for-delivery leg, at the same seam the
                # pipeline runs. The hotkey path dispatches before its pipeline
                # and types nothing on a match (runtime/dictation_capture.py:117-173)
                # and the remote relay does the same (routes/dictation/pipeline.py:724-764);
                # this is that contract for the browser's streaming leg. The
                # delivery that follows carries ``raw: true``, which never
                # dispatches, so a keyword fires exactly once for one utterance.
                # A speak-to-fill NEVER dispatches: typing with your voice is not
                # a command. Macros off (the default) -> this block is inert.
                fired = None
                if _macros_enabled(config_snapshot):
                    def _fire() -> Any:
                        return _dispatch_stream_macro(ctx, final_text, config_snapshot)

                    # Inside the SAME cancellation election the hotkey path uses:
                    # a macro is a real connector effect, and a session cancelled
                    # while Whisper was working must not fire one.
                    elected, fired = interval.session.fence.publish(
                        "browser stream voice-command dispatch", _fire
                    )
                    if not elected:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error": "The microphone session closed.",
                                "mic_interval": MIC_INTERVAL_CLOSED,
                                "reason": interval.session.fence.reason()
                                or "speech_session_not_live",
                                "failure_category": "speech_session_refused",
                            }
                        )
                        return
                if fired is not None and fired.handled:
                    # The command consumed the utterance: no pipeline pass, no
                    # journal row, and nothing typed as prose.
                    await websocket.send_json(
                        {
                            "type": "final",
                            "text": "",
                            "fired": {
                                "keyword": fired.keyword,
                                "kind": fired.kind,
                                "preview": fired.preview,
                                "ok": fired.ok,
                                "error": fired.error,
                            },
                        }
                    )
                    return
                try:
                    from ....dictation_runner import process_transcript
                    # HS-131-09: the final pass's classify/rewrite are children of
                    # THIS socket's interval parent — the same authority the
                    # utterance transcribed under, never unwrapped runtime work.
                    corrected = await process_transcript(
                        raw_text=final_text,
                        source="browser",
                        context=None,
                        config=config_snapshot,
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
