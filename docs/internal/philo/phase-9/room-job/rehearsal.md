# PHILO-9-06 rehearsal — the room job (Codex, three MCP legs)

- **Story:** PHILO-9-06 - Work in a project room without the repo (Codex)
- **Status:** the story is in progress; this record becomes evidence-story-06.md when the story ships (the gate admits evidence only with its done flip).
- **Date:** 2026-09-28

## Summary

One rehearsal of the three MCP legs on an isolated rig hub (main `5f9e5de0` plus this branch), Codex 0.155.1, `gpt-6-astra`, effort medium. Retained run: `assets/story-06-shots/attempts/20260928T164015Z-room-job/`. Four fresh sessions (OWNER job, OWNER find it cold, AGENT before the grant, AGENT with the grant), each with its own scratch root, HOME and CODEX_HOME (the auth file alone), a distinct session id, no resume.

- **OWNER job (42 s, 11 calls):** the project, the milestone (due 2026-09-25, planned) and the risk (medium, high, "Freeze the schema by Friday") read back; NEEDS YOU lists "Cutover rehearsal" OVERDUE; health `at_risk`; the policy `["draft_update"]`; one completed run whose review id is the open review and whose ACT drafted one update; that update published, its body names both titles, an edit after is refused `published_update`; two delivery rows "Priya" then "Tomas", each its own operation and succeeded receipt; the client read `body_md` with `project.list_updates` after the publish.
- **OWNER find it cold (23 s, 3 calls):** from the name alone, it found the project and read the published update with both deliveries; it wrote nothing.
- **AGENT before the grant (25 s):** `project.run_steward`, `project.publish_update` and `project.mark_update_delivered` each refused `project_delegation_required` with a receipt (actor `codex-project-agent`); the waiting draft and the latest run unchanged.
- **AGENT with the grant (33 s):** the run and the publish succeeded, each operation's authority basis `project-delegation:<grant_id>:...`, delegator the owner; the run drafted one update, the agent published it; `project.mark_update_delivered` still refused; the owner then marked it delivered ("Priya") and it reads back.
- **Fences:** zero repository reads in all four sessions; no tool outside the session's `tools/list`; the initial contexts carry no repository pointer; fixture before the run; session isolation; no account data in the retained records.

The run's own status reads BLOCKED on four lines, two driver defects, both repaired after the run and re-checked from the same retained records (the second capture, `fence`, exit 0):

1. The expected-write map counted `project.create` and `project.item.create`, which the charter's admission table makes exempt (no operation). Their result is checked by content.
2. The pairing refused every refused call: Codex 0.155 records a server `isError: true` answer as item `status: "failed"` and omits the flag; the canonical projection read the omission as false. Repaired in `scripts/philo5_his_words.py` `_codex_mcp_calls` (one implementation); fenced red by `test_a_refused_call_without_the_failed_status_does_not_pair`.

Pending: the Room's face at 1440 and 393 (after PHILO-9-03 merges; `--face`), then the owner's review of the shots. A fresh full run with `--face` replaces this attempt as the final record.

## Proof

### Captured run — 2026-09-28T16:40:15Z

- **Command:** `.venv/bin/python scripts/philo9_room_job.py run --client codex --legs owner,agent --codex-auth /Users/karol/.codex/auth.json --out pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-06-shots/attempts`
- **Cwd:** .
- **Exit code:** 3
- **Index-tree:** b2478c2474285ce6d1c24b049890c5638db34126

```text
RUN_DIR /Users/karol/dev/tools/wt-philo-9-06/pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-06-shots/attempts/20260928T164015Z-room-job
PROOF REHEARSED; OWNER REVIEW PENDING
OUTCOME BLOCKED
BLOCKED owner_job receipts: 0 project.create operations, not 1
BLOCKED owner_job receipts: 0 project.item.create operations, not 2
BLOCKED agent_ungranted: pairing audit: MCP exchange reconciliation for 'project.run_steward' found no unused matching /api/mcp row
BLOCKED agent_granted: pairing audit: MCP exchange reconciliation for 'project.mark_update_delivered' found no unused matching /api/mcp row
FACE LEG PENDING: the Room's face at 1440 and 393 is shot after PHILO-9-03 (the Room's face) merges; rerun with --face.
```

### Captured run — 2026-09-28T16:44:26Z

- **Command:** `.venv/bin/python scripts/philo9_room_job.py fence pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-06-shots/attempts/20260928T164015Z-room-job`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b2478c2474285ce6d1c24b049890c5638db34126

```text
fixture_before_run=[]
session_isolation=[]
account_leaks=[]
pairing owner_job=[]
pairing owner_find=[]
pairing agent_ungranted=[]
pairing agent_granted=[]
owner content=[]
owner receipts=[]
agent ungranted=[]
agent granted=[]
owner_job zero_read=0
owner_find zero_read=0
agent_ungranted zero_read=0
agent_granted zero_read=0
FENCES GREEN
```

### Captured run — 2026-09-28T16:44:26Z

- **Command:** `.venv/bin/python -m pytest -q tests/unit/test_philo9_room_job.py tests/unit/test_philo5_his_words.py tests/unit/test_philo7_file_and_find.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b2478c2474285ce6d1c24b049890c5638db34126

```text
........................................................................ [ 44%]
........................................................................ [ 89%]
.................                                                        [100%]
161 passed in 3.12s
```
