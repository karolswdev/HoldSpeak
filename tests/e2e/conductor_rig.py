"""The Conductor rig (PHILO-14 C4), lifted verbatim from
`test_philo14_c4_conductor_glass.py` (the test diet, 2026-10-11): that file
is parked and its successors read the same seed. Seeded as the Conductor F2
seed does, through the product's producers: three action items on a
meeting, two hook-reported sessions (Claude Code asks, Codex works) and three
launches on the ledger with their Work attempts (the freeze flag with PR #412
open on its follow-through). No agent runs; nothing leaves the machine.

Importers: the Conductor glass files and `tests/integration/test_desk_agents_wire.py`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

QUESTION = "The runbook needs a rollback owner. Jordan or Avery?"
TOKEN = "p14-c4-conductor"


def _seed(home: Path) -> None:
    import holdspeak.agent_context as agent_context_pkg
    from holdspeak.agent_context import event_log, ingest_agent_hook_event
    from holdspeak.db import get_database
    from holdspeak.delivery.factory_launch import LaunchLedger
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db = get_database()
    start = (datetime.now() - timedelta(hours=2)).replace(microsecond=0)
    tasks = ["Write the rollback runbook", "Shard the reconciliation job", "Add the ledger freeze flag"]
    db.meetings.save_meeting(MeetingState(
        id="m-cutover", started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger cutover sync",
        segments=[TranscriptSegment(text="We freeze the ledger on Nov 12.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="We freeze the ledger on Nov 12.", action_items=[{
            "id": f"m-cutover-a{i}", "task": task, "owner": None, "due": None, "status": "pending",
            "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}
            for i, task in enumerate(tasks)]),
        intel_status="completed"))
    with db._connection() as conn:
        ids = {task: str(conn.execute("SELECT id FROM action_items WHERE task=? LIMIT 1", (task,)).fetchone()[0])
               for task in tasks}

    spool = {"state_path": agent_context_pkg.AGENT_CONTEXT_FILE, "events_spool_dir": event_log.default_spool_dir()}
    ingest_agent_hook_event(agent="claude", payload={
        "session_id": "c1a0de00-runbook", "cwd": str(home / "dev" / "payments-ledger-runbook"),
        "hook_event_name": "Notification", "message": QUESTION}, **spool)
    ingest_agent_hook_event(agent="codex", payload={
        "session_id": "c0dex000-recon", "cwd": str(home / "dev" / "payments-ledger-recon"),
        "hook_event_name": "PreToolUse", "tool_name": "Bash"}, **spool)

    launched = datetime.now(timezone.utc) - timedelta(minutes=30)
    iso = launched.isoformat().replace("+00:00", "Z")
    launches = [
        ("launch_c4_runbook", tasks[0], "claude-default", "claude:c1a0de00-runbook", None),
        ("launch_c4_recon", tasks[1], "codex-default", "codex:c0dex000-recon", None),
        ("launch_c4_flag", tasks[2], "claude-default", None, {
            "pr": {"number": 412, "url": "https://github.com/acme/payments-ledger/pull/412", "state": "open"},
            "pr_state": "pr_open"}),
    ]
    ledger = LaunchLedger()
    for launch_id, task, profile, session_key, follow in launches:
        item = ids[task]
        attempt = db.work_attempts.create(
            source_id="src_ledger", worktree_id=f"wt_{launch_id}", project="payments-ledger",
            story_id=f"action-{item}", node_id="this-node", session_id=session_key, target_id=f"tgt_{launch_id}",
            kind="launch", exact=True, claimed_by=f"launch:{profile}", state="working", origin_ref=f"action:{item}")
        record: dict[str, Any] = {
            "launch_schema": 1, "launch_id": launch_id, "state": "launched", "node_id": "this-node",
            "profile_id": profile, "gate": "gated", "branch": f"hs/action-{item}", "session": f"hs-{launch_id}",
            "origin_ref": {"kind": "action", "id": item}, "attempt_id": attempt.attempt_id,
            "launched_at": iso, "control_mode": "normal", "instruction_state": "sent",
        }
        if follow:
            record["follow_through"] = follow
        ledger.record(record)
