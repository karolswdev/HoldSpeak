"""Meeting-recording and transcript import route.

The route owns multipart upload storage only. ``MeetingService`` owns the
visible importing state and its background import lifecycle.
"""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from ...config import Config
from ...services.errors import ValidationError


def _default_transcriber_factory(config: Config):
    from ...transcribe import Transcriber

    return Transcriber(
        model_name=config.model.name,
        backend=getattr(config.model, "backend", None),
        language=getattr(config.model, "language", "auto"),
    )


# Tests monkeypatch this to inject a fake transcriber.
_transcriber_factory = _default_transcriber_factory


def build_meeting_import_router(ctx) -> APIRouter:
    router = APIRouter()

    def _service():
        service = getattr(ctx, "meeting_service", None)
        if service is None:
            factory = getattr(ctx, "meeting_service_factory", None)
            service = factory() if factory is not None else None
        if service is None:
            raise RuntimeError("MeetingService is not composed")
        return service

    def _principal(request: Request):
        from ...principals import UNAUTHENTICATED

        return getattr(request.state, "principal", UNAUTHENTICATED)

    @router.post("/api/meetings/import")
    async def import_recording(
        request: Request,
        file: UploadFile = File(...),
        title: Optional[str] = Form(None),
        speaker: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),
        started_at_ms: Optional[int] = Form(None),
    ):
        filename = file.filename or "recording"
        try:
            _service().validate_import(_principal(request), filename)
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)

        suffix = Path(filename).suffix.lower() or ".wav"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_path = Path(tmp.name)
        try:
            with tmp:
                shutil.copyfileobj(file.file, tmp)
        except Exception as exc:  # pragma: no cover — disk-level failure
            tmp_path.unlink(missing_ok=True)
            return JSONResponse(
                {"error": f"Could not store the upload on the hub: {exc}. No Meeting was created. Check disk space and retry the import."},
                status_code=500,
            )
        if tmp_path.stat().st_size == 0:
            tmp_path.unlink(missing_ok=True)
            return JSONResponse({"error": "The uploaded file is empty."}, status_code=400)

        started_at = (
            datetime.fromtimestamp(started_at_ms / 1000.0)
            if started_at_ms
            else datetime.now()
        )
        tag_list = [tag.strip() for tag in (tags or "").split(",") if tag.strip()]
        try:
            result = _service().import_meeting(
                _principal(request),
                tmp_path=tmp_path,
                filename=filename,
                title=title,
                speaker=speaker,
                tags=tag_list,
                started_at=started_at,
                config=Config.load(),
                transcriber_factory=_transcriber_factory,
            )
        except ValidationError as exc:
            tmp_path.unlink(missing_ok=True)
            return JSONResponse({"error": exc.detail}, status_code=400)
        return JSONResponse(result, status_code=202)

    return router
