"""Conductor canvas seed (copied from the story-15 canvas seed; adds two hook-reported agent sessions). PHILO-13-15/17 canvas seed (C1's seed, ../../story-11-canvas/harness/seed_db.py, plus a meeting with no summary and an accepted artifact). PHILO-13-11 canvas seed (the Phase 13 grounding seed, docs/internal/philo/phase-13/grounding/probes/faces-surfaces-seed.py.txt, with Priya as the peer).

Seed a meaningful week for a Senior Software Architect with three reports.

Runs with HOME=<throwaway> BEFORE the populated hub boots. Writes only the
throwaway DB under that HOME, through the real producers (the
scripts/philo11_send_job.py `mint` pattern). Never renders, prepares or sends.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path(os.environ["HOME"]).resolve()
assert not str(HOME).startswith("/Users/karol") and "kcanvas" in str(HOME), f"refusing: HOME is not a canvas scratch HOME: {HOME}"

from holdspeak.db.core import Database  # noqa: E402
from holdspeak.db.decisions import backfill_decisions  # noqa: E402
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment  # noqa: E402
from holdspeak.people import production_people_store  # noqa: E402
from holdspeak.principals import Principal, PrincipalKind  # noqa: E402
from holdspeak.services.decision_record_service import DecisionRecordService  # noqa: E402
from holdspeak.services.monday_brief_service import MondayBriefService  # noqa: E402
from holdspeak.services.people_service import PeopleService  # noqa: E402
from holdspeak.services.primitive_service import PrimitiveService  # noqa: E402
from holdspeak.services.project_service import ProjectService  # noqa: E402
from holdspeak.services.project_update_service import ProjectUpdateService  # noqa: E402

now = datetime.now()
path = HOME / ".local/share/holdspeak/holdspeak.db"
path.parent.mkdir(parents=True, exist_ok=True)
db = Database(path)
owner = Principal(PrincipalKind.OWNER, "karol")
out: dict = {"db": str(path)}

PROJECTS = [
    ("p-ledger", "Payments ledger cutover", "Move settlement to the new ledger by Nov 5."),
    ("p-obs", "Platform observability", "One tracing stack for all services."),
    ("p-hiring", "Staff hiring loop", "Two senior hires before Q1."),
]
for pid, name, desc in PROJECTS:
    db.projects.create_project(project_id=pid, name=name, description=desc,
                               keywords=name.lower().split()[:3])
db.project_updates.insert_update(
    update_id="upd-ledger-1", project_id="p-ledger", project_revision=1,
    body_md="## Week 40\n\n- Dual-write is live in staging.\n- Cutover date holds: Nov 5.\n- Risk: reconciliation job is slow on month-end data.\n")
ProjectUpdateService(db, project_service=ProjectService(db)).publish_update(owner, "upd-ledger-1")
db.project_updates.insert_update(
    update_id="upd-obs-1", project_id="p-obs", project_revision=1,
    body_md="## Draft\n\n- Tracing in 4 of 9 services.\n")
out["projects"] = [p[0] for p in PROJECTS]

prim = PrimitiveService(db)
prim.create_decision(owner, decision_id="d-freeze", title="Freeze the old ledger on Nov 5", status="accepted",
                     deciders=["karol"], context_markdown="Dual-write is stable.",
                     decision_markdown="Freeze writes to the old ledger on Nov 5.",
                     alternatives=["Freeze on Nov 12"], consequences_markdown="Month-end runs on the new ledger.")
prim.create_decision(owner, decision_id="d-otel", title="Adopt OpenTelemetry for all services", status="proposed",
                     decision_markdown="Use the OTel SDK in every service.")
for nid, title, body in [
    ("n-1", "Ledger cutover risks", "- reconciliation job slow\n- rollback plan owner: Jordan"),
    ("n-2", "Questions for Avery 1:1", "- promo packet\n- on-call load"),
    ("n-3", "Architecture review notes", "Event sourcing for the ledger: yes. CQRS: not yet."),
]:
    prim.create_note(owner, note_id=nid, title=title, body_markdown=body, tags=["week40"])

MEETINGS = [
    ("m-standup", "Ledger cutover sync", 2, 30, "p-ledger",
     "Dual-write is stable. The team agreed to freeze the old ledger on Nov 5. Jordan owns the rollback plan.",
     ["cutover", "rollback"], "Write the rollback runbook", ["Freeze the old ledger on Nov 5"]),
    ("m-arch", "Architecture review: tracing", 26, 60, "p-obs",
     "Reviewed the tracing options. OpenTelemetry chosen. Sam will pilot it in the billing service.",
     ["tracing", "otel"], "Pilot OTel in billing", ["Adopt OpenTelemetry"]),
    ("m-avery", "1:1 Avery", 50, 30, None,
     "Avery wants to lead the ledger cutover. Promo packet due in two weeks.",
     ["career", "promo"], "Review Avery's promo packet", []),
    ("m-hiring", "Hiring debrief: staff engineer", 74, 45, "p-hiring",
     "Strong system design. Weak on incident handling. Decision: second interview on operations.",
     ["hiring"], "Schedule the ops interview", ["Run a second ops interview"]),
]
for mid, title, hours_ago, minutes, pid, summary, topics, action, decisions in MEETINGS:
    start = (now - timedelta(hours=hours_ago)).replace(microsecond=0)
    m = MeetingState(
        id=mid, started_at=start, ended_at=start + timedelta(minutes=minutes), title=title,
        segments=[TranscriptSegment(text=summary.split(".")[0] + ".", speaker="Me", start_time=1.0, end_time=4.0),
                  TranscriptSegment(text="Agreed.", speaker="Avery", start_time=4.0, end_time=5.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=topics, summary=summary, action_items=[{
            "id": f"{mid}-a1", "task": action, "owner": None, "due": None, "status": "pending",
            "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}]),
        intel_status="completed")
    db.meetings.save_meeting(m)
    if pid:
        db.projects.associate_meeting_project(meeting_id=mid, project_id=pid, source="manual", confidence=1.0)
    if decisions:
        db.plugins.record_artifact(artifact_id=f"{mid}-decisions", meeting_id=mid, artifact_type="decisions",
                                   title="Meeting decisions", structured_json={"decisions": [{"decision": d, "rationale": "Agreed in the meeting."} for d in decisions]},
                                   plugin_id="fs13-seed")
    db.plugins.record_artifact(artifact_id=f"{mid}-notes", meeting_id=mid, artifact_type="notes",
                               title=f"{title}: notes", body_markdown=summary, plugin_id="fs13-seed",
                               status="draft")
with db._connection() as conn:
    backfill_decisions(conn)
lifecycle = db.decisions.list(meeting_id="m-standup")[0]
rec = DecisionRecordService(db).create_from_meeting(owner, lifecycle.id)
DecisionRecordService(db).update_record(owner, rec["id"], {"owner": "Jordan Patel",
                                                           "review_date": (now.date() + timedelta(days=14)).isoformat()})
out["meetings"] = [m[0] for m in MEETINGS]

# J5: voice captures in the dictation journal
for t in ["Remember to ask Sam about the billing trace sampling rate",
          "Idea: run the ledger reconciliation in parallel shards",
          "Follow up with Jordan on the rollback runbook by Friday"]:
    db.dictation_journal.record(source="dictation", transcript=t, final_text=t, intent="note", total_ms=820.0)

people_out = []
store = production_people_store()
store.initialize()
people = PeopleService(store)
REPORTS = [("Avery Chen", "direct_report", "Senior engineer, ledger"),
           ("Jordan Patel", "direct_report", "Engineer, payments"),
           ("Sam Rivera", "direct_report", "Engineer, platform"),
           ("Priya Nair", "peer", "Director, product")]
for name, kind, role in REPORTS:
    rel = people.create_relationship(owner, {"display_name": name, "relationship_kind": kind,
                                             "role_context": role, "cadence": "weekly"})
    people_out.append(rel["id"])
    if kind == "direct_report":
        people.create_one_on_one(owner, rel["id"], {"agenda": "Ledger cutover; growth", "private_prep": "Ask about load."})
        req = people.create_request(owner, rel["id"], {"body": f"{name.split()[0]}: send the status by Thursday"})
        people.accept_request(owner, req["id"])
        people.create_note(owner, rel["id"], {"topic": "context", "body": f"{name.split()[0]} prefers async updates."})
        try:
            people.link_project(owner, rel["id"], "p-ledger")
        except Exception as exc:  # noqa: BLE001
            out.setdefault("link_errors", []).append(repr(exc)[:200])
out["people"] = people_out

# C5 additions: a meeting with NO summary (Send to is withheld) and an accepted artifact (its own well).
db.meetings.save_meeting(MeetingState(
    id="m-bare", started_at=(now - timedelta(hours=3)).replace(microsecond=0),
    ended_at=(now - timedelta(hours=2, minutes=40)).replace(microsecond=0), title="Vendor call",
    segments=[TranscriptSegment(text="Hello, can you hear me.", speaker="Me", start_time=1.0, end_time=3.0)],
    intel_status="disabled"))
db.plugins.record_artifact(artifact_id="art-cutover-reqs", meeting_id="m-standup", artifact_type="requirements",
                           title="Cutover requirements",
                           body_markdown=("### Cutover requirements\n\nThe new ledger takes every write from Nov 5.\n\n"
                                          "- Freeze the old ledger on Nov 5.\n- Finance runs one more reconciliation before the freeze.\n"
                                          "- Rollback window closes Nov 12.\n"),
                           status="accepted", plugin_id="requirements_extractor", confidence=0.9)
out["artifact"] = "art-cutover-reqs"


# Conductor additions: two hook-reported agent sessions, through the product's own ingest
# (holdspeak.agent_context.ingest_agent_hook_event), each in its own git worktree under the scratch HOME.
import subprocess  # noqa: E402
from holdspeak.agent_context import ingest_agent_hook_event  # noqa: E402

def _repo(name: str) -> str:
    d = HOME / "dev" / name
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    return str(d)

claude_cwd = _repo("payments-ledger-runbook")
codex_cwd = _repo("payments-ledger-recon")
for ev in [{"hook_event_name": "SessionStart"},
           {"hook_event_name": "UserPromptSubmit", "prompt": "Write the rollback runbook for the Nov 5 ledger freeze."},
           {"hook_event_name": "PreToolUse", "tool_name": "Write"},
           {"hook_event_name": "Notification",
            "message": "The runbook needs a rollback owner. Jordan or Avery?"}]:
    ingest_agent_hook_event(agent="claude", payload={"session_id": "c1a0de00-runbook", "cwd": claude_cwd, **ev})
for ev in [{"hook_event_name": "SessionStart"},
           {"hook_event_name": "UserPromptSubmit", "prompt": "Shard the reconciliation job by account range."},
           {"hook_event_name": "PreToolUse", "tool_name": "Bash"}]:
    ingest_agent_hook_event(agent="codex", payload={"session_id": "c0dex000-recon", "cwd": codex_cwd, **ev})
out["agent_sessions"] = ["claude:c1a0de00-runbook", "codex:c0dex000-recon"]

brief = MondayBriefService(db).generate(owner, now=now)
out["brief"] = brief.id
db.close()
print(json.dumps(out))
