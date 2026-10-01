"""PHILO-12-02 canvas seed: the records no HTTP route makes (a recorded meeting
with its stored intelligence, a meeting with no summary, a synthesized
artifact with its lineage footer).

Run ONLY with HOME set to the run's throwaway HOME (shoot.py does this). It
writes through the product's own DB layer (holdspeak.db), the Phase 11 method.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta

assert "philo12-02" in os.environ.get("HOME", ""), "refusing: HOME is not a canvas scratch HOME"

from holdspeak.db import get_database  # noqa: E402
from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment  # noqa: E402


def main() -> None:
    db = get_database()
    now = datetime.now().replace(microsecond=0)
    start = now - timedelta(hours=3)
    db.meetings.save_meeting(MeetingState(
        id="m-sync", started_at=start, ended_at=start + timedelta(minutes=45), title="Ledger cutover sync",
        segments=[TranscriptSegment(text="Two write paths still hit the old ledger.", speaker="Me", start_time=4.0, end_time=9.0)],
        intel=IntelSnapshot(
            timestamp=0.0,
            summary=("The team agreed to freeze the old ledger on Nov 3. Finance runs one more reconciliation "
                     "before the freeze. Priya owns the rollback plan."),
            topics=["cutover", "reconciliation"],
            action_items=[{"id": "a1", "task": "Write the rollback plan", "owner": "Priya", "due": "Fri", "status": "pending",
                           "review_state": "pending", "source_timestamp": None, "created_at": now.isoformat()}],
        ),
        intel_status="completed",
    ))
    db.meetings.save_meeting(MeetingState(
        id="m-bare", started_at=now - timedelta(hours=1), ended_at=now - timedelta(minutes=50), title="Vendor call",
        segments=[TranscriptSegment(text="Hello, can you hear me.", speaker="Me", start_time=1.0, end_time=3.0)],
        intel_status="disabled",
    ))
    # A synthesized artifact as meeting synthesis writes it: the body ends with the
    # synthesis-owned source footer (holdspeak/plugins/synthesis.py _compose_body).
    body = ("### Cutover requirements\n\nThe new ledger takes every write from Nov 3.\n\n"
            "- Freeze the old ledger on Nov 3.\n- Finance runs one more reconciliation before the freeze.\n"
            "- Rollback window closes Nov 10.\n\n"
            "- Source windows: win-7f3a2c\n- Source plugin runs: run-91bd04")
    db.plugins.record_artifact(artifact_id="art-cutover-reqs", meeting_id="m-sync", artifact_type="requirements",
                               title="Cutover requirements", body_markdown=body, status="accepted",
                               plugin_id="requirements_extractor", confidence=0.9)
    print(json.dumps({"meetings": ["m-sync", "m-bare"], "artifact": "art-cutover-reqs"}))


if __name__ == "__main__":
    sys.exit(main())
