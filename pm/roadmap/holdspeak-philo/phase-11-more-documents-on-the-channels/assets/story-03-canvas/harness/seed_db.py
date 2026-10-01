"""PHILO-11-03 canvas seed: the records no HTTP route makes (a recorded
meeting with its stored intelligence, the decision records it produced).

Run ONLY with HOME set to the run's throwaway HOME (shoot.py does this). It
writes through the product's own DB layer (holdspeak.db), the same way the
Phase 11 faces grounding seeded its meeting. The transcript carries a
SENTINEL word: no meeting form may show it (design section 3).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, UTC

assert "philo11-03" in os.environ.get("HOME", ""), "refusing: HOME is not a canvas scratch HOME"

from holdspeak.db import get_database  # noqa: E402
from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment  # noqa: E402
from holdspeak.services.decision_record_service import DecisionRecordService  # noqa: E402

SENTINEL = "TRANSCRIPT-SENTINEL-7Q"


def action(item_id, task, owner=None, status="pending", due=None):
    return {"id": item_id, "task": task, "owner": owner, "due": due, "status": status,
            "review_state": "pending", "source_timestamp": None,
            "created_at": datetime.now().replace(microsecond=0).isoformat()}


def main() -> None:
    db = get_database()
    now = datetime.now().replace(microsecond=0)
    prior = now - timedelta(days=7)
    db.meetings.save_meeting(MeetingState(
        id="m-prior", started_at=prior, ended_at=prior + timedelta(minutes=30), title="Ledger cutover kickoff",
        intel=IntelSnapshot(timestamp=0.0, summary="The team set the cutover scope.", topics=["cutover"],
                            action_items=[action("p1", "Map the old ledger write paths", "Priya", status="done")]),
        intel_status="completed",
    ))
    db.plugins.record_artifact(artifact_id="prior-decisions", meeting_id="m-prior", artifact_type="decisions",
                               title="Decisions", plugin_id="decision_capture",
                               structured_json={"decisions": [{"decision": "Keep the old ledger read-only for 30 days"}]})
    start = now - timedelta(hours=3)
    segs = [
        TranscriptSegment(text=f"Two write paths still hit the old ledger. {SENTINEL}", speaker="Me", start_time=4.0, end_time=9.0),
        TranscriptSegment(text="Then we freeze it on November third and run one more reconciliation.", speaker="Priya", start_time=10.0, end_time=16.0),
        TranscriptSegment(text="I own the rollback plan.", speaker="Priya", start_time=17.0, end_time=19.0),
    ]
    db.meetings.save_meeting(MeetingState(
        id="m-sync", started_at=start, ended_at=start + timedelta(minutes=45), title="Ledger cutover sync", segments=segs,
        intel=IntelSnapshot(
            timestamp=0.0,
            summary=("The team agreed to freeze the old ledger on Nov 3. Finance runs one more reconciliation "
                     "before the freeze. Priya owns the rollback plan."),
            topics=["cutover", "reconciliation"],
            action_items=[action("a1", "Write the rollback plan", "Priya", due="Fri"),
                          action("a2", "Run the last reconciliation", "Marek"),
                          action("a3", "Tell support the freeze date")],
        ),
        intel_status="completed",
    ))
    db.plugins.record_artifact(artifact_id="sync-decisions", meeting_id="m-sync", artifact_type="decisions",
                               title="Decisions", plugin_id="decision_capture",
                               structured_json={"decisions": [
                                   {"decision": "Freeze the old ledger on Nov 3", "rationale": "Two write paths remain"},
                                   {"decision": "Cut over by space, not by region"}]})
    # A meeting with no summary (board C4).
    db.meetings.save_meeting(MeetingState(
        id="m-bare", started_at=now - timedelta(hours=1), ended_at=now - timedelta(minutes=50), title="Vendor call",
        segments=[TranscriptSegment(text=f"Hello, can you hear me. {SENTINEL}", speaker="Me", start_time=1.0, end_time=3.0)],
        intel_status="disabled",
    ))

    # A meeting whose summary is longer than the Slack limit (board T1): a real
    # stored record, 13 paragraphs of the offsite's notes.
    para = ("Finance walked through every open reconciliation break by ledger space, the owner of each break, "
            "and the date it must close before the freeze. ")
    long_summary = "\n\n".join(f"Space {n}: " + para * 22 for n in range(1, 14))
    db.meetings.save_meeting(MeetingState(
        id="m-offsite", started_at=now - timedelta(days=1), ended_at=now - timedelta(days=1) + timedelta(hours=6),
        title="Cutover planning offsite", intel=IntelSnapshot(timestamp=0.0, summary=long_summary, topics=["cutover"]),
        intel_status="completed",
    ))
    svc = DecisionRecordService(db)
    rec = svc.create(None, decision_text="Freeze the old ledger on Nov 3",
                     rationale="The cutover rehearsal found two write paths into the old ledger.",
                     alternatives="Freeze by region; freeze after the quarter close.",
                     owner="Priya", review_date=(now + timedelta(days=14)).date().isoformat(),
                     source_type="meeting", source_id="m-sync")
    svc._add_sources(rec["id"], (("meeting", "m-sync"),))
    rec2 = svc.create(None, decision_text="Finance runs one more reconciliation before the freeze",
                      rationale="The last run found 3 unmatched entries.", owner="Marek",
                      source_type="meeting", source_id="m-sync")
    svc._add_sources(rec2["id"], (("meeting", "m-sync"),))
    # rec2 came from a confirmed meeting proposal: the Room labels it source="meeting" (MTG).
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO follow_through_proposals (id, meeting_id, kind, text, owner_hint, source_plugin, fingerprint,
                   state, original_text, decision_record_id, decided_at)
               VALUES (?, ?, 'decision', ?, 'Marek', 'decision_capture', ?, 'confirmed', ?, ?, ?)""",
            ("ftp-1", "m-sync", rec2["decision_text"], "fp-1", rec2["decision_text"], rec2["id"],
             datetime.now(UTC).isoformat()))
    print(json.dumps({"record": rec["id"], "record_mtg": rec2["id"], "meetings": ["m-sync", "m-bare", "m-prior", "m-offsite"], "long_summary_chars": len(long_summary)}))


if __name__ == "__main__":
    sys.exit(main())
