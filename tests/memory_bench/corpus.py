"""The fixed memory benchmark corpus (docs/internal/MEMORY-DESIGN.md §7).

Every source is written through the product's own producer: the note,
artifact, desk-decision, meeting, thread and project repositories the routes
and services call.  No row is inserted by hand.  Two projects (``atlas``,
``harbor``) and a few desk-wide sources, so project isolation is in the
benchmark.

The text here is the fixture key: ``vectors.npz`` holds one real-model vector
per chunk text and per question.  Change a text and you must run
``scripts/memory_bench_vectors.py`` again.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from holdspeak.meeting_session.models import MeetingState, TranscriptSegment

ATLAS = "atlas"
HARBOR = "harbor"

# (id, project, title, body)
NOTES = [
    ("n-cutover", ATLAS, "Accounting cutover plan", "The accounting cutover moves to the first week of November. Dana owns the runbook and the rollback steps."),
    ("n-vendor", ATLAS, "Northwind contract", "The vendor contract with Northwind renews in January at the same price. Legal wants a ninety day exit clause."),
    ("n-backup", ATLAS, "Backup schedule", "Database backups now run every six hours. Restore drills happen on the first Monday of each month."),
    ("n-latency", ATLAS, "Latency regression", "Report generation got slower after the index change. P95 went from two seconds to nine."),
    ("n-budget", None, "Budget for next year", "The budget stays flat. Travel is cut by a third and the tooling line grows."),
    ("n-hiring", None, "Hiring plan", "We agreed to hire two backend engineers and one designer for the platform team before spring."),
    ("n-offsite", None, "Offsite", "The team offsite is in Lisbon in March. Priya books the venue."),
    ("n-oncall", None, "On-call rotation", "The platform team takes weekend on-call from October. Handover happens Friday at four."),
    ("n-onboarding", None, "New hire onboarding", "Every new engineer gets a buddy and ships a small fix in the first week."),
    ("n-parking", None, "Office parking", "The garage closes for repairs in February. Use the street lot behind the building."),
    ("n-churn", HARBOR, "Churn review", "Customer churn rose in the third quarter among small accounts. Most cancellations cite missing invoices export."),
    ("n-login", HARBOR, "Login crash", "The mobile release was delayed two weeks because of a crash on the login screen for older Android phones."),
    ("n-pricing", HARBOR, "Pricing experiment", "The annual plan discount test raised conversions by eight percent. We keep the twenty percent discount."),
    ("n-security", HARBOR, "Security review", "The security review of the sign-in flow found a missing rate limit on password reset."),
]

# (id, project, title, body)
ARTIFACTS = [
    ("a-runbook", ATLAS, "Cutover runbook", "Step one: freeze postings in the old ledger.\n\nStep two: export balances.\n\nStep three: reconcile totals before opening the new books."),
    ("a-incident", ATLAS, "Incident report: duplicate payments", "A retry bug sent some supplier payments twice on Tuesday. Finance reversed them the next morning.\n\nWe added an idempotency key."),
    ("a-roadmap", HARBOR, "Harbor roadmap", "Quarter one ships offline mode. Quarter two ships tablet layout.\n\nPush notifications wait until the backend supports topics."),
    ("a-research", HARBOR, "User interviews summary", "Field technicians work in basements with no signal. They want to fill forms without a connection and sync later."),
    ("a-accessibility", HARBOR, "Accessibility audit", "Screen reader labels are missing on the checkout buttons. Colour contrast fails on the grey text."),
    ("a-retro", None, "Sprint retrospective", "Too many meetings on Wednesday. The team wants a no-meeting afternoon and smaller pull requests."),
]

# (id, project, title, started_at, [(speaker, text)])
MEETINGS = [
    ("m-atlas-sync", ATLAS, "Atlas weekly sync", "2026-09-14T10:00:00", [
        ("Me", "Let us start with the migration status."),
        ("Dana", "The trial run of the ledger import finished. Two currency accounts did not match."),
        ("Me", "What is the gap?"),
        ("Dana", "About four hundred euros from rounding. I will fix the conversion table by Thursday."),
        ("Sam", "The auditors asked for read access to the new books."),
    ]),
    ("m-vendor-call", ATLAS, "Northwind call", "2026-09-16T15:00:00", [
        ("Remote", "Northwind offered a ten percent discount for a three year term."),
        ("Me", "We prefer one year with an option to extend."),
        ("Remote", "Then the price stays as it is today."),
    ]),
    ("m-harbor-standup", HARBOR, "Harbor standup", "2026-09-15T09:30:00", [
        ("Lee", "The Android build is red since the SDK upgrade."),
        ("Ana", "I can pair on it after lunch."),
        ("Me", "Is the beta still on for Friday?"),
        ("Lee", "Only if the crash fix lands today."),
    ]),
    ("m-support", HARBOR, "Support review", "2026-09-17T11:00:00", [
        ("Ana", "Tickets about failed photo uploads doubled."),
        ("Lee", "The uploads fail on slow networks because the timeout is ten seconds."),
        ("Me", "Raise it to sixty and add resume."),
    ]),
    ("m-arch", None, "Architecture review", "2026-09-18T14:00:00", [
        ("Me", "Should we split the billing service?"),
        ("Sam", "Not yet. The team is small and the module boundaries are fine."),
        ("Me", "Then we keep one deployable and revisit after the summer."),
    ]),
    ("m-planning", None, "Quarter planning", "2026-09-21T10:00:00", [
        ("Me", "The data warehouse project needs a product owner."),
        ("Priya", "I can take it from May."),
    ]),
]

# (id, project, title, context, decision, consequences)
DESK_DECISIONS = [
    ("dd-single-deploy", None, "Keep billing as one deployable", "Splitting adds operational cost for a small team.", "We keep one service until the team doubles.", "Module boundaries are enforced by lint rules."),
    ("dd-postgres", ATLAS, "Use Postgres for the new ledger", "The old system runs on a mainframe file store.", "The new ledger stores entries in Postgres with monthly partitions.", "Reporting queries move to a read replica."),
    ("dd-freeze", ATLAS, "Code freeze before cutover", "A late change broke the last trial run.", "No deploys to the finance services for five days before the cutover.", "Urgent fixes need two approvals."),
    ("dd-offline", HARBOR, "Offline first for forms", "Technicians lose signal underground.", "Forms save on the device and sync when a connection returns.", "Conflict handling is last write wins per field."),
    ("dd-languages", HARBOR, "Ship Spanish and German first", "Most non-English users are in Spain and Germany.", "The first translations are Spanish and German.", "French waits for the next release."),
]

# (label, project, title, [(role, text)])
THREADS = [
    ("th-export", HARBOR, "Invoices export", [
        ("user", "Customers keep asking for a CSV export of invoices."),
        ("assistant", "A CSV export with date range filters would cover most requests. Add it to the billing page."),
    ]),
    ("th-audit", ATLAS, "Audit trail", [
        ("user", "Every posting needs who changed it and when."),
        ("assistant", "Store an append-only change log next to each ledger entry."),
    ]),
]


def build_corpus(db: Any) -> dict[str, str]:
    """Write the corpus through the real producers.

    Returns ``label -> source ref`` (a thread id is minted by its producer,
    so a question names a label and this map gives the ref).
    """
    refs: dict[str, str] = {}
    db.projects.create_project(project_id=ATLAS, name="Atlas")
    db.projects.create_project(project_id=HARBOR, name="Harbor")

    def link(project: str | None, ref: str) -> None:
        if project:
            db.project_relationships.upsert(project_id=project, resource_ref=ref)

    # The note and desk-decision producers stamp `updated_at` from the wall
    # clock, and recency breaks ties in the ranking.  Pin the clock (not the
    # content) so the corpus is the same on every run.
    from holdspeak.db import primitives

    real_now = primitives._now_iso
    try:
        for index, (note_id, project, title, body) in enumerate(NOTES):
            stamp = f"2026-09-{index + 1:02d}T09:00:00Z"
            primitives._now_iso = lambda stamp=stamp: stamp
            db.notes.upsert(
                note_id=note_id, title=title, body_markdown=body,
                last_modified=stamp, created_at=stamp,
            )
            refs[note_id] = f"note:{note_id}"
            link(project, refs[note_id])
        for index, (decision_id, project, title, context, decision, consequences) in enumerate(DESK_DECISIONS):
            stamp = f"2026-09-{index + 10:02d}T08:00:00Z"
            primitives._now_iso = lambda stamp=stamp: stamp
            db.desk_decisions.upsert(
                decision_id=decision_id, title=title, status="accepted",
                decided_at=f"2026-09-{index + 10:02d}",
                context_markdown=context, decision_markdown=decision,
                consequences_markdown=consequences, created_at=stamp,
            )
            refs[decision_id] = f"desk_decision:{decision_id}"
            link(project, refs[decision_id])
    finally:
        primitives._now_iso = real_now

    for index, (artifact_id, project, title, body) in enumerate(ARTIFACTS):
        db.plugins.record_artifact(
            artifact_id=artifact_id, meeting_id="", artifact_type="memo",
            title=title, body_markdown=body,
            updated_at=f"2026-09-{index + 2:02d}T12:00:00",
        )
        refs[artifact_id] = f"artifact:{artifact_id}"
        link(project, refs[artifact_id])

    for meeting_id, project, title, started_at, turns in MEETINGS:
        started = datetime.fromisoformat(started_at)
        db.meetings.save_meeting(
            MeetingState(
                id=meeting_id,
                started_at=started,
                ended_at=started.replace(minute=started.minute + 20),
                title=title,
                segments=[
                    TranscriptSegment(
                        text=text, speaker=speaker,
                        start_time=float(position * 20), end_time=float(position * 20 + 15),
                    )
                    for position, (speaker, text) in enumerate(turns)
                ],
            )
        )
        refs[meeting_id] = f"meeting:{meeting_id}"
        if project:
            db.projects.associate_meeting_project(
                meeting_id=meeting_id, project_id=project, source="manual", confidence=1.0
            )

    for label, project, title, messages in THREADS:
        thread = db.threads.create_thread(title=title)
        for role, text in messages:
            message = db.threads.append_message(thread.id, role=role)
            db.threads.append_part(message.id, kind="text", text=text)
        refs[label] = f"thread:{thread.id}"
        link(project, refs[label])

    return refs
