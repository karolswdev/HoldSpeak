"""`holdspeak import` — import an existing recording as a meeting.

Synchronous (the right shape for huge files and headless machines): decodes,
transcribes window by window with visible progress, persists the meeting, and
reports the intel posture. Exits non-zero on a refusal or failure.
"""

from __future__ import annotations

import sys
from pathlib import Path


def run_import_command(args) -> int:
    from ..config import Config
    from ..db import get_database
    from ..meeting_import import (
        DEFAULT_SPEAKER_LABEL,
        MeetingImportError,
        import_meeting,
        validate_format,
    )

    path = Path(args.file).expanduser()
    config = Config.load()

    try:
        validate_format(path.name)
    except MeetingImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Importing {path.name} …")
    print(f"  model: {config.model.name} (loading)")
    from ..transcribe import Transcriber

    transcriber = Transcriber(
        model_name=config.model.name, backend=getattr(config.model, "backend", None)
    )

    def on_progress(done: int, total: int) -> None:
        print(f"  transcribing window {done}/{total}", flush=True)

    try:
        result = import_meeting(
            path,
            db=get_database(),
            transcriber=transcriber,
            config=config,
            title=args.title,
            speaker=args.speaker or DEFAULT_SPEAKER_LABEL,
            tags=args.tag or [],
            progress=on_progress,
        )
    except MeetingImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    state = result.state
    minutes, seconds = divmod(int(result.duration_seconds), 60)
    print(
        f"Imported meeting {state.id}: \"{state.title}\" — "
        f"{len(state.segments)} segment(s), {minutes}m{seconds:02d}s."
    )
    if result.intel_job_enqueued:
        print(
            "Meeting intelligence queued. Process it with `holdspeak intel --process` "
            "or let the web runtime pick it up."
        )
    else:
        print(f"Meeting intelligence: {state.intel_status_detail}")
    print("Review it on the History page of the web runtime.")
    return 0
