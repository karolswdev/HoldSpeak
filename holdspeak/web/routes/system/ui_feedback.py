"""Owner-local Desk UI feedback routes."""

from __future__ import annotations

import asyncio
import io
import wave
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.ui_feedback import (
    UIFeedbackConflict,
    UIFeedbackError,
    fail_transcript,
    feedback_audio,
    feedback_transcript,
    save_transcript,
)
from ....services.ui_feedback import enabled as feedback_enabled
from ....services.ui_feedback import save_feedback
from ....speech_session import SpeechSessionRefused

import numpy as np

from .voice import _route_principal

log = get_logger("web.routes.system")


def build_ui_feedback_router(ctx: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/api/ui-feedback/status")
    def api_ui_feedback_status() -> dict[str, bool]:
        return {"enabled": feedback_enabled()}

    @router.post("/api/ui-feedback")
    async def api_ui_feedback(request: Request) -> Any:
        if not feedback_enabled():
            return JSONResponse(
                {"success": False, "error": "UI feedback is disabled."}, status_code=404
            )
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(
                {"success": False, "error": "A JSON object is required."}, status_code=400
            )
        try:
            return JSONResponse(save_feedback(payload))
        except UIFeedbackConflict as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=409)
        except UIFeedbackError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
        except Exception as exc:  # pragma: no cover - filesystem-specific failures
            log.exception("Failed to save local UI feedback: %s", exc)
            return JSONResponse(
                {"success": False, "error": "The local feedback bundle could not be saved."},
                status_code=500,
            )

    @router.post("/api/ui-feedback/{identifier}/transcribe")
    async def api_ui_feedback_transcribe(identifier: str, request: Request) -> Any:
        """Transcribe one already-saved recording under the configured speech route."""
        if not feedback_enabled():
            return JSONResponse(
                {"success": False, "error": "UI feedback is disabled."}, status_code=404
            )
        try:
            current = feedback_transcript(identifier)
        except UIFeedbackError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=404)
        if current.get("transcript_status") == "complete":
            return current
        try:
            raw = feedback_audio(identifier)
            with wave.open(io.BytesIO(raw), "rb") as source:
                frames = source.readframes(source.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        except (OSError, EOFError, ValueError, wave.Error) as exc:
            log.exception("Saved feedback audio could not be decoded: %s", exc)
            return fail_transcript(identifier, "audio_unreadable")

        if ctx.on_transcribe_admitted is None:
            return fail_transcript(identifier, "transcription_unavailable")

        principal = _route_principal(request)

        def transcribe_and_attach() -> dict[str, Any]:
            admitted = None
            outcome = "failed"
            try:
                admitted = ctx.on_transcribe_admitted(
                    audio,
                    principal=principal,
                    mic_handle="",
                    verbatim=True,
                )
                text = str(admitted.text)
                if not text.strip():
                    return fail_transcript(identifier, "no_speech")
                boundary = str(admitted.provider.egress_boundary)
                result = save_transcript(identifier, text, boundary)
                outcome = "succeeded"
                return result
            except SpeechSessionRefused as exc:
                return fail_transcript(identifier, exc.reason)
            except Exception as exc:  # pragma: no cover - provider/runtime specific
                log.exception("Saved feedback transcription failed: %s", exc)
                reason = str(getattr(exc, "reason", "") or "transcription_failed")
                return fail_transcript(identifier, reason)
            finally:
                if admitted is not None:
                    admitted.close(outcome)

        return await asyncio.to_thread(transcribe_and_attach)

    return router


__all__ = ["build_ui_feedback_router"]
