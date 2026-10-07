"""Conductor F2 built proof: the records K2 writes, for the BUILT faces (no shim).

Runs with HOME=<the canvas scratch HOME> and TMUX_TMPDIR=<a /tmp/p14tmux-* socket dir> AFTER
the hub boots (seed_db.py already wrote the Project, the runbook action item and the two
hook-reported sessions). It writes what a Hand to agent launch leaves behind, through the
product's producers:

- two more open action items on the cutover meeting, so the Room has three OPEN HERE rows to
  hand (main cannot hand a GitHub issue to an agent: `agent_brief.BRIEF_KINDS`);
- a real clone `~/dev/payments-ledger` (origin github.com/acme/payments-ledger) and one real git
  worktree per launch on its `hs/action-<id>` branch, registered as a Delivery Source
  (`DeliveryRegistry.register`);
- a tmux server on the scratch socket with one `cat` pane per launch, the panes reported on the
  sessions through the product's hook ingest (`ingest_agent_hook_event`);
- three launches in the launch ledger (`LaunchLedger`) with `origin_ref`, their target pane and
  their Work attempts (`db.work_attempts`, `kind=launch`), each BOUND to its session the way
  the rider binds it: the runbook to Claude Code (waiting), the reconciliation job to Codex
  (working), the freeze flag to Claude Code (its PR comes from the follow-through, below).

Nothing here writes a follow-through state. The PRs come from the fake `gh` the rig puts on the
hub's PATH (shoot_built.py: the process boundary), and K4's real observer selects them when the
rig presses the Heartbeat's Run now. `gh <state>` (argv[1] == "gh") rewrites the fake gh's
answer: `open` (PR #412 open on the flag branch) or `merged` (also PR #413 merged on the
runbook branch). Prints its ids as JSON.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True
HOME = Path(os.environ["HOME"]).resolve()
assert "p14canvas" in str(HOME), f"refusing: HOME is not a canvas scratch HOME: {HOME}"
assert "p14tmux-" in os.environ.get("TMUX_TMPDIR", ""), "refusing: tmux must run on the scratch socket"

from holdspeak.agent_context import ingest_agent_hook_event  # noqa: E402
from holdspeak.db.core import Database  # noqa: E402
from holdspeak.delivery import DeliveryRegistry  # noqa: E402
from holdspeak.delivery.factory_launch import LaunchLedger  # noqa: E402

db = Database(HOME / ".local/share/holdspeak/holdspeak.db")
ledger = LaunchLedger(HOME / ".holdspeak" / "agent_launches.json")
GH = HOME / ".f2-gh.json"
CLONE = HOME / "dev" / "payments-ledger"
REPO = "acme/payments-ledger"
iso = lambda t=None: (t or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")  # noqa: E731


def git(*argv: str, cwd: Path = CLONE) -> str:
    return subprocess.run(["git", "-C", str(cwd), *argv], check=True, capture_output=True, text=True).stdout.strip()


def action_id(task: str) -> str:
    with db._connection() as conn:
        row = conn.execute("SELECT id FROM action_items WHERE task=? ORDER BY rowid LIMIT 1", (task,)).fetchone()
    assert row, f"no action item {task!r}"
    return str(row[0])


def pr(number: int, branch: str, state: str, title: str, merged_at: str = "") -> dict:
    head = git("rev-parse", branch)
    return {
        "number": number, "title": title, "url": f"https://github.com/{REPO}/pull/{number}",
        "headRefName": branch, "headRefOid": head, "baseRefName": "main", "baseRefOid": git("rev-parse", "main"),
        "state": state, "isDraft": False, "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        "author": {"login": "karol"}, "reviewDecision": "APPROVED", "mergedAt": merged_at or None,
        "mergeCommit": {"oid": head} if merged_at else None, "isCrossRepository": False,
        "headRepositoryOwner": {"login": "acme"}, "headRepository": {"name": "payments-ledger"},
    }


if len(sys.argv) > 1 and sys.argv[1] == "gh":
    ids = json.loads((HOME / ".f2-ids.json").read_text())
    rows = [pr(412, f"hs/action-{ids['flag']}", "OPEN", "Add the ledger freeze flag")]
    if sys.argv[2] == "merged":
        rows.append(pr(413, f"hs/action-{ids['runbook']}", "MERGED", "Write the rollback runbook", iso()))
    GH.write_text(json.dumps(rows))
    print(json.dumps({"gh": sys.argv[2], "prs": [r["number"] for r in rows]}))
    sys.exit(0)

# 1. two more open commitments on the cutover meeting.
with db._connection() as conn:
    for aid, task in [("m-standup-a2", "Shard the reconciliation job"), ("m-standup-a3", "Add the ledger freeze flag")]:
        conn.execute("INSERT OR IGNORE INTO action_items (id, meeting_id, task, owner, status) VALUES (?, 'm-standup', ?, NULL, 'pending')",
                     (aid, task))
ids = {"runbook": action_id("Write the rollback runbook"), "recon": action_id("Shard the reconciliation job"),
       "flag": action_id("Add the ledger freeze flag")}
(HOME / ".f2-ids.json").write_text(json.dumps(ids))
GH.write_text("[]")

# 2. the clone, one worktree per launch, registered as a Delivery Source.
CLONE.mkdir(parents=True, exist_ok=True)
subprocess.run(["git", "init", "-q", "-b", "main", str(CLONE)], check=True)
git("config", "user.email", "canvas@example.invalid")
git("config", "user.name", "canvas")
git("remote", "add", "origin", f"https://github.com/{REPO}.git")
(CLONE / "README.md").write_text("payments ledger\n")
git("add", "README.md")
git("commit", "-q", "-m", "init")
registry = DeliveryRegistry()
registry.register(str(CLONE), label="payments-ledger")
worktrees: dict[str, tuple[str, str, Path]] = {}
for key, item in ids.items():
    path = HOME / "dev" / "wt" / f"hs-action-{item}"
    path.parent.mkdir(parents=True, exist_ok=True)
    git("worktree", "add", "-q", "-b", f"hs/action-{item}", str(path))
    (path / f"{key}.md").write_text(f"{key}\n")
    git("add", f"{key}.md", cwd=path)
    git("commit", "-q", "-m", key, cwd=path)
    source, wt = registry.register(str(path))
    worktrees[key] = (source.source_id, wt.worktree_id, path)

# 3. one cat pane per launch on the scratch tmux socket, reported on the sessions.
def pane(name: str) -> str:
    subprocess.run(["tmux", "new-session", "-d", "-s", name, "-x", "160", "-y", "40", "cat"], check=True)
    return subprocess.run(["tmux", "display-message", "-p", "-t", name, "#{pane_id}"], check=True,
                          capture_output=True, text=True).stdout.strip()

panes = {"runbook": pane("hs-runbook"), "recon": pane("hs-recon"), "flag": pane("hs-flag")}
ingest_agent_hook_event(agent="claude", payload={
    "session_id": "c1a0de00-runbook", "cwd": str(HOME / "dev" / "payments-ledger-runbook"), "hook_event_name": "Notification",
    "tmux_pane": panes["runbook"], "message": "The runbook needs a rollback owner. Jordan or Avery?"})
ingest_agent_hook_event(agent="codex", payload={
    "session_id": "c0dex000-recon", "cwd": str(HOME / "dev" / "payments-ledger-recon"), "hook_event_name": "PreToolUse",
    "tool_name": "Bash", "tmux_pane": panes["recon"]})

# 4. the launches (K2) with their attempts, bound as the rider binds them.
launched = datetime.now(timezone.utc) - timedelta(minutes=30)
LAUNCHES = [
    ("launch_f2_runbook", "runbook", "claude-default", "claude:c1a0de00-runbook", "hs-runbook"),
    ("launch_f2_recon", "recon", "codex-default", "codex:c0dex000-recon", "hs-recon"),
    ("launch_f2_flag", "flag", "claude-default", None, "hs-flag"),
]
for launch_id, key, profile, session_key, tmux_name in LAUNCHES:
    item = ids[key]
    source_id, worktree_id, _path = worktrees[key]
    attempt = db.work_attempts.create(
        source_id=source_id, worktree_id=worktree_id, project="p-ledger", story_id=f"action-{item}",
        node_id="this-node", session_id=session_key, target_id=f"tgt_{key}", kind="launch", exact=True,
        claimed_by=f"launch:{profile}", state="working", origin_ref=f"action:{item}", now=launched)
    ledger.record({
        "launch_schema": 1, "launch_id": launch_id, "state": "launched", "node_id": "this-node",
        "profile_id": profile, "gate": "gated", "source_id": source_id, "worktree_id": worktree_id,
        "story_ref": {"project": "p-ledger", "story_id": f"action-{item}"},
        "origin_ref": {"kind": "action", "id": item}, "session": tmux_name,
        "target": {"target_id": f"tgt_{key}", "target_generation": 1, "pane_id": panes[key]},
        "attempt_id": attempt.attempt_id,
        "commands": {"worktree_create": f"cmd_wt_{key}", "spawn": f"cmd_spawn_{key}", "instruction": None},
        "launched_at": iso(launched),
    })
print(json.dumps({"actions": ids, "panes": panes}))
