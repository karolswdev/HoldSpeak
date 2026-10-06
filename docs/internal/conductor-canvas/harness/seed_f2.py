"""Conductor F2 built proof: the records K2 and K4 write, for the BUILT faces (no shim).

Runs with HOME=<the canvas scratch HOME> and TMUX_TMPDIR=<scratch> AFTER the hub boots (seed_db.py
already wrote the Project, the runbook action item and the two hook-reported sessions). Writes:

- two more open action items on the cutover meeting, so the Room has three OPEN HERE rows to
  hand (main's Room rows hold no GitHub issue an agent can take: `agent_brief.BRIEF_KINDS`);
- one tmux server of its own (TMUX_TMPDIR), one `cat` pane per session, reported on each session
  through the product's hook ingest (so a steer has a real pane to land in; nothing else runs);
- three Hand to agent launches in the launch ledger (`factory_launch.LaunchLedger`) with
  `origin_ref`, each with its Work attempt (`db.work_attempts`, `kind=launch`) bound to its
  session: the runbook to Claude Code (waiting), the reconciliation job to Codex (working), the
  freeze flag to Claude Code with PR #412 open (K4's `follow_through.pr`).

`merge` (argv[1]) is the K6 step: PR #413 merged on the runbook launch, its follow-through closed,
the evidence kept (`follow_through.evidence`), and the action item completed through the product
(`FollowThroughService.complete(..., "done")`, the K4 close). Prints the ids as JSON.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
HOME = Path(os.environ["HOME"]).resolve()
assert "kcanvas" in str(HOME), f"refusing: HOME is not a canvas scratch HOME: {HOME}"
assert "kcanvas-tmux-" in os.environ.get("TMUX_TMPDIR", ""), "refusing: tmux must run on the scratch socket"

from holdspeak.agent_context import ingest_agent_hook_event  # noqa: E402
from holdspeak.db.core import Database  # noqa: E402
from holdspeak.delivery.factory_launch import LaunchLedger  # noqa: E402

db = Database(HOME / ".local/share/holdspeak/holdspeak.db")
ledger = LaunchLedger(HOME / ".holdspeak" / "agent_launches.json")
iso = lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  # noqa: E731


def action_id(task: str) -> str:
    with db._connection() as conn:
        row = conn.execute("SELECT id FROM action_items WHERE task=? ORDER BY rowid LIMIT 1", (task,)).fetchone()
    assert row, f"no action item {task!r}"
    return str(row[0])


if len(sys.argv) > 1 and sys.argv[1] == "merge":
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.follow_through_service import FollowThroughService

    runbook = action_id("Write the rollback runbook")
    url = "https://github.com/acme/payments-ledger/pull/413"
    evidence = {"pr_url": url, "merged_sha": "4f1c2d9", "merged_at": iso(), "attempt_id": "", "launch_id": "launch_f2_runbook"}
    rec = ledger.get("launch_f2_runbook")
    evidence["attempt_id"] = str(rec.get("attempt_id") or "")
    FollowThroughService(db).complete(Principal(PrincipalKind.OWNER, "karol"), runbook, "done", {"evidence": evidence})
    ledger.update("launch_f2_runbook", follow_through={
        "pr_state": "pr_merged", "pr": {"number": 413, "url": url, "state": "merged", "review_decision": "APPROVED"},
        "close": "closed", "evidence": evidence,
        "cleanup": {"session": "killed", "worktree": "worktree_removed", "attempts": "reconciled"}, "done": True,
    })
    print(json.dumps({"merged": runbook}))
    sys.exit(0)

# 1. two more open commitments on the cutover meeting.
with db._connection() as conn:
    for aid, task in [("m-standup-a2", "Shard the reconciliation job"), ("m-standup-a3", "Add the ledger freeze flag")]:
        conn.execute("INSERT OR IGNORE INTO action_items (id, meeting_id, task, owner, status) VALUES (?, 'm-standup', ?, NULL, 'pending')",
                     (aid, task))

# 2. a tmux server on the scratch socket, one cat pane per session.
def pane(name: str) -> str:
    subprocess.run(["tmux", "new-session", "-d", "-s", name, "-x", "160", "-y", "40", "cat"], check=True)
    return subprocess.run(["tmux", "display-message", "-p", "-t", name, "#{pane_id}"], check=True,
                          capture_output=True, text=True).stdout.strip()

claude_pane, codex_pane = pane("hs-runbook"), pane("hs-recon")
claude_cwd = str(HOME / "dev" / "payments-ledger-runbook")
codex_cwd = str(HOME / "dev" / "payments-ledger-recon")
ingest_agent_hook_event(agent="claude", payload={
    "session_id": "c1a0de00-runbook", "cwd": claude_cwd, "hook_event_name": "Notification", "tmux_pane": claude_pane,
    "message": "The runbook needs a rollback owner. Jordan or Avery?"})
ingest_agent_hook_event(agent="codex", payload={
    "session_id": "c0dex000-recon", "cwd": codex_cwd, "hook_event_name": "PreToolUse", "tool_name": "Bash", "tmux_pane": codex_pane})

# 3. the launches (K2) with their attempts, and one PR the Heartbeat follows (K4).
ids = {"runbook": action_id("Write the rollback runbook"), "recon": action_id("Shard the reconciliation job"),
       "flag": action_id("Add the ledger freeze flag")}
LAUNCHES = [
    ("launch_f2_runbook", "runbook", "claude-default", "claude:c1a0de00-runbook", "hs-runbook", None),
    ("launch_f2_recon", "recon", "codex-default", "codex:c0dex000-recon", "hs-recon", None),
    ("launch_f2_flag", "flag", "claude-default", None, "hs-flag",
     {"pr_state": "pr_open", "pr": {"number": 412, "url": "https://github.com/acme/payments-ledger/pull/412",
                                    "state": "open", "review_decision": None}}),
]
for launch_id, key, profile, session_key, tmux_name, follow in LAUNCHES:
    item = ids[key]
    attempt = db.work_attempts.create(
        source_id="src_payments_ledger", worktree_id=f"wt_{key}", project="p-ledger", story_id=f"action-{item}",
        node_id="this-node", session_id=session_key, target_id=None, kind="launch", exact=True,
        claimed_by=f"launch:{profile}", state="working", origin_ref=f"action:{item}")
    record = {
        "launch_schema": 1, "launch_id": launch_id, "state": "launched", "node_id": "this-node",
        "profile_id": profile, "gate": "gated", "source_id": "src_payments_ledger", "worktree_id": f"wt_{key}",
        "story_ref": {"project": "p-ledger", "story_id": f"action-{item}"},
        "origin_ref": {"kind": "action", "id": item}, "session": tmux_name, "attempt_id": attempt.attempt_id,
        "launched_at": iso(),
    }
    if follow:
        record["follow_through"] = follow
    ledger.record(record)
print(json.dumps({"actions": ids, "panes": [claude_pane, codex_pane]}))
