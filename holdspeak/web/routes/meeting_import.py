"""The meeting-import route: upload a recording, get a real meeting.

``POST /api/meetings/import`` accepts a multipart upload, refuses unsupported
formats up front (including the honest missing-ffmpeg message), creates the
meeting row **immediately** in a visible ``importing`` state, and runs the
import engine on a background thread so the event loop stays responsive
during minutes of Whisper. Progress is written into the meeting row's
``intel_status_detail`` (the same load → mutate → ``save_meeting`` pattern
the deferred-intel queue uses), so `/history` polling needs nothing new:
the normal list/detail payloads carry the state.

Status contract on the meeting row:

* ``intel_status="importing"`` + a "Transcribing — window x of y." detail
  while the engine runs;
* on success the engine's own save replaces it with the live-mirrored
  ``queued`` / ``disabled`` intel posture;
* on failure ``intel_status="import_failed"`` + the actionable error detail
  (the row stays, honestly labeled, deletable via the existing delete path).

The Whisper ``Transcriber`` is built lazily **inside** the worker thread
(model load takes seconds) via a module-level factory that tests monkeypatch.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from ...config import Config
from ...meeting_import import (
    DEFAULT_SPEAKER_LABEL,
    MeetingImportError,
    import_meeting,
    validate_format,
)
from ...meeting_session import MeetingState

log = logging.getLogger("holdspeak.web.meeting_import")


def _default_transcriber_factory(config: Config):
    from ...transcribe import Transcriber

    return Transcriber(
        model_name=config.model.name, backend=getattr(config.model, "backend", None)
    )


# Tests monkeypatch this to inject a fake transcriber.
_transcriber_factory = _default_transcriber_factory


def _set_import_status(db, meeting_id: str, status: str, detail: str) -> None:
    """load → mutate → save_meeting, the same pattern the intel queue uses."""
    state = db.meetings.get_meeting(meeting_id)
    if state is None:
        return
    state.intel_status = status
    state.intel_status_detail = detail
    db.meetings.save_meeting(state)


def _run_import_job(
    *,
    db,
    config: Config,
    meeting_id: str,
    tmp_path: Path,
    title: Optional[str],
    speaker: str,
    tags: list[str],
    started_at: datetime,
) -> None:
    try:
        transcriber = _transcriber_factory(config)

        def on_progress(done: int, total: int) -> None:
            _set_import_status(
                db,
                meeting_id,
                "importing",
                f"Transcribing — window {done} of {total}.",
            )

        import_meeting(
            tmp_path,
            db=db,
            transcriber=transcriber,
            config=config,
            meeting_id=meeting_id,
            title=title,
            speaker=speaker,
            tags=tags,
            started_at=started_at,
            progress=on_progress,
        )
        log.info(f"Import finished for meeting {meeting_id}")
    except MeetingImportError as exc:
        log.warning(f"Import failed for meeting {meeting_id}: {exc}")
        _set_import_status(db, meeting_id, "import_failed", str(exc))
    except Exception as exc:  # noqa: BLE001 — surface anything honestly.
        log.error(f"Import crashed for meeting {meeting_id}: {exc}")
        _set_import_status(
            db, meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def build_meeting_import_router(ctx) -> APIRouter:
    router = APIRouter()

    @router.post("/api/meetings/import")
    async def import_recording(
        file: UploadFile = File(...),
        title: Optional[str] = Form(None),
        speaker: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),
        started_at_ms: Optional[int] = Form(None),
    ):
        filename = file.filename or "recording"
        try:
            validate_format(filename)
        except MeetingImportError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

        suffix = Path(filename).suffix.lower() or ".wav"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_path = Path(tmp.name)
        try:
            with tmp:
                shutil.copyfileobj(file.file, tmp)
        except Exception as exc:  # pragma: no cover — disk-level failure
            tmp_path.unlink(missing_ok=True)
            return JSONResponse(
                {"error": f"Could not store the upload: {exc}"}, status_code=500
            )
        if tmp_path.stat().st_size == 0:
            tmp_path.unlink(missing_ok=True)
            return JSONResponse({"error": "The uploaded file is empty."}, status_code=400)

        config = Config.load()
        # The browser can pass the file's real last-modified time so an old
        # recording sorts where it happened, not where it was imported.
        started_at = (
            datetime.fromtimestamp(started_at_ms / 1000.0)
            if started_at_ms
            else datetime.now()
        )
        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
        meeting_id = str(uuid.uuid4())[:8]

        placeholder = MeetingState(
            id=meeting_id,
            started_at=started_at,
            title=(title or Path(filename).stem).strip() or Path(filename).stem,
            tags=tag_list,
            segments=[],
        )
        placeholder.intel_status = "importing"
        placeholder.intel_status_detail = "Preparing transcription…"
        from ...db import get_database

        db = get_database()
        db.meetings.save_meeting(placeholder)

        worker = threading.Thread(
            target=_run_import_job,
            kwargs={
                "db": db,
                "config": config,
                "meeting_id": meeting_id,
                "tmp_path": tmp_path,
                "title": title,
                "speaker": (speaker or DEFAULT_SPEAKER_LABEL),
                "tags": tag_list,
                "started_at": started_at,
            },
            daemon=True,
            name=f"meeting-import-{meeting_id}",
        )
        worker.start()

        return JSONResponse(
            {"meeting_id": meeting_id, "status": "importing"}, status_code=202
        )

    return router
