"""The canvas week (assets/story-11-canvas/harness/seed_db.py), minted by the
real producers: three projects, two decisions, a note, three meetings, four
people with their requests, a brief, the Team updates folder.

Was `_seed` in tests/e2e/test_philo13_11_chair_glass.py (the test diet,
push 2, 2026-10-12, moved it here so the Chair glass and the files that
share its week import a rig, not a test module).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path


def _seed(home: Path) -> None:
    """The canvas week (assets/story-11-canvas/harness/seed_db.py), minted by
    the real producers into this rig's database (the singleton _boot reset)."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.people import production_people_store
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.services.people_service import PeopleService
    from holdspeak.services.primitive_service import PrimitiveService

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "karol")
    now = datetime.now()
    for pid, name, desc in [
        ("p-ledger", "Payments ledger cutover", "Move settlement to the new ledger by Nov 5."),
        ("p-obs", "Platform observability", "One tracing stack for all services."),
        ("p-hiring", "Staff hiring loop", "Two senior hires before Q1."),
    ]:
        db.projects.create_project(project_id=pid, name=name, description=desc, keywords=name.lower().split()[:3])
    prim = PrimitiveService(db)
    prim.create_decision(owner, decision_id="d-freeze", title="Freeze the old ledger on Nov 5", status="accepted",
                         decision_markdown="Freeze writes to the old ledger on Nov 5.")
    prim.create_decision(owner, decision_id="d-otel", title="Adopt OpenTelemetry for all services",
                         status="proposed", decision_markdown="Use the OTel SDK in every service.")
    prim.create_note(owner, note_id="n-1", title="Ledger cutover risks",
                     body_markdown="- reconciliation job slow\n- rollback plan owner: Jordan", tags=["week40"])
    for mid, title, hours_ago, pid, summary, topics, action, status in [
        ("m-standup", "Ledger cutover sync", 2, "p-ledger",
         "Dual-write is stable. The team agreed to freeze the old ledger on Nov 5. Jordan owns the rollback plan.",
         ["cutover", "rollback"], "Write the rollback runbook", "completed"),
        ("m-arch", "Architecture review: tracing", 26, "p-obs",
         "Reviewed the tracing options. OpenTelemetry chosen. Sam will pilot it in the billing service.",
         ["tracing", "otel"], "Pilot OTel in billing", "completed"),
        # a stored summary with the run switch OFF: SUMMARY STORED, never Run summary
        ("m-avery", "1:1 Avery", 50, None,
         "Avery wants to lead the ledger cutover. Promo packet due in two weeks.",
         ["career", "promo"], "Review Avery's promo packet", "disabled"),
    ]:
        start = (now - timedelta(hours=hours_ago)).replace(microsecond=0)
        db.meetings.save_meeting(MeetingState(
            id=mid, started_at=start, ended_at=start + timedelta(minutes=30), title=title,
            segments=[TranscriptSegment(text=summary.split(".")[0] + ".", speaker="Me", start_time=1.0, end_time=4.0),
                      TranscriptSegment(text="Agreed.", speaker="Avery", start_time=4.0, end_time=5.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=topics, summary=summary, action_items=[{
                "id": f"{mid}-a1", "task": action, "owner": None, "due": None, "status": "pending",
                "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}]),
            intel_status=status))
        if pid:
            db.projects.associate_meeting_project(meeting_id=mid, project_id=pid, source="manual", confidence=1.0)
    store = production_people_store()
    store.initialize()
    people = PeopleService(store)
    for name, kind in [("Avery Chen", "direct_report"), ("Jordan Patel", "direct_report"),
                       ("Sam Rivera", "direct_report"), ("Priya Nair", "peer")]:
        rel = people.create_relationship(owner, {"display_name": name, "relationship_kind": kind,
                                                 "role_context": "Engineer", "cadence": "weekly"})
        if kind == "direct_report":
            req = people.create_request(owner, rel["id"], {"body": f"{name.split()[0]}: send the status by Thursday"})
            people.accept_request(owner, req["id"])
    MondayBriefService(db).generate(owner, now=now)
    (home / "Documents" / "HoldSpeak" / "Team updates").mkdir(parents=True, exist_ok=True)
