"""The streaming-dictation socket: one utterance, one admitted pass.

Carved out of ``voice.py`` (HS-132-12) when HS-132-04's wire declaration,
HS-132-05's single final pass, the floor heartbeat and the named refusals grew
that module past the 600-line single-concern budget. The bodies are the bodies
those stories shipped, moved verbatim; nothing here changed behavior.

The interval registry arrives as an injected accessor (``sessions``) instead of
an import of this module's own: the voice lane keeps ONE seam for the browser
mic registry — ``voice.browser_mic_sessions`` — so the socket and the HTTP
open-mic legs can never end up reading two different registries.
"""
from __future__ import annotations

import json
from typing import Any, Callable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ....logging_config import get_logger
from ....speech_session import MIC_INTERVAL_CLOSED, SpeechProviderFailure, SpeechSessionRefused
from ...context import WebContext

from .voice_support import (
    _claim_browser_audio_floor,
    _release_browser_audio_floor,
    _renew_browser_audio_floor,
    _resolve_config,
    _resolve_server,
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


def build_voice_stream_router(
    ctx: WebContext, *, sessions: Callable[[], Any]
) -> APIRouter:
    """The socket, composed by ``build_voice_router`` with the lane's registry."""
    router = APIRouter()

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
            interval = sessions().open(principal)
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
                # HS-176 C1 (the SPOKEN half): the sink the pipeline writes its
                # own three loop facts into. The spoken leg is the one that runs
                # the pipeline and writes the journal row, so it is the only
                # place these facts exist; the delivery that follows sends
                # `raw: true` and rightly invents nothing. R2 forbids a
                # read-time "newest journal row" lookup — they are CARRIED.
                run_facts: dict[str, Any] = {}
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
                        facts=run_facts,
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

                # The `final` frame carries the run's own facts beside the
                # landed text: the APPLIED chip, the TEXT teach's pre-fill and
                # the journal correct route all read them off this one frame. A
                # run that published nothing leaves `run_facts` empty and the
                # frame keeps its old shape — nothing is invented.
                final_frame: dict[str, Any] = {"type": "final", "text": final_text}
                if run_facts:
                    final_frame["raw_text"] = str(run_facts.get("raw_text") or "")
                    final_frame["corrections_applied"] = list(
                        run_facts.get("corrections_applied") or []
                    )
                    final_frame["journal_id"] = run_facts.get("journal_id")
                await websocket.send_json(final_frame)
            else:
                await websocket.send_json({"type": "final", "text": ""})

        except WebSocketDisconnect:
            pass
        except Exception as exc:
            log.debug(f"Streaming dictation error: {exc}")
        finally:
            # The socket closing IS the interval ending: the parent is cancelled
            # and closed here, never left holding authority.
            sessions().close(principal, reason="browser_mic_stream_closed")
            _release_browser_audio_floor(ctx)

    return router
