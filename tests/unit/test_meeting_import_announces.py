"""HS-202-02 (coordinator item 9) — an import announces itself.

Astra's first-use fence caught `import-refresh` failing at both widths:
after an Import, the meeting record does not show the transcript or
`Run summary` without a browser reload.

Traced: the import route answers `202` and hands the work to a background
thread (`MeetingService.import_meeting`), and `_run_import_job` publishes
NOTHING when that thread finishes — no frame, no broadcast, nothing the
open face could listen to. The Meetings face already subscribes to
`desk_changed`; the desk really did change (a meeting gained a
transcript), so the import says so.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import holdspeak.db as hsdb
from holdspeak.config import Config
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "the-owner")


def _service(tmp_path: Path, announced: list[tuple[str, str, str]]):
    from holdspeak.services.meeting_service import MeetingService

    reset_database()
    db = Database(tmp_path / "hs202-import.db")
    service = MeetingService(db)
    # The seam the product uses for a writer with no `on_changed` of its
    # own (`holdspeak/runtime/composition.py:343`).
    import holdspeak.services.meeting_service as module

    module.notify_desk_changed = lambda kind, obj_id, op: announced.append(
        (kind, obj_id, op)
    )
    return db, service


def _transcript(tmp_path: Path) -> Path:
    path = tmp_path / "hs-202-02.txt"
    path.write_text(
        "Karol: The freeze window moves to Sunday.\n"
        "Priya: I will confirm with payments before Friday.\n"
    )
    return path


def test_a_finished_import_announces_the_desk_change(tmp_path: Path) -> None:
    announced: list[tuple[str, str, str]] = []
    db, service = _service(tmp_path, announced)
    result = service.import_meeting(
        OWNER,
        tmp_path=_transcript(tmp_path),
        filename="hs-202-02.txt",
        title="HS-202-02 transcript",
        speaker=None,
        tags=[],
        started_at=datetime.now(),
        config=Config(),
        transcriber_factory=lambda cfg: None,
    )
    meeting_id = result["meeting_id"]

    # The worker is a daemon thread; wait for the row to settle.
    import time

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not announced:
        time.sleep(0.1)

    assert announced, "a finished import announced nothing"
    kinds = {kind for kind, _, _ in announced}
    assert "meeting" in kinds, announced
    assert any(obj_id == meeting_id for _, obj_id, _ in announced), announced
    reset_database()


def test_a_refused_import_announces_it_too(tmp_path: Path) -> None:
    """A failed import changes the row the owner is looking at as much as
    a successful one; silence would strand the same face."""
    announced: list[tuple[str, str, str]] = []
    db, service = _service(tmp_path, announced)
    broken = tmp_path / "broken.wav"
    broken.write_bytes(b"not audio")

    def _explode(cfg: Any) -> Any:
        raise RuntimeError("no transcriber here")

    result = service.import_meeting(
        OWNER,
        tmp_path=broken,
        filename="broken.wav",
        title="broken",
        speaker=None,
        tags=[],
        started_at=datetime.now(),
        config=Config(),
        transcriber_factory=_explode,
    )
    import time

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not announced:
        time.sleep(0.1)

    assert announced, "a refused import announced nothing"
    assert any(obj_id == result["meeting_id"] for _, obj_id, _ in announced)
    reset_database()
